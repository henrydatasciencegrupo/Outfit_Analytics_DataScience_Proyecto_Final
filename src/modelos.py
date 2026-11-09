"""
modelos.py — Modelos de recomendación
=====================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autora: Margot Huaman Quispe

Interfaz común
--------------
Todos los modelos se usan igual, lo que permite compararlos y combinarlos:
    modelo.fit(trans, hasta)        # aprende SOLO con compras anteriores a `hasta`
    modelo.recomendar(cliente_id)   # devuelve una lista ordenada de 12 article_id

Modelos
-------
| # | Modelo               | Tipo                         | Idea                                                    |
|---|----------------------|------------------------------|---------------------------------------------------------|
| 0 | PopularidadReciente  | Baseline                     | Lo más vendido de los últimos N días (lo que se hace hoy)|
| 1 | PopularidadPorEdad   | Personalización simple       | Lo más vendido entre clientes del mismo tramo de edad   |
| 2 | CoCompraRecompra     | No supervisado (item-item)   | "Quienes compraron esto también compraron…" + recompra  |
| 3 | RankerSupervisado    | Supervisado (learning to rank)| Estima la probabilidad de compra combinando todas las señales |

El ranker admite cuatro algoritmos (parámetro `algoritmo`): "hgb" (HistGradientBoosting,
scikit-learn), "xgb" (XGBoost), "lgbm" (LightGBM) y "logreg" (regresión logística).

Modelo final
------------
`modelo_final(...)` construye el modelo elegido para producción (sistema por etapas): el
modelo personalizado ganador para los clientes con historial y "lo más vendido de la
semana" para los clientes nuevos.

Cuando un modelo no tiene información suficiente para un cliente (por ejemplo, un
cliente sin historial), completa la lista con un modelo de respaldo: así nadie queda
sin recomendación (sistema por etapas).
"""
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import pares_cocompra, features_cliente, features_articulo

K = 12

ALGORITMOS = {"logreg": "Regresión logística", "hgb": "HistGradientBoosting",
              "xgb": "XGBoost", "lgbm": "LightGBM"}


def crear_clasificador(algoritmo: str = "hgb", semilla: int = 42):
    """Crea el clasificador del ranker supervisado.

    - "logreg": regresión logística (lineal, muy explicable; requiere imputar y escalar).
    - "hgb":    HistGradientBoosting de scikit-learn (boosting de árboles, admite vacíos).
    - "xgb":    XGBoost (boosting de árboles, referencia de la industria).
    - "lgbm":   LightGBM (boosting de árboles, muy rápido con muchos datos).
    """
    if algoritmo == "hgb":
        return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_leaf_nodes=31,
                                              random_state=semilla)
    if algoritmo == "logreg":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(max_iter=1000))
    if algoritmo == "xgb":
        try:
            from xgboost import XGBClassifier
        except ImportError as e:
            raise ImportError("Falta XGBoost: ejecutar  pip install xgboost") from e
        return XGBClassifier(n_estimators=300, learning_rate=0.08, max_depth=6, subsample=0.8,
                             colsample_bytree=0.8, tree_method="hist", eval_metric="logloss",
                             random_state=semilla, n_jobs=-1)
    if algoritmo == "lgbm":
        try:
            from lightgbm import LGBMClassifier
        except ImportError as e:
            raise ImportError("Falta LightGBM: ejecutar  pip install lightgbm") from e
        return LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.8, random_state=semilla, verbose=-1)
    raise ValueError(f"Algoritmo desconocido: {algoritmo}. Opciones: {list(ALGORITMOS)}")


def _ventana(trans: pd.DataFrame, hasta: pd.Timestamp, dias: int | None) -> pd.DataFrame:
    """Compras anteriores a `hasta`; si se indica `dias`, solo las de esa ventana."""
    d = trans[trans["t_dat"] < hasta]
    if dias is not None:
        d = d[d["t_dat"] >= hasta - pd.Timedelta(days=dias)]
    return d


