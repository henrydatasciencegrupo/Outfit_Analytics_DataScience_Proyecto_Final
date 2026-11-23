# Manual de usuario

**Lookwise Data Lab** · Recomendador de moda para la tienda online de H&M en Argentina

Este manual explica cómo **usar** la demo del recomendador y el dashboard, sin necesidad de conocimientos técnicos. Cómo se construyó cada pieza está en [`demo_api_streamlit.md`](demo_api_streamlit.md).

## Índice

1. [Qué es y para quién](#1-qué-es-y-para-quién)
2. [Qué se necesita](#2-qué-se-necesita)
3. [Cómo ponerla en marcha](#3-cómo-ponerla-en-marcha)
4. [Cómo usar la pantalla](#4-cómo-usar-la-pantalla)
5. [Casos para probar](#5-casos-para-probar)
6. [Cómo usar la API sola](#6-cómo-usar-la-api-sola)
7. [Cómo usar el dashboard](#7-cómo-usar-el-dashboard)
8. [Si algo falla](#8-si-algo-falla)
9. [Qué no hace la demo](#9-qué-no-hace-la-demo)
10. [Preguntas frecuentes](#10-preguntas-frecuentes)

## 1. Qué es y para quién

La demo muestra cómo funciona el recomendador: se elige un cliente y se ven las **12 prendas** que el sistema le mostraría en la tienda online, en orden de prioridad.

- **A un cliente nuevo** (sin compras previas) le muestra lo más vendido de la semana: la misma lista para todos.
- **A un cliente con historial** le arma una vitrina personalizada según lo que compró.

Sirve para personas de negocio, del equipo de H&M o de evaluación que quieran ver el sistema funcionando. Usa clientes reales anonimizados de una semana de prueba: del 16 al 22 de septiembre de 2020.

La demo tiene dos partes que trabajan juntas:

| Parte | Qué hace | Dónde se ve |
| --- | --- | --- |
| **API** | Recibe un cliente y devuelve los códigos de sus 12 prendas | En el navegador, en `http://127.0.0.1:8000/docs` |
| **Pantalla** | Pide las prendas a la API y las muestra con nombre, tipo y color | En el navegador, en `http://localhost:8501` |

## 2. Qué se necesita

- Una computadora con Windows, macOS o Linux.
- **Una de estas dos opciones:**
  - **Docker Desktop** instalado (opción más simple: un solo comando).
  - **Python 3.11 o superior** (probado con 3.13). Con Python 3.10 la instalación falla.
- Una copia del repositorio en la computadora.

No hace falta descargar los datos del proyecto: la demo trae en el repositorio todo lo que necesita.

## 3. Cómo ponerla en marcha

### Opción A: con Docker (recomendada)

Desde la carpeta del repositorio, en una terminal:

```bash
docker compose up
```

La primera vez tarda unos minutos, porque instala todo. Cuando termine, abrir **`http://localhost:8501`** en el navegador.

Para apagarla: `Ctrl+C` en la terminal.

### Opción B: con Python

**Paso 1. Crear el entorno** (solo la primera vez). Desde la carpeta del repositorio:

```bash
python -m venv .venv
```

Activarlo:

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`. Si PowerShell lo bloquea, correr antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
- macOS o Linux: `source .venv/bin/activate`

Instalar las librerías:

```bash
python -m pip install -r requirements.txt
```

**Paso 2. Prender la API.** En una terminal, con el entorno activado:

```bash
cd api
uvicorn lookwise_api:app
```

Para comprobar que funciona, abrir `http://127.0.0.1:8000/salud`: tiene que decir `{"estado":"ok","clientes":4162}`.

**Paso 3. Prender la pantalla.** En **otra** terminal, también con el entorno activado:

```bash
cd app
streamlit run app.py
```

Se abre sola en el navegador, en `http://localhost:8501`.

> **Importante:** las dos terminales tienen que quedar abiertas mientras se usa la demo. Primero se prende la API y después la pantalla.

Para apagarla: `Ctrl+C` en cada terminal.

## 4. Cómo usar la pantalla

Todo se maneja desde la **barra lateral izquierda**, de arriba hacia abajo:

1. **Tipo de cliente:** elegir *Con historial* (3.725 clientes) o *Nuevo* (437 clientes).
2. **Compras previas** (aparece solo con *Con historial*): filtra a los clientes según cuánto compraron antes.
   - *Pocas (1 a 5)*: 416 clientes.
   - *Medias (6 a 80)*: 2.374 clientes.
   - *Muchas (81 o más)*: 935 clientes.
   - *Todas*: sin filtro.
3. **Cliente:** elegir uno de la lista. Se ve el comienzo de su identificador, que es un código anonimizado.
4. **Compras previas del cliente:** cuántas compras tenía antes de la semana de prueba.
5. **Recall@12 del modelo (test):** el acierto promedio del sistema para ese tipo de cliente. **No es el acierto del cliente elegido**, sino el promedio de todos los de su tipo.

En el centro de la pantalla aparece:

- **Una etiqueta de color** que dice qué hizo el sistema: *Cliente nuevo* (lo más vendido) o *Cliente con historial* (recomendación personalizada).
- **La tabla de 12 prendas**, en orden: la fila 1 es la primera recomendación. Para cada prenda se ve el código, el nombre, el tipo (por ejemplo, Trousers o Dress), el grupo y el color.

## 5. Casos para probar

| Caso | Cómo | Qué tiene que pasar |
| --- | --- | --- |
| Cliente nuevo | *Tipo de cliente* → *Nuevo* y elegir cualquiera | La lista es la misma para todos los clientes nuevos |
| Cliente con historial | *Con historial* y elegir cualquiera | La lista es personalizada y distinta de la de un cliente nuevo |
| Pocas contra muchas compras | Comparar un cliente de *Pocas* con uno de *Muchas* | Las listas son distintas: el sistema se adapta a lo que cada uno compró |
| Consistencia | Elegir un cliente, pasar a otro y volver | Aparece la misma lista, en el mismo orden |

## 6. Cómo usar la API sola

Útil para quien quiera conectar el recomendador con otro sistema.

1. Con la API prendida, abrir **`http://127.0.0.1:8000/docs`**.
2. Hacer clic en **`GET /recomendar`** y después en **Try it out**.
3. En el campo `cliente`, pegar un identificador de cliente. Hay ejemplos en el archivo `api/datos/clientes_test.csv`.
4. Hacer clic en **Execute**.

La respuesta tiene tres datos:

```json
{
  "cliente": "00164322e9af...",
  "etapa": "con_historial",
  "prendas": [865587001, 898918002, 896169002, ...]
}
```

- `etapa`: `nuevo` o `con_historial`.
- `prendas`: los códigos de las 12 prendas, en orden. La API devuelve solo códigos: los nombres y colores los agrega la pantalla.

## 7. Cómo usar el dashboard

El dashboard de Power BI está en la carpeta [`dashboard/`](../dashboard/). Se abre con Power BI Desktop (gratuito, para Windows) y tiene una pestaña por tema, en la barra superior:

| Pestaña | Qué muestra | Qué se puede filtrar |
| --- | --- | --- |
| Portada | Presentación del proyecto | — |
| Resumen | Compras, clientes y artículos de la muestra; compras por mes y por sección | Rango de fechas y de edad |
| Ventas en el tiempo | Compras por mes de 2018 a 2020 | — |
| Categorías | Compras por sección y los 10 tipos de producto más comprados | — |
| Clientes nuevos | Cuántos clientes llegan sin historial y por qué lo más vendido acierta poco | — |
| Resultados modelos | Aciertos de cada modelo, para clientes con historial y nuevos | — |
| Simulación | Desde cuántas compras conviene personalizar | — |
| Recomendaciones | Qué recomendamos a H&M | — |
| Piloto A/B | Aciertos del modelo contra lo más vendido, por sección de la tienda | — |
| Costos y ROI | Inversión, mes de recupero y ganancia acumulada | Escenario (base, optimista, pesimista) e incluir o no el costo de la tienda online |

Al pasar el mouse sobre un gráfico se ven los valores exactos.

## 8. Si algo falla

| Lo que se ve | Por qué pasa | Qué hacer |
| --- | --- | --- |
| Cuadro rojo: *"No se pudo conectar con la API. ¿Está encendida?"* | La API está apagada o se cerró su terminal | Prender la API (paso 2 de la opción B) y recargar la pantalla |
| Cuadro rojo: *"Cliente no encontrado."* | El cliente no está en la semana de prueba | Elegir un cliente de la lista |
| Cuadro rojo: *"Error de la API (código 500)."* | Falla dentro de la API | Mirar la terminal de la API: el detalle está en la última línea del mensaje |
| La API no arranca y dice `[Errno 10048]` o *address already in use* | Ya hay otra API prendida en el puerto 8000 | Cerrar la terminal de la API anterior y volver a arrancar |
| La pantalla abre otra aplicación | El puerto 8501 está ocupado | Arrancar la pantalla con `streamlit run app.py --server.port 8502` y abrir `http://localhost:8502` |
| La instalación termina con *Requires-Python >=3.11* | La versión de Python es anterior a 3.11 | Instalar Python 3.11 o superior |
| Las listas no coinciden con las del proyecto | La versión de scikit-learn no es la correcta | Instalar las librerías con el `requirements.txt` del repositorio, que fija `scikit-learn==1.9.1` |
| La pantalla se ve con otra tipografía | No hay conexión a internet (las tipografías se cargan desde la web) | No afecta el funcionamiento |

## 9. Qué no hace la demo

- **No es la tienda de H&M** ni un sistema en producción: es un prototipo que corre en una computadora.
- **Solo conoce a los clientes de la semana de prueba** (16 al 22 de septiembre de 2020). No se pueden agregar clientes nuevos ni consultar otras fechas.
- **Los clientes nuevos ven siempre la misma lista:** sin compras previas no hay información para personalizar.
- **No muestra fotos** de las prendas, por derechos de imagen.
- **No tiene usuario ni contraseña:** no debe publicarse en internet tal como está.
- Los datos son de otro mercado y de 2018 a 2020: las prendas recomendadas sirven para ver cómo funciona el sistema, no como recomendaciones actuales para Argentina.

## 10. Preguntas frecuentes

**¿Por qué un cliente nuevo ve siempre las mismas 12 prendas?**
Porque el sistema no sabe nada de él. Le muestra lo más vendido de la semana hasta su primera compra; desde ahí, personaliza.

**¿Qué significa un Recall@12 de 7,53%?**
Que, en promedio, el 7,53% de las prendas que compraron los clientes con historial estaban entre sus 12 recomendadas. Mostrando lo más vendido, ese número es 2,78%: el sistema acierta unas 2,7 veces más.

**¿Por qué aparece la misma prenda en dos colores?**
Porque cada color es un artículo distinto en el catálogo de H&M.

**¿Las recomendaciones cambian si vuelvo a elegir al mismo cliente?**
No. Para el mismo cliente, el sistema devuelve siempre la misma lista y en el mismo orden.

**¿Dónde veo los resultados completos?**
En el [resumen ejecutivo](resumen_ejecutivo.pdf), en el dashboard y, con más detalle técnico, en [`modelado.md`](modelado.md).

**¿A quién consulto?**
Al equipo de Lookwise Data Lab: integrantes y contactos en el [`README.md`](../README.md#equipo).
