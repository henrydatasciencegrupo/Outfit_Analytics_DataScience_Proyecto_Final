# Muestreo y controles de integridad de los datos (H&M, Lookwise Data Lab)

> Documentación del **muestreo y la calidad de los datos**: anexo de apoyo al EDA, no un análisis exploratorio. Los hallazgos del EDA están en `EDA_Lookwise.md` y en el notebook `02_EDA_unificado_p10.ipynb`; el método para obtener la muestra, en `dataset_README.md`.

Registro de lo que se verificó con los datos y lo que falta verificar. Se actualiza a medida que se controlan los datos. Última actualización: 2026-11-04 (cierre del EDA de `trans`, `cust` y `art` sobre p10).

## Decisiones tomadas

- **Solo canal 2 (online):** confirmado por todo el grupo (2026-11-02).
- **Tamaño de la muestra:** se empieza con **p10 como muestra oficial** y p5 como respaldo (misma estructura). Se confirma con el grupo **antes de arrancar el EDA**, con una celda de prueba que corre cada integrante en su compu. Todos usan **la misma** muestra. Una vez iniciado el EDA **no se cambia de tamaño**, porque invalida la comparación de lo ya hecho. Si a alguien se le cuelga, primero se hacen pruebas para que funcione (cerrar aplicaciones, cargar menos columnas, consultar el Parquet con DuckDB); si no alcanza, baja **todo el grupo** a p5. Ver "Elección del tamaño". Faltan los resultados de la celda de prueba de los compañeros.
- **EDA:** lo hace cada integrante por su cuenta y después se compara (ver "Cómo se organiza el EDA").
- **Corte train/test (provisorio, a confirmar con el grupo):** test = **16/9/2020 a 22/9/2020** (últimos 7 días del dataset); train = todo lo anterior (hasta el 15/9/2020), sin solapamiento. Es la misma regla que usa Kaggle (7 días posteriores al fin del entrenamiento). Septiembre 2020 **no** está incompleto: el dataset va del 20/9/2018 al 22/9/2020 (734 días, sin días faltantes) y los últimos días tienen entre 2.482 y 2.552 compras diarias en total. Desde el corte, la exploración que depende de fechas o artículos se hace solo con el train (para evitar leakage); los controles de calidad usan los datos completos.

## Verificado sobre los archivos originales

| Control | Resultado | Fecha |
|---|---|---|
| Canal de venta: valor que corresponde a online | `sales_channel_id` = 2. Respaldo: comentario del Host de Kaggle y los datos (en abril 2020 el canal 1 no tiene filas) | 2026-10-31 (confirmado 2026-11-03) |
| Transacciones online (canal 2) | 22.379.862 filas | 2026-10-31 |
| Clientes con al menos una compra online | 1.108.418 | 2026-10-31 |
| Total sin filtrar | 31.788.324 filas y 1.371.980 clientes (en transacciones) | 2026-10-31 |
| `articles.csv`: filas | 105.542 | 2026-11-01 |
| `articles.csv`: `article_id` únicos | 105.542 (sin repetidos; se puede unir con `transactions` sin duplicar filas) | 2026-11-01 |
| `customers.csv`: filas | 1.371.980 | 2026-11-01 |
| `customers.csv`: `customer_id` únicos | 1.371.980 (sin repetidos; coincide con los clientes distintos de `transactions` sin filtrar) | 2026-11-01 |
| `customers.csv`: `postal_code` con valor | 1.371.980 (sin vacíos) | 2026-11-01 |
| Artículos con al menos una compra online | 98.322 de 105.542 (7.220 nunca se vendieron online) | 2026-11-02 |
| Artículos con 5 o más compras online | 85.223 | 2026-11-02 |
| Rango de fechas (muestra p10) | 20/9/2018 a 22/9/2020, 734 días, sin días faltantes; no hay hora | 2026-11-03 |

## Valores vacíos en edad

