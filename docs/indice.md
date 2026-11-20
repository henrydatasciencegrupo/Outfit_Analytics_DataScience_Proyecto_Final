# Índice del repositorio

Guía para recorrer el proyecto **Lookwise Data Lab: recomendador para clientes sin historial (cold start)**. Sigue el recorrido del proyecto según la metodología **CRISP-DM** (del negocio a los datos, el modelado, la evaluación y el despliegue) y, para cada entregable que pide la consigna y cada criterio de las rúbricas de la Demo 1 y la Demo Final, indica dónde está la evidencia en el repositorio.

> **Estado:** versión del 20/11/2026. Lo marcado como *pendiente* se completa antes de la Demo Final; lo marcado como *en revisión* está en un pull request abierto.
>
> **Cómo se mantiene:** este índice se actualiza con cada entrega. Quien suba algo nuevo (por ejemplo, la demo, el dashboard o el manual) agrega su enlace en la sección que corresponde y cambia el estado a *Listo* en el mismo pull request.

## Cómo leer este repositorio

Para entender el proyecto en pocos minutos:

1. [`README.md`](../README.md): de qué se trata, resultados principales, limitaciones y equipo.
2. [`docs/eda.md`](eda.md): qué encontramos en los datos.
3. [`docs/modelado.md`](modelado.md): modelos, resultados y recomendaciones para H&M.
4. [`docs/plan_validacion.md`](plan_validacion.md): cómo se validó el modelo y cómo se probaría en producción antes de escalar.
5. [`docs/costos_roi.md`](costos_roi.md): cuánto cuesta el sistema y en cuánto tiempo se recupera la inversión.

Para reproducirlo, seguir la sección **Cómo reproducirlo** del [`README.md`](../README.md).

## Mapa de la rúbrica

Dónde está la evidencia de cada criterio de evaluación.

