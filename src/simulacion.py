"""
simulacion.py — Simulación de clientes nuevos (cold start simulado)
===================================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Pregunta de negocio
-------------------
¿A partir de cuántas compras conviene dejar de mostrar "lo más vendido" y empezar a
personalizar? Con pocos clientes nuevos reales (437 en la semana de test) la respuesta no
es concluyente, así que se simula: a clientes que sí tienen historial se les "borra" casi
todo el pasado y se deja visible solo 0, 1 o 2 compras.

Reglas de la simulación (fijadas antes de ver resultados)
---------------------------------------------------------
1. Quién entra: clientes que compran en la semana de test (16–22/09/2020) y que antes del
   corte compraron al menos MIN_ARTICULOS artículos distintos (así siempre queda algo oculto).
   Es el MISMO grupo para todos los escenarios: la única diferencia es cuánto se ve.
2. Cuántas compras quedan visibles: 0, 1 y 2 (más el historial completo como referencia).
3. Cuáles: las más recientes (escenario principal). Un cliente nuevo real recién llega:
   sus primeras compras son de los últimos días, no de hace dos años. Como control de
   sensibilidad se repite con las primeras compras de su vida.
4. Regla contra la fuga de información: las compras ocultas se BORRAN de toda la base
   (no solo del perfil del cliente): no cuentan para la popularidad, ni para los pares de
   co-compra, ni para entrenar el ranker. Solo se usan compras anteriores al 16/09.
5. Qué se evalúa: lo que esos clientes compran en la misma semana de test (16–22/09).
6. Métricas: MAP@12 y Hit Rate@12, con intervalo de confianza del 95% (bootstrap pareado).
7. Criterio de éxito: un modelo le gana a "lo más vendido" con N compras visibles si mejora
   MAP@12 y Hit Rate@12 y el intervalo de la mejora en MAP@12 no incluye el 0.
   El umbral es el menor N desde el cual eso se cumple.
8. Reporte: los resultados simulados se informan separados de los clientes nuevos reales.
9. Modelos: Baseline, Modelo 1 (edad), Modelo 2 (co-compra) y Modelo 3 (ranker).
"""
import pandas as pd

from metricas import metricas, bootstrap_diferencia
from modelos import PopularidadReciente, PopularidadPorEdad, CoCompraRecompra, RankerSupervisado

MIN_ARTICULOS = 3
VISIBLES = [0, 1, 2]
COMPLETO = "completo"


def elegir_clientes(train: pd.DataFrame, compras_test: dict, min_articulos: int = MIN_ARTICULOS) -> list:
    """Clientes del test con al menos `min_articulos` artículos distintos comprados antes del corte."""
    distintos = train.groupby("customer_id")["article_id"].nunique()
    con_historial = set(distintos[distintos >= min_articulos].index)
    return sorted(c for c in compras_test if c in con_historial)


def ocultar_historial(train: pd.DataFrame, clientes, n_visibles, cuales: str = "recientes") -> pd.DataFrame:
    """Devuelve una copia de `train` donde cada cliente simulado conserva solo `n_visibles` artículos.

    - cuales="recientes": los artículos distintos comprados más recientemente.
    - cuales="primeras":  los primeros artículos distintos de su vida como cliente.
    Las demás compras de esos clientes se eliminan de toda la base (regla anti-fuga).
    n_visibles = "completo" devuelve `train` sin cambios (referencia).
    """
    if n_visibles == COMPLETO:
        return train
    clientes = set(clientes)
    es_sim = train["customer_id"].isin(clientes)
    sim = train[es_sim]
    if n_visibles > 0:
        orden = sim.sort_values("t_dat", ascending=(cuales == "primeras"), kind="stable")
        primera_vez = orden.drop_duplicates(["customer_id", "article_id"])
        visibles = primera_vez.groupby("customer_id").head(n_visibles)[["customer_id", "article_id"]]
        clave = visibles.assign(_v=True)
        sim = sim.merge(clave, on=["customer_id", "article_id"], how="left")
        sim = sim[sim["_v"].fillna(False).astype(bool)].drop(columns="_v")
        # De cada artículo visible se conservan solo sus compras en la(s) fecha(s) visibles:
        # para "recientes", la última fecha; para "primeras", la primera.
        fecha = (sim.groupby(["customer_id", "article_id"])["t_dat"].transform("max") if cuales == "recientes"
                 else sim.groupby(["customer_id", "article_id"])["t_dat"].transform("min"))
        sim = sim[sim["t_dat"] == fecha]
    else:
        sim = sim.iloc[0:0]
    return pd.concat([train[~es_sim], sim], ignore_index=True)


def modelos_escenario(trans_sim, hasta, tramo, cust, art, clientes, params: dict, con_ranker: bool = True):
    """Entrena todos los modelos con la base del escenario y devuelve {nombre_corto: modelo}."""
    base = PopularidadReciente(params["dias_baseline"]).fit(trans_sim, hasta)
    edad = PopularidadPorEdad(tramo, params["dias_edad"]).fit(trans_sim, hasta)
    cocompra = CoCompraRecompra(edad, dias_pares=params["dias_pares"],
                                peso_recompra=params["peso_recompra"]).fit(trans_sim, hasta)
    modelos = {"Baseline": base, "M1 · Edad": edad, "M2 · Co-compra": cocompra}
    if con_ranker:
        ranker = RankerSupervisado(tramo, cust, art, dias_pares=params["dias_pares"], algoritmo=params["algoritmo"])
        ranker.fit(trans_sim, hasta, clientes=list(clientes))
        modelos["M3 · Ranker"] = ranker
    return modelos


def evaluar_escenario(modelos: dict, compras: dict, n_visibles, cuales: str, n_boot: int = 1000) -> pd.DataFrame:
    """Métricas de cada modelo y diferencia contra el baseline con intervalo del 95%."""
    filas = []
    base = modelos["Baseline"]
    for nombre, m in modelos.items():
        fila = {"Compras visibles": str(n_visibles), "Cuáles": cuales, "Modelo": nombre,
                "Clientes": len(compras), **metricas(compras, m.recomendar)}
        if nombre != "Baseline":
            b = bootstrap_diferencia(compras, base.recomendar, m.recomendar, n=n_boot)["MAP@12"]
            fila.update({"Dif. MAP@12 vs baseline": b["diferencia"], "IC bajo": b["ic_bajo"], "IC alto": b["ic_alto"]})
        filas.append(fila)
    tabla = pd.DataFrame(filas)
    hr_base = tabla.loc[tabla["Modelo"] == "Baseline", "Hit Rate@12"].iloc[0]
    map_base = tabla.loc[tabla["Modelo"] == "Baseline", "MAP@12"].iloc[0]
    tabla["Le gana al baseline"] = ((tabla["MAP@12"] > map_base) & (tabla["Hit Rate@12"] > hr_base)
                                    & (tabla["IC bajo"] > 0)).where(tabla["Modelo"] != "Baseline")
    return tabla


def umbral(resultados: pd.DataFrame, modelo: str, cuales: str = "recientes"):
    """Menor cantidad de compras visibles desde la cual `modelo` le gana al baseline (y sigue ganando)."""
    r = resultados[(resultados["Modelo"] == modelo) & (resultados["Cuáles"] == cuales)
                   & (resultados["Compras visibles"] != COMPLETO)]
    r = r.assign(n=r["Compras visibles"].astype(int)).sort_values("n")
    gana = r["Le gana al baseline"].fillna(False).astype(bool).tolist()
    for i, n in enumerate(r["n"]):
        if all(gana[i:]):
            return int(n)
    return None
