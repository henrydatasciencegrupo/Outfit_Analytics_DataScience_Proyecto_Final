# Empezá por aquí

**Lookwise Data Lab** · Recomendador de moda para la tienda online de H&M en Argentina

Este repositorio tiene muchos archivos. Esta página te dice **por dónde empezar según lo que necesites**, sin tener que abrir notebooks ni código.

## En una frase

H&M abre su tienda online en Argentina sin clientes conocidos. Construimos un sistema que decide qué 12 prendas mostrarle a cada cliente: lo más vendido de la semana a quien nunca compró y una vitrina personalizada desde su primera compra. Con historial, el sistema duplica los aciertos de mostrar lo más vendido.

## ¿Qué necesitás?

| Si querés… | Abrí | Tiempo de lectura |
| --- | --- | --- |
| Entender el proyecto sin tecnicismos: problema, resultados, costos y recomendaciones | [`docs/resumen_ejecutivo.pdf`](docs/resumen_ejecutivo.pdf) | 10 minutos |
| Ver los resultados de forma interactiva | Dashboard en [`dashboard/`](dashboard/) | 10 minutos |
| Probar el sistema: elegir un cliente y ver sus 12 prendas | [`docs/manual_usuario.md`](docs/manual_usuario.md) | 15 minutos |
| Saber qué datos usa el sistema, qué riesgos tiene y qué marco legal aplica | [`docs/gobernanza_ia_datos.md`](docs/gobernanza_ia_datos.md) | 15 minutos |
| Conocer cuánto cuesta y cuándo se recupera la inversión | [`docs/costos_roi.md`](docs/costos_roi.md) | 10 minutos |
| Ver cómo se eligió el modelo y por qué | [`docs/modelado.md`](docs/modelado.md) | 20 minutos |
| Ver cómo se validó y cómo se probaría con clientes reales | [`docs/plan_validacion.md`](docs/plan_validacion.md) | 15 minutos |
| Entender los datos: de dónde salen, qué tienen y qué problemas encontramos | [`docs/dataset.md`](docs/dataset.md) · [`docs/eda.md`](docs/eda.md) | 20 minutos |
| Reproducir todo en tu computadora | [`README.md`](README.md), sección *Cómo reproducirlo* | Variable |
| Saber qué se prueba automáticamente en cada cambio del repositorio | [`docs/github_actions_ci.md`](docs/github_actions_ci.md) | 5 minutos |
| Buscar la evidencia de cada criterio de evaluación | [`docs/indice.md`](docs/indice.md) | Consulta |

## Recorridos sugeridos

**Si sos de negocio o de otra área (sin perfil técnico):**
1. Resumen ejecutivo.
2. Dashboard.
3. Documento de gobernanza, secciones *Por qué este documento* y *Nuestras recomendaciones*.

**Si sos del equipo técnico:**
1. [`README.md`](README.md).
2. [`docs/modelado.md`](docs/modelado.md) y el notebook final, [`notebooks/06_metricas_optimizacion_decisiones.ipynb`](notebooks/06_metricas_optimizacion_decisiones.ipynb).
3. [`docs/plan_validacion.md`](docs/plan_validacion.md).
4. El código en [`src/`](src/), empezando por [`src/pipeline.py`](src/pipeline.py), que corre todo de punta a punta.
5. [`docs/github_actions_ci.md`](docs/github_actions_ci.md): qué prueba GitHub Actions en cada cambio.

## Qué hay en cada carpeta

| Carpeta | Qué contiene |
| --- | --- |
| [`docs/`](docs/) | Toda la documentación, por tema |
| [`notebooks/`](notebooks/) | El análisis paso a paso, del 01 al 08. **El 06 es el final**: de ahí salen el modelo elegido y los resultados; del 03 al 05 son etapas previas |
| [`src/`](src/) | El código que usan los notebooks y el pipeline |
| [`models/`](models/) | El modelo entrenado, su configuración y las recomendaciones de la semana de prueba |
| [`reports/`](reports/) | Resultados en tablas (CSV) y gráficos; son la fuente del dashboard |
| [`api/`](api/) | La API que entrega las 12 prendas de un cliente |
| [`app/`](app/) | La pantalla de demostración (Streamlit), que consulta la API |
| [`dashboard/`](dashboard/) | El dashboard de Power BI |
| [`.github/workflows/`](.github/workflows/) | Las pruebas automáticas (GitHub Actions) de la API y la pantalla |
| [`compose.yaml`](compose.yaml) | Levanta la API y la pantalla juntas con Docker (archivo, no carpeta) |

Los datos no están en el repositorio: pertenecen a H&M Group y se usan bajo las reglas de la competencia de Kaggle. Cómo obtenerlos está en [`docs/dataset.md`](docs/dataset.md).

## Glosario mínimo

- **Cliente nuevo:** quien todavía no compró nada. El sistema le muestra lo más vendido de la semana.
- **Cliente con historial:** quien ya compró al menos una vez. El sistema le arma una vitrina personalizada.
- **Recall@12:** de lo que un cliente compró, qué parte estaba entre las 12 prendas recomendadas. Es la métrica que decidió qué modelo usar.
- **Hit Rate@12:** de cada 100 clientes, cuántos compraron al menos una de las 12 prendas recomendadas.
- **Piloto A/B:** prueba con clientes reales en la que una parte ve la vitrina personalizada y el resto, lo más vendido, para medir la diferencia.

El significado de cada variable de los datos está en [`docs/glosario_variables.md`](docs/glosario_variables.md).

## Equipo

Integrantes, roles y contactos en el [`README.md`](README.md#equipo).
