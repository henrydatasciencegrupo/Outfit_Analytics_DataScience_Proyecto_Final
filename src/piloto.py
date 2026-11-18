"""
piloto.py — Piloto en producción (prueba A/B) antes de escalar el recomendador
==============================================================================
Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)
Autor: Lookwise Data Lab

Herramientas para el plan de validación en producción (docs/plan_validacion.md):

1. `asignar_grupo`: asigna cada cliente al grupo "modelo" o "control" con un hash fijo.
   El mismo cliente cae siempre en el mismo grupo, y para escalar solo se sube el porcentaje:
   los clientes que ya estaban en el grupo "modelo" siguen ahí.
2. `tamano_muestra`: cuántos clientes hacen falta por grupo para detectar una mejora dada.
3. `balance_por_grupo`: control de que los dos grupos sean comparables (por ejemplo, por tramo de edad).
4. `comparar_grupos`: diferencia de una tasa entre grupos con su intervalo de confianza del 95%.

Por qué un hash y no un sorteo aleatorio común
----------------------------------------------
Un sorteo con `random` cambia cada vez que se ejecuta. El hash convierte el `customer_id` en un número
fijo entre 0 y 9.999: es reproducible, no depende del orden de llegada de los clientes y no requiere
guardar una tabla de asignaciones. Es el mismo principio que se usó para armar la muestra p10
(notebooks/01_muestreo_p10.ipynb), con otra "sal" para que el piloto sea independiente de esa muestra.
"""
import hashlib
from statistics import NormalDist

import numpy as np
import pandas as pd

SAL_PILOTO = "lookwise-piloto"   # distinta de la sal del muestreo ("lookwise42")
CUBETAS = 10_000                 # cada cliente recibe un número entre 0 y 9.999
ETAPAS_ESCALADO = [10, 20, 50, 100]   # % de clientes que ve el modelo en cada etapa


def cubeta(customer_id: str, sal: str = SAL_PILOTO) -> int:
    """Número fijo entre 0 y 9.999 calculado a partir del cliente (SHA-256 de `customer_id + sal`)."""
    digesto = hashlib.sha256(f"{customer_id}{sal}".encode("utf-8")).hexdigest()
    return int(digesto[:15], 16) % CUBETAS


def asignar_grupo(customer_id: str, porcentaje_modelo: float = 10, sal: str = SAL_PILOTO) -> str:
    """Devuelve "modelo" si el cliente ve las recomendaciones personalizadas y "control" si ve lo más vendido.

    Con `porcentaje_modelo=10`, entran al grupo "modelo" los clientes con cubeta < 1.000.
    Al subir a 20, entran los de cubeta < 2.000: los anteriores siguen adentro (asignación anidada).
    """
    if not 0 <= porcentaje_modelo <= 100:
        raise ValueError("porcentaje_modelo debe estar entre 0 y 100")
    return "modelo" if cubeta(customer_id, sal) < porcentaje_modelo / 100 * CUBETAS else "control"


def tamano_muestra(tasa_base: float, mejora_minima: float, alfa: float = 0.05, potencia: float = 0.80) -> int:
    """Clientes necesarios por grupo para detectar `mejora_minima` (en proporción) sobre `tasa_base`.

    Prueba de dos proporciones, bilateral. Ejemplo: tasa_base=0.07 y mejora_minima=0.01
    (de 7% a 8% de clientes con al menos una compra de su vitrina).
    """
    z_alfa = NormalDist().inv_cdf(1 - alfa / 2)
    z_beta = NormalDist().inv_cdf(potencia)
    p1, p2 = tasa_base, tasa_base + mejora_minima
    p_media = (p1 + p2) / 2
    numerador = (z_alfa * np.sqrt(2 * p_media * (1 - p_media)) + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return int(np.ceil(numerador / mejora_minima ** 2))


def balance_por_grupo(clientes: pd.DataFrame, columna: str = "tramo_edad") -> pd.DataFrame:
    """Reparto (%) de `columna` dentro de cada grupo. Si los grupos son comparables, los porcentajes se parecen.

    `clientes` debe tener las columnas `grupo` y `columna`.
    """
    tabla = pd.crosstab(clientes[columna], clientes["grupo"], normalize="columns") * 100
    tabla["diferencia (puntos)"] = (tabla.get("modelo", 0) - tabla.get("control", 0)).abs()
    return tabla.round(2)


def comparar_grupos(exitos_modelo: int, n_modelo: int, exitos_control: int, n_control: int, alfa: float = 0.05) -> dict:
    """Diferencia de tasas (modelo − control) con intervalo de confianza normal.

    Regla de escalado: se pasa a la etapa siguiente solo si el intervalo no incluye el 0
    y la diferencia es positiva.
    """
    p_m, p_c = exitos_modelo / n_modelo, exitos_control / n_control
    error = np.sqrt(p_m * (1 - p_m) / n_modelo + p_c * (1 - p_c) / n_control)
    z = NormalDist().inv_cdf(1 - alfa / 2)
    dif = p_m - p_c
    return {"tasa_modelo": p_m, "tasa_control": p_c, "diferencia": dif,
            "ic_bajo": dif - z * error, "ic_alto": dif + z * error,
            "escalar": bool(dif - z * error > 0)}


if __name__ == "__main__":
    # Demostración con identificadores ficticios: reparto, anidamiento y tamaño de muestra
    ids = [f"cliente_{i:05d}" for i in range(20_000)]
    g10 = {c for c in ids if asignar_grupo(c, 10) == "modelo"}
    g20 = {c for c in ids if asignar_grupo(c, 20) == "modelo"}
    print(f"Grupo modelo al 10%: {len(g10) / len(ids):.1%} · al 20%: {len(g20) / len(ids):.1%} · "
          f"anidado: {g10 <= g20}")
    print(f"Clientes por grupo para detectar +1 punto sobre 7% de Hit Rate: {tamano_muestra(0.07, 0.01):,}")
