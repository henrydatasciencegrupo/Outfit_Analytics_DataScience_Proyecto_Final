"""
roi.py — Costos y retorno de la inversión (ROI) del recomendador
================================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Pregunta del cliente: ¿cuánto hay que invertir y cuánto retorna el recomendador?

Criterios del análisis:
- Costos técnicos con precios publicados de servicios en la nube y de software.
- Beneficio calculado solo sobre la facturación del canal online, donde funciona el recomendador.
- Incluir honorarios profesionales con tarifas norteamericanas, separados de los costos técnicos.
- Simular escenarios con datos sintéticos (Monte Carlo) porque H&M Argentina todavía no vende online
  y los precios del dataset están escalados (no son precios reales).

Todos los supuestos están en este archivo y se pueden cambiar.
"""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------
# 1. Costos técnicos (precios publicados)
# ---------------------------------------------------------------------------------------------
HORAS_MES = 730
PRECIO_HORA = {"m7i.large": 0.1008, "m7i.xlarge": 0.2016}       # AWS on-demand, us-east-1, USD/hora
NUBE_MENSUAL = {
    "API de recomendaciones (2 servidores m7i.large, 24 h)": 2 * PRECIO_HORA["m7i.large"] * HORAS_MES,
    "Reentrenamiento semanal (m7i.xlarge, 10 h por semana)": PRECIO_HORA["m7i.xlarge"] * 10 * 52 / 12,
    "Seguimiento de experimentos (MLflow) y monitoreo (1 m7i.large)": PRECIO_HORA["m7i.large"] * HORAS_MES,
}
IMPREVISTOS_NUBE = 0.20               # almacenamiento, transferencia de datos y otros
SOFTWARE_MENSUAL = 0.0                # pandas, scikit-learn, MLflow, FastAPI, Streamlit: código abierto
PLATAFORMA_MENSUAL = 2_500.0          # tienda online tipo Shopify Plus, contrato de 1 año (referencia)

# ---------------------------------------------------------------------------------------------
# 2. Honorarios profesionales (tarifas norteamericanas)
# ---------------------------------------------------------------------------------------------
HONORARIO_MENSUAL_DS = 1_500.0        # USD por científico de datos por mes (valor del proyecto; referencia: sueldos de EE. UU. de USD 160.000 al año)
INTEGRANTES = 5
MESES_DESARROLLO = 2
DEDICACION_MANTENIMIENTO = 0.25       # un científico de datos al 25% para operar y reentrenar

# ---------------------------------------------------------------------------------------------
# 3. Facturación del canal online (datos públicos de H&M)
# ---------------------------------------------------------------------------------------------
VENTAS_HM_SEK = 228_285e6             # ventas netas del grupo, año fiscal 2025
SEK_USD = 0.104                       # USD por SEK, 2026
PARTE_ONLINE = 0.30                   # el canal online es algo más del 30% de las ventas
MERCADOS_ONLINE = 61
ONLINE_POR_MERCADO_MES = VENTAS_HM_SEK * SEK_USD * PARTE_ONLINE / MERCADOS_ONLINE / 12

# ---------------------------------------------------------------------------------------------
# 4. Escenarios (mínimo, más probable, máximo)
# ---------------------------------------------------------------------------------------------
TAMANO_ARGENTINA = (0.02, 0.10, 0.25)   # facturación online de Argentina como fracción de un mercado online promedio de H&M (mínimo: equivale a la venta online asociada a una sola tienda)
MEJORA_VENTAS = (0.01, 0.03, 0.06)      # venta online extra que genera el recomendador
MARGEN = (0.35, 0.45, 0.534)            # margen de contribución: bruto de H&M menos costos variables online
MESES_RAMPA = 6                         # el canal online crece de 40% a 100% en los primeros 6 meses
HORIZONTE = 12                          # meses de operación evaluados


def costos_tecnicos_mensuales(con_plataforma=False):
    nube = sum(NUBE_MENSUAL.values()) * (1 + IMPREVISTOS_NUBE)
    return nube + SOFTWARE_MENSUAL + (PLATAFORMA_MENSUAL if con_plataforma else 0.0)


def honorarios():
    desarrollo = HONORARIO_MENSUAL_DS * INTEGRANTES * MESES_DESARROLLO
    mantenimiento = HONORARIO_MENSUAL_DS * DEDICACION_MANTENIMIENTO
    return desarrollo, mantenimiento


def tabla_costos():
    desarrollo, mantenimiento = honorarios()
    filas = [{"Tipo": "Técnico (nube)", "Concepto": k, "Única vez (USD)": 0, "Por mes (USD)": round(v)}
             for k, v in NUBE_MENSUAL.items()]
    filas += [
        {"Tipo": "Técnico (nube)", "Concepto": f"Imprevistos ({IMPREVISTOS_NUBE:.0%})", "Única vez (USD)": 0,
         "Por mes (USD)": round(sum(NUBE_MENSUAL.values()) * IMPREVISTOS_NUBE)},
        {"Tipo": "Técnico (software)", "Concepto": "Licencias (todo es código abierto)", "Única vez (USD)": 0, "Por mes (USD)": 0},
        {"Tipo": "Honorarios", "Concepto": f"Desarrollo: {INTEGRANTES} científicos de datos × {MESES_DESARROLLO} meses",
         "Única vez (USD)": round(desarrollo), "Por mes (USD)": 0},
        {"Tipo": "Honorarios", "Concepto": f"Operación y reentrenamiento: 1 científico de datos al {DEDICACION_MANTENIMIENTO:.0%}",
         "Única vez (USD)": 0, "Por mes (USD)": round(mantenimiento)},
        {"Tipo": "Referencia (aparte)", "Concepto": "Plataforma de la tienda online (tipo Shopify Plus)", "Única vez (USD)": 0,
         "Por mes (USD)": round(PLATAFORMA_MENSUAL)},
    ]
    return pd.DataFrame(filas)