| Población | Clientes | Con edad | Sin edad | % sin edad |
|---|---|---|---|---|
| Todos los clientes (`customers.csv`) | 1.371.980 | 1.356.119 | 15.861 | 1,16% |
| **Clientes online (referencia del proyecto)** | 1.108.418 | 1.096.081 | 12.337 | 1,11% |
| Muestra p5 | 55.454 | | | 1,11% |
| Muestra p10 | 110.252 | 109.044 | 1.208 | 1,10% |

El cruce con los clientes que compraron por canal 2 devolvió 1.108.418, igual que el conteo previo. Las dos muestras conservan el porcentaje de la población online (2026-11-02).

**Edad en p10 (EDA, 2026-11-03):** rango 16 a 98, mediana 31, media 35,9, distribución bimodal (alrededor de 20-30 y de 50). 27 clientes con más de 84 años y 7 con más de 90 (valores raros, se conservan). Los 1.208 sin edad compran menos (mediana 3 contra 8; media 6,5 contra 20,3). En el test solo 7 clientes no tienen edad y ninguno es frío.

## Otras variables de `customers` (EDA, p10, 2026-11-03)

- `FN`: 66,24% vacío (el 99,8% de los FN=1 son "Regularly"; el 98,1% de los vacíos son "NONE"; 204 inconsistencias).
- `Active`: 66,98% vacío. El 87,4% de los Active vacíos son club ACTIVE: vacío no significa inactivo.
- `club_member_status`: ACTIVE 100.381 / PRE-CREATE 9.217 / LEFT CLUB 53 / vacío 601. **PRE-CREATE no son cuentas nuevas** (primera compra mediana 2019-03-13 contra 2019-04-19 de ACTIVE; mediana de 4 compras contra 8). Es un detector débil de fríos: 77 en el test, 26 fríos (33,8%), cubre el 5,9% de los 437 fríos.
- `fashion_news_frequency`: NONE 71.709 / Regularly 37.293 / Monthly 46 / vacío 1.204.
- `postal_code`: 87.652 valores distintos para 110.252 clientes; el 82% de los códigos (72.201) aparece en un solo cliente; el código dominante concentra 2.857 clientes (2,6%, 136 veces el segundo), probablemente un valor por defecto. Ese grupo tiene más edad vacía (7,6% contra 0,9%) y menos PRE-CREATE (0,7% contra 8,6%).
- `customers` es una foto de un único momento: riesgo de leakage con FN, Active, club_member_status y edad.

## Variables de `articles` (EDA, p10, 2026-11-03)

- 105.542 filas × 25 columnas; el único campo con vacíos es `detail_desc` (416, 0,39%).
- `article_id` de 10 caracteres, único. `product_code` = primeros 7 dígitos (47.224 productos, 2,23 variantes en promedio).
- Valores "Unknown" que funcionan como faltantes disfrazados: `garment_group_name` 3.873 (3,67%), `product_group_name`/`product_type_name` 121, color con código -1: 28.
- Códigos y nombres consistentes (un código, un nombre). 61.722 descripciones repetidas; 517 `prod_name` con doble espacio.

## Muestras generadas (2026-11-01)

**Método:** a cada cliente online se le asigna un número fijo, `bucket = hash(customer_id || 'lookwise42') % 10000`. La muestra del 5% son los clientes con `bucket < 500` y la del 10% los de `bucket < 1000`. La del 5% queda contenida en la del 10%. Se conserva todo el historial online de cada cliente y `articles` va completo. El script (semilla, fórmula y umbrales) está guardado en el notebook. Ubicación: carpeta local `dataset/` (subcarpetas `p5` y `p10`); los datos no se suben al repositorio.

| Control | p5 (5%) | p10 (10%) |
|---|---|---|
| Clientes sorteados | 55.454 (5,00% de 1.108.418) | 110.252 (9,95%) |
| Filas de `transactions` | 1.122.274 (5,01% de las filas online) | 2.226.486 (9,95%) |
| Clientes distintos en `transactions` | 55.454 | 110.252 |
| Filas de `customers` | 55.454 | 110.252 |
| Filas de `articles` | 105.542 | 105.542 |
| Filas con canal distinto de 2 | 0 | 0 |
| Transacciones sin cliente en `customers` (huérfanos) | 0 | 0 |
| Transacciones sin artículo en `articles` (huérfanos) | 0 | 0 |
| Peso `transactions.parquet` | 20,7 MB | 43,2 MB |
| Peso `customers.parquet` | 7,1 MB | 14,1 MB |
| Peso `articles.parquet` | 6,2 MB | 6,2 MB |
| Peso total aproximado | 34,0 MB | 63,5 MB |

