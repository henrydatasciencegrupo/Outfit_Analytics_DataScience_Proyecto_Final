# EDA del dataset H&M (Lookwise Data Lab)

Documento de trabajo del análisis exploratorio. Los controles de las muestras (método, tamaño, representatividad) se resumen en `docs/dataset_README.md`. Acá va lo que se descubre de los datos y qué decisiones quedan.

Base de trabajo: muestra del 10% (`p10`), solo canal online. Las tres tablas se llaman `trans`, `cust` y `art` en el notebook. El notebook con todo el análisis y las salidas es `notebooks/EDA_unificado_p10.ipynb` (unifica los EDA individuales del grupo; todas las cifras de este documento salen de ahí).

## Parte 1. Calidad de datos

Se hace con las tablas completas de la muestra (no depende del corte train/test). Lo que depende de fechas o artículos (parte 2) se hace solo con el train.

### Estado por tabla

| Tabla | Estado |
|---|---|
| `trans` (transacciones) | Cerrada |
| `cust` (clientes) | Cerrada (incluye el cruce de `postal_code` con edad, `FN` y `PRE-CREATE`) |
| `art` (artículos) | Cerrada |
| Parte 2 (train) | Hecha en el notebook unificado; conclusiones abajo |

## Diccionario de variables

Fuente de las definiciones marcadas como "Kaggle": discusión de la competencia (resumen de zakopuro con comentarios atribuidos al Host y al staff de Kaggle; fuente de segunda mano) https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations/discussion/307001. El resto se interpreta por el nombre de la columna y debe verificarse contra la pestaña Data de la competencia.

### `trans` (transacciones): una fila por compra de un artículo. 2.226.486 filas en p10

| Variable | Qué es | Tipo | Notas |
|---|---|---|---|
| `t_dat` | Fecha de la compra | fecha (viene como texto, se convierte) | Sin hora. Del 20/9/2018 al 22/9/2020. 734 días, ninguno sin compras |
| `customer_id` | Identificador anónimo del cliente (hash de 64 caracteres) | texto | Se une con `cust`. No se convierte a número |
| `article_id` | Identificador del artículo (10 dígitos) | texto | Se une con `art`. Conserva ceros iniciales. No incluye talle |
| `price` | Precio pagado, escalado | decimal | Sin unidad: no revelan los valores reales (Kaggle). Mediana 0,0254, máximo 0,5068 |
| `sales_channel_id` | Canal de venta: 1 = tienda, 2 = online | entero | Kaggle y verificado con los datos (abril 2020). En p10 vale siempre 2: se excluye del análisis |

### `cust` (clientes): una fila por cliente. 110.252 filas en p10

| Variable | Qué es | Tipo | Notas |
|---|---|---|---|
| `customer_id` | Identificador del cliente | texto | Clave. Sin repetidos |
| `FN` | Si el cliente recibe el newsletter de moda (Kaggle) | decimal (1.0 o vacío) | 66,2% de vacíos. El vacío equivale casi siempre a "no recibe" (inferencia de los datos) |
| `Active` | Si el cliente está activo para comunicaciones (Kaggle) | decimal (1.0 o vacío) | 67,0% de vacíos. El vacío no significa "inactivo" y no se puede interpretar |
| `club_member_status` | Estado como socio del club (ACTIVE, PRE-CREATE, LEFT CLUB) | texto | 0,5% de vacíos. PRE-CREATE sin definición en Kaggle |
| `fashion_news_frequency` | Frecuencia del newsletter (NONE, Regularly, Monthly) | texto | 1,1% de vacíos |
| `age` | Edad del cliente | decimal | 1,1% de vacíos. 16 a 98 años |
| `postal_code` | Código postal anonimizado (hash) | texto | Sin vacíos. No se interpreta como ubicación |

### `art` (artículos): una fila por artículo. 105.542 filas, 25 columnas

Descripciones por el nombre de la columna. A verificar contra Kaggle.

| Variable | Qué es probable que sea |
|---|---|
| `article_id` | Identificador del artículo (clave) |
| `product_code` | Código del producto (**primeros 7 dígitos** del `article_id`); agrupa variantes de color |
| `prod_name` | Nombre del producto |
| `product_type_no` / `product_type_name` | Tipo de producto (código y nombre) |
| `product_group_name` | Grupo de producto |
| `graphical_appearance_no` / `graphical_appearance_name` | Aspecto gráfico (liso, rayas, estampado...) |
| `colour_group_code` / `colour_group_name` | Grupo de color (el código es texto con ceros iniciales; '-1' = Unknown) |
| `perceived_colour_value_id` / `perceived_colour_value_name` | Valor del color percibido (claro, oscuro...) |
| `perceived_colour_master_id` / `perceived_colour_master_name` | Color percibido principal |
| `department_no` / `department_name` | Departamento |
| `index_code` / `index_name` | Índice (línea de producto) |
| `index_group_no` / `index_group_name` | Grupo de índice |
| `section_no` / `section_name` | Sección |
| `garment_group_no` / `garment_group_name` | Grupo de prenda |
| `detail_desc` | Descripción en texto del artículo |

