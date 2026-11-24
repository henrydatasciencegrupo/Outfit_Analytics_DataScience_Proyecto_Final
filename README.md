# Lookwise Data Lab: recomendador para clientes sin historial (cold start)

[![Pruebas automáticas](https://github.com/henrydatasciencegrupo/Outfit_Analytics_DataScience_Proyecto_Final/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/henrydatasciencegrupo/Outfit_Analytics_DataScience_Proyecto_Final/actions/workflows/ci.yml)

Equipo **Lookwise Data Lab**. 
Metodología: **CRISP-DM con Scrum (sprints)**.

**¿Primera vez en el repositorio?** Empezá por [`EMPIEZA_POR_AQUI.md`](EMPIEZA_POR_AQUI.md): una guía para práctica para leer, sin abrir notebooks ni código.

## Contexto y objetivo

H&M, multinacional sueca de moda, prevé abrir su primera tienda en Argentina en 2027. Como escenario del caso, planteamos que la apertura vaya acompañada del lanzamiento de su tienda online. Sin clientes ni compras locales, el sitio no puede personalizar la experiencia de sus primeros visitantes (*cold start*). Diseñamos un sistema de recomendación para ese lanzamiento.

- **Módulo 1 (principal):** ranking de 12 productos para clientes nuevos o con poco historial, evaluado frente a un baseline de popularidad con **Recall@12** como métrica de decisión (y MAP@12, Precision@12 y Hit Rate@12 como apoyo), incluyendo clientes simulados como «fríos».
- **Módulo 2 (posible extensión):** productos complementarios («Completá el look»).

## Datos

Dataset **H&M Personalized Fashion Recommendations**. No se incluye en este repositorio: ver [`docs/dataset.md`](docs/dataset.md) para obtenerlo, ver las fuentes y referencias y reproducir la muestra del 10% (p10) que usamos. El significado de cada variable está en [`docs/glosario_variables.md`](docs/glosario_variables.md).

## Estructura

```text
.
├── notebooks/                    se ejecutan en orden, desde la carpeta notebooks/
│   ├── 01_muestreo_p10.ipynb               muestra p10 del 10% de clientes y sus controles
│   ├── 02_EDA_unificado_p10.ipynb          EDA final del equipo (con salidas)
│   ├── 02_EDA_individual_p10.ipynb         pre-exploración individual
│   ├── 03_baseline.ipynb                   baseline: lo más vendido
│   ├── 04_pipeline_modelos.ipynb           features, modelos y comparación
│   ├── 05_simulacion_cold_start.ipynb      desde cuántas compras conviene personalizar
│   ├── 06_metricas_optimizacion_decisiones.ipynb   métricas, optimización y modelo final
│   ├── 07_piloto_ab_simulado.ipynb         piloto A/B simulado antes de escalar
│   └── 08_costos_roi.ipynb                 costos, retorno de la inversión y simulación Monte Carlo
├── src/                          código del pipeline, importado por los notebooks
│   ├── datos.py  features.py  metricas.py  modelos.py
│   ├── optimizacion.py  simulacion.py  piloto.py  roi.py
│   └── pipeline.py                         ejecución de punta a punta
├── models/                       modelo final entrenado, su configuración y recomendaciones de test
├── reports/                      resultados en CSV (insumo del dashboard)
│   └── figures/                            gráficos de los notebooks (01 a 27) y de la documentación (eda_*, modelado_*)
├── api/                          API de recomendación (FastAPI): sirve las 12 prendas de un cliente; lee el modelo de models/
├── app/                          demo en Streamlit: consulta la API y muestra las prendas recomendadas
├── dashboard/                    dashboard de Power BI (Sprint 2)
├── .github/workflows/ci.yml      pruebas automáticas de la API y la pantalla (GitHub Actions)
├── docs/                         documentación por tema
│   ├── dataset.md                          cómo obtener los datos, fuentes y estructura local
│   ├── controles_integridad.md             controles de la muestra y calidad de los datos
│   ├── glosario_variables.md               significado de cada variable
│   ├── eda.md                              hallazgos y decisiones del EDA
│   ├── modelado.md                         modelos, validación y resultados
│   ├── costos_roi.md                       inversión, retorno y probabilidad de recuperar la inversión
│   ├── plan_validacion.md                  plan de validación offline, piloto A/B y monitoreo
│   ├── demo_api_streamlit.md               API y demo: uso, decisiones, código y limitaciones
│   ├── github_actions_ci.md                pruebas automáticas con GitHub Actions: qué validan y qué no
│   ├── manual_usuario.md                   cómo probar el sistema: elegir un cliente y ver sus 12 prendas
│   ├── gobernanza_ia_datos.md              datos que usa el sistema, riesgos y marco legal
│   ├── resumen_ejecutivo.pdf               resumen del proyecto sin tecnicismos
│   ├── indice.md                           evidencia de cada criterio de evaluación
│   └── solucion_errores_git.md             problemas frecuentes con Git y VS Code
├── dataset/p10/                  datos locales (no se suben: ver docs/dataset.md)
├── compose.yaml                  API y pantalla con Docker (ver «Demo: API y pantalla»)
├── EMPIEZA_POR_AQUI.md           guía de lectura según lo que se necesite
├── requirements.txt
└── README.md
```

Todos los notebooks leen los datos desde `../dataset/p10` (ruta relativa a `notebooks/`), por lo tanto solo se deben dejar los Parquet en esa carpeta y ejecutar **Run All**, sin editar rutas.

## Cómo reproducirlo

1. **Crear el entorno.** Un único entorno virtual sirve para todo el proyecto: notebooks, API y pantalla. Requiere Python 3.11 o superior (probado con 3.13): antes de empezar, verificá la versión con `python --version`. Desde la carpeta del repositorio:

   ```bash
   python -m venv .venv
   ```

   En Windows, si se tienen varias versiones de Python instaladas y `python --version` muestra una anterior a 3.11, recomendamos crear el entorno indicando la versión: `py -3.13 -m venv .venv`. Si  posteriormente `pip install` falla con *Could not find a version that satisfies the requirement pandas==3.1.1*, significa que el entorno se creó con un Python anterior a 3.11: eliminá la carpeta `.venv` y volvé a crearla.

   Activarlo:

   - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`. Si PowerShell lo bloquea, correr antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
   - macOS o Linux: `source .venv/bin/activate`

   Y con el entorno activado, instalar las librerías:

   ```bash
   python -m pip install -r requirements.txt
   ```

   Las versiones están fijadas a propósito: la API reproduce las recomendaciones oficiales solo con `scikit-learn==1.9.1` (con la 1.7.2, por ejemplo, las listas coinciden en cerca del 88%). Las carpetas `api/` y `app/` conservan su propio `requirements.txt`, útil para levantar una sola pieza; con el entorno único no hace falta instalarlos aparte. La carpeta `.venv` no se sube al repositorio.

2. **Conseguir los datos:** los tres archivos Parquet de la muestra p10 (unos 63 MB) no se incluyen en este repositorio por su tamaño. Están a disposición para ser solicitados al equipo de Lookwise Data Lab (ver contactos en la sección [Equipo](#equipo)) y se dejan en `dataset/p10/`. Ver la estructura en [`docs/dataset.md`](docs/dataset.md). *Opcional:* quien quiera auditar cómo se armó la muestra puede reproducirla desde cero con `notebooks/01_muestreo_p10.ipynb`, descargando los CSV originales (ver [`docs/dataset.md`](docs/dataset.md)); no hace falta para correr el resto del proyecto.
3. **Correr el EDA:** abrir `notebooks/02_EDA_unificado_p10.ipynb` desde la carpeta `notebooks/` y ejecutar todas las celdas.
4. **Correr el modelado:** ejecutar los notebooks `03`, `04`, `05` y `06` en ese orden; el `06` es el final y de él salen el modelo elegido y los resultados.

   También se puede reproducir sin notebooks: el script `src/pipeline.py` ejecuta de punta a punta el modelo final del notebook `06` (con la búsqueda de hiperparámetros y la selección del algoritmo por Recall@12) y regenera los resultados y los artefactos de `models/`. Se corre desde la carpeta del repositorio y tarda unos 5 minutos:

   ```bash
   python src/pipeline.py --base dataset/p10 --salida reports --modelos models
   ```

   Tanto los notebooks como el script reescriben archivos de `reports/` y `models/`: si solo se desea probarlos, recomendamos usar otras carpetas (`--salida salida_prueba --modelos salida_prueba`) o una copia del repositorio, para no incluir esos cambios en un commit.

   Los resultados y las decisiones están en la sección [Modelado y evaluación](#modelado-y-evaluación) de este README y en el notebook `06`.

Para probar la API y la pantalla, ver [Demo: API y pantalla](#demo-api-y-pantalla).

## Estado

**Sprint 1:** muestreo, análisis exploratorio y modelado (baseline, modelos y simulación de clientes nuevos) realizados sobre la muestra p10. **Sprint 2:** API y demo en Streamlit (listas y probadas) y dashboard. Corte train/test por fecha: el test es del 16 al 22/9/2020 (siete días, la última semana del dataset) y todo lo anterior es entrenamiento; en el modelado, ese entrenamiento se divide en train hasta el 8/9 y validación del 9 al 15/9.

## Principales hallazgos del EDA

- **Muestra p10:** 110.252 clientes, 2.226.486 compras y 105.542 artículos, del 20/9/2018 al 22/9/2020, sin días sin compras. Integridad completa entre tablas.
- **Duplicados:** el 11,96% de las compras son filas repetidas; no se puede confirmar si son varias unidades, distintos talles o devoluciones. No se eliminan: la tabla no tiene talle ni cantidad e incluye compras devueltas, y hay 17.647 filas repetidas que solo difieren en el precio. Borrarlas perdería información posiblemente real y no se puede deshacer; por eso se ofrecen las dos versiones y se elige con el modelo funcionando.
- **Edad:** 1,10% de vacíos; la distribución tiene dos grupos (alrededor de los 20 a 30 y de los 50 años). Los clientes sin edad compran menos (mediana de 3 compras contra 8). No se imputa en la tabla original: son pocos y en el test solo 7 clientes no tienen edad (ninguno es frío); que falte la edad es informativo y rellenar en silencio taparía esa señal; y cómo imputar depende del algoritmo, por eso se ofrecen tres columnas y cada modelo elige.
- **Estacionalidad:** las ventas siguen un patrón del hemisferio norte (ropa de baño entre mayo y julio, punto entre septiembre y noviembre), invertido respecto de Argentina.
- **Cola larga:** los 12 artículos más vendidos suman 1,1% de las ventas y hacen falta 6.290 artículos para cubrir la mitad.
- **Clientes fríos:** solo 437 clientes del test (10,5%) no tienen compras previas; hace falta simular más fríos ocultando historial (método en [`docs/controles_integridad.md`](docs/controles_integridad.md)).

## Modelado y evaluación

### Modelos evaluados

| Tipo | Modelo | Rol |
| --- | --- | --- |
| Referencia sin aprendizaje | Popularidad (lo más vendido, con decaimiento temporal) | Vara a superar y recomendación para clientes nuevos |
| Referencia por reglas | Popularidad por tramo de edad | Primer intento de personalizar a clientes nuevos |
| No supervisado | Co-compra + recompra (filtrado colaborativo ítem-ítem) | Genera candidatas y señales para el ranker |
| Supervisado | Ranker con regresión logística y Gradient Boosting | Ordena las candidatas por puntaje de compra |

### Protocolo de validación

Partición temporal: entrenamiento hasta el 08/09/2020, validación del 09/09 al 15/09 (todas las elecciones) y test del 16/09 al 22/09 (medición única). Métrica de decisión: **Recall@12**; Accuracy, Precision, F1 y matriz de confusión como diagnóstico. La Accuracy no se utiliza para la elección porque solo el 0,5% de los pares cliente–prenda son compras. El plan completo, con el piloto A/B en producción antes de escalar, se encuentra en [`docs/plan_validacion.md`](docs/plan_validacion.md).

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

Sistema por etapas: popularidad reciente para clientes sin historial y ranker con Gradient Boosting desde la primera compra. El modelo entrenado se encuentra en `models/` y la API de `api/` lo entrega.

### Notebooks

| Notebook | Contenido |
| --- | --- |
| `03_baseline.ipynb` | Baseline, métricas y modelo por edad |
| `04_pipeline_modelos.ipynb` | Tratamiento de datos, features, co-compra y ranker |
| `05_simulacion_cold_start.ipynb` | Desde cuántas compras conviene personalizar |
| `06_metricas_optimizacion_decisiones.ipynb` | **Final:** optimización, selección y justificación del modelo (los 03 a 05 son etapas previas) |
| `07_piloto_ab_simulado.ipynb` | Piloto A/B simulado con la semana de test: reparto con hash, comparabilidad de grupos y regla de escalado |
| `08_costos_roi.ipynb` | Costos técnicos y honorarios, facturación del canal online y simulación Monte Carlo del retorno de la inversión |

## Demo: API y pantalla

El sistema final se puede probar con una API (FastAPI) y una pantalla (Streamlit). La API recibe un cliente de la semana de test y devuelve las 12 prendas recomendadas: la lista fija de populares si es un cliente nuevo y el ranker si tiene historial. La pantalla consulta la API y muestra nombre, tipo, grupo y color de cada prenda, en orden de ranking. Es un prototipo local: usa variables ya calculadas para la semana de test (16 al 22/9/2020) y no calcula nada en vivo.

Con el entorno único activo (ver [Cómo reproducirlo](#cómo-reproducirlo)) alcanza para las dos piezas. Hacen falta dos terminales, con el entorno activado en cada una y la API prendida primero:

```bash
# Terminal 1: API (puerto 8000)
cd api
uvicorn lookwise_api:app

# Terminal 2: pantalla
cd app
streamlit run app.py
```

La API se prueba sola en `http://127.0.0.1:8000/docs` y sus 7 tests se corren con `pytest` desde `api/`. Esos tests, junto con una verificación de sintaxis y de los archivos de la pantalla, corren automáticamente con GitHub Actions en cada push a `main` y en cada pull request hacia `main` (no reentrena el modelo; ver [`docs/github_actions_ci.md`](docs/github_actions_ci.md)). Si en lugar del entorno único se prefiere instalar una sola pieza, cada carpeta (`api/` y `app/`) trae su `requirements.txt` con versiones exactas. Los pasos completos, el contrato de la API, las decisiones de diseño y las limitaciones están en [`docs/demo_api_streamlit.md`](docs/demo_api_streamlit.md).

### Con Docker (opcional)

Si tenés Docker instalado, la API y la pantalla se pueden levantar juntas sin crear el entorno de Python. Desde la carpeta del repositorio:

```bash
docker compose up --build
```

La API queda en `http://localhost:8000` y la pantalla en `http://localhost:8501`. Docker prende primero la API y espera a que responda en `/salud` antes de levantar la pantalla. Las imágenes usan Python 3.13 y los `requirements.txt` de `api/` y `app/`. Para apagar todo: `docker compose down`.

## Costos y retorno de la inversión (ROI)

Estimación bajo supuestos editables y datos sintéticos; el detalle y la simulación están en [`docs/costos_roi.md`](docs/costos_roi.md) y en el notebook `08`.

- **Inversión:** USD 15.000 de desarrollo y USD 650 por mes de operación; USD 22.805 en el primer año.
- **Retorno:** en el escenario más probable, el recomendador se paga en el mes 3 y cierra el primer año con un ROI de +488%.
- **Punto de equilibrio operativo:** unos USD 48.000 de facturación online por mes.
- **Riesgo:** en 10.000 escenarios simulados (Monte Carlo), la inversión se recupera en 6 meses en el 98% de los casos; sumando el costo de la tienda online, baja al 87% en 6 meses y al 96% en 12.

## Decisiones sobre los datos

**No se utiliza el código postal.** La propuesta contemplaba simular un mercado nuevo apartando clientes por código postal, pero con los datos actuales no conviene:

1. Es un hash anonimizado: no posee significado geográfico ni permite agrupar zonas.
2. Hay 87.652 códigos distintos para 110.252 clientes y el 82% de los códigos tiene un solo cliente.
3. Un único código concentra 2.857 clientes (2,6%), unas 136 veces más que el siguiente (21 clientes), y parece un valor por defecto para datos faltantes. Esos clientes se comportan distinto al resto (por ejemplo, 7,6% sin edad contra 0,9%).

Apartar clientes por código postal daría grupos arbitrarios, que no representarían un mercado nuevo. Por lo tanto, los clientes fríos se simulan ocultando historial (0, 1 o 2 compras visibles).

Tampoco utilizamos `FN` y `Active` (66% de vacíos y el vacío de `Active` no se puede interpretar), y no recomendamos usar `club_member_status` ni `fashion_news_frequency`: la tabla de clientes es una foto de un solo momento y puede reflejar información posterior a las compras (*data leakage*).

## Limitaciones

Mercado de origen desconocido (el hemisferio norte se infiere de la estacionalidad); precio sin unidad; sin talle ni cantidad, y la tabla incluye devoluciones; la fecha no tiene hora; evaluación *offline* (solo se registran transacciones, no lo que vio cada cliente); la muestra es el 10% de los clientes, por lo que las cifras por artículo están infladas respecto del dataset completo. No se trabaja con imágenes.

La demo (API y pantalla) corre en local, solo conoce a los clientes de la semana de test y lee variables ya calculadas; no es un despliegue en producción.

Los clientes nuevos reciben la misma lista de populares: el dataset no tiene género y la edad no mejoró lo más vendido. Como mejora, en el mercado argentino se podría capturar de forma opcional una preferencia de sección al registrarse y validarla con el piloto A/B antes de escalar.

## Equipo

**Lookwise Data Lab**: integrantes y roles.

| Integrante | Rol en el proyecto | LinkedIn |
| --- | --- | --- |
| María Isabel Fernández | Muestreo, EDA y documentación | [LinkedIn](https://www.linkedin.com/in/isabelfernandez-ai-data) |
| Florencia Dinelli | Muestreo, EDA, README, API y demo en Streamlit | [LinkedIn](https://www.linkedin.com/in/florencia-dinelli-3672253b9) |
| Ignacio Sironi | Baseline y estructura del repositorio | [LinkedIn](https://www.linkedin.com/in/ignacio-sironi-626464113) |
| Margot Huaman Quispe | Modelado, métricas, optimización y estructura del repositorio | [LinkedIn](https://www.linkedin.com/in/margothuamaneconomista) |
| Alejandra Blandón | Simulación, conclusiones y dashboard | [LinkedIn](https://www.linkedin.com/in/alejandra-blandon-analyst) |
