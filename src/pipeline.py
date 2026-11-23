"""
pipeline.py — Ejecución de punta a punta (reproducible)
=======================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Reproduce, sin notebooks, el modelo final del notebook 06 y sus resultados:

1. Cargar, verificar y tratar los datos (tratamiento cuantificado).
2. Partición temporal: train hasta el 15/09/2020 y test del 16 al 22/09/2020.
   Todas las decisiones se toman con la semana de validación (09–15/09), sin mirar el test.
3. Baseline optimizado: variantes de "lo más vendido" (ventanas y decaimiento), elegidas por
   Recall@12 promedio en 4 semanas de validación.
4. Co-compra + recompra: la variante con mayor Recall@12 en validación.
5. Ranker supervisado: búsqueda de hiperparámetros de regresión logística y Gradient Boosting.
   Se elige Gradient Boosting solo si su mejora de Recall@12 sobre la regresión logística es
   significativa (intervalo del 95% por bootstrap pareado, 1.000 remuestreos).
6. Modelo final por etapas: ranker para clientes con historial y baseline optimizado para nuevos.
7. Evaluación en test por segmento (todos, con historial, nuevos) e intervalos de confianza
   frente a la referencia actual (popularidad de 7 días).
8. Exportación: CSV de resultados en `--salida` y artefactos del modelo en `--modelos`
   (clasificador, configuración y recomendaciones de la semana de test).

Uso desde la terminal (en la carpeta del repositorio)
-----------------------------------------------------
    python src/pipeline.py --base dataset/p10 --salida reports --modelos models

Para probarlo sin tocar los archivos versionados, usar carpetas de salida aparte:
    python src/pipeline.py --base dataset/p10 --salida salida_prueba --modelos salida_prueba
"""
import argparse
import json
import os
import time

import joblib
import numpy as np
import pandas as pd

from datos import cargar, verificar, tratar, separar, clientes_frios, CORTE_TEST
from metricas import compras_por_cliente, metricas, detalle_por_cliente, tabla_bonita
from modelos import PopularidadReciente, CoCompraRecompra, RankerSupervisado, SistemaPorEtapas
from optimizacion import (PopularidadDecaimiento, etiquetas, metricas_clasificacion, umbral_mejor_f1,
                          recomendador_desde_prob, crear, buscar, CONFIGS_LOGREG, CONFIGS_HGB)

NOMBRE_ALG = {"logreg": "Regresión logística", "hgb": "Gradient Boosting"}
REFERENCIA = "Popularidad 7 días (referencia actual)"
FINAL = "Modelo final (por etapas)"


def bootstrap(dif, n=1000, semilla=42):
    """Media e intervalo de confianza del 95% de una diferencia por cliente (remuestreo de clientes)."""
    rng = np.random.default_rng(semilla)
    medias = dif[rng.integers(0, len(dif), size=(n, len(dif)))].mean(axis=1)
    return dif.mean(), *np.percentile(medias, [2.5, 97.5])


def elegir_baseline(train, val_inicio):
    """Variantes de lo más vendido, promediadas en 4 semanas de validación; gana el mayor Recall@12."""
    candidatos = ([PopularidadReciente(d) for d in [1, 3, 7, 14, 30, None]]
                  + [PopularidadDecaimiento(v) for v in [3, 7, 14]])
    semanas = [val_inicio - pd.Timedelta(days=7 * i) for i in range(4)]
    compras_semana = {s: compras_por_cliente(train[(train["t_dat"] >= s) & (train["t_dat"] < s + pd.Timedelta(days=7))])
                      for s in semanas}
    filas = []
    for m in candidatos:
        res = []
        for s in semanas:
            m.fit(train, s)
            res.append(metricas(compras_semana[s], m.recomendar))
        prom = {k: float(np.mean([r[k] for r in res])) for k in res[0]}
        prom["Prendas distintas"] = int(round(prom["Prendas distintas"]))
        filas.append({"Baseline": m.nombre, **prom, "_obj": m})
    tabla = pd.DataFrame(filas).sort_values(["Recall@12", "MAP@12"], ascending=False).reset_index(drop=True)
    return tabla.loc[0, "_obj"], tabla.drop(columns="_obj")


def elegir_cocompra(baseline, train, val_inicio, compras_val):
    """Variantes de co-compra + recompra; gana el mayor Recall@12 en validación."""
    filas = []
    for dp in [14, 28]:
        for w in [0.0, 1.0]:
            m = CoCompraRecompra(baseline, dias_pares=dp, peso_recompra=w).fit(train, val_inicio)
            filas.append({"Modelo": m.nombre, **metricas(compras_val, m.recomendar), "_obj": m})
    tabla = pd.DataFrame(filas).sort_values(["Recall@12", "MAP@12"], ascending=False).reset_index(drop=True)
    return tabla.loc[0, "_obj"]