Contenido: son las tres tablas originales filtradas y recortadas. No traen corte train/test, vacíos tratados, meses atípicos marcados ni variables nuevas. Todo eso es trabajo del EDA y de la preparación de datos (ver "Paquete de modelado"). No se trabaja con imágenes. Los Parquet se abren con `pd.read_parquet` (hace falta `pyarrow`); DuckDB no es obligatorio.

## Representatividad de las muestras

**Compras por cliente** (% de clientes en cada tramo, 2026-11-01):

| Tramo de compras | Total online | p5 | p10 |
|---|---|---|---|
| 1 compra | 11,36% | 11,27% | 11,28% |
| 2 a 5 | 30,50% | 30,43% | 30,54% |
| 6 a 20 | 32,66% | 32,66% | 32,68% |
| Más de 20 | 25,47% | 25,63% | 25,49% |

La diferencia máxima contra el total es 0,16 puntos porcentuales (p5, tramo de más de 20). En este aspecto las dos muestras son representativas.

Dato para el EDA (propiedad del dataset online, no de la muestra: el total online da casi lo mismo): solo alrededor del 11% de los clientes tiene una única compra online y cerca del 25% tiene más de 20. Esos tramos cuentan solo compras online (por el filtro de canal), así que un cliente con una compra online pudo haber comprado también en tienda. Los clientes "fríos" no están todos hechos en los datos: hay que construirlos recortando el historial, además de los clientes cuya primera compra cae después del corte. La definición de "cliente frío" se mide contra la fecha de corte, no contra el total de compras.

**Estadísticas por cliente vs. por artículo:** las estadísticas por cliente no se sesgan por muestrear clientes. Las de artículo sí se inflan en la muestra (por ejemplo, 25,8% de artículos sin ventas y artículos del test ausentes en el train): se leen como cotas, no como valores de la población.

**Fecha de primera compra** (% de clientes por mes de su primera compra online, 2026-11-02; 25 meses, sept 2018 a sept 2020):

- La distribución mensual de p5 y de p10 sigue de cerca la del total online. La mayor diferencia es de unos 0,3 puntos (p5 en diciembre 2018: 6,05% contra 5,77%); en p10 no pasa de unos 0,15 puntos.
- Meses recientes (total online / p5 / p10): julio 2020 1,87 / 1,79 / 1,82; agosto 2020 1,83 / 1,85 / 1,80; septiembre 2020 1,28 / 1,29 / 1,30.
- Los primeros meses del dataset (septiembre y octubre 2018: 7,06% y 12,61%) están inflados: la "primera compra" es la primera dentro de la ventana observada, y ahí hay clientes que ya existían antes. No se pueden leer como clientes nuevos reales.

**Cobertura de artículos** (2026-11-02):

| Control | Total online | p5 | p10 |
|---|---|---|---|
| Artículos con al menos 1 compra | 98.322 | 68.978 (70,2% del total) | 78.318 (79,7%) |
| Artículos con 5 o más compras | 85.223 | 38.944 (45,7%) | 49.820 (58,5%) |
| % de las compras online del total que usan artículos presentes en la muestra | 100% | **98,60%** | **99,41%** |

Lectura: por cantidad de artículos el 5% pierde alrededor del 30% de los artículos con ventas, pero son artículos de muy baja venta (cola larga): ponderado por compras, solo se pierde el 1,4% (5%) o el 0,6% (10%). La cobertura deja de ser un argumento fuerte a favor del 10%. Limitación: la medida cuenta si el artículo aparece al menos una vez, no cuánta señal hay sobre él (un artículo con una sola venta en la muestra aporta poco a co-compra). `articles` va completo en las dos muestras, así que un modelo de contenido puede trabajar con los atributos de todos los artículos aunque no tengan ventas en la muestra.