# ---------------------------------------------------------------------------
# Modelo 0 · Baseline
# ---------------------------------------------------------------------------
class PopularidadReciente:
    """Baseline: las K prendas más vendidas de los últimos `dias` (None = todo el historial).

    Representa lo que la tienda puede hacer hoy sin ciencia de datos. Todo modelo
    propuesto debe superarlo para justificar su costo.
    """

    def __init__(self, dias: int | None = 7, k: int = K):
        self.dias, self.k = dias, k
        self.nombre = f"Baseline: popularidad {dias} días" if dias else "Baseline: popularidad histórica"

    def fit(self, trans, hasta):
        self.top = _ventana(trans, hasta, self.dias)["article_id"].value_counts().head(self.k).index.tolist()
        return self

    def recomendar(self, cliente):
        return self.top


# ---------------------------------------------------------------------------
# Modelo 1 · Popularidad por edad
# ---------------------------------------------------------------------------
class PopularidadPorEdad:
    """Lo más vendido dentro del tramo de edad del cliente; completa con el top general.

    Usa el único dato disponible de un cliente nuevo antes de su primera compra.
    """

    def __init__(self, tramo_por_cliente: dict, dias: int = 7, k: int = K):
        self.tramo, self.dias, self.k = tramo_por_cliente, dias, k
        self.nombre = f"Modelo 1: popularidad por edad ({dias} días)"

    def fit(self, trans, hasta):
        d = _ventana(trans, hasta, self.dias)
        self.general = d["article_id"].value_counts().head(self.k).index.tolist()
        d = d.assign(tramo=d["customer_id"].map(self.tramo))
        conteo = d.groupby("tramo")["article_id"].value_counts()
        self.tops = {t: s.sort_values(ascending=False).head(self.k).index.get_level_values("article_id").tolist()
                     for t, s in conteo.groupby(level=0)}
        return self

    def recomendar(self, cliente):
        lista = self.tops.get(self.tramo.get(cliente), [])
        return (lista + [a for a in self.general if a not in lista])[: self.k]


# ---------------------------------------------------------------------------
# Modelo 2 · Co-compra + recompra (no supervisado)
# ---------------------------------------------------------------------------
class CoCompraRecompra:
    """Filtrado colaborativo item-item (no supervisado).

    Para cada cliente toma sus últimas `n_ultimas` prendas compradas y suma puntos a:
      - recompra: la misma prenda (peso `peso_recompra`), porque en moda se repiten
        básicos, talles y colores;
      - co-compra: las prendas que otros clientes compraron junto con ella el mismo día,
        ponderadas por la frecuencia del par.
    Las compras más recientes pesan más. Si no se alcanzan 12 prendas (o el cliente no
    tiene historial), la lista se completa con el modelo de respaldo.
    """

    def __init__(self, respaldo, dias_pares: int = 28, n_ultimas: int = 10, vecinos: int = 20,
                 peso_recompra: float = 1.0, k: int = K):
        self.respaldo, self.dias_pares, self.n_ultimas = respaldo, dias_pares, n_ultimas
        self.vecinos, self.peso_recompra, self.k = vecinos, peso_recompra, k
        etiqueta = "co-compra + recompra" if peso_recompra > 0 else "co-compra"
        self.nombre = f"Modelo 2: {etiqueta} ({dias_pares} días)"

    def fit(self, trans, hasta):
        # 1) Vecinos de cada artículo según la co-compra reciente
        pares = pares_cocompra(trans, hasta, self.dias_pares)
        pares["peso"] = pares["veces"] / pares.groupby("article_id")["veces"].transform("max")
        pares = pares.groupby("article_id").head(self.vecinos)
        self.vecinos_de = {a: list(zip(g["article_id_vecino"], g["peso"])) for a, g in pares.groupby("article_id")}
        # 2) Últimas compras distintas de cada cliente, con su antigüedad en días
        h = trans[trans["t_dat"] < hasta][["customer_id", "article_id", "t_dat"]]
        h = h.sort_values("t_dat", ascending=False).drop_duplicates(["customer_id", "article_id"])
        h = h.groupby("customer_id").head(self.n_ultimas)
        h["dias"] = (hasta - h["t_dat"]).dt.days
        self.historial = {c: list(zip(g["article_id"], g["dias"])) for c, g in h.groupby("customer_id")}
        return self

    def puntajes(self, cliente) -> dict:
        """Puntaje de co-compra + recompra de cada artículo candidato para el cliente."""
        puntaje = defaultdict(float)
        for articulo, dias in self.historial.get(cliente, []):
            peso_tiempo = 1.0 / (1.0 + dias / 7.0)   # lo comprado esta semana pesa más que hace un mes
            if self.peso_recompra:
                puntaje[articulo] += self.peso_recompra * peso_tiempo
            for vecino, peso in self.vecinos_de.get(articulo, []):
                puntaje[vecino] += peso_tiempo * peso
        return puntaje

    def recomendar(self, cliente):
        puntaje = self.puntajes(cliente)
        lista = [a for a, _ in sorted(puntaje.items(), key=lambda x: -x[1])][: self.k]
        if len(lista) < self.k:
            lista += [a for a in self.respaldo.recomendar(cliente) if a not in lista]
        return lista[: self.k]