def elegir_ranker(tramo, cust, art, train, val_inicio, compras_val):
    """Búsqueda de hiperparámetros y regla de decisión: Gradient Boosting solo si mejora significativamente."""
    ranker_val = RankerSupervisado(tramo, cust, art, dias_pares=28, algoritmo="logreg")
    ranker_val.fit(train, val_inicio, clientes=list(compras_val))
    cols = RankerSupervisado.COLUMNAS
    X_tr, y_tr = ranker_val.X_entrenamiento, ranker_val.y_entrenamiento
    tabla_val = ranker_val.tabla_prediccion.reset_index(drop=True)
    y_val = etiquetas(tabla_val, compras_val)

    busqueda = pd.concat([buscar(CONFIGS_LOGREG, X_tr, y_tr, tabla_val, y_val, compras_val, metricas, ranker_val._respaldo, cols),
                          buscar(CONFIGS_HGB, X_tr, y_tr, tabla_val, y_val, compras_val, metricas, ranker_val._respaldo, cols)],
                         ignore_index=True).sort_values(["Recall@12", "MAP@12"], ascending=False).reset_index(drop=True)
    mejor_lr = busqueda[busqueda["algoritmo"] == "logreg"].iloc[0]
    mejor_hgb = busqueda[busqueda["algoritmo"] == "hgb"].iloc[0]

    def recomendador(cfg):
        clf = crear(cfg).fit(X_tr, y_tr)
        prob = clf.predict_proba(tabla_val[cols])[:, 1]
        return prob, recomendador_desde_prob(tabla_val, prob, ranker_val._respaldo)

    prob_lr, rec_lr = recomendador(mejor_lr["_cfg"])
    prob_gb, rec_gb = recomendador(mejor_hgb["_cfg"])
    r_lr = detalle_por_cliente(compras_val, rec_lr)[0]["recall"].to_numpy()
    r_gb = detalle_por_cliente(compras_val, rec_gb)[0]["recall"].to_numpy()
    media, bajo, alto = bootstrap(r_gb - r_lr)
    gb_significativo = bajo > 0
    mejor_cfg = mejor_hgb["_cfg"] if gb_significativo else mejor_lr["_cfg"]
    umbral = umbral_mejor_f1(y_val, prob_gb if gb_significativo else prob_lr)
    print(f"Gradient Boosting - regresión logística (Recall@12, validación): {media * 100:+.2f} puntos "
          f"[IC 95%: {bajo * 100:+.2f}; {alto * 100:+.2f}]")
    print(f"Algoritmo elegido: {NOMBRE_ALG[mejor_cfg['algoritmo']]} | {mejor_hgb['Configuración'] if gb_significativo else mejor_lr['Configuración']}")
    return mejor_cfg, umbral, busqueda


