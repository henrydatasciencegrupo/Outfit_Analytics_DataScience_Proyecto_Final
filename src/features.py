"""
features.py — Pipeline de ingeniería de características
=======================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autora: Margot Huaman Quispe

Propósito
---------
Transformar el historial de compras en variables (features) que describen el
comportamiento de clientes y productos, listas para alimentar los modelos.

Regla anti-fuga de información
------------------------------
Todas las features se calculan **solo con compras anteriores a la fecha `hasta`**.
Así, al evaluar en la semana de test, ningún modelo usa información del futuro.

Salidas
-------
- clientes : una fila por cliente (frecuencia, recencia, antigüedad, gasto, preferencias, perfil)
- articulos: una fila por artículo (popularidad, tendencia, novedad, precio, atributos)
- cocompra : pares de artículos comprados juntos (mismo cliente, mismo día)

Uso desde la terminal
---------------------
    python src/features.py --base <carpeta_p10> --salida <carpeta_features>
"""
import argparse
import os

import pandas as pd

from datos import cargar, tratar, CORTE_TEST

ATRIBUTOS_ARTICULO = ["prod_name", "product_type_name", "product_group_name", "colour_group_name",
                      "index_group_name", "section_name", "garment_group_name"]


def _antes(trans: pd.DataFrame, hasta: pd.Timestamp, dias: int | None = None) -> pd.DataFrame:
    """Compras anteriores a `hasta`; si se indica `dias`, solo las de esa ventana."""
    d = trans[trans["t_dat"] < hasta]
    if dias is not None:
        d = d[d["t_dat"] >= hasta - pd.Timedelta(days=dias)]
    return d


def features_cliente(trans: pd.DataFrame, cust: pd.DataFrame, art: pd.DataFrame,
                     hasta: pd.Timestamp) -> pd.DataFrame:
    """Perfil y comportamiento de cada cliente con la información disponible hasta `hasta`."""
    h = _antes(trans, hasta)
    g = h.groupby("customer_id")
    f = pd.DataFrame({
        "n_compras": g.size(),                                       # frecuencia
        "n_articulos_distintos": g["article_id"].nunique(),          # variedad
        "dias_activos": g["t_dat"].nunique(),                        # días con compra
        "dias_desde_ultima": (hasta - g["t_dat"].max()).dt.days,     # recencia
        "dias_desde_primera": (hasta - g["t_dat"].min()).dt.days,    # antigüedad
        "precio_medio": g["price"].mean() if "price" in h else None,  # nivel de gasto
    })
    f["compras_por_dia_activo"] = f["n_compras"] / f["dias_activos"]  # tamaño de canasta

    # Preferencia de estilo: % de las compras del cliente en cada grupo de producto
    if "index_group_name" in art:
        hh = h[["customer_id", "article_id"]].merge(art[["article_id", "index_group_name"]], on="article_id")
        preferencias = pd.crosstab(hh["customer_id"], hh["index_group_name"], normalize="index").add_prefix("pref_")
        f = f.join(preferencias)

    perfil = cust.set_index("customer_id")[[c for c in ["age", "edad_faltante", "tramo_edad"] if c in cust]]
    f = perfil.join(f)
    conteos = ["n_compras", "n_articulos_distintos", "dias_activos"]
    f[conteos] = f[conteos].fillna(0).astype(int)
    f["es_frio"] = f["n_compras"] == 0                               # sin historial antes de `hasta`
    return f.reset_index()


