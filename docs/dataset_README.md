# Datos

**Este repositorio no incluye los datos.** Pertenecen a H&M Group y se publicaron para la competencia de Kaggle [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations), bajo las reglas de esa competencia (uso no comercial y de investigación académica). Para usarlos hay que aceptar esas reglas en Kaggle y descargarlos desde ahí.

## Archivos originales

- `transactions_train.csv`: 31.788.324 compras (cliente, artículo, fecha, precio, canal).
- `customers.csv`: 1.371.980 clientes.
- `articles.csv`: 105.542 artículos.

## Muestra que usa el proyecto (p10)

Para trabajar en computadoras comunes se usa una muestra del 10% de los clientes, solo del canal online. El método está documentado y se puede reproducir con `notebooks/muestreo_p10_documentado.ipynb`:

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