def correr(base, salida, modelos_dir, corte=CORTE_TEST):
    """Ejecuta el pipeline completo y devuelve la tabla de resultados del test."""
    t0 = time.time()
    # 1–2. Datos y partición temporal
    trans, cust, art = cargar(base)
    print(verificar(trans, cust, art).to_string(index=False))
    trans, cust, art, impacto = tratar(trans, cust, art)
    train, test = separar(trans, corte)
    val_inicio = corte - pd.Timedelta(days=7)
    tramo = cust.set_index("customer_id")["tramo_edad"].to_dict()
    compras_val = compras_por_cliente(train[train["t_dat"] >= val_inicio])
    compras_test = compras_por_cliente(test)
    frios = clientes_frios(trans, corte)

    # 3–5. Decisiones en validación
    baseline_opt, val_base = elegir_baseline(train, val_inicio)
    print(f"Baseline elegido: {baseline_opt.nombre}")
    cocompra = elegir_cocompra(baseline_opt, train, val_inicio, compras_val)
    print(f"Co-compra elegida: {cocompra.nombre}")
    mejor_cfg, umbral, busqueda = elegir_ranker(tramo, cust, art, train, val_inicio, compras_val)

    # 6. Modelos entrenados hasta el corte y modelo final por etapas
    base_test = type(baseline_opt)(**({"dias": baseline_opt.dias} if isinstance(baseline_opt, PopularidadReciente)
                                      else {"vida_media": baseline_opt.vida_media})).fit(train, corte)
    base_orig = PopularidadReciente(7).fit(train, corte)
    cc_test = CoCompraRecompra(base_test, dias_pares=cocompra.dias_pares, peso_recompra=cocompra.peso_recompra).fit(train, corte)
    ranker = RankerSupervisado(tramo, cust, art, dias_pares=28, algoritmo="logreg")
    ranker.fit(train, corte, clientes=list(compras_test))
    ranker.clf = crear(mejor_cfg).fit(ranker.X_entrenamiento, ranker.y_entrenamiento)
    ranker.recs = {}
    ranker._ordenar(ranker.tabla_prediccion)
    ranker.nombre = f"Ranker ({NOMBRE_ALG[mejor_cfg['algoritmo']]})"
    final = SistemaPorEtapas(ranker, base_test, set(train["customer_id"].unique()), "ranker")

    # 7. Evaluación en test por segmento e intervalos de confianza
    segmentos = {"Todos": compras_test,
                 "Con historial": {c: a for c, a in compras_test.items() if c not in frios},
                 "Nuevos": {c: a for c, a in compras_test.items() if c in frios}}
    modelos_test = [(REFERENCIA, base_orig), ("Baseline optimizado", base_test), ("Co-compra + recompra", cc_test),
                    (ranker.nombre, ranker), (FINAL, final)]
    res_test = pd.DataFrame([{"Modelo": n, "Grupo": g, "Clientes": len(comp), **metricas(comp, m.recomendar)}
                             for n, m in modelos_test for g, comp in segmentos.items()])
    piv = res_test.pivot_table(index="Modelo", columns="Grupo", values="Recall@12", sort=False) * 100
    filas_ic = []
    for g in ["Con historial", "Nuevos"]:
        comp = segmentos[g]
        dif = (detalle_por_cliente(comp, final.recomendar)[0]["recall"].to_numpy()
               - detalle_por_cliente(comp, base_orig.recomendar)[0]["recall"].to_numpy())
        media, bajo, alto = bootstrap(dif)
        filas_ic.append({"Segmento": g, "Clientes": len(comp), "Diferencia Recall@12 (puntos)": round(media * 100, 2),
                         "IC 95% inferior": round(bajo * 100, 2), "IC 95% superior": round(alto * 100, 2),
                         "Conclusión": "Mejora significativa" if bajo > 0 else ("Empeora" if alto < 0 else "Sin diferencia significativa")})
    ic = pd.DataFrame(filas_ic)
    y_test = etiquetas(ranker.tabla_prediccion, compras_test)
    prob_test = ranker.clf.predict_proba(ranker.tabla_prediccion[RankerSupervisado.COLUMNAS])[:, 1]
    clf_test = pd.DataFrame([{"Umbral": "0,5", **metricas_clasificacion(y_test, prob_test, 0.5)},
                             {"Umbral": f"{umbral:.3f} (mejor F1 en validación)", **metricas_clasificacion(y_test, prob_test, umbral)},
                             {"Umbral": "Siempre 'no compra'", **metricas_clasificacion(y_test, np.zeros_like(prob_test) + 1e-9)}])

    # 8. Exportación
    os.makedirs(salida, exist_ok=True)
    os.makedirs(modelos_dir, exist_ok=True)
    impacto.to_csv(f"{salida}/tratamiento_datos.csv", index=False, encoding="utf-8-sig")
    val_base.pipe(tabla_bonita).to_csv(f"{salida}/baseline_optimizado_validacion.csv", index=False, encoding="utf-8-sig")
    busqueda.drop(columns="_cfg").round(5).to_csv(f"{salida}/busqueda_hiperparametros.csv", index=False, encoding="utf-8-sig")
    tabla_bonita(res_test).to_csv(f"{salida}/resultados_test_optimizado.csv", index=False, encoding="utf-8-sig")
    clf_test.round(5).to_csv(f"{salida}/metricas_clasificacion_test.csv", index=False, encoding="utf-8-sig")
    ic.to_csv(f"{salida}/intervalos_confianza_test.csv", index=False, encoding="utf-8-sig")

    joblib.dump(ranker.clf, f"{modelos_dir}/ranker_clasificador.joblib")
    config = {
        "fecha_corte": str(corte.date()),
        "ranker": {"algoritmo": NOMBRE_ALG[mejor_cfg["algoritmo"]],
                   "hiperparametros": {k: v for k, v in mejor_cfg.items() if k != "algoritmo"},
                   "variables": list(RankerSupervisado.COLUMNAS), "umbral_mejor_f1": round(umbral, 5)},
        "baseline_optimizado": {"nombre": baseline_opt.nombre, "top12": [int(a) for a in base_test.top]},
        "cocompra": {"dias_pares": cocompra.dias_pares, "peso_recompra": cocompra.peso_recompra},
        "metricas_test_recall_at_12": {g: round(float(piv.loc[FINAL, g]) / 100, 5) for g in ["Todos", "Con historial", "Nuevos"]},
    }
    with open(f"{modelos_dir}/configuracion_modelo.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    recs = pd.DataFrame([{"customer_id": c, "posicion": i + 1, "article_id": int(a)}
                         for c in compras_test for i, a in enumerate(final.recomendar(c))])
    recs.to_csv(f"{modelos_dir}/recomendaciones_semana_test.csv", index=False, encoding="utf-8")

    print("\nRecall@12 en test (%):")
    print(piv.round(2).to_string())
    print(f"\nTiempo total: {(time.time() - t0) / 60:,.1f} minutos")
    return res_test


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pipeline de punta a punta del sistema de recomendación Lookwise.")
    ap.add_argument("--base", required=True, help="Carpeta con la muestra p10 (parquet)")
    ap.add_argument("--salida", default="reports", help="Carpeta para los CSV de resultados")
    ap.add_argument("--modelos", default="models", help="Carpeta para el modelo entrenado, su configuración y las recomendaciones")
    args = ap.parse_args()
    correr(args.base, args.salida, args.modelos)
    print(f"Resultados guardados en {args.salida}/ y artefactos en {args.modelos}/")