| Instancia | Criterio | Evidencia principal | Estado |
|---|---|---|---|
| Demo 1 | Calidad del análisis exploratorio | [Sección 3](#3-análisis-exploratorio-eda) | Listo |
| Demo 1 | Tratamiento de datos | [Sección 4](#4-tratamiento-de-datos) | Listo |
| Demo 1 | Ingeniería de características | [Sección 5](#5-ingeniería-de-características) | Listo |
| Demo 1 | Modelado del sistema de recomendación | [Sección 6](#6-modelos) | Listo |
| Demo 1 | Justificación del modelo elegido | [Sección 7](#7-selección-y-justificación-del-modelo) | Listo |
| Demo 1 y Final | Metodología ágil y retrospectiva | [Sección 14](#14-metodología-y-trabajo-en-equipo) | Retrospectiva pendiente |
| Demo Final | Plan de validación y evaluación | [Sección 8](#8-plan-de-validación-y-evaluación) | Listo |
| Demo Final | Pipeline reproducible (end-to-end) | [Sección 10](#10-pipeline-reproducible) | MLflow y GitHub Actions pendientes |
| Demo Final | Despliegue funcional | [Sección 11](#11-despliegue) | Manual de usuario pendiente |
| Demo Final | Dashboard interactivo | [Sección 12](#12-dashboard-interactivo) | Pendiente |
| Demo Final | Comprensión y defensa técnica | [Secciones 7 a 9](#7-selección-y-justificación-del-modelo) y [sección 13](#13-conclusiones-limitaciones-y-recomendaciones) | Listo |
| Ambas | Calidad de la presentación y trabajo en equipo | [Sección 14](#14-metodología-y-trabajo-en-equipo) | Deck final pendiente |

## Entregables de la consigna

| Entregable | Dónde | Estado |
|---|---|---|
| Documento de formulación del PF y diseño de solución | [`README.md`](../README.md) → *Contexto y objetivo* · [`docs/modelado.md`](modelado.md) → *2. Qué hicimos* | Listo |
| Análisis exploratorio e ingeniería de características | [Secciones 3 a 5](#3-análisis-exploratorio-eda) | Listo |
| Prototipo funcional | [`models/`](../models/) · API en [`api/`](../api/) · demo en [`app/`](../app/) | Listo |
| Plan de validación y despliegue | [`docs/plan_validacion.md`](plan_validacion.md) | Listo |
| Informe técnico y manual de usuario | Documentación en [`docs/`](.) · manual de usuario | Manual pendiente |
| Herramienta de comunicación | Presentación final y dashboard | Pendiente |

## 1. Problema y contexto

| Qué | Dónde |
|---|---|
| Problema de negocio, objetivo, alcance y KPIs | [`README.md`](../README.md) → *Contexto y objetivo* |
| Del KPI de negocio a la métrica técnica | [`notebooks/03_baseline.ipynb`](../notebooks/03_baseline.ipynb) → sección 2.3 · [`docs/plan_validacion.md`](plan_validacion.md) → *4. Métricas de evaluación* |
| Contexto del EDA | [`docs/eda.md`](eda.md) → *Contexto y objetivo* |

## 2. Datos y muestra

| Qué | Dónde |
|---|---|
| Origen de los datos, reglas de uso y cómo obtenerlos | [`docs/dataset.md`](dataset.md) |
| Cómo se armó la muestra del 10% (p10), paso a paso | [`notebooks/01_muestreo_p10.ipynb`](../notebooks/01_muestreo_p10.ipynb) · [`docs/dataset.md`](dataset.md) → *Cómo se armó la muestra, paso a paso* |
| Criterio de muestreo y cómo escalar la muestra | [`docs/plan_validacion.md`](plan_validacion.md) → *2. Muestra de datos para entrenar y evaluar* |
| Controles de integridad y representatividad | [`docs/controles_integridad.md`](controles_integridad.md) |
| Significado de cada variable | [`docs/glosario_variables.md`](glosario_variables.md) |

Los datos no se incluyen en el repositorio: se dejan en `dataset/p10/` (ver [`docs/dataset.md`](dataset.md) → *Dónde dejar los archivos*).

## 3. Análisis exploratorio (EDA)

| Qué | Dónde |
|---|---|
| EDA final, con salidas | [`notebooks/02_EDA_unificado_p10.ipynb`](../notebooks/02_EDA_unificado_p10.ipynb) |
| Exploración individual previa | [`notebooks/02_EDA_individual_p10.ipynb`](../notebooks/02_EDA_individual_p10.ipynb) |
| Hallazgos principales: estacionalidad, cola larga, clientes fríos, edad | [`docs/eda.md`](eda.md) → *Resumen: principales hallazgos del EDA* |
| Gráficos del EDA | [`reports/figures/`](../reports/figures/) (archivos `eda_01` a `eda_08`) |

## 4. Tratamiento de datos

| Qué | Dónde |
|---|---|
| Decisiones del grupo: duplicados, meses atípicos, edad vacía, variables excluidas | [`docs/eda.md`](eda.md) → *Decisiones tomadas (del grupo)* · [`README.md`](../README.md) → *Decisiones sobre los datos* |
| Tratamiento cuantificado (casos afectados y justificación de cada decisión) | [`reports/tratamiento_datos.csv`](../reports/tratamiento_datos.csv) · [`notebooks/04_pipeline_modelos.ipynb`](../notebooks/04_pipeline_modelos.ipynb) → sección 1 |
| Código del tratamiento | [`src/datos.py`](../src/datos.py) |

## 5. Ingeniería de características

| Qué | Dónde |
|---|---|
| Pipeline de features sin fuga de información | [`src/features.py`](../src/features.py) · [`notebooks/04_pipeline_modelos.ipynb`](../notebooks/04_pipeline_modelos.ipynb) → sección 2 |
| Qué variables pesan más en el modelo final | [`notebooks/06_metricas_optimizacion_decisiones.ipynb`](../notebooks/06_metricas_optimizacion_decisiones.ipynb) → sección 9 · [`reports/importancia_variables.csv`](../reports/importancia_variables.csv) |

## 6. Modelos

| Qué | Dónde |
|---|---|
| Baseline (lo más vendido) y Modelo 1 (edad) | [`notebooks/03_baseline.ipynb`](../notebooks/03_baseline.ipynb) |
| Modelo 2 (co-compra + recompra, no supervisado) y Modelo 3 (ranker supervisado) | [`notebooks/04_pipeline_modelos.ipynb`](../notebooks/04_pipeline_modelos.ipynb) |
| Modelo final: baseline optimizado, hiperparámetros, regresión logística frente a Gradient Boosting y co-compra optimizada | [`notebooks/06_metricas_optimizacion_decisiones.ipynb`](../notebooks/06_metricas_optimizacion_decisiones.ipynb) (notebook final; los 03 a 05 son etapas previas) |
| Ejemplos de recomendaciones para clientes reales | [`notebooks/06_metricas_optimizacion_decisiones.ipynb`](../notebooks/06_metricas_optimizacion_decisiones.ipynb) → sección 10 |
| Código de los modelos | [`src/modelos.py`](../src/modelos.py) · [`src/optimizacion.py`](../src/optimizacion.py) |
| Resumen de los modelos y sus ideas | [`docs/modelado.md`](modelado.md) → *2. Qué hicimos* |

## 7. Selección y justificación del modelo

| Qué | Dónde |
|---|---|
| Por qué Gradient Boosting (prueba con intervalo de confianza) y por qué un sistema por etapas | [`notebooks/06_metricas_optimizacion_decisiones.ipynb`](../notebooks/06_metricas_optimizacion_decisiones.ipynb) → secciones 6 y 11 |
| Alternativas descartadas y decisiones durante el modelado | [`docs/modelado.md`](modelado.md) → *4. Qué pasó en el camino* |
| Verificación de hipótesis | [`docs/modelado.md`](modelado.md) → *3. Qué encontramos* |

## 8. Plan de validación y evaluación

| Qué | Dónde |
|---|---|
| Plan completo: muestra, protocolo, métricas, regla de decisión, resultados, piloto A/B, monitoreo y limitaciones | [`docs/plan_validacion.md`](plan_validacion.md) |
| Corte temporal (train, validación y test) y por qué | [`docs/plan_validacion.md`](plan_validacion.md) → *3. Protocolo de validación offline* |
| Métricas y por qué decide Recall@12 (y no la Accuracy) | [`docs/plan_validacion.md`](plan_validacion.md) → *4. Métricas de evaluación* · [`src/metricas.py`](../src/metricas.py) |
| Simulación de clientes nuevos (desde cuántas compras personalizar) | [`notebooks/05_simulacion_cold_start.ipynb`](../notebooks/05_simulacion_cold_start.ipynb) |
| Evaluación final en la semana de test | [`notebooks/06_metricas_optimizacion_decisiones.ipynb`](../notebooks/06_metricas_optimizacion_decisiones.ipynb) → sección 8 |
| Piloto A/B simulado antes de escalar | [`notebooks/07_piloto_ab_simulado.ipynb`](../notebooks/07_piloto_ab_simulado.ipynb) · [`src/piloto.py`](../src/piloto.py) |
| Costos y retorno de la inversión: cuánto invierte H&M, punto de equilibrio, escenarios y simulación Monte Carlo | [`docs/costos_roi.md`](costos_roi.md) · [`notebooks/08_costos_roi.ipynb`](../notebooks/08_costos_roi.ipynb) · [`src/roi.py`](../src/roi.py) |

## 9. Resultados y modelo final

| Qué | Dónde |
|---|---|
| Resultados en la semana de test | [`docs/modelado.md`](modelado.md) → *3. Qué encontramos* · [`README.md`](../README.md) → *Modelado y evaluación* |
| Tablas de resultados (CSV) | [`reports/`](../reports/), por ejemplo [`resultados_test_optimizado.csv`](../reports/resultados_test_optimizado.csv), [`intervalos_confianza_test.csv`](../reports/intervalos_confianza_test.csv), [`simulacion_cold_start.csv`](../reports/simulacion_cold_start.csv), [`piloto_ab_simulado.csv`](../reports/piloto_ab_simulado.csv) y [`roi_escenarios.csv`](../reports/roi_escenarios.csv) |
| Gráficos | [`reports/figures/`](../reports/figures/) |
| Modelo final entrenado (Gradient Boosting), su configuración y las recomendaciones de la semana de test | [`models/`](../models/) |

## 10. Pipeline reproducible

| Qué | Dónde | Estado |
|---|---|---|
| Código separado por etapa: datos, features, métricas, modelos, optimización, simulación, piloto y ROI | [`src/`](../src/) | Listo |
| Ejecución de punta a punta | [`src/pipeline.py`](../src/pipeline.py) | Listo |
| Librerías necesarias | [`requirements.txt`](../requirements.txt) | Listo |
| Pasos para reproducir (rutas relativas, semillas fijas) | [`README.md`](../README.md) → *Cómo reproducirlo* | Listo |
| Seguimiento de experimentos con MLflow | | Pendiente |
| Automatización con GitHub Actions | | Pendiente |

## 11. Despliegue

| Qué | Dónde | Estado |
|---|---|---|
| Aplicación de demostración (Streamlit): elegir un cliente y ver sus 12 recomendaciones | [`app/`](../app/) · [`docs/demo_api_streamlit.md`](demo_api_streamlit.md) | Listo |
| API de recomendaciones | [`api/`](../api/) · [`docs/demo_api_streamlit.md`](demo_api_streamlit.md) | Listo |
| Manual de usuario | | Pendiente |
| Plan de despliegue: piloto A/B, escalado por etapas y monitoreo | [`docs/plan_validacion.md`](plan_validacion.md) → secciones 7 y 8 | Listo |

## 12. Dashboard interactivo

| Qué | Dónde | Estado |
|---|---|---|
| Dashboard en Power BI con métricas y resultados | [`dashboard/`](../dashboard/) | Pendiente |
| Datos del dashboard | [`reports/`](../reports/) (CSV) | Listo |

## 13. Conclusiones, limitaciones y recomendaciones

| Qué | Dónde |
|---|---|
| Recomendaciones para H&M | [`docs/modelado.md`](modelado.md) → *5. Recomendaciones para H&M* |
| Limitaciones y oportunidades de mejora | [`README.md`](../README.md) → *Limitaciones* · [`docs/eda.md`](eda.md) → *Limitaciones a declarar* · [`docs/plan_validacion.md`](plan_validacion.md) → *9. Limitaciones y oportunidades de mejora* |
| Próximos pasos | [`docs/modelado.md`](modelado.md) → *Próximos pasos del proyecto* |

## 14. Metodología y trabajo en equipo

| Qué | Dónde | Estado |
|---|---|---|
| Metodología: CRISP-DM con Scrum (sprints de una semana, dailies, demos) | [`README.md`](../README.md) | Listo |
| Integrantes, roles y LinkedIn | [`README.md`](../README.md) → *Equipo* | Listo |
| Versionamiento: ramas por integrante y pull requests aprobados por un par | Historial de pull requests del repositorio | Listo |
| Guía para resolver errores de Git | [`docs/solucion_errores_git.md`](solucion_errores_git.md) | Listo |
| Retrospectiva de los sprints: qué funcionó, qué mejorar y aprendizajes | | Pendiente |
| Presentación final | | Pendiente |