Los pares código y nombre (`_no` y `_name`) son consistentes: ningún código tiene más de un nombre. Al revés pasa en `department_name` (22 nombres con más de un código), `product_type_name` y `section_name` (1 cada uno): para agrupar conviene usar el código.

## Hallazgos en `trans`

- **Nulos:** ninguno en las 5 columnas.
- **Tipos:** fecha convertida a fecha; ids como texto (largo constante: 64 y 10 caracteres).
- **Canal:** un único valor (2), se excluye del análisis.
- **Fecha:** 734 días continuos, sin huecos. Sin hora. Día récord: 11/4/2020 (16.104 compras).
- **Precio:** cola larga y gradual a la derecha. Cuantiles: mediana 0,0254; p90 0,0508; p99 0,1017; p99,9 0,1749; máximo 0,5068. Sin precios cero o negativos. No se elimina nada: la cola alta corresponde a abrigos y camperas (ver Parte 2).
- **Duplicados:** 266.398 filas completamente repetidas (11,96%) y 284.045 ignorando el precio. La diferencia (17.647) son casos con precio distinto. Posibles causas: varias unidades, distintos talles o compra más devolución. No se puede confirmar.

## Hallazgos en `cust` (variable por variable)

- **`FN`:** 66,24% de vacíos (73.027). El 99,8% de los `FN = 1` es `Regularly` y el 98,1% de los vacíos es `NONE`: el vacío equivale casi siempre a "no recibe". Redundante con `fashion_news_frequency`: se conserva pero no se usa.
- **`Active`:** 66,98% de vacíos (73.845). El 98,4% de los `Active = 1` es socio ACTIVE, pero el 87,4% de los vacíos también. El vacío no significa "inactivo" y no equivale a `club_member_status`. Se conserva, no se usa.
- **`club_member_status`:** ACTIVE 100.381 (91,0%), PRE-CREATE 9.217 (8,4%), LEFT CLUB 53 (0,05%), vacío 601 (0,55%). PRE-CREATE (sin definición en Kaggle): 94,1% tiene `Active` vacío y pesa 6,0% entre los fríos naturales del test contra 1,4% entre los que tienen historial. **No parecen cuentas nuevas**: su primera compra tiene mediana en marzo de 2019 (ACTIVE: abril de 2019), pero compran menos (mediana de 4 compras contra 8). Qué significa sigue abierto. Riesgo de leakage (foto de un solo momento).
- **`fashion_news_frequency`:** NONE 71.709 (65,0%), Regularly 37.293 (33,8%), Monthly 46 (0,04%), vacío 1.204 (1,09%, todos con `FN` vacío). Se conserva, sin uso.
- **`age`:** 1.208 vacíos (1,10%); 16 a 98 años, mediana 31, promedio 35,9. Histograma con dos grupos (20 a 30 y alrededor de 50). 27 clientes superan los 84 años (7 los 90): plausible, no se eliminan. Los clientes sin edad compran menos (mediana 3 contra 8 compras): el vacío no parece aleatorio. Propuesta: grupo "sin edad" aparte, sin imputar con la mediana.
- **`postal_code`:** 87.652 valores distintos, 82% con un solo cliente. Un código concentra 2.857 clientes (136 veces el segundo): parece un valor por defecto. Ese grupo tiene más edad vacía (7,6% contra 0,9%) y casi no tiene PRE-CREATE (0,7% contra 8,6%). Se conserva, no se usa como variable. La propuesta prevé simular un mercado nuevo apartando clientes por código postal, pero con estos datos no conviene: el hash no tiene significado geográfico, el 82% de los códigos tiene un solo cliente y el código dominante parece "sin dato", así que solo se podrían apartar grupos arbitrarios. La justificación completa va en el README.

## Hallazgos en `art`

- **Nulos:** solo `detail_desc` (416, 0,39%), sobre todo en prendas de arriba y calzado.
- **Clave:** `article_id` sin repetidos, siempre 10 caracteres. `product_code` = primeros 7 dígitos; 47.224 productos para 105.542 artículos (2,2 variantes por producto).
- **"Unknown" escondidos:** `garment_group_name` 3.873 (3,67%), `product_group_name` y `product_type_name` 121 (0,11%), `colour_group_name` 28 (0,03%, código -1). Se tratan como una categoría más.
- **Descripción:** promedio 142 caracteres; 61.722 repetidas (las variantes comparten texto).
- **Categorías:** bien escritas. Grupos chicos que no son ropa (Cosmetic, Bags, Items, Furniture). `index_group_name` lo domina Ladieswear (37,6% del catálogo).
- **Sin ventas:** 27.224 (25,8%) en la muestra completa; 27.762 (26,3%) en train. Inflado por la muestra del 10%.

## Integridad entre tablas

Todos los clientes y artículos de `trans` existen en sus tablas; todos los clientes de `cust` compraron al menos una vez.

## Lo que aporta la discusión de Kaggle