def features_articulo(trans: pd.DataFrame, art: pd.DataFrame, hasta: pd.Timestamp) -> pd.DataFrame:
    """Popularidad, tendencia, novedad, precio y atributos de cada artículo hasta `hasta`."""
    h = _antes(trans, hasta)
    semana_previa = h[(h["t_dat"] >= hasta - pd.Timedelta(days=14)) & (h["t_dat"] < hasta - pd.Timedelta(days=7))]
    f = pd.DataFrame({
        "ventas_7d": _antes(h, hasta, 7)["article_id"].value_counts(),
        "ventas_7d_previa": semana_previa["article_id"].value_counts(),
        "ventas_30d": _antes(h, hasta, 30)["article_id"].value_counts(),
        "ventas_total": h["article_id"].value_counts(),
        "dias_desde_primera_venta": (hasta - h.groupby("article_id")["t_dat"].min()).dt.days,
    })
    if "price" in h:
        f["precio_medio"] = h.groupby("article_id")["price"].mean()
    atributos = art.set_index("article_id")[[c for c in ATRIBUTOS_ARTICULO if c in art]]
    f = atributos.join(f)
    ventas = ["ventas_7d", "ventas_7d_previa", "ventas_30d", "ventas_total"]
    f[ventas] = f[ventas].fillna(0).astype(int)
    f["tendencia"] = (f["ventas_7d"] + 1) / (f["ventas_7d_previa"] + 1)  # > 1: ventas en aumento
    f["es_novedad"] = f["dias_desde_primera_venta"] <= 14
    f["sin_ventas"] = f["ventas_total"] == 0
    return f.reset_index()


def pares_cocompra(trans: pd.DataFrame, hasta: pd.Timestamp, dias: int = 28, max_canasta: int = 30) -> pd.DataFrame:
    """Pares de artículos comprados juntos por un mismo cliente en un mismo día.

    Se ignoran las canastas de un solo artículo (no forman pares) y las muy grandes
    (más de `max_canasta` artículos), que suelen ser compras atípicas y agregan ruido.
    """
    d = _antes(trans, hasta, dias)[["customer_id", "t_dat", "article_id"]].drop_duplicates()
    tamano = d.groupby(["customer_id", "t_dat"])["article_id"].transform("size")
    d = d[(tamano >= 2) & (tamano <= max_canasta)]
    pares = d.merge(d, on=["customer_id", "t_dat"], suffixes=("", "_vecino"))
    pares = pares[pares["article_id"] != pares["article_id_vecino"]]
    return (pares.groupby(["article_id", "article_id_vecino"]).size()
                 .rename("veces").reset_index()
                 .sort_values(["article_id", "veces"], ascending=[True, False]))


def construir_features(trans: pd.DataFrame, cust: pd.DataFrame, art: pd.DataFrame,
                       hasta: pd.Timestamp, dias_cocompra: int = 28) -> dict:
    """Ejecuta el pipeline completo y devuelve las tres tablas de features."""
    return {"clientes": features_cliente(trans, cust, art, hasta),
            "articulos": features_articulo(trans, art, hasta),
            "cocompra": pares_cocompra(trans, hasta, dias_cocompra)}


def chequeo_sin_leakage(trans: pd.DataFrame, hasta: pd.Timestamp, features: dict) -> bool:
    """Control automático: ninguna feature puede reflejar compras posteriores a `hasta`."""
    clientes = features["clientes"]
    nuevos_despues = (set(trans[trans["t_dat"] >= hasta]["customer_id"])
                      - set(trans[trans["t_dat"] < hasta]["customer_id"]))
    contaminados = clientes[clientes["customer_id"].isin(nuevos_despues) & (clientes["n_compras"] > 0)]
    return len(contaminados) == 0 and bool((clientes["dias_desde_ultima"].dropna() >= 0).all())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera las features del sistema de recomendación sin fuga de información.")
    ap.add_argument("--base", required=True, help="Carpeta con la muestra p10 (parquet)")
    ap.add_argument("--salida", required=True, help="Carpeta donde guardar las features")
    ap.add_argument("--hasta", default=str(CORTE_TEST.date()), help="Fecha de corte (AAAA-MM-DD)")
    args = ap.parse_args()

    trans, cust, art = cargar(args.base)
    trans, cust, art, _ = tratar(trans, cust, art)
    hasta = pd.Timestamp(args.hasta)
    feats = construir_features(trans, cust, art, hasta)
    os.makedirs(args.salida, exist_ok=True)
    for nombre, tabla in feats.items():
        tabla.to_parquet(f"{args.salida}/{nombre}.parquet", index=False)
        print(f"{nombre:<10} {tabla.shape}  -> {args.salida}/{nombre}.parquet")
    print("Sin fuga de información:", "✅" if chequeo_sin_leakage(trans, hasta, feats) else "❌")