## Elección del tamaño (p5 o p10)

**Tamaño de la semana de test con el corte provisorio del 16/9/2020** (test = 16 a 22/9; recalculado 2026-11-03, reemplaza la tabla anterior que usaba el 15/9):

| | p5 | p10 |
|---|---|---|
| Transacciones en train | 1.113.960 | 2.210.154 |
| Clientes con compras en el test | 2.093 | 4.162 |
| Compras en el test | 8.314 | 16.332 |
| Clientes del test con historial en train | 1.861 | 3.725 |
| Clientes fríos naturales (primera compra online desde el 16/9) | 232 (11,1%) | 437 (10,5%) |
| Compras de los fríos naturales | 765 | 1.442 (8,8% del test) |
| Artículos distintos en el test | 3.277 | 4.778 |
| Artículos del test ausentes en el train | 460 (14,0%) | 538 (11,3%) |
| Compras del test sobre artículos ausentes en el train | 1.036 (12,5%) | 1.537 (9,4%) |

Para comparar modelos sobre todos los clientes alcanzan los ~2.100 clientes del 5%. Para los clientes fríos reales, el 5% deja solo 232 en el test (el 10%, 437): con ese tamaño el MAP@12 del grupo se mueve mucho por azar, y el 10% queda justo para abrirlo por segmentos (0, 1 o 2 compras visibles). La simulación de fríos (ver más abajo) compensa la cantidad de casos pero no reemplaza a los fríos reales. Las cifras de artículos ausentes están infladas por el muestreo (ver "Representatividad").

**Pruebas de costo en una compu de prueba** (16,7 GB de RAM en total, 3,0 GB disponibles en el momento de la prueba), 2026-11-02:

| Prueba | p5 | p10 |
|---|---|---|
| Carga de las tres tablas, unión con `articles` (4 columnas) y `customers` (edad), top 12 de más vendidos | no medido | 3,5 s en total; la tabla unida ocupa 927 MB |
| Prueba pesada de co-compra (todos los pares de artículos comprados por el mismo cliente, `memory_limit` de 2 GB) | 4,7 s | 11,1 s (x2,4) |
| Pares distintos de artículos | 28.383.189 | 53.149.275 (x1,9) |
| Co-ocurrencias totales | 31.429.744 | 63.074.954 (x2,0) |
| Repeticiones (co-ocurrencias menos pares distintos) | 3.046.555 | 9.925.679 (x3,3) |
| Tope de % de pares que aparecen más de una vez | 10,7% | 18,7% |

Lectura: el costo del 10% es bajo en estas pruebas. Con el doble de datos, las repeticiones de pares se triplican, lo que mejora la señal de co-compra (que necesita ver pares repetidos). Aun así, más del 80% de los pares aparece una sola vez: la matriz de co-compra es muy dispersa (en p5, los pares presentes son alrededor del 1,2% de las combinaciones posibles de sus 68.978 artículos), así que cualquier modelo de co-compra necesita un formato disperso. Limitaciones: la prueba cuenta todo lo que un cliente compró en dos años como un solo carrito (un modelo real probablemente use ventanas más cortas); mide solo co-compra; el tiempo de entrenamiento de los modelos de verdad no se conoce hasta el Sprint 2; el tamaño de la tabla unida crece si se unen las 25 columnas de `articles`; no se midió el pico de memoria de la unión.

**Propuesta de justificación:**

> Se generaron dos muestras (5% y 10%). Se elige el 10% como principal porque duplica los clientes fríos reales de la semana de test (de 232 a 437), triplica las repeticiones de pares de artículos que necesita co-compra y tiene un costo bajo medido (unión en unos 4 segundos y 930 MB; prueba de co-compra en 11 segundos). El 5% queda como respaldo para quien tenga una compu justa; si hay problemas de memoria o se cuelga, se usa p5 (misma estructura). Los clientes fríos simulados (recortando el historial) complementan a los reales, pero no los reemplazan.

