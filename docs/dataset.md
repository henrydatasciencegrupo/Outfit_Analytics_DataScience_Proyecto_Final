# Datos

**Este repositorio no incluye los datos.** Pertenecen a H&M Group y se publicaron para la competencia de Kaggle [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations), bajo las reglas de esa competencia (uso no comercial y de investigación académica). Para usarlos hay que aceptar esas reglas en Kaggle y descargarlos desde ahí.

## Índice

- [Archivos originales](#archivos-originales)
- [Muestra que usa el proyecto (p10)](#muestra-que-usa-el-proyecto-p10)
- [Dónde dejar los archivos](#dónde-dejar-los-archivos)
- [Índice del notebook de muestreo](#índice-del-notebook-de-muestreo)
- [Librerías utilizadas](#librerías-utilizadas)
- [Cómo se armó la muestra, paso a paso](#cómo-se-armó-la-muestra-paso-a-paso)
  - [1. Qué canal es el online](#1-qué-canal-es-el-online)
  - [2. Filtro online](#2-filtro-online)
  - [3. Verificación de las tablas originales](#3-verificación-de-las-tablas-originales)
  - [4. Sorteo de clientes con número fijo](#4-sorteo-de-clientes-con-número-fijo)
  - [5. Guardado en Parquet y controles de integridad](#5-guardado-en-parquet-y-controles-de-integridad)
  - [6. Representatividad de las muestras](#6-representatividad-de-las-muestras)
  - [7. Pruebas de tamaño: p5 o p10](#7-pruebas-de-tamaño-p5-o-p10)
- [Conclusiones del muestreo](#conclusiones-del-muestreo)
- [Fuentes y referencias](#fuentes-y-referencias)

## Archivos originales

- `transactions_train.csv`: 31.788.324 compras (cliente, artículo, fecha, precio, canal).
- `customers.csv`: 1.371.980 clientes.
- `articles.csv`: 105.542 artículos.

## Muestra que usa el proyecto (p10)

Para trabajar en computadoras comunes se usa una muestra del 10% de los clientes, solo del canal online. El método está documentado y se puede reproducir con `notebooks/01_muestreo_p10.ipynb`:

- **Solo canal 2 (online):** 22.379.862 compras y 1.108.418 clientes con al menos una compra online.
- **Sorteo por cliente, con un número fijo:** `bucket = hash(customer_id || 'lookwise42') % 10000`. La muestra del 5% (p5) son los clientes con `bucket < 500` y la del 10% (p10), los de `bucket < 1000`. El 5% queda contenido en el 10%.
- **Se conserva todo el historial online de cada cliente elegido**, y `articles` va completo.
- **Resultado p10:** 110.252 clientes, 2.226.486 compras y 105.542 artículos, en tres archivos Parquet (unos 63 MB).
- **Controles:** sin clientes ni artículos huérfanos; la muestra conserva la distribución de compras por cliente y el porcentaje de edades vacías de la población online (1,10%).

## Dónde dejar los archivos

Los notebooks esperan esta estructura (la carpeta `dataset/p10/` está ignorada por git):

```
dataset/
  p10/
    transactions.parquet
    customers.parquet
    articles.parquet
```

Los Parquet se abren con `pd.read_parquet(...)` (hace falta `pyarrow`).

## Índice del notebook de muestreo

Notebook: [`notebooks/01_muestreo_p10.ipynb`](../notebooks/01_muestreo_p10.ipynb). Este documento resume cada sección; las consultas y los resultados completos están en el notebook.

| Sección del notebook | Contenido |
|---|---|
| 1. Preparación del entorno | Instalación de DuckDB y pandas |
| 2. Verificación del canal de venta | Transacciones por mes y canal · Porcentaje online en todo el período |
| 3. Filtro online | Filas y clientes del canal online |
| 4. Verificación de las tablas originales | `articles`: estructura y claves únicas · `customers`: filas, claves únicas y vacíos de edad |
| 5. Muestra de clientes con semilla | Número fijo por cliente (`bucket`) · Filas que tendría cada muestra |
| 6. Guardado en Parquet | Una carpeta por tamaño (p5 y p10) con las tres tablas |
| 7. Controles de integridad de las muestras | Filas, clientes, claves huérfanas y peso de los archivos |
| 8. Representatividad de las muestras | Compras por cliente · Cobertura de artículos · Fecha de primera compra · Clientes sin edad |
| 9. Pruebas de tamaño | Cobertura ponderada · Material de test · Memoria y tiempo · Prueba pesada de co-compra |
| 10. Conclusiones y pendientes | Resumen y decisión sobre el tamaño |

Antes de correr el notebook hay que cambiar las rutas a las de cada computadora: `ruta_trans` (primera celda de código de la sección 2) y `ruta_base` (celda de la sección 6).

## Librerías utilizadas

| Librería | Para qué se usa en el muestreo |
|---|---|
| `duckdb` | Consultar los CSV grandes directamente (la tabla de transacciones tiene más de 31 millones de filas) y guardar los archivos Parquet |
| `pandas` | Ver los resultados como tablas y medir los tiempos de carga y unión |
| `psutil` | Medir la memoria RAM total y disponible de la computadora |
| `pyarrow` | Leer los archivos Parquet desde `pandas` |

El módulo `os` y la librería `time` vienen con Python y no se instalan. Las versiones están en el [`requirements.txt`](../requirements.txt) de la raíz del repositorio. Para instalarlas: `pip install -r requirements.txt`.

## Cómo se armó la muestra, paso a paso

La muestra se sortea **por cliente** (con todo su historial online), con un número fijo calculado a partir del `customer_id`, y se guarda en Parquet. Cada paso se verifica con los datos antes de seguir.

### 1. Qué canal es el online

El dataset no documenta qué significan los valores 1 y 2 de `sales_channel_id`. Antes de filtrar por online se verificó con los datos: se contaron las transacciones de cada canal por mes durante el confinamiento de 2020.

| Mes | Canal 1 | Canal 2 |
|---|---|---|
| Febrero 2020 | 324.660 | 677.199 |
| Marzo 2020 | 154.087 | 893.665 |
| Abril 2020 | sin transacciones | 1.340.882 |
| Mayo 2020 | 391.746 | 970.069 |
| Junio 2020 | 590.345 | 1.174.162 |
| Julio 2020 | 535.082 | 816.420 |

El canal 1 cae a menos de la mitad en marzo, desaparece en abril y vuelve en mayo. El canal 2 nunca se interrumpe y llega a su máximo en abril. Es coherente con el cierre de las tiendas físicas durante el confinamiento, por lo que **canal 1 = tienda y canal 2 = online**.

Es una inferencia respaldada por los datos y por comentarios públicos sobre el dataset (ver [Fuentes y referencias](#fuentes-y-referencias)), no una definición oficial: la ausencia de registros también podría ser un hueco en los datos. En todo el período, el canal 2 es el mayoritario: entre el 60% y el 74% de las transacciones de cada mes, con un máximo de 85,3% en marzo de 2020.

### 2. Filtro online

El canal 2 tiene **22.379.862 filas** (alrededor del 70% de las 31.788.324 totales) y **1.108.418 clientes** con al menos una compra online (alrededor del 81% de los 1.371.980 clientes). Filtrar por online conserva a la gran mayoría de los clientes; la reducción fuerte de tamaño la hace el sorteo, no el filtro.

### 3. Verificación de las tablas originales

| Tabla | Filas | Claves únicas | Observación |
|---|---|---|---|
| `articles` | 105.542 | 105.542 | 25 columnas. `article_id` se lee como texto, con los ceros iniciales |
| `customers` | 1.371.980 | 1.371.980 | Coincide con el total de clientes de las transacciones sin filtrar |

Sin claves repetidas, se pueden unir las tres tablas sin duplicar filas.

**Edad vacía.** Hay 15.861 clientes sin edad en la tabla completa (1,16%). Entre los clientes online son 12.337 de 1.108.418 (1,11%). El filtro online casi no cambia el porcentaje, y 1,11% es la cifra de referencia para comparar con las muestras. El código postal no tiene vacíos.

### 4. Sorteo de clientes con número fijo

A cada cliente online se le asigna un número entre 0 y 9999, calculado con `hash(customer_id || 'lookwise42') % 10000`. La muestra del 5% (**p5**) son los clientes con `bucket < 500` y la del 10% (**p10**), los de `bucket < 1000`.

- **Reproducible:** con la misma semilla sale siempre lo mismo.
- **Anidada:** p5 queda contenida en p10, así que se pueden probar varios tamaños sin rehacer nada.
- **Por cliente y no por fila:** no se cortan los historiales.

| | Clientes | % de los clientes online | Filas de `transactions` | % de las filas online |
|---|---|---|---|---|
| p5 | 55.454 | 5,00% | 1.122.274 | 5,01% |
| p10 | 110.252 | 9,95% | 2.226.486 | 9,95% |

El porcentaje de filas es casi igual al de clientes, lo que indica que el sorteo no se inclinó hacia clientes con mucha o poca actividad. El 10% no da exactamente 10% porque el sorteo por número fijo es aleatorio.

### 5. Guardado en Parquet y controles de integridad

Para cada tamaño se guarda una carpeta con tres archivos Parquet: `transactions` (solo canal 2 y solo clientes de la muestra), `customers` (solo los de la muestra) y `articles` (completa). Parquet pesa poco, se abre rápido y se puede compartir por Drive.

Que el guardado termine sin error no prueba que el contenido sea correcto, así que se compara con las cifras ya medidas:

| Control | p5 | p10 |
|---|---|---|
| Filas de `transactions` | 1.122.274 | 2.226.486 |
| Clientes en `transactions` y en `customers` | 55.454 | 110.252 |
| Filas de `articles` | 105.542 | 105.542 |
| Filas de otros canales | 0 | 0 |
| Huérfanos (cliente / artículo) | 0 / 0 | 0 / 0 |
| Peso total aproximado | 34 MB | 63,5 MB |

Todo coincide con lo esperado: las tres tablas de cada muestra se pueden unir sin perder ni duplicar filas.

### 6. Representatividad de las muestras

Que la muestra esté bien armada no garantiza que se parezca al total. Se compara con la población online completa.

**Compras por cliente** (% de clientes en cada tramo de cantidad de compras):

| Tramo de compras | Total online | p5 | p10 |
|---|---|---|---|
| 1 | 11,36 | 11,27 | 11,28 |
| 2 a 5 | 30,50 | 30,43 | 30,54 |
| 6 a 20 | 32,66 | 32,66 | 32,68 |
| Más de 20 | 25,47 | 25,63 | 25,49 |

La diferencia máxima contra el total es de 0,16 puntos porcentuales en p5 (tramo de más de 20) y de 0,08 en p10 (tramo de 1 compra).

**Fecha de primera compra.** Los meses de p5 y p10 siguen de cerca a los del total online; la mayor diferencia es de unos 0,3 puntos (p5, diciembre de 2018). Los primeros meses (septiembre y octubre de 2018) están inflados: la "primera compra" es la primera dentro de la ventana observada, y hay clientes que ya existían antes.

**Clientes sin edad:** p5 = 1,11% y p10 = 1,10%, contra 1,11% del total online.

**Cobertura de artículos.** Acá la muestra no es representativa, y es esperable al achicarla:

| | Total online | p5 | p10 |
|---|---|---|---|
| Artículos con al menos 1 compra | 98.322 | 68.978 (70,2%) | 78.318 (79,7%) |
| Artículos con 5 o más compras | 85.223 | 38.944 (45,7%) | 49.820 (58,5%) |

El 5% pierde alrededor del 30% de los artículos con ventas y el 10% alrededor del 20%. Por eso las cifras por artículo (artículos sin ventas, artículos del test ausentes en el train) se leen como cotas, mientras que las cifras por cliente no se ven afectadas, porque de cada cliente elegido se conserva todo su historial.

### 7. Pruebas de tamaño: p5 o p10

Para decidir entre los dos tamaños se midieron la cobertura ponderada, el material de test, el costo de memoria y tiempo, y una prueba pesada. Son controles de la muestra, no EDA.

**Cobertura ponderada por compras.** Un artículo con 2 compras pesa igual que uno con 10.000 al contar artículos distintos; ponderando por compras se ve qué parte de la actividad real queda cubierta:

| | p5 | p10 |
|---|---|---|
| % de las compras online cubiertas por artículos de la muestra | 98,60% | 99,41% |

**Costo en una computadora de prueba** (16,7 GB de RAM en total y 3,0 GB disponibles en ese momento, con otras aplicaciones abiertas):

| Prueba | p5 | p10 |
|---|---|---|
| Carga, unión de las tres tablas y top 12 de artículos | sin medir | 3,5 s en total; la tabla unida ocupa 927 MB |
| Prueba pesada: todos los pares de artículos comprados por un mismo cliente (co-compra), con tope de memoria de 2 GB | 4,7 s | 11,1 s |
| Pares distintos de artículos | 28.383.189 | 53.149.275 |
| Co-ocurrencias | 31.429.744 | 63.074.954 |

Al duplicar la muestra el tiempo se multiplica por 2,4 y los pares distintos por 1,9. Los pares repetidos, que son los que aportan señal de co-compra, pasan de 3,05 millones a 9,93 millones (x3,3): el 10% aporta más señal, no solo más volumen.

**Clientes de la semana de test.** Con el corte definitivo (test del 16 al 22/9/2020):

| | p5 | p10 |
|---|---|---|
| Clientes con compras en el test | 2.093 | 4.162 |
| Clientes nuevos (sin compras previas) | 232 | 437 |

Con el 5% quedan pocos clientes nuevos para evaluar el caso en frío por segmentos; el 10% los duplica. El detalle de esta comparación está en [`controles_integridad.md`](controles_integridad.md).

> El notebook conserva los conteos de la fecha de corte provisoria (15/9/2020), que dan 2.317 y 4.600 clientes y 257 y 489 clientes nuevos. Los valores definitivos son los de la tabla de arriba.

## Conclusiones del muestreo

- El canal 2 es el online (inferencia respaldada por el patrón de abril de 2020) y concentra alrededor del 70% de las transacciones. Todo el proyecto trabaja solo con online.
- Se generaron dos muestras por cliente (número fijo calculado con el `customer_id`, p5 contenida en p10) con las tres tablas en Parquet, sin claves huérfanas ni otros canales.
- Ambas son representativas en compras por cliente, antigüedad de primera compra y vacíos de edad, con diferencias de hasta 0,16 puntos porcentuales. No lo son en cobertura de artículos: se leen como cotas.
- **Decisión:** la muestra del proyecto es **p10**. Duplica los clientes nuevos de la semana de test (de 232 a 437), triplica los pares repetidos de co-compra y tiene un costo bajo medido (3,5 s y 927 MB para la unión de las tres tablas). La p5 queda como respaldo para quien tenga una computadora justa, y todos trabajan con la misma muestra.
- Una vez que arrancó el EDA no se cambia de tamaño: cambiarlo invalidaría la comparación de lo ya hecho.

## Fuentes y referencias

Qué fuentes externas usamos para entender los datos. Donde el EDA habla de la "documentación del dataset", se refiere a las referencias 2 y 4 de esta tabla.

| # | Referencia | Qué respalda | Tipo de fuente |
|---|---|---|---|
| 1 | [Página de la competencia H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations) | Origen de los datos, archivos originales y condiciones de uso | Primaria |
| 2 | [Discusión de la competencia: resumen de un participante con comentarios del organizador y del staff](https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations/discussion/307001) | El precio está escalado y no revela valores reales; `sales_channel_id`: 1 = tienda, 2 = online; la tabla de transacciones incluye compras devueltas; se permite recomendar artículos ya comprados; `FN` indica si recibe el newsletter de moda y `Active` si está activo para comunicaciones; no se revela el mercado de origen; el test de la competencia son los 7 días posteriores al fin de los datos | Segunda mano (un participante resume lo que dijeron el organizador y el staff) |
| 3 | [Hilo "Recommender systems - Evaluation hell", de la misma competencia](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/discussion/307153) | La evaluación *offline* solo registra compras, no lo que vio cada cliente (sesgo de exposición) | Opinión de un participante, no del organizador |
| 4 | [Pestaña *Data* de la competencia](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data) | Descripción oficial de los archivos; las filas duplicadas de transacciones son compras múltiples del mismo artículo; el test son los 7 días posteriores al fin de los datos; se puntúan todos los clientes que compraron en ese período, tengan o no historial | Primaria. **No incluye diccionario de columnas**: las definiciones de `customers` y `articles` se interpretan por el nombre de la columna |

Una afirmación del EDA **no tiene fuente puntual registrada**: que las ventas siguen un patrón de hemisferio norte (se infiere de los propios datos). Sobre abril de 2020 (mes atípico), la referencia 2 recoge comentarios de participantes, **no del organizador**: señalan que faltan las transacciones de tienda física de ese mes, lo vinculan con el cierre de tiendas por la pandemia y proponen tratarlo como atípico. Es una explicación plausible; el dataset no la confirma.

El significado de cada variable está en [`glosario_variables.md`](glosario_variables.md).