def flujo(tamano, mejora, margen, con_plataforma=False, horizonte=HORIZONTE):
    """Flujo mensual en USD: mes 0 = inversión en desarrollo; meses 1..horizonte = operación."""
    desarrollo, mantenimiento = honorarios()
    meses = np.arange(1, horizonte + 1)
    rampa = np.clip(0.4 + 0.6 * (meses - 1) / (MESES_RAMPA - 1), 0, 1)
    facturacion = ONLINE_POR_MERCADO_MES * tamano * rampa
    beneficio = facturacion * mejora * margen
    costo = costos_tecnicos_mensuales(con_plataforma) + mantenimiento
    neto = np.concatenate([[-desarrollo], beneficio - costo])
    return pd.DataFrame({"Mes": np.arange(0, horizonte + 1),
                         "Facturación online (USD)": np.concatenate([[0], facturacion]),
                         "Beneficio del recomendador (USD)": np.concatenate([[0], beneficio]),
                         "Costos (USD)": np.concatenate([[desarrollo], np.full(horizonte, costo)]),
                         "Flujo neto (USD)": neto,
                         "Acumulado (USD)": np.cumsum(neto)})


def mes_recupero(acumulado):
    """Primer mes en que el acumulado deja de ser negativo (None si no ocurre en el horizonte)."""
    pos = np.where(np.asarray(acumulado)[1:] >= 0)[0]
    return int(pos[0] + 1) if len(pos) else None


def resumen(f):
    inversion = f["Costos (USD)"].sum()
    ganancia = f["Beneficio del recomendador (USD)"].sum()
    r6 = f.loc[f["Mes"] <= 6]
    return {"Inversión total (USD)": round(inversion), "Beneficio total (USD)": round(ganancia),
            "Resultado a 12 meses (USD)": round(f["Acumulado (USD)"].iloc[-1]),
            "ROI a 6 meses (%)": round((r6["Beneficio del recomendador (USD)"].sum() - r6["Costos (USD)"].sum())
                                       / r6["Costos (USD)"].sum() * 100, 1),
            "ROI a 12 meses (%)": round((ganancia - inversion) / inversion * 100, 1),
            "Mes de recupero": mes_recupero(f["Acumulado (USD)"])}


def escenarios(con_plataforma=False):
    filas = []
    for i, nombre in enumerate(["Pesimista", "Base", "Optimista"]):
        f = flujo(TAMANO_ARGENTINA[i], MEJORA_VENTAS[i], MARGEN[i], con_plataforma)
        filas.append({"Escenario": nombre, "Facturación online madura por mes (USD)": round(ONLINE_POR_MERCADO_MES * TAMANO_ARGENTINA[i]),
                      "Venta extra por el recomendador (%)": round(MEJORA_VENTAS[i] * 100, 1), "Margen (%)": round(MARGEN[i] * 100, 1),
                      **resumen(f)})
    return pd.DataFrame(filas)


def montecarlo(n=10_000, semilla=42, con_plataforma=False):
    """Simulación con datos sintéticos: cada corrida sortea los supuestos de una distribución triangular."""
    rng = np.random.default_rng(semilla)
    tam = rng.triangular(*TAMANO_ARGENTINA, n)
    mej = rng.triangular(*MEJORA_VENTAS, n)
    mar = rng.triangular(*MARGEN, n)
    acumulados, filas = [], []
    for t, m, g in zip(tam, mej, mar):
        f = flujo(t, m, g, con_plataforma)
        acumulados.append(f["Acumulado (USD)"].to_numpy())
        filas.append({"tamano": t, "mejora": m, "margen": g, **resumen(f)})
    return pd.DataFrame(filas), np.array(acumulados)


def punto_equilibrio(meses=6, con_plataforma=False, mejora=MEJORA_VENTAS[1], margen=MARGEN[1]):
    """Facturación online mensual necesaria para recuperar toda la inversión en `meses` (sin rampa)."""
    desarrollo, mantenimiento = honorarios()
    costo_mes = costos_tecnicos_mensuales(con_plataforma) + mantenimiento
    return (desarrollo / meses + costo_mes) / (mejora * margen)


def punto_equilibrio_operativo(con_plataforma=False, mejora=MEJORA_VENTAS[1], margen=MARGEN[1]):
    """Facturación online mensual a partir de la cual el beneficio del mes cubre el costo del mes."""
    _, mantenimiento = honorarios()
    return (costos_tecnicos_mensuales(con_plataforma) + mantenimiento) / (mejora * margen)


def flujos_powerbi(con_plataforma=False):
    """Tabla larga (escenario × mes) para gráficos interactivos segmentados en Power BI."""
    tablas = []
    for i, nombre in enumerate(["Pesimista", "Base", "Optimista"]):
        f = flujo(TAMANO_ARGENTINA[i], MEJORA_VENTAS[i], MARGEN[i], con_plataforma)
        f.insert(0, "Escenario", nombre)
        f.insert(1, "Incluye plataforma", "Sí" if con_plataforma else "No")
        tablas.append(f)
    return pd.concat(tablas, ignore_index=True).round(2)