**Criterio para el grupo:**

1. Cada integrante corre la celda de prueba (RAM + carga, unión y top 12 de p10), con sus programas habituales abiertos, y le pasa al responsable del EDA las dos líneas de salida.
2. Si a alguien le da error de memoria, tarda más de unos 3 minutos (umbral propuesto, no medido) o se le cuelga la compu, avisa y se hacen pruebas para que funcione (cerrar aplicaciones, cargar menos columnas, consultar el Parquet con DuckDB).
3. Si no se logra, baja **todo el grupo** a p5: todos trabajan con la misma muestra.
4. Se decide **antes de arrancar el EDA** y después no se cambia. Si en el Sprint 2 un modelo pesa demasiado, se optimiza el código; el p5 (contenido en el p10) puede usarse solo para pruebas rápidas, pero la evaluación final se hace sobre el p10.

## Clientes fríos simulados (método propuesto)

- Idea: ocultarle al modelo parte del historial de clientes que ya tienen compras, no borrar datos. Ejemplo: una clienta con 12 compras antes del corte y 2 compras en la semana de test. Evaluación normal: el modelo ve las 12. Simulación de fría: ve solo su primera compra (o 0, o 2) y se compara con las mismas 2 compras del test.
- Con el corte del 16/9 hay 1.861 clientes en p5 y 3.725 en p10 que compran en la semana de test y ya tenían historial; cada uno puede ser un caso de frío con 0, 1 o 2 compras visibles.
- Condición: las compras ocultas tampoco se pueden usar para entrenar (si no, hay leakage).
- Limitación a declarar: un cliente con historial largo conserva gustos de cliente frecuente aunque se le oculte el historial; no es idéntico a un cliente realmente nuevo. Se evalúan y se informan por separado los fríos reales y los simulados.
- Momento: la decisión del método se anota en el EDA; la lista de clientes y compras ocultas se arma en la preparación de datos con el corte fijado; la evaluación es el final del Sprint 1 y el Sprint 2. Para Demo 1 alcanza con el método definido y justificado. Bonus: al probar con 0, 1 y 2 compras visibles se puede mostrar cómo cambia el resultado según el historial.
- Simular un mercado nuevo usando `postal_code` **no es viable** (códigos casi únicos y un código dominante que parece valor por defecto); la justificación está en el README. El criterio alternativo está pendiente.

## Cómo se organiza el EDA

El grupo acordó que todos hacen el EDA por su cuenta y después comparan. Para que la comparación sirva y no se repita trabajo:

- **Mismos archivos:** todos usan el mismo tamaño de muestra.
- **Misma lista de preguntas:** por ejemplo, ventas por mes, compras por cliente, artículos más vendidos, edad, clientes fríos y qué hacer con marzo-abril 2020. Cada una responde la lista completa por su cuenta.
- **Un responsable por tema:** además, cada integrante lidera una de las preguntas (se anota en Trello), para que al comparar alguien se haga cargo de cada punto.
- **Fecha fija para comparar:** propuesta, domingo 8/11, con un único notebook final donde se junta lo acordado.
- **Decisiones que afectan a todos** (fecha de corte, meses atípicos, tratamiento de la edad vacía) se toman en grupo y se anotan en este documento, no individualmente.

Riesgo a vigilar: si cada una decide por su cuenta, el baseline y las métricas dan distinto y no se pueden comparar.

## Resultados del EDA relevantes para estos controles (p10, train, 2026-11-03)

