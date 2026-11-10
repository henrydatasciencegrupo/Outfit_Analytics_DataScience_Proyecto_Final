"""
datos.py — Carga, verificación y tratamiento de los datos
=========================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Propósito
---------
Dejar los datos listos para el modelado de forma **reproducible** y **auditable**:
cada decisión de calidad se aplica con un criterio explícito y se **cuantifica**
(cuántas filas o clientes afecta), de modo que su impacto pueda defenderse.

Principio de tratamiento
------------------------
En un recomendador cada compra es una señal de preferencia. Por eso no se elimina
ninguna compra real sin evidencia de error: los casos dudosos se documentan y se
conservan.

Uso
---
    from datos import cargar, verificar, tratar, separar, clientes_frios
    trans, cust, art = cargar("<carpeta_p10>")
    print(verificar(trans, cust, art))
    trans, cust, art, impacto = tratar(trans, cust, art)
    train, test = separar(trans)
    frios = clientes_frios(trans)
"""
import pandas as pd

# ---------------------------------------------------------------------------
# Parámetros del estudio
# ---------------------------------------------------------------------------
CORTE_TEST = pd.Timestamp("2020-09-16")   # primer día de la semana de evaluación (16–22/09/2020)
DIAS_TEST = 7                             # horizonte de evaluación: una semana
CANAL_ONLINE = 2                          # canal de venta e-commerce

BINS_EDAD = [0, 25, 35, 45, 55, 120]
TRAMOS_EDAD = ["<25", "25-34", "35-44", "45-54", "55+"]
SIN_EDAD = "sin edad"                     # la edad faltante no se imputa: forma su propio grupo

# Variables de cliente que no se usan: son una foto de un único momento (posible fuga
# de información del futuro) y aportan poca señal predictiva.
COLUMNAS_CLIENTE_EXCLUIDAS = ["FN", "Active", "club_member_status", "fashion_news_frequency", "postal_code"]

# Tamaños de referencia de la muestra p10 (control de reproducibilidad)
ESPERADO = {"transactions": (2226486, 5), "customers": (110252, 7), "articles": (105542, 25)}


# ---------------------------------------------------------------------------
# Carga y verificación
# ---------------------------------------------------------------------------
def cargar(base: str):
    """Lee las tablas de transacciones, clientes y artículos (formato parquet).

    Parámetros
    ----------
    base : carpeta que contiene transactions.parquet, customers.parquet y articles.parquet.

    Devuelve
    --------
    (trans, cust, art) como DataFrames, con la fecha de compra convertida a datetime.
    """
    trans = pd.read_parquet(f"{base}/transactions.parquet")
    cust = pd.read_parquet(f"{base}/customers.parquet")
    art = pd.read_parquet(f"{base}/articles.parquet")
    trans["t_dat"] = pd.to_datetime(trans["t_dat"])
    return trans, cust, art


def verificar(trans: pd.DataFrame, cust: pd.DataFrame, art: pd.DataFrame) -> pd.DataFrame:
    """Compara el tamaño de cada tabla con el de referencia y devuelve una tabla de control."""
    obtenido = {"transactions": trans.shape, "customers": cust.shape, "articles": art.shape}
    filas = []
    for tabla, esperado in ESPERADO.items():
        filas.append({"Tabla": tabla, "Esperado (EDA)": str(esperado), "Obtenido": str(obtenido[tabla]),
                      "OK": "Sí" if obtenido[tabla] == esperado else "Distinto"})
    return pd.DataFrame(filas)


def _fuera_de_iqr(serie: pd.Series) -> int:
    """Cantidad de valores fuera del rango intercuartílico ampliado (1,5 × IQR)."""
    q1, q3 = serie.quantile([0.25, 0.75])
    rango = q3 - q1
    return int(((serie < q1 - 1.5 * rango) | (serie > q3 + 1.5 * rango)).sum())


