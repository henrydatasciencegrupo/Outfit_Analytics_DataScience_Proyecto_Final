import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

AQUI = Path(__file__).resolve().parent
# Dirección de la API. Por defecto, local; con Docker se define LOOKWISE_API_URL (p. ej. http://api:8000)
API = os.environ.get("LOOKWISE_API_URL", "http://127.0.0.1:8000")

RANGOS = {
    "Todas": (1, 10**9),
    "Pocas (1 a 5)": (1, 5),
    "Medias (6 a 80)": (6, 80),
    "Muchas (81 o más)": (81, 10**9),
}

st.set_page_config(page_title="Lookwise Data Lab", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebarHeader"] { height: 2rem; }
    [data-testid="stSidebarUserContent"] { padding-top: 0; }
    [data-testid="stMainBlockContainer"] { padding-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def cargar_clientes():
    return pd.read_csv(AQUI / "datos/clientes_test.csv")


@st.cache_data
def cargar_prendas():
    return pd.read_parquet(AQUI / "datos/prendas_min.parquet").set_index("article_id")


@st.cache_data
def cargar_metricas():
    with open(AQUI / "datos/configuracion_modelo.json", encoding="utf-8") as f:
        return json.load(f)["metricas_test_recall_at_12"]


def pedir_recomendacion(cliente):
    try:
        r = requests.get(f"{API}/recomendar", params={"cliente": cliente}, timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar con la API. ¿Está encendida?"
    if r.status_code == 404:
        return None, "Cliente no encontrado."
    if r.status_code != 200:
        return None, f"Error de la API (código {r.status_code})."
    return r.json(), None


clientes = cargar_clientes()
prendas = cargar_prendas()
metricas = cargar_metricas()

st.title("Lookwise Data Lab")
st.caption("Recomendaciones de prendas para clientes de la semana de test (16 al 22/09/2020)")

tipo = st.sidebar.radio("Tipo de cliente", ["Con historial", "Nuevo"])
filtro = clientes[clientes["es_nuevo"] == (tipo == "Nuevo")]

if tipo == "Con historial":
    nivel = st.sidebar.radio("Compras previas", list(RANGOS))
    minimo, maximo = RANGOS[nivel]
    filtro = filtro[filtro["n_compras_previas"].between(minimo, maximo)]

st.sidebar.write(f"{len(filtro):,} clientes")

cliente = st.sidebar.selectbox(
    "Cliente", filtro["customer_id"].tolist(), format_func=lambda c: c[:10] + "…"
)

# Mostrar el ID completo del cliente seleccionado
st.sidebar.code(cliente)

compras = int(filtro.loc[filtro["customer_id"] == cliente, "n_compras_previas"].iloc[0])
st.sidebar.metric("Compras previas del cliente", compras)

st.sidebar.divider()
clave = "Nuevos" if tipo == "Nuevo" else "Con historial"
recall = f"{metricas[clave] * 100:.2f}".replace(".", ",")
st.sidebar.metric("Recall@12 del modelo (test)", f"{recall} %")
st.sidebar.caption(
    "Promedio de todos los clientes de este tipo en la semana de test. "
    "No es el acierto de este cliente en particular."
)

datos, error = pedir_recomendacion(cliente)
if error:
    st.error(error)
else:
    etapas = {
        "nuevo": ("Cliente nuevo", "Las prendas más vendidas recientemente"),
        "con_historial": ("Cliente con historial", "Recomendación personalizada"),
    }
    etiqueta, descripcion = etapas.get(datos["etapa"], (datos["etapa"], ""))
    st.markdown(
        f"<span style='background:#E9B8A8; color:#17161A; padding:4px 14px; "
        f"border-radius:14px; font-weight:700; font-size:0.85rem'>{etiqueta}</span>",
        unsafe_allow_html=True,
    )
    st.subheader(descripcion)

    tabla = prendas.reindex(datos["prendas"]).reset_index()
    tabla.index = tabla.index + 1
    tabla = tabla.rename(columns={
        "article_id": "Código",
        "prod_name": "Prenda",
        "product_type_name": "Tipo",
        "product_group_name": "Grupo",
        "colour_group_name": "Color",
    })
    st.dataframe(tabla, height=(len(tabla) + 1) * 35 + 3)