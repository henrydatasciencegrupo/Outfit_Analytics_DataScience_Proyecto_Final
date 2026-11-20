import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

AQUI = Path(__file__).resolve().parent
MODELOS = AQUI.parent / "models"  # el modelo oficial: api/ y models/ quedan lado a lado en el repo
app = FastAPI()

# Se cargan UNA sola vez, al arrancar
modelo = joblib.load(MODELOS / "ranker_clasificador.joblib")
with open(MODELOS / "configuracion_modelo.json", encoding="utf-8") as f:
    config = json.load(f)
clientes = pd.read_csv(AQUI / "datos/clientes_test.csv").set_index("customer_id")
candidatas = pd.read_parquet(AQUI / "datos/candidatas_test.parquet").set_index("customer_id").sort_index()
baseline = [int(x) for x in config["baseline_optimizado"]["top12"]]

COLUMNAS = ["rank_pop", "rank_edad", "rank_cocompra", "puntaje_cocompra", "ya_lo_compro",
            "ventas_7d", "ventas_30d", "tendencia", "dias_desde_primera_venta", "precio_articulo",
            "ventas_tramo_7d", "afinidad_grupo", "age", "edad_faltante", "n_compras",
            "dias_desde_ultima", "compras_por_dia_activo"]


def recomendar(cliente):
    if cliente not in clientes.index:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if bool(clientes.at[cliente, "es_nuevo"]):
        return {"cliente": cliente, "etapa": "nuevo", "prendas": baseline}
    t = candidatas.loc[[cliente]]
    prob = modelo.predict_proba(t[COLUMNAS])[:, 1]
    orden = pd.Series(prob, index=t["article_id"].values).sort_values(ascending=False, kind="stable")
    prendas = [int(a) for a in orden.index[:12]]
    return {"cliente": cliente, "etapa": "con_historial", "prendas": prendas}


@app.get("/recomendar")
def endpoint_recomendar(cliente: str):
    return recomendar(cliente)

@app.get("/salud")
def salud():
    return {"estado": "ok", "clientes": int(len(clientes))}