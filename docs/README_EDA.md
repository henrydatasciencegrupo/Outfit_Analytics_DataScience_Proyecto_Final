# Lookwise Data Lab: recomendador para clientes sin historial (cold start)

Proyecto final del bootcamp de Data Science de Soy Henry, hecho por el equipo **Lookwise Data Lab**. Metodología: CRISP-DM con Scrum (sprints).

## Contexto y objetivo

H&M, multinacional sueca de moda, prevé abrir su primera tienda en Argentina en 2027. Como escenario del caso, planteamos que la apertura vaya acompañada del lanzamiento de su tienda online. Sin clientes ni compras locales, el sitio no puede personalizar la experiencia de sus primeros visitantes (*cold start*). Diseñamos un sistema de recomendación para ese lanzamiento.

- **Módulo 1 (principal):** ranking de 12 productos para clientes nuevos o con poco historial, evaluado frente a un baseline de popularidad con MAP@12, Precision@12 y Recall@12 sobre clientes simulados como "fríos".
- **Módulo 2 (posible extensión):** productos complementarios ("Completá el look").

## Datos

Dataset H&M Personalized Fashion Recommendations. **No se incluye en este repositorio**: ver `docs/dataset_README.md` para obtenerlo y para reproducir la muestra del 10% (p10) que usamos.

## Estructura

```
notebooks/
  dataset_documentado_v2.ipynb   cómo se armó la muestra y sus controles
  EDA_unificado_p10.ipynb        análisis exploratorio completo, con salidas
docs/
  EDA_Lookwise.md                resumen del EDA: diccionario, hallazgos y decisiones
dataset/
  README.md                      cómo obtener los datos y la muestra
```

## Estado

Sprint 1: análisis exploratorio terminado sobre la muestra p10. El corte train/test (test = 16 al 22/9/2020, 7 días) es provisorio hasta su confirmación por el equipo.

## Principales hallazgos del EDA

- **Muestra p10:** 110.252 clientes, 2.226.486 compras y 105.542 artículos, del 20/9/2018 al 22/9/2020, sin días sin compras. Integridad completa entre tablas.
- **Duplicados:** el 11,96% de las compras son filas repetidas; no se puede confirmar si son varias unidades, distintos talles o devoluciones.
  **Por qué no se eliminan los duplicados.** No se puede confirmar si son errores: la tabla no tiene talle ni cantidad e incluye compras devueltas, así que una fila repetida puede ser una segunda unidad, otro talle o una compra más su devolución. Hay además 17.647 filas repetidas que solo difieren en el precio. Borrarlas perdería información posiblemente real y no se puede deshacer; por eso se ofrecen las dos versiones y se elige con el modelo funcionando.
- **Edad:** 1,10% de vacíos; la distribución tiene dos grupos (alrededor de los 20 a 30 y de los 50 años). Los clientes sin edad compran menos (mediana de 3 compras contra 8).
  Por qué no se imputa en la tabla original: son pocos (1,10%) y en el test solo 7 clientes no tienen edad (ninguno es frío), así que la decisión casi no cambia la evaluación; que falte la edad es informativo (esos clientes compran menos) y rellenar en silencio taparía esa señal; y cómo imputar depende del algoritmo, por eso se ofrecen las tres columnas y cada modelo elige.
- **Estacionalidad:** las ventas siguen un patrón del hemisferio norte (ropa de baño entre mayo y julio, punto entre septiembre y noviembre), invertido respecto de Argentina.
- **Cola larga:** los 12 artículos más vendidos suman 1,1% de las ventas y hacen falta 6.290 artículos para cubrir la mitad.
- **Clientes fríos:** solo 437 clientes del test (10,5%) no tienen compras previas; hace falta simular más fríos ocultando historial.

## Decisiones sobre los datos

**No usamos el código postal.** La propuesta contemplaba simular un mercado nuevo apartando clientes por código postal, pero con estos datos no conviene:

1. Es un hash anonimizado: no tiene significado geográfico ni permite agrupar zonas.
2. Hay 87.652 códigos distintos para 110.252 clientes y el 82% de los códigos tiene un solo cliente.
3. Un único código concentra 2.857 clientes (2,6%), unas 136 veces más que el siguiente (21 clientes), y parece un valor por defecto para datos faltantes. Esos clientes se comportan distinto al resto (por ejemplo, 7,6% sin edad contra 0,9%).

Apartar clientes por código postal daría grupos arbitrarios, que no representarían un mercado nuevo. El criterio para simularlo queda por definir.

**Tampoco usamos `FN` y `Active`** (66% de vacíos y el vacío de `Active` no se puede interpretar), y no recomendamos usar `club_member_status` ni `fashion_news_frequency`: la tabla de clientes es una foto de un solo momento y puede reflejar información posterior a las compras (*data leakage*).

## Limitaciones

Mercado de origen desconocido (el hemisferio norte se infiere de la estacionalidad); precio sin unidad; sin talle ni cantidad, y la tabla incluye devoluciones; la fecha no tiene hora; evaluación *offline* (solo se registran compras, no lo que vio cada cliente); la muestra es el 10% de los clientes, por lo que las cifras por artículo están infladas respecto del dataset completo. No se trabaja con imágenes.