- Duplicados (mismo día, cliente y artículo): 266.398 filas (11,96%); 284.045 ignorando el precio; 17.082 combinaciones día-cliente-artículo con más de un precio. Más frecuentes en Swimwear (16,8%), Socks & Tights (14,7%) y Lower (13,9%). Se conservan (ver propuestas).
- Compras por cliente (train): mediana 7, media 20,1, p99 180, máximo 1.068; 11,3% con una sola compra; 41,8% con 5 o menos.
- Artículos (train): top 12 = 1,1% de las ventas; top 1.000 = 18,9%; 6.290 cubren el 50%; 11.591 vendidos una sola vez; 27.762 (26,3%) sin ventas en el train. El top 12 del train pesa solo 0,92% de las compras del test.
- Temporalidad: pico de abril 2020 (4.459 compras/día) y de junio 2019 (4.480/día); día récord 11/4/2020 (16.104); diciembre es el mes más bajo; el miércoles concentra 16,1%. La estacionalidad corresponde al **hemisferio norte** (Swimwear 17,6% en mayo / 16,3% en junio / 15,6% en julio contra 1,7% en noviembre; Knitwear 16,0% en noviembre). Va a las limitaciones por la inversión de estaciones respecto de Argentina.
- Precios: el 0,1% más caro son Coat, Jacket, Dress y Sweater; las medianas de Coat (0,0949) y Jacket (0,0678) son muy superiores a T-shirt/Socks (0,0135). Los outliers de precio se conservan.
- Mezcla de edad e índice: Divided baja de 36,8% a 18,6% con la edad; Ladieswear sube de 56,5% a 71,2%.

## Propuestas para confirmar con el grupo (no son decisiones todavía)

1. **Corte:** test 16 a 22/9/2020, train hasta el 15/9.
2. **Meses atípicos (marzo a mayo 2020):** se conservan en train; el test no cae en ellos. Opcional: prueba de estrés reportada aparte.
3. **Duplicados:** se conservan filas originales; se ofrece además una versión colapsada (cantidad, precio mínimo y máximo).
4. **Edad vacía:** no se imputa en la tabla original; se agregan `edad_faltante`, `tramo_edad` (con categoría "sin edad") y `edad_relleno` (31, la mediana).
5. **Variables de `customers`:** `FN`, `Active` y `postal_code` se conservan pero no se usan; `club_member_status` y `fashion_news_frequency` se recomienda no usarlas (leakage y poca señal).
6. **Valores atípicos (edad >84, precios altos, clientes con muchas compras):** no se eliminan.
7. **Artículos del test ausentes en el train:** decidir si se evalúan igual (sin posibilidad de acierto para modelos de co-compra) o se reportan por separado.
8. **Definición de baseline:** historial completo contra ventana reciente (tarea de quien modela).
9. **Simulación de mercado nuevo:** criterio alternativo a `postal_code`.
10. **Verificación pendiente:** diccionario de datos de la pestaña Data de Kaggle.

## Paquete de modelado (p10)

Carpeta local `p10_modelado` (no se sube al repositorio por su tamaño), pensada para quien entrena los modelos: `train.parquet`, `train_colapsado.parquet`, `test.parquet`, `test_verdad.parquet`, `customers.parquet` (con las columnas de edad nuevas), `articles.parquet`, `evaluar.py` (MAP@12), `README_modelado.md` y `00_verificar_datos.ipynb`. Reglas: el test solo se usa para evaluar, las estadísticas se calculan solo con el train, no se usan `FN`, `Active` ni `postal_code`, no se eliminan filas ni outliers. El EDA completo está en el notebook `EDA_unificado_p10.ipynb`.

## Pendiente

- Recibir el resultado de la celda de prueba de cada integrante y confirmar el tamaño de muestra (los resultados de los compañeros para p10 todavía no están).
- Confirmar en grupo las propuestas de arriba.
- Sprint 2: medir el costo real de entrenar los modelos (todavía desconocido).
- Configurar colaboradores en el repositorio de GitHub (es público: no se suben datos).

## Notas

- Septiembre 2020 **no** está incompleto (verificado el 2026-11-03 con conteos diarios): no hay días faltantes y el nivel diario es estable.
- Marzo a mayo 2020 son meses atípicos (pico de abril: 4.459 compras/día): decidir cómo tratarlos. Se pueden usar en train; el test principal va en la última semana. Descartar marzo a septiembre 2020 sacaría el 29% de las filas online y el período más reciente: no se recomienda como opción por defecto.