- El test de la competencia son los 7 días posteriores al fin de los datos, la misma semana para todos los clientes: respalda nuestra regla de test de 7 días.
- Se permite recomendar artículos que el cliente ya compró.
- La tabla de transacciones incluye todas las compras, aunque se hayan devuelto después.
- No se revela de qué mercado vienen los datos (Host): limitación para la estacionalidad.
- Abril 2020 sin ventas de tienda; propuesta de la comunidad: tratar como atípico.

## Parte 2. Con el train

Corte propuesto, **pendiente de acuerdo del grupo**: train hasta el 15/9/2020, test del 16 al 22/9/2020 (7 días completos). Otro EDA individual del grupo llegó al mismo corte de forma independiente. Train: 2.210.154 compras (99,3%) y 109.815 clientes. Test: 16.332 compras y 4.162 clientes.

- **Temporal:** septiembre de 2018 (11 días) y de 2020 (15 días en train) incompletos en días, no en ritmo. Picos de ritmo: junio 2019 (4.480 por día) y abril 2020 (4.459 por día); diciembre es el mes más bajo. Miércoles el día más alto (16,1%).
- **Estacionalidad:** ropa de baño 15,6 a 17,6% de las compras entre mayo y julio contra 1,7 a 2,2% en noviembre y septiembre; punto (`Knitwear`) al revés (13,6 a 16,0% entre septiembre y noviembre). Es **hemisferio norte**, invertido respecto de Argentina. Indica el hemisferio, no el país.
- **Precio por tipo:** el 0,1% más caro (2.230 compras) son abrigos, camperas, vestidos y suéteres. Mediana: Coat 0,0949 y Jacket 0,0678 contra 0,0135 de T-shirt y Socks. No hay errores: el precio depende del tipo de producto.
- **Duplicados por grupo:** ropa de baño 16,8%, medias y pantys 14,7%, prendas de abajo 13,9%, de arriba 10,6%, calzado 8,4%, accesorios 5,6%. Aparecen en todos los grupos (menos en accesorios, pero no son cero): no alcanza para decidir la causa.
- **Compras por cliente:** mediana 7, promedio 20,1, p99 180, máximo 1.068; 11,3% con una sola compra y 41,8% con 5 o menos.
- **Artículos:** top 12 = 1,1% de las ventas, top 1.000 = 18,9%; 6.290 artículos cubren la mitad; 11.591 vendidos una sola vez.
- **Edad y mix:** Divided pesa 36,8% entre menores de 20 y 18,6% después de los 60; Ladieswear sube de 56,5% a 71,2%; Baby/Children se concentra entre los 31 y 50 años. La edad es una señal útil para clientes fríos (hipótesis).
- **Clientes fríos:** 437 naturales (10,5% de los 4.162 del test; 1.442 compras, 8,8% del test). Mediana de edad 29 contra 31; PRE-CREATE 6,0% contra 1,4%, pero como detector de fríos es débil: de los 77 PRE-CREATE del test solo 26 son fríos (33,8%) y cubren el 5,9% de los fríos. 538 de los 4.778 artículos del test (11,3%) no aparecen en train; los 12 más vendidos de train cubren solo 0,92% de las compras del test: baseline débil.

## Decisiones pendientes (de grupo)

- Fecha de corte train/test (propuesta 16/9/2020).
- Tratamiento de los meses atípicos (marzo a mayo 2020; abril confirmado como pico).
- Duplicados: mantener o colapsar a una interacción por cliente, artículo y día.
- Edad vacía (grupo "sin edad"), edad por tramos y uso de `PRE-CREATE` (propuesta: no usarla).
- Método de simulación de clientes fríos (0, 1 o 2 compras visibles) y tratamiento de los artículos del test ausentes en train.
- Criterio para simular el mercado nuevo, ya que no se usa el código postal (la justificación va en el README).
- Verificar las definiciones de las columnas contra la pestaña Data de Kaggle.

## Limitaciones a declarar

- Canal 2 = online según el Host (indirecto) y confirmado con los datos.
- Mercado desconocido; el hemisferio norte se infiere de la estacionalidad.
- Precio sin unidad.
- Sin talle ni cantidad; la tabla incluye devoluciones.
- Fecha sin hora.
- `customers` es una foto de un solo momento, sin fecha de registro de cada valor. No se sabe si `Active`, `FN`, `club_member_status` o `age` reflejan al cliente cuando compró por primera vez o su situación posterior; usarlas podría filtrar información del futuro (leakage), un riesgo relevante para los clientes en frío.
- Evaluación offline: los datos solo registran compras, no qué artículos vio cada cliente (sesgo de exposición). La evaluación (MAP@12 sobre la semana de test) mide si se acierta lo que efectivamente se compró. El top 12 del baseline parte de ese sesgo. Fuente: hilo "Recommender systems - Evaluation hell" de la competencia (participante, no Host).
- La muestra es el 10% de los clientes: las cifras por artículo (artículos sin ventas, artículos del test ausentes en train) están infladas; las cifras por cliente no, porque se conserva todo el historial de cada cliente elegido.
- No se trabaja con imágenes.
