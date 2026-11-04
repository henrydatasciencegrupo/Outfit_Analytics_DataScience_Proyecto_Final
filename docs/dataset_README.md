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
