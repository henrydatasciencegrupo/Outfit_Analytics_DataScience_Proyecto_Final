"""
optimizacion.py — Métricas de clasificación, baseline optimizado y búsqueda de hiperparámetros
=============================================================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Propósito
---------
1. Medir el ranker como lo que es por dentro: un CLASIFICADOR que, para cada par
   (cliente, prenda candidata), estima si el cliente la va a comprar. Así se pueden
   reportar Accuracy, Recall, Precision, F1, ROC-AUC y PR-AUC, además de las métricas
   de recomendación (Recall@12, Hit Rate@12, MAP@12).
2. Optimizar el baseline: popularidad con distintas ventanas y con decaimiento
   temporal (lo reciente pesa más), elegido en validación por Recall@12.
3. Optimizar los hiperparámetros de la regresión logística y del Gradient Boosting,
   eligiendo en validación por Recall@12 (la métrica que prioriza el negocio).

Todas las elecciones se hacen en la semana de validación (09–15/09/2020); el test
(16–22/09/2020) se usa una sola vez, al final.
"""
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from modelos import K, _ventana


# ---------------------------------------------------------------------------
# Baseline optimizado: popularidad con decaimiento temporal
# ---------------------------------------------------------------------------
class PopularidadDecaimiento:
    """Lo más vendido, pero cada venta pesa según su antigüedad.

    Una venta de hace `vida_media` días pesa la mitad que una de hoy. Así el ranking
    reacciona a las tendencias sin descartar del todo las semanas anteriores.
    """

    def __init__(self, vida_media: float = 7, dias: int = 60, k: int = K):
        self.vida_media, self.dias, self.k = vida_media, dias, k
        self.nombre = f"Baseline con decaimiento (vida media {vida_media} días)"

    def fit(self, trans, hasta):
        d = _ventana(trans, hasta, self.dias)
        antiguedad = (hasta - d["t_dat"]).dt.days
        peso = 0.5 ** (antiguedad / self.vida_media)
        self.top = peso.groupby(d["article_id"]).sum().sort_values(ascending=False).head(self.k).index.tolist()
        return self

    def recomendar(self, cliente):
        return self.top


# ---------------------------------------------------------------------------
# El ranker como clasificador
# ---------------------------------------------------------------------------
def etiquetas(tabla: pd.DataFrame, compras: dict) -> np.ndarray:
    """1 si el cliente compró la prenda candidata en el período evaluado, 0 si no."""
    return np.array([a in compras.get(c, ()) for c, a in zip(tabla["customer_id"], tabla["article_id"])], dtype=int)


def metricas_clasificacion(y: np.ndarray, prob: np.ndarray, umbral: float = 0.5) -> dict:
    """Métricas de clasificación sobre los pares (cliente, prenda candidata)."""
    pred = (prob >= umbral).astype(int)
    return {"Umbral": umbral,
            "Accuracy": accuracy_score(y, pred),
            "Balanced accuracy": balanced_accuracy_score(y, pred),
            "Recall": recall_score(y, pred, zero_division=0),
            "Precision": precision_score(y, pred, zero_division=0),
            "F1": f1_score(y, pred, zero_division=0),
            "ROC-AUC": roc_auc_score(y, prob) if 0 < y.sum() < len(y) else np.nan,
            "PR-AUC": average_precision_score(y, prob) if y.sum() > 0 else np.nan}


def matriz_confusion(y: np.ndarray, prob: np.ndarray, umbral: float = 0.5) -> pd.DataFrame:
    pred = (prob >= umbral).astype(int)
    m = confusion_matrix(y, pred, labels=[0, 1])
    return pd.DataFrame(m, index=["Real: no compra", "Real: compra"], columns=["Predice: no compra", "Predice: compra"])


def umbral_mejor_f1(y: np.ndarray, prob: np.ndarray) -> float:
    """Umbral que maximiza F1 (equilibrio entre Recall y Precision)."""
    candidatos = np.unique(np.quantile(prob, np.linspace(0.5, 0.999, 200)))
    f1 = [f1_score(y, (prob >= u).astype(int), zero_division=0) for u in candidatos]
    return float(candidatos[int(np.argmax(f1))])


