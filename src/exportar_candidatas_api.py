"""
exportar_candidatas_api.py — Datos de entrada de la API, generados con el mismo código del modelo oficial
=========================================================================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Reproduce los pasos del notebook 06 (sección 13) que generaron `models/recomendaciones_semana_test.csv`
y guarda lo que la API necesita para mostrar exactamente esas recomendaciones:

- `candidatas_test.parquet`: una fila por (cliente, prenda candidata) con las 17 variables del ranker,
  en el mismo orden de filas que usó el modelo (importa para los empates de probabilidad).
- `clientes_test.csv`: los 4.162 clientes de la semana de test, si son nuevos y cuántas compras previas tienen.

Configuración oficial (la misma del notebook 06):
- Datos: muestra p10 después de `tratar()` (solo canal online; los duplicados se conservan, sin colapsar).
- Fecha de corte: 2020-09-16. Las variables se calculan solo con compras anteriores al corte (`train`).
- Candidatas: `RankerSupervisado` con n_candidatos=40 y dias_pares=28 (popularidad de 7 días,
  popularidad por tramo de edad de 7 días y co-compra con recompra).
- Clientes nuevos (sin compras antes del corte): top 12 del baseline optimizado de `configuracion_modelo.json`.

Al final verifica, con `models/ranker_clasificador.joblib`, que las 12 prendas de cada cliente coinciden
con `models/recomendaciones_semana_test.csv`.

Uso, desde la raíz del repositorio:
    python src/exportar_candidatas_api.py --base dataset/p10 --salida api/datos
"""
import argparse
import json
import os
import sys

import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datos import cargar, tratar, separar, CORTE_TEST
from metricas import compras_por_cliente
from modelos import RankerSupervisado, PopularidadPorEdad, K

N_CANDIDATOS = 40
DIAS_PARES = 28


def exportar(base: str, salida: str, modelos: str = "models"):
    trans, cust, art = cargar(base)
    trans, cust, art, _ = tratar(trans, cust, art)
    train, test = separar(trans, CORTE_TEST)
    tramo = cust.set_index("customer_id")["tramo_edad"].to_dict()
    compras_test = compras_por_cliente(test)
    clientes = list(compras_test)                    # mismo orden que en el notebook 06

    # 1. Candidatas y variables (mismo código y mismo lote de clientes que el modelo oficial)
    ranker = RankerSupervisado(tramo, cust, art, dias_pares=DIAS_PARES, n_candidatos=N_CANDIDATOS)
    tabla = ranker._tabla(train, CORTE_TEST, clientes)
    candidatas = tabla[["customer_id", "article_id"] + RankerSupervisado.COLUMNAS].copy()
    candidatas["article_id"] = candidatas["article_id"].astype("int64")

    # 2. Clientes de la semana de test
    previas = train.groupby("customer_id").size()
    info = pd.DataFrame({"customer_id": clientes})
    info["n_compras_previas"] = info["customer_id"].map(previas).fillna(0).astype(int)
    info["es_nuevo"] = info["n_compras_previas"] == 0
    info = info[["customer_id", "es_nuevo", "n_compras_previas"]]

    os.makedirs(salida, exist_ok=True)
    candidatas.to_parquet(os.path.join(salida, "candidatas_test.parquet"), index=False)
    info.to_csv(os.path.join(salida, "clientes_test.csv"), index=False, encoding="utf-8")
    print(f"Guardadas {len(candidatas):,} candidatas de {candidatas['customer_id'].nunique():,} clientes "
          f"y {len(info):,} clientes ({info['es_nuevo'].sum():,} nuevos) en {salida}/")

    # 3. Verificación contra las recomendaciones oficiales
    modelo = joblib.load(os.path.join(modelos, "ranker_clasificador.joblib"))
    with open(os.path.join(modelos, "configuracion_modelo.json"), encoding="utf-8") as f:
        top_nuevos = [int(a) for a in json.load(f)["baseline_optimizado"]["top12"]]
    respaldo = PopularidadPorEdad(tramo, 7, k=K).fit(train, CORTE_TEST)

    t = candidatas.copy()
    t["prob"] = modelo.predict_proba(t[RankerSupervisado.COLUMNAS])[:, 1]
    t = t.sort_values(["customer_id", "prob"], ascending=[True, False])   # mismo orden que RankerSupervisado._ordenar
    top = t.groupby("customer_id")["article_id"].apply(lambda s: s.head(K).tolist()).to_dict()

    nuevos = set(info.loc[info["es_nuevo"], "customer_id"])
    propias = {}
    for c in clientes:
        if c in nuevos:
            propias[c] = top_nuevos
        else:
            lista = top.get(c, [])
            if len(lista) < K:
                lista = lista + [a for a in respaldo.recomendar(c) if a not in lista]
            propias[c] = [int(a) for a in lista[:K]]

    oficiales = (pd.read_csv(os.path.join(modelos, "recomendaciones_semana_test.csv"))
                   .sort_values(["customer_id", "posicion"])
                   .groupby("customer_id")["article_id"].apply(list).to_dict())
    iguales = sum(propias[c] == oficiales.get(c) for c in clientes)
    print(f"Verificación: {iguales:,} de {len(clientes):,} clientes con las mismas 12 prendas y en el mismo orden "
          f"que models/recomendaciones_semana_test.csv")
    return iguales == len(clientes)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Exporta las candidatas y los clientes de test para la API.")
    p.add_argument("--base", default="dataset/p10", help="carpeta con la muestra p10 (no se versiona)")
    p.add_argument("--salida", default="api/datos", help="carpeta donde se guardan los archivos para la API")
    p.add_argument("--modelos", default="models", help="carpeta con los artefactos del modelo oficial")
    a = p.parse_args()
    sys.exit(0 if exportar(a.base, a.salida, a.modelos) else 1)