# ---------------------------------------------------------------------------
# Modelo 3 · Ranker supervisado
# ---------------------------------------------------------------------------
class RankerSupervisado:
    """Modelo supervisado de ordenamiento ("learning to rank").

    1. Candidatos: une las mejores `n_candidatos` prendas de los modelos 0, 1 y 2.
    2. Features de cada par (cliente, prenda): posición en cada modelo, puntaje de
       co-compra, si es una recompra, popularidad y tendencia de la prenda, popularidad
       en el tramo de edad del cliente, afinidad del cliente con el grupo de la prenda,
       y frecuencia y recencia del cliente.
    3. Entrenamiento: la etiqueta es 1 si el cliente compró la prenda en la semana
       ANTERIOR a `hasta`; las features de ese entrenamiento se calculan con datos
       previos a esa semana (sin fuga de información).
    4. Recomendación: con features calculadas hasta `hasta`, ordena los candidatos por
       probabilidad de compra y devuelve los 12 primeros.
    """

    COLUMNAS = ["rank_pop", "rank_edad", "rank_cocompra", "puntaje_cocompra", "ya_lo_compro",
                "ventas_7d", "ventas_30d", "tendencia", "dias_desde_primera_venta", "precio_articulo",
                "ventas_tramo_7d", "afinidad_grupo", "age", "edad_faltante", "n_compras",
                "dias_desde_ultima", "compras_por_dia_activo"]

    def __init__(self, tramo_por_cliente: dict, cust: pd.DataFrame, art: pd.DataFrame,
                 dias_pares: int = 28, n_candidatos: int = 40, semilla: int = 42, k: int = K,
                 algoritmo: str = "hgb"):
        self.tramo, self.cust, self.art = tramo_por_cliente, cust, art
        self.dias_pares, self.n, self.semilla, self.k = dias_pares, n_candidatos, semilla, k
        self.algoritmo = algoritmo
        self.nombre = "Modelo 3: ranker supervisado"
        self.tabla_prediccion = None

    # ---------- internos ----------
    def _generadores(self, trans, hasta):
        pop = PopularidadReciente(7, k=self.n).fit(trans, hasta)
        edad = PopularidadPorEdad(self.tramo, 7, k=self.n).fit(trans, hasta)
        cocompra = CoCompraRecompra(edad, dias_pares=self.dias_pares, k=self.n).fit(trans, hasta)
        return pop, edad, cocompra

    def _tabla(self, trans, hasta, clientes):
        """Una fila por (cliente, candidato) con features calculadas solo con datos anteriores a `hasta`."""
        pop, edad, cocompra = self._generadores(trans, hasta)
        filas = []
        for c in clientes:
            puntos = cocompra.puntajes(c)
            posiciones = {}
            for fuente, lista in [("rank_pop", pop.recomendar(c)), ("rank_edad", edad.recomendar(c)),
                                  ("rank_cocompra", [a for a, _ in sorted(puntos.items(), key=lambda x: -x[1])][: self.n])]:
                for pos, a in enumerate(lista, 1):
                    posiciones.setdefault(a, {})[fuente] = pos
            ya_comprados = {a for a, _ in cocompra.historial.get(c, [])}
            for a, r in posiciones.items():
                filas.append({"customer_id": c, "article_id": a, **r, "puntaje_cocompra": puntos.get(a, 0.0),
                              "ya_lo_compro": int(a in ya_comprados)})
        t = pd.DataFrame(filas)
        if t.empty:
            return t
        for col in ["rank_pop", "rank_edad", "rank_cocompra"]:
            t[col] = t[col].fillna(self.n + 1) if col in t else self.n + 1   # no figuraba en esa lista

        fa = features_articulo(trans, self.art, hasta).set_index("article_id")
        t = t.join(fa[["ventas_7d", "ventas_30d", "tendencia", "dias_desde_primera_venta"]], on="article_id")
        if "precio_medio" in fa:
            t["precio_articulo"] = t["article_id"].map(fa["precio_medio"])
        fc = features_cliente(trans, self.cust, self.art, hasta).set_index("customer_id")
        t = t.join(fc[["age", "edad_faltante", "n_compras", "dias_desde_ultima", "compras_por_dia_activo"]],
                   on="customer_id")
        t["edad_faltante"] = t["edad_faltante"].astype(float)

        # Popularidad de la prenda dentro del tramo de edad del cliente (última semana)
        semana = trans[(trans["t_dat"] < hasta) & (trans["t_dat"] >= hasta - pd.Timedelta(days=7))]
        por_tramo = (semana.assign(tramo=semana["customer_id"].map(self.tramo))
                           .groupby(["tramo", "article_id"]).size().rename("ventas_tramo_7d").reset_index())
        t["tramo"] = t["customer_id"].map(self.tramo)
        t = t.merge(por_tramo, on=["tramo", "article_id"], how="left")
        t["ventas_tramo_7d"] = t["ventas_tramo_7d"].fillna(0)

        # Afinidad: % de las compras del cliente en el grupo de producto de la prenda
        preferencias = [c for c in fc.columns if c.startswith("pref_")]
        if "index_group_name" in self.art and preferencias:
            largo = (fc[preferencias].reset_index()
                       .melt(id_vars="customer_id", var_name="grupo", value_name="afinidad_grupo").dropna())
            largo["grupo"] = largo["grupo"].str[len("pref_"):]
            t["grupo"] = t["article_id"].map(self.art.set_index("article_id")["index_group_name"])
            t = t.merge(largo, on=["customer_id", "grupo"], how="left")

        for col in self.COLUMNAS:
            if col not in t:
                t[col] = np.nan
        return t

    # ---------- interfaz ----------
    def fit(self, trans, hasta, clientes=None):
        """Entrena con la semana anterior a `hasta` y, si se indican, prepara las recomendaciones de `clientes`."""
        inicio = hasta - pd.Timedelta(days=7)
        semana = trans[(trans["t_dat"] >= inicio) & (trans["t_dat"] < hasta)]
        compras = semana.groupby("customer_id")["article_id"].apply(set).to_dict()
        X = self._tabla(trans[trans["t_dat"] < inicio], inicio, list(compras))
        y = np.array([a in compras[c] for c, a in zip(X["customer_id"], X["article_id"])], dtype=int)
        if y.sum() == 0:
            raise ValueError("Ningún candidato fue comprado en la semana de entrenamiento: no hay ejemplos para aprender.")
        self.positivos_entrenamiento = int(y.sum())
        self.filas_entrenamiento = len(y)
        self.clf = crear_clasificador(self.algoritmo, self.semilla)
        self.clf.fit(X[self.COLUMNAS], y)
        self.X_entrenamiento, self.y_entrenamiento = X[self.COLUMNAS], y

        self._trans, self._hasta = trans[trans["t_dat"] < hasta], hasta
        self._respaldo = PopularidadPorEdad(self.tramo, 7, k=self.k).fit(trans, hasta)
        self.recs = {}
        if clientes is not None:
            self.preparar(clientes)
        return self

    def preparar(self, clientes):
        """Calcula en bloque las recomendaciones de muchos clientes (más eficiente que de a uno)."""
        pendientes = [c for c in clientes if c not in self.recs]
        if not pendientes:
            return self
        t = self._tabla(self._trans, self._hasta, pendientes)
        self.tabla_prediccion = t if self.tabla_prediccion is None else pd.concat([self.tabla_prediccion, t])
        self._ordenar(t)
        return self

    def _ordenar(self, t):
        """Ordena los candidatos de `t` por probabilidad de compra y guarda los 12 primeros por cliente."""
        t = t.copy()
        t["prob"] = self.clf.predict_proba(t[self.COLUMNAS])[:, 1]
        t = t.sort_values(["customer_id", "prob"], ascending=[True, False])
        for c, g in t.groupby("customer_id"):
            self.recs[c] = g["article_id"].head(self.k).tolist()

    def usar_algoritmo(self, algoritmo: str):
        """Reentrena el clasificador con otro algoritmo (mismos datos) y recalcula las recomendaciones preparadas."""
        self.algoritmo = algoritmo
        self.clf = crear_clasificador(algoritmo, self.semilla)
        self.clf.fit(self.X_entrenamiento, self.y_entrenamiento)
        self.recs = {}
        if self.tabla_prediccion is not None:
            self._ordenar(self.tabla_prediccion)
        return self

    def recomendar(self, cliente):
        if cliente not in self.recs:
            self.preparar([cliente])
        lista = self.recs.get(cliente, [])
        if len(lista) < self.k:
            lista = lista + [a for a in self._respaldo.recomendar(cliente) if a not in lista]
        return lista[: self.k]

    def comparar_algoritmos(self, compras: dict, algoritmos=("logreg", "hgb", "xgb", "lgbm"), evaluar=None):
        """Entrena varios algoritmos con la MISMA tabla de entrenamiento y los evalúa sobre los
        MISMOS candidatos (los preparados en `fit`). Así la única diferencia es el algoritmo.

        Devuelve (tabla_de_resultados, recomendaciones_por_algoritmo). Los algoritmos que no
        estén instalados se informan y se omiten.
        """
        import time
        if self.tabla_prediccion is None:
            raise ValueError("Primero ejecutar fit(..., clientes=...) para preparar los candidatos.")
        t = self.tabla_prediccion
        filas, recs_por_alg = [], {}
        for alg in algoritmos:
            try:
                clf = crear_clasificador(alg, self.semilla)
            except ImportError as e:
                print(f"⚠️ {ALGORITMOS[alg]} omitido: {e}")
                continue
            inicio = time.time()
            clf.fit(self.X_entrenamiento, self.y_entrenamiento)
            prob = clf.predict_proba(t[self.COLUMNAS])[:, 1]
            segundos = time.time() - inicio
            orden = t[["customer_id", "article_id"]].assign(prob=prob).sort_values(
                ["customer_id", "prob"], ascending=[True, False])
            recs = {c: g["article_id"].head(self.k).tolist() for c, g in orden.groupby("customer_id")}
            recs_por_alg[alg] = recs

            def rec(cliente, recs=recs):
                lista = recs.get(cliente, [])
                if len(lista) < self.k:
                    lista = lista + [a for a in self._respaldo.recomendar(cliente) if a not in lista]
                return lista[: self.k]

            fila = {"Algoritmo": ALGORITMOS[alg], "clave": alg, "Segundos de entrenamiento": round(segundos, 1)}
            if evaluar is not None:
                fila.update(evaluar(compras, rec))
            filas.append(fila)
        return pd.DataFrame(filas), recs_por_alg


