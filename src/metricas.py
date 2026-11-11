"""
metricas.py — Métricas de evaluación del sistema de recomendación
=================================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Todos los modelos se evalúan con estas mismas funciones (criterio único de comparación).

Relación entre KPIs de negocio y métricas
-----------------------------------------
| KPI de negocio                           | Métrica            | Pregunta que responde                              |
|------------------------------------------|--------------------|----------------------------------------------------|
| Experiencia (métrica principal)          | MAP@12             | ¿Acertamos y pusimos lo correcto arriba?           |
| Conversión de clientes nuevos            | Hit Rate@12        | ¿Qué % de clientes compró algo de la lista?        |
| Productos por pedido                     | Recall@12          | ¿Qué parte de su compra anticipamos?               |
| Aprovechamiento de la vitrina            | Precision@12       | ¿Qué parte de los 12 lugares se aprovechó?         |
| Salud del catálogo                       | Prendas distintas  | ¿A cuántas prendas damos visibilidad?              |
"""
import numpy as np
import pandas as pd

K = 12   # tamaño de la lista de recomendaciones (carrusel)


def compras_por_cliente(df: pd.DataFrame) -> dict:
    """Diccionario cliente -> conjunto de artículos comprados en el período de `df`."""
    return df.groupby("customer_id")["article_id"].apply(set).to_dict()


def ap_at_k(reales: set, predichos: list, k: int = K) -> float:
    """Average Precision@k de un cliente: premia acertar y ubicar los aciertos en las primeras posiciones."""
    aciertos, suma = 0, 0.0
    for i, p in enumerate(predichos[:k]):
        if p in reales:
            aciertos += 1
            suma += aciertos / (i + 1)
    return suma / min(len(reales), k) if reales else 0.0


def detalle_por_cliente(compras: dict, recomendar, k: int = K):
    """Métricas de cada cliente y cantidad de prendas distintas recomendadas.

    Parámetros
    ----------
    compras    : dict cliente -> set de artículos comprados en el período evaluado.
    recomendar : función cliente -> lista ordenada de artículos recomendados.
    """
    filas, recomendadas = [], set()
    for cliente, reales in compras.items():
        pred = list(recomendar(cliente))[:k]
        recomendadas.update(pred)
        aciertos = len(reales & set(pred))
        filas.append((cliente, ap_at_k(reales, pred, k), aciertos > 0, aciertos / k, aciertos / len(reales)))
    detalle = pd.DataFrame(filas, columns=["customer_id", "ap", "hit", "precision", "recall"])
    return detalle, len(recomendadas)


def metricas(compras: dict, recomendar, k: int = K) -> dict:
    """Las cinco métricas del sistema para un grupo de clientes."""
    detalle, distintas = detalle_por_cliente(compras, recomendar, k)
    if detalle.empty:
        return {"MAP@12": np.nan, "Hit Rate@12": np.nan, "Recall@12": np.nan,
                "Precision@12": np.nan, "Prendas distintas": 0}
    return {"MAP@12": detalle["ap"].mean(), "Hit Rate@12": detalle["hit"].mean(),
            "Recall@12": detalle["recall"].mean(), "Precision@12": detalle["precision"].mean(),
            "Prendas distintas": distintas}


def bootstrap_diferencia(compras: dict, recomendar_a, recomendar_b, n: int = 1000, semilla: int = 42) -> dict:
    """Intervalo de confianza del 95% de la diferencia (B − A), evaluada sobre los mismos clientes.

    Remuestrea los clientes con reposición `n` veces. Si el intervalo no incluye el 0,
    la diferencia se considera robusta (no atribuible al azar).
    """
    det_a, _ = detalle_por_cliente(compras, recomendar_a)
    det_b, _ = detalle_por_cliente(compras, recomendar_b)
    rng = np.random.default_rng(semilla)
    indices = rng.integers(0, len(det_a), size=(n, len(det_a)))
    salida = {}
    for col, nombre in [("ap", "MAP@12"), ("hit", "Hit Rate@12")]:
        diferencia = det_b[col].to_numpy(float) - det_a[col].to_numpy(float)
        remuestras = diferencia[indices].mean(axis=1)
        bajo, alto = np.percentile(remuestras, [2.5, 97.5])
        salida[nombre] = {"diferencia": diferencia.mean(), "ic_bajo": bajo, "ic_alto": alto,
                          "robusta": bool(bajo > 0 or alto < 0)}
    return salida


def tabla_bonita(df: pd.DataFrame) -> pd.DataFrame:
    """Redondea MAP@12 y expresa Hit Rate, Recall y Precision en porcentaje."""
    out = df.copy()
    if "MAP@12" in out:
        out["MAP@12"] = out["MAP@12"].round(4)
    for col in ["Hit Rate@12", "Recall@12", "Precision@12"]:
        if col in out:
            out[col + " (%)"] = (out.pop(col) * 100).round(2)
    return out
