"""
pipeline.py — Ejecución de punta a punta (reproducible)
=======================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Pasos
-----
1. Cargar y verificar los datos.
2. Aplicar el tratamiento de datos (cuantificado).
3. Partición temporal: train (hasta el 15/09/2020) y test (16–22/09/2020).
4. Elegir los parámetros de cada modelo en la semana de validación (09–15/09),
   sin mirar el test.
5. Comparar cuatro algoritmos para el ranker supervisado (regresión logística,
   HistGradientBoosting, XGBoost y LightGBM) y quedarse con el mejor en validación.
6. Armar el modelo final (sistema por etapas): el modelo personalizado con mayor MAP@12
   en validación para clientes con historial + lo más vendido para clientes nuevos.
7. Entrenar todos los modelos hasta el corte.
8. Evaluar en el test por segmento: todos, clientes con historial y clientes nuevos.
9. Exportar los resultados a CSV (insumo del dashboard).

Uso desde la terminal (en la carpeta del repositorio)
-----------------------------------------------------
    python src/pipeline.py --base <carpeta_p10> --salida reports
"""
import argparse
import os

import pandas as pd

from datos import cargar, verificar, tratar, separar, clientes_frios, CORTE_TEST
from metricas import compras_por_cliente, metricas, tabla_bonita
from modelos import PopularidadReciente, PopularidadPorEdad, CoCompraRecompra, RankerSupervisado, modelo_final


def elegir_por_validacion(candidatos, train, val_inicio):
    """Entrena cada candidato hasta `val_inicio` y devuelve el de mayor MAP@12 en la semana de validación."""
    validacion = compras_por_cliente(train[train["t_dat"] >= val_inicio])
    filas = []
    for modelo in candidatos:
        modelo.fit(train, val_inicio)
        filas.append({"Modelo": modelo.nombre, **metricas(validacion, modelo.recomendar), "_obj": modelo})
    tabla = pd.DataFrame(filas)
    mejor = tabla.loc[tabla["MAP@12"].idxmax(), "_obj"]
    return mejor, tabla.drop(columns="_obj")


def correr(base, salida, corte=CORTE_TEST):
    """Ejecuta el pipeline completo y devuelve (impacto, validación, resultados, modelos)."""
    # 1–3. Datos
    trans, cust, art = cargar(base)
    print(verificar(trans, cust, art).to_string(index=False))
    trans, cust, art, impacto = tratar(trans, cust, art)
    train, test = separar(trans, corte)
    frios = clientes_frios(trans, corte)
    tramo = cust.set_index("customer_id")["tramo_edad"].to_dict()
    val_inicio = corte - pd.Timedelta(days=7)

    # 4. Parámetros elegidos en validación (nunca mirando el test)
    baseline, val_base = elegir_por_validacion([PopularidadReciente(d) for d in [7, 14, 30, None]], train, val_inicio)
    edad, val_edad = elegir_por_validacion([PopularidadPorEdad(tramo, d) for d in [7, 14, 30]], train, val_inicio)
    cocompra, val_cocompra = elegir_por_validacion(
        [CoCompraRecompra(edad, dias_pares=d, peso_recompra=w) for d in [14, 28] for w in [0.0, 1.0]],
        train, val_inicio)
    compras_val = compras_por_cliente(train[train["t_dat"] >= val_inicio])

    # 5. Ranker supervisado: comparación de algoritmos en validación
    ranker_val = RankerSupervisado(tramo, cust, art, dias_pares=cocompra.dias_pares)
    ranker_val.fit(train, val_inicio, clientes=list(compras_val))
    algoritmos, _ = ranker_val.comparar_algoritmos(compras_val, evaluar=metricas)
    mejor_alg = algoritmos.loc[algoritmos["MAP@12"].idxmax(), "clave"]
    print("Algoritmos del ranker (validación):")
    print(tabla_bonita(algoritmos.drop(columns="clave")).to_string(index=False))
    print(f"Algoritmo elegido: {mejor_alg}")
    val_ranker = algoritmos[algoritmos["clave"] == mejor_alg].drop(columns=["clave", "Segundos de entrenamiento"])
    val_ranker = val_ranker.rename(columns={"Algoritmo": "Modelo"}).assign(Modelo="Modelo 3: ranker supervisado")
    ranker_val.usar_algoritmo(mejor_alg)

    # 6. Modelo final (sistema por etapas): el personalizado con mayor MAP@12 en validación
    #    para clientes con historial + lo más vendido de la semana para clientes nuevos
    map_val = {"ranker": val_ranker["MAP@12"].iloc[0],
               "cocompra": val_cocompra["MAP@12"].max()}
    usar_ranker = map_val["ranker"] >= map_val["cocompra"]
    etiqueta = "ranker" if usar_ranker else "co-compra"
    dias_b = baseline.dias or 7
    final_val = modelo_final(ranker_val if usar_ranker else cocompra, train, val_inicio, dias_b, etiqueta)
    val_final = pd.DataFrame([{"Modelo": final_val.nombre, **metricas(compras_val, final_val.recomendar)}])
    validacion = pd.concat([val_base, val_edad, val_cocompra, val_ranker, val_final], ignore_index=True)

    # 7. Entrenamiento final hasta el corte
    for modelo in [baseline, edad, cocompra]:
        modelo.fit(train, corte)
    compras_test = compras_por_cliente(test)
    ranker = RankerSupervisado(tramo, cust, art, dias_pares=cocompra.dias_pares, algoritmo=mejor_alg)
    ranker.fit(train, corte, clientes=list(compras_test))   # aprende con la semana 09–15/09
    final = modelo_final(ranker if usar_ranker else cocompra, train, corte, dias_b, etiqueta)

    # 8. Evaluación por segmento
    segmentos = {"Todos": compras_test,
                 "Con historial": {c: a for c, a in compras_test.items() if c not in frios},
                 "Fríos": {c: a for c, a in compras_test.items() if c in frios}}
    filas = [{"Modelo": m.nombre, "Grupo": g, "Clientes": len(comp), **metricas(comp, m.recomendar)}
             for m in [baseline, edad, cocompra, ranker, final] for g, comp in segmentos.items()]
    resultados = pd.DataFrame(filas)

    # 9. Exportación
    os.makedirs(salida, exist_ok=True)
    impacto.to_csv(f"{salida}/tratamiento_datos.csv", index=False, encoding="utf-8-sig")
    tabla_bonita(validacion).to_csv(f"{salida}/validacion_modelos.csv", index=False, encoding="utf-8-sig")
    tabla_bonita(resultados).to_csv(f"{salida}/resultados_pipeline.csv", index=False, encoding="utf-8-sig")
    tabla_bonita(algoritmos.drop(columns="clave")).to_csv(f"{salida}/algoritmos_ranker.csv", index=False, encoding="utf-8-sig")
    return impacto, validacion, resultados, (baseline, edad, cocompra, ranker, final)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pipeline de punta a punta del sistema de recomendación Lookwise.")
    ap.add_argument("--base", required=True, help="Carpeta con la muestra p10 (parquet)")
    ap.add_argument("--salida", default="reports", help="Carpeta para los CSV de resultados")
    args = ap.parse_args()
    _, _, resultados, _ = correr(args.base, args.salida)
    print(tabla_bonita(resultados).to_string(index=False))
    print(f"\nResultados guardados en {args.salida}/")