# ---------------------------------------------------------------------------
# Modelo final para producción: sistema por etapas
# ---------------------------------------------------------------------------
class SistemaPorEtapas:
    """Un único modelo en producción que decide según lo que se sabe del cliente.

    - Cliente CON historial (compró antes de `hasta`): recomendaciones del modelo personalizado.
    - Cliente SIN historial (cliente nuevo): recomendaciones del modelo de respaldo.

    La asignación de cada etapa se decide en la semana de validación: ahí el mejor modelo
    para clientes nuevos fue "lo más vendido de la semana" (la edad no lo superó: H1).
    """

    def __init__(self, personalizado, respaldo, con_historial: set, etiqueta: str = "personalizado"):
        self.personalizado, self.respaldo, self.con_historial = personalizado, respaldo, con_historial
        self.nombre = f"Modelo final: {etiqueta} + lo más vendido para nuevos"

    def recomendar(self, cliente):
        if cliente in self.con_historial:
            return self.personalizado.recomendar(cliente)
        return self.respaldo.recomendar(cliente)


def modelo_final(personalizado, trans, hasta, dias_baseline: int = 7, etiqueta: str = "personalizado"):
    """Construye el modelo final (sistema por etapas) entrenado hasta `hasta`.

    personalizado : modelo ya entrenado hasta `hasta` (por ejemplo, el ranker con el mejor algoritmo
                    o la co-compra), o cualquier objeto con el método `recomendar(cliente)`.
    """
    respaldo = PopularidadReciente(dias_baseline).fit(trans, hasta)
    con_historial = set(trans.loc[trans["t_dat"] < hasta, "customer_id"].unique())
    return SistemaPorEtapas(personalizado, respaldo, con_historial, etiqueta)
