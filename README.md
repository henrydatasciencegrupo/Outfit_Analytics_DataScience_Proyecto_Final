# Lookwise Data Lab: recomendador para clientes sin historial (cold start)

Proyecto final del bootcamp de Data Science de Soy Henry, hecho por el equipo **Lookwise Data Lab**. Metodología: **CRISP-DM con Scrum (sprints)**.

## Contexto y objetivo

H&M, multinacional sueca de moda, prevé abrir su primera tienda en Argentina en 2027. Como escenario del caso, planteamos que la apertura vaya acompañada del lanzamiento de su tienda online. Sin clientes ni compras locales, el sitio no puede personalizar la experiencia de sus primeros visitantes (*cold start*). Diseñamos un sistema de recomendación para ese lanzamiento.

- **Módulo 1 (principal):** ranking de 12 productos para clientes nuevos o con poco historial, evaluado frente a un baseline de popularidad con **Recall@12** como métrica de decisión (y MAP@12, Precision@12 y Hit Rate@12 como apoyo), incluyendo clientes simulados como «fríos».
- **Módulo 2 (posible extensión):** productos complementarios («Completá el look»).

## Datos

Dataset **H&M Personalized Fashion Recommendations**. No se incluye en este repositorio: ver [`docs/dataset_README.md`](docs/dataset_README.md) para obtenerlo, ver las fuentes y referencias y reproducir la muestra del 10% (p10) que usamos. El significado de cada variable está en [`docs/glosario_variables.md`](docs/glosario_variables.md).

## Estructura

```text
notebooks/        muestreo, EDA (02), baseline (03), modelos (04), simulación de clientes nuevos (05)
                  y métricas, optimización y decisiones del modelo (06)
src/              código del pipeline (datos, features, métricas, modelos, optimización, simulación)
models/           modelo final entrenado y su configuración
reports/          resultados en CSV y gráficos
docs/             documentación por tema: EDA, datos y fuentes, controles de la muestra, glosario de variables
requirements.txt
```

En `notebooks/`, `02_EDA_unificado_p10.ipynb` es el EDA final (con salidas) y `02_EDA_individual_p10.ipynb`, la pre-exploración individual.

## Cómo reproducirlo

1. Instalar las librerías (Python 3.10 o superior):

   ```bash
   pip install -r requirements.txt
   ```

2. Conseguir los datos, de **una de estas dos formas**:
   - **Desde cero:** aceptar las condiciones de uso del dataset (ver [`docs/dataset_README.md`](docs/dataset_README.md)), descargar los tres CSV y correr `notebooks/muestreo_p10_documentado.ipynb` (antes hay que poner en la celda de rutas dónde guardaste los CSV). Genera la muestra p10 con una semilla fija, así que todas obtienen la misma.
   - **Con la muestra ya armada:** pedirle al equipo los tres archivos Parquet de la p10 (unos 63 MB) y dejarlos en `dataset/p10/` (esa carpeta no se sube al repositorio). Ver la estructura en [`docs/dataset_README.md`](docs/dataset_README.md).
