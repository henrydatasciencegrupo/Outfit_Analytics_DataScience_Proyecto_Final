# Glosario de variables

Qué significa cada columna de las tres tablas del dataset (H&M Personalized Fashion Recommendations). Las tablas se unen por `customer_id` y `article_id`.

## Compras (`transactions`)

| Variable | Qué significa |
|---|---|
| `t_dat` | Fecha de la compra (sin hora) |
| `customer_id` | Identificador anónimo del cliente |
| `article_id` | Identificador del artículo comprado (no incluye talle) |
| `price` | Precio pagado, escalado (sin unidad real) |
| `sales_channel_id` | Canal de venta: 1 = tienda física, 2 = online |

## Clientes (`customers`)

| Variable | Qué significa |
|---|---|
| `customer_id` | Identificador anónimo del cliente |
| `FN` | Si recibe el newsletter de moda (1 o vacío) |
| `Active` | Si está activo para comunicaciones (1 o vacío) |
| `club_member_status` | Estado como socio del club: ACTIVE, PRE-CREATE o LEFT CLUB |
| `fashion_news_frequency` | Frecuencia del newsletter: NONE, Regularly o Monthly |
| `age` | Edad del cliente en años |
| `postal_code` | Código postal anonimizado (sin significado geográfico) |
| `edad_faltante` | Verdadero si el cliente no tiene edad cargada (columna del equipo) |
| `tramo_edad` | Grupo de edad: <=20, 21-25, 26-30, 31-40, 41-50, 51-60, >60 o sin edad (columna del equipo) |
| `edad_relleno` | La edad, con la mediana (31 años) donde falta (columna del equipo) |

## Artículos (`articles`)

| Variable | Qué significa |
|---|---|
| `article_id` | Identificador único del artículo (un producto en un color) |
| `product_code` | Código del producto (los primeros 7 dígitos de `article_id`); agrupa los colores de un mismo producto |
| `prod_name` | Nombre del producto |
| `product_type_no` / `product_type_name` | Tipo de producto (por ejemplo, Trousers, Dress) |
| `product_group_name` | Grupo amplio de producto (por ejemplo, Accessories, Shoes) |
| `graphical_appearance_no` / `graphical_appearance_name` | Aspecto de la prenda (por ejemplo, Solid = liso, Stripe = rayas) |
| `colour_group_code` / `colour_group_name` | Color de la prenda (por ejemplo, Black, Dark Blue) |
| `perceived_colour_value_id` / `perceived_colour_value_name` | Qué tan claro u oscuro se percibe el color (Dark, Light, Bright...) |
| `perceived_colour_master_id` / `perceived_colour_master_name` | Color principal percibido (Black, Blue, White...) |
| `department_no` / `department_name` | Departamento de H&M donde se vende (el nivel más detallado) |
| `index_code` / `index_name` | Línea comercial (por ejemplo, Ladieswear, Menswear) |
| `index_group_no` / `index_group_name` | Grupo de líneas comerciales (Ladieswear, Menswear, Baby/Children, Divided, Sport) |
| `section_no` / `section_name` | Sección de la tienda |
| `garment_group_no` / `garment_group_name` | Grupo de prenda según tejido o uso (por ejemplo, Jersey Basic, Knitwear) |
| `detail_desc` | Descripción del artículo en texto libre |

*Las columnas con pares `_no` / `_name` (o `_code`, `_id`) dicen lo mismo: el código sirve para agrupar y el nombre para leer. Las definiciones de `customers` y `articles` son las de la documentación del dataset o se interpretan por el nombre de la columna; conviene verificarlas contra la documentación oficial.*