def recomendador_desde_prob(tabla: pd.DataFrame, prob: np.ndarray, respaldo, k: int = K):
    """Convierte las probabilidades en una lista de 12 prendas por cliente (completa con el respaldo)."""
    orden = tabla[["customer_id", "article_id"]].assign(prob=prob).sort_values(["customer_id", "prob"], ascending=[True, False])
    recs = {c: g["article_id"].head(k).tolist() for c, g in orden.groupby("customer_id")}

    def recomendar(cliente):
        lista = recs.get(cliente, [])
        if len(lista) < k:
            lista = lista + [a for a in respaldo.recomendar(cliente) if a not in lista]
        return lista[:k]
    return recomendar


def cobertura_candidatos(tabla: pd.DataFrame, compras: dict) -> float:
    """% de las compras reales que están entre los candidatos: es el techo del Recall del ranker."""
    candidatos = tabla.groupby("customer_id")["article_id"].apply(set).to_dict()
    total = sum(len(a) for a in compras.values())
    dentro = sum(len(a & candidatos.get(c, set())) for c, a in compras.items())
    return dentro / total if total else np.nan


# ---------------------------------------------------------------------------
# Búsqueda de hiperparámetros
# ---------------------------------------------------------------------------
def crear(config: dict, semilla: int = 42):
    """Crea un clasificador a partir de una configuración {'algoritmo': ..., parámetros...}."""
    p = {k: v for k, v in config.items() if k != "algoritmo"}
    if config["algoritmo"] == "logreg":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(max_iter=2000, **p))
    if config["algoritmo"] == "hgb":
        return HistGradientBoostingClassifier(random_state=semilla, **p)
    raise ValueError(config["algoritmo"])


CONFIGS_LOGREG = [{"algoritmo": "logreg", "C": c, "class_weight": w}
                  for c in [0.01, 0.1, 1.0, 10.0] for w in [None, "balanced"]]

CONFIGS_HGB = [{"algoritmo": "hgb", "learning_rate": lr, "max_leaf_nodes": h, "max_iter": it,
                "l2_regularization": 1.0, "class_weight": w}
               for lr, h, it in [(0.05, 15, 200), (0.1, 31, 200), (0.05, 31, 400), (0.1, 63, 300)]
               for w in [None, "balanced"]]


def buscar(configs, X_train, y_train, tabla_val, y_val, compras_val, evaluar, respaldo, columnas) -> pd.DataFrame:
    """Entrena cada configuración con la semana de entrenamiento y la evalúa en validación.

    Devuelve una fila por configuración con métricas de clasificación (umbral 0,5) y de
    recomendación (Recall@12, Hit Rate@12, MAP@12).
    """
    filas = []
    for cfg in configs:
        inicio = time.time()
        clf = crear(cfg)
        clf.fit(X_train, y_train)
        prob = clf.predict_proba(tabla_val[columnas])[:, 1]
        rec = recomendador_desde_prob(tabla_val, prob, respaldo)
        m_rec = evaluar(compras_val, rec)
        m_clf = metricas_clasificacion(y_val, prob)
        filas.append({"Configuración": ", ".join(f"{k}={v}" for k, v in cfg.items() if k != "algoritmo"),
                      "algoritmo": cfg["algoritmo"], "_cfg": cfg,
                      "Recall@12": m_rec["Recall@12"], "Hit Rate@12": m_rec["Hit Rate@12"], "MAP@12": m_rec["MAP@12"],
                      "Accuracy": m_clf["Accuracy"], "Recall (clasificador)": m_clf["Recall"],
                      "Precision (clasificador)": m_clf["Precision"], "F1": m_clf["F1"], "PR-AUC": m_clf["PR-AUC"],
                      "Segundos": round(time.time() - inicio, 1)})
    return pd.DataFrame(filas)