3. **Correr el EDA:** abrir `notebooks/02_EDA_unificado_p10.ipynb` desde la carpeta `notebooks/` y ejecutar todas las celdas.
4. **Correr el modelado:** ejecutar los notebooks `03`, `04`, `05` y `06` en ese orden, o el pipeline completo desde la carpeta del repositorio:

   ```bash
   python src/pipeline.py --base dataset/p10 --salida reports
   ```

   Los resultados y las decisiones están en la sección [Modelado y evaluación](#modelado-y-evaluación) de este README y en el notebook `06`.

## Estado

**Sprint 1:** muestreo, análisis exploratorio y modelado (baseline, modelos y simulación de clientes nuevos) realizados sobre la muestra p10. **Sprint 2:** demo en Streamlit y dashboard. Corte train/test por fecha: el test es del 16 al 22/9/2020 (siete días, la última semana del dataset) y todo lo anterior es entrenamiento; en el modelado, ese entrenamiento se divide en train hasta el 8/9 y validación del 9 al 15/9.

## Principales hallazgos del EDA

- **Muestra p10:** 110.252 clientes, 2.226.486 compras y 105.542 artículos, del 20/9/2018 al 22/9/2020, sin días sin compras. Integridad completa entre tablas.
- **Duplicados:** el 11,96% de las compras son filas repetidas; no se puede confirmar si son varias unidades, distintos talles o devoluciones. No se eliminan: la tabla no tiene talle ni cantidad e incluye compras devueltas, y hay 17.647 filas repetidas que solo difieren en el precio. Borrarlas perdería información posiblemente real y no se puede deshacer; por eso se ofrecen las dos versiones y se elige con el modelo funcionando.
- **Edad:** 1,10% de vacíos; la distribución tiene dos grupos (alrededor de los 20 a 30 y de los 50 años). Los clientes sin edad compran menos (mediana de 3 compras contra 8). No se imputa en la tabla original: son pocos y en el test solo 7 clientes no tienen edad (ninguno es frío); que falte la edad es informativo y rellenar en silencio taparía esa señal; y cómo imputar depende del algoritmo, por eso se ofrecen tres columnas y cada modelo elige.
- **Estacionalidad:** las ventas siguen un patrón del hemisferio norte (ropa de baño entre mayo y julio, punto entre septiembre y noviembre), invertido respecto de Argentina.
- **Cola larga:** los 12 artículos más vendidos suman 1,1% de las ventas y hacen falta 6.290 artículos para cubrir la mitad.
- **Clientes fríos:** solo 437 clientes del test (10,5%) no tienen compras previas; hace falta simular más fríos ocultando historial (método en [`docs/Controles_de_integridad.md`](docs/Controles_de_integridad.md)).

## Modelado y evaluación

### Modelos evaluados

| Tipo | Modelo | Rol |
| --- | --- | --- |
| Referencia sin aprendizaje | Popularidad (lo más vendido, con decaimiento temporal) | Vara a superar y recomendación para clientes nuevos |
| Referencia por reglas | Popularidad por tramo de edad | Primer intento de personalizar a clientes nuevos |
| No supervisado | Co-compra + recompra (filtrado colaborativo ítem-ítem) | Genera candidatas y señales para el ranker |
| Supervisado | Ranker con regresión logística y Gradient Boosting | Ordena las candidatas por probabilidad de compra |

### Protocolo de validación

Partición temporal: entrenamiento hasta el 08/09/2020, validación del 09/09 al 15/09 (todas las elecciones) y test del 16/09 al 22/09 (medición única). Métrica de decisión: **Recall@12**; Accuracy, Precision, F1 y matriz de confusión como diagnóstico. La Accuracy no se usa para elegir porque solo el 0,5% de los pares cliente–prenda son compras.

### Resultados (semana de test)

- **Modelo seleccionado:** ranker supervisado con Gradient Boosting (+0,40 puntos de Recall@12 sobre la regresión logística, IC 95% de +0,11 a +0,68).
- **Clientes con historial:** Recall@12 de 2,78% a 7,53% frente a la popularidad actual (IC 95% de la mejora: +3,89 a +5,48 puntos).
- **Clientes nuevos:** se recomienda la popularidad reciente; desde la primera compra conviene personalizar (notebook `05`).
- **Señales más importantes:** recompra, co-compra y recencia del cliente.

| Tipo de cliente | Popularidad actual | Modelo final |
| --- | ---: | ---: |
| Todos (4.162) | 2,71 | 6,95 |
| Con historial (3.725) | 2,78 | 7,53 |
| Nuevos, sin compras previas (437) | 2,07 | 2,04 |

*Recall@12 (%) en la semana de test. Fuente: `reports/resultados_test_optimizado.csv`.*

### Sistema final

Sistema por etapas: popularidad reciente para clientes sin historial y ranker con Gradient Boosting desde la primera compra. El modelo entrenado está en `models/`.

### Notebooks

| Notebook | Contenido |
| --- | --- |
| `03_baseline.ipynb` | Baseline, métricas y modelo por edad |
| `04_pipeline_modelos.ipynb` | Tratamiento de datos, features, co-compra y ranker |
| `05_simulacion_cold_start.ipynb` | Desde cuántas compras conviene personalizar |
| `06_metricas_optimizacion_decisiones.ipynb` | Optimización, selección y justificación del modelo |

## Decisiones sobre los datos

**No usamos el código postal.** La propuesta contemplaba simular un mercado nuevo apartando clientes por código postal, pero con estos datos no conviene:

1. Es un hash anonimizado: no tiene significado geográfico ni permite agrupar zonas.
2. Hay 87.652 códigos distintos para 110.252 clientes y el 82% de los códigos tiene un solo cliente.
3. Un único código concentra 2.857 clientes (2,6%), unas 136 veces más que el siguiente (21 clientes), y parece un valor por defecto para datos faltantes. Esos clientes se comportan distinto al resto (por ejemplo, 7,6% sin edad contra 0,9%).

Apartar clientes por código postal daría grupos arbitrarios, que no representarían un mercado nuevo. Por eso los clientes fríos se simulan ocultando historial (0, 1 o 2 compras visibles).

Tampoco usamos `FN` y `Active` (66% de vacíos y el vacío de `Active` no se puede interpretar), y no recomendamos usar `club_member_status` ni `fashion_news_frequency`: la tabla de clientes es una foto de un solo momento y puede reflejar información posterior a las compras (*data leakage*).

## Limitaciones

Mercado de origen desconocido (el hemisferio norte se infiere de la estacionalidad); precio sin unidad; sin talle ni cantidad, y la tabla incluye devoluciones; la fecha no tiene hora; evaluación *offline* (solo se registran compras, no lo que vio cada cliente); la muestra es el 10% de los clientes, por lo que las cifras por artículo están infladas respecto del dataset completo. No se trabaja con imágenes.