# ---------------------------------------------------------------------------
# Tratamiento de datos
# ---------------------------------------------------------------------------
def tratar(trans: pd.DataFrame, cust: pd.DataFrame, art: pd.DataFrame):
    """Aplica las decisiones de calidad y mide el impacto de cada una.

    Devuelve
    --------
    (trans, cust, art, impacto), donde `impacto` es una tabla con una fila por decisión:
    tema, hallazgo, casos afectados, % del total, decisión tomada y justificación.
    """
    impacto = []

    def registrar(tema, hallazgo, afectados, total, decision, justificacion):
        impacto.append({"Tema": tema, "Hallazgo": hallazgo, "Afectados": int(afectados),
                        "% del total": round(100 * afectados / total, 2) if total else 0.0,
                        "Decisión": decision, "Por qué": justificacion})

    trans, cust, art = trans.copy(), cust.copy(), art.copy()
    total_compras = len(trans)

    # 1. Canal de venta: el sistema recomienda en la tienda online
    fuera_canal = (trans["sales_channel_id"] != CANAL_ONLINE).sum()
    trans = trans[trans["sales_channel_id"] == CANAL_ONLINE]
    registrar("Canal de venta", "Filas fuera del canal online", fuera_canal, total_compras,
              "Solo canal 2 (online)", "El sistema recomienda en e-commerce; la muestra ya viene filtrada")

    # 2. Duplicados: misma prenda, mismo cliente, mismo día
    duplicados = trans.duplicated(["t_dat", "customer_id", "article_id"]).sum()
    registrar("Duplicados", "Misma prenda, mismo cliente, mismo día", duplicados, len(trans),
              "Se conservan", "No hay evidencia de error (pueden ser varias unidades); representan más demanda")

    # 3. Meses atípicos (marzo a mayo de 2020)
    atipicos = trans["t_dat"].between("2020-03-01", "2020-05-31").sum()
    registrar("Meses atípicos", "Compras de marzo a mayo 2020", atipicos, len(trans),
              "Se conservan en train", "La evaluación no cae en ese período; quitarlos eliminaría datos recientes")

    # 4. Precios extremos
    if "price" in trans:
        registrar("Precios extremos", "Precios fuera del rango IQR", _fuera_de_iqr(trans["price"]), len(trans),
                  "No se eliminan", "Son ventas reales; el precio no es la variable objetivo (solo se usa como promedio)")

    # 5. Edad faltante: no se imputa
    total_clientes = len(cust)
    sin_edad = cust["age"].isna().sum()
    cust["edad_faltante"] = cust["age"].isna()
    cust["tramo_edad"] = pd.cut(cust["age"], bins=BINS_EDAD, labels=TRAMOS_EDAD, right=False).astype(str)
    cust.loc[cust["edad_faltante"], "tramo_edad"] = SIN_EDAD
    registrar("Edad vacía", "Clientes sin edad", sin_edad, total_clientes,
              "No se imputa: grupo 'sin edad'", "Imputar asignaría gustos ajenos; afecta a ~1% de los clientes")

    # 6. Edades extremas
    extremas = ((cust["age"] < 18) | (cust["age"] > 90)).sum()
    registrar("Edades extremas", "Edad < 18 o > 90", extremas, total_clientes,
              "Se conservan", "Son valores posibles; quedan en los tramos <25 y 55+")

    # 7. Variables de cliente excluidas
    excluidas = [c for c in COLUMNAS_CLIENTE_EXCLUIDAS if c in cust.columns]
    cust = cust.drop(columns=excluidas)
    registrar("Variables de cliente", f"Columnas excluidas: {', '.join(excluidas)}", len(excluidas), len(excluidas) + 2,
              "Solo se usa la edad", "Son una foto de un único momento (riesgo de fuga de información) y aportan poca señal")

    # 8. Artículos: descripción vacía y categoría 'Unknown'
    total_articulos = len(art)
    if "detail_desc" in art:
        registrar("Descripción de artículo", "detail_desc vacía", art["detail_desc"].isna().sum(), total_articulos,
                  "Se conserva vacía", "Los modelos actuales no usan texto libre")
    if "garment_group_name" in art:
        desconocida = (art["garment_group_name"] == "Unknown").sum()
        registrar("Categoría 'Unknown'", "garment_group_name = 'Unknown'", desconocida, total_articulos,
                  "Se trata como una categoría más", "Es una clasificación explícita, no un faltante oculto")

    return trans, cust, art, pd.DataFrame(impacto)


# ---------------------------------------------------------------------------
# Partición temporal y segmentación
# ---------------------------------------------------------------------------
def separar(trans: pd.DataFrame, corte: pd.Timestamp = CORTE_TEST, dias: int = DIAS_TEST):
    """Partición temporal sin solapamiento.

    train = compras anteriores al corte · test = compras de los `dias` siguientes.
    Simula el uso real: se recomienda con el pasado y se evalúa con lo que ocurre después.
    """
    train = trans[trans["t_dat"] < corte]
    test = trans[(trans["t_dat"] >= corte) & (trans["t_dat"] < corte + pd.Timedelta(days=dias))]
    return train, test


def clientes_frios(trans: pd.DataFrame, corte: pd.Timestamp = CORTE_TEST) -> set:
    """Clientes cuya primera compra ocurre en o después del corte (sin historial: cold start)."""
    primera = trans.groupby("customer_id")["t_dat"].min()
    return set(primera[primera >= corte].index)
