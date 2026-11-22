# Demo Lookwise Data Lab — API de recomendación + pantalla (Streamlit)

Este documento explica **qué se construyó, cómo se usa, por qué se tomó cada decisión y qué se descartó**, e incluye el código importante. Todas las afirmaciones sobre números se han verificado con los archivos del proyecto.

## Índice

1. [Qué es y qué problema resuelve](#1-qué-es-y-qué-problema-resuelve)
2. [Arquitectura: cómo viaja un pedido](#2-arquitectura-cómo-viaja-un-pedido)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [Entorno y requisitos](#4-entorno-y-requisitos)
5. [Puesta en marcha](#5-puesta-en-marcha)
6. [La API en detalle](#6-la-api-en-detalle)
7. [La pantalla en detalle](#7-la-pantalla-en-detalle)
8. [Decisiones de diseño y alternativas descartadas](#8-decisiones-de-diseño-y-alternativas-descartadas)
9. [Pruebas y verificación](#9-pruebas-y-verificación)
10. [Casos de uso para recorrer la demo](#10-casos-de-uso-para-recorrer-la-demo)
11. [Errores que aparecieron y cómo se resolvieron](#11-errores-que-aparecieron-y-cómo-se-resolvieron)
12. [Limitaciones](#12-limitaciones)
13. [Mejoras a futuro](#13-mejoras-a-futuro)
14. [Glosario](#14-glosario)

---

## 1. Qué es y qué problema resuelve

**El problema.** Una tienda online de moda tiene miles de prendas y muchos clientes. Para un cliente que ya compró se puede aprender de su historial; para uno **nuevo** (sin compras) no hay historial: es el problema de *arranque en frío*. El modelo final del proyecto lo resuelve con un **sistema por etapas**:

| Etapa             | Cuándo                             | Qué recomienda                                                                                                                             |
| ----------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `nuevo`         | El cliente no tiene compras previas | Las 12 prendas más vendidas recientemente (baseline con decaimiento, vida media de 3 días). La misma lista para todos los clientes nuevos |
| `con_historial` | El cliente ya compró               | Un **ranker** (Gradient Boosting) puntúa unas 90 prendas candidatas del cliente y se quedan las 12 de mayor puntaje                  |

**La demo.** Es un prototipo que muestra cómo se comporta ese modelo: se elige un cliente de la semana de test (16 al 22/09/2020) y se ven las 12 prendas que el sistema le recomendaría, con nombre, tipo, grupo y color. **No es la página de H&M ni un sistema en producción**: las variables de cada prenda candidata están calculadas de antemano para esa semana.

**Qué demuestra frente a la rúbrica:** una demo estable y clara (API y aplicación) que genera recomendaciones de forma consistente, con casos comunes (cliente nuevo, con pocas y con muchas compras) y documentación de uso.

---

## 2. Arquitectura: cómo viaja un pedido

```
 [ Persona ]  →  [ Pantalla (Streamlit, :8502) ]  →  [ API (FastAPI + uvicorn, :8000) ]  →  [ Modelo + datos ]
   elige un          arma el pedido y muestra            decide la etapa y devuelve             ranker, candidatas,
   cliente           nombre, tipo y color                12 códigos de prenda                   baseline (archivos)
```

Paso a paso, cuando se elige un cliente:

1. La **pantalla** envía `GET http://127.0.0.1:8000/recomendar?cliente=<id>`.
2. La **API** verifica que el cliente exista (si no, responde 404). Mira si es nuevo o con historial y calcula la lista.
3. La API responde un JSON con **solo códigos**: `{cliente, etapa, prendas: [12 ids]}`.
4. La **pantalla** cruza esos 12 códigos con el catálogo reducido y los muestra, **respetando el orden del ranking**.

**Por qué dos piezas separadas.** La API es el camino por el que la pantalla le hace un pedido al modelo y recibe la respuesta. Mientras se mantenga el formato del pedido y de la respuesta (el *contrato*), se puede cambiar el modelo o los datos por dentro sin tocar la pantalla, y la pantalla se puede reemplazar (otra web, otra app) sin tocar el modelo. Además, el grupo confirmó que API y Streamlit son piezas distintas. Quien lee la respuesta cruda ve solo números: dar nombres y colores es trabajo de la pantalla.

| Pieza    | Responsabilidad                                             | Tecnología                                                                        |
| -------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| API      | Recibir un cliente y devolver 12 códigos. Decidir la etapa | FastAPI (define los *endpoints*) + uvicorn (el servidor que los pone a escuchar) |
| Pantalla | Pedir, mostrar, explicar                                    | Streamlit + `requests` + pandas                                                  |

---

## 3. Estructura de carpetas

Estructura de carpetas en el repositorio del grupo:

```
(repositorio)/
├── api/
│   ├── lookwise_api.py                  # la API
│   ├── test_lookwise_api.py             # 7 tests automáticos
│   ├── requirements.txt
│   └── datos/
│       ├── clientes_test.csv        # 4.162 clientes: customer_id, es_nuevo, n_compras_previas
│       └── candidatas_test.parquet  # 370.882 filas: cliente × prenda candidata × 17 variables
├── app/
│   ├── app.py                       # la pantalla
│   ├── requirements.txt
│   ├── .streamlit/
│   │   └── config.toml              # tema: colores y tipografías
│   └── datos/
│       ├── clientes_test.csv        # copia (para filtrar y mostrar compras previas)
│       ├── prendas_min.parquet      # catálogo reducido (15.029 prendas × 5 columnas)
│       └── configuracion_modelo.json  # copia (para mostrar el Recall@12)
└── models/                          # ya existía en el repositorio; es del grupo
    ├── ranker_clasificador.joblib   # modelo entrenado
    └── configuracion_modelo.json    # fecha de corte, hiperparámetros, baseline top 12, Recall@12
```

**Por qué esta estructura.**

- **`api/` y `models/` quedan lado a lado.** La API lee el modelo y la configuración de `../models/`, que son los oficiales del grupo, en lugar de tener una copia propia. Antes la API traía su copia: era idéntica byte a byte a la oficial, y al comparar las respuestas de los 4.162 clientes con una y con otra hubo 0 diferencias, así que el cambio no altera ninguna lista. La ventaja es una sola fuente de verdad; el costo, que `api/` ya no funciona suelta: tiene que estar junto a `models/` (ver la advertencia de la sección 6.2).
- **La pantalla se llama `app.py`** para coincidir con la instrucción `streamlit run app/app.py` que ya tenía el README de `app/`.
- **`prendas_min.parquet` está solo en `app/datos/`:** la API nunca lo lee, solo la pantalla (por eso se lo dejó afuera de `api/datos/`).
- **Por qué hay copias de datos en `app/datos/`.** Streamlit solo lee lo que está en su propia carpeta; copiar mantiene las dos carpetas independientes. El costo: si cambian los datos, hay que **actualizar las copias**. (Mejora posible: que la pantalla lea `configuracion_modelo.json` de `../models/`, como la API.)
- **Los archivos `.parquet` necesitan una excepción en `.gitignore`.** El `.gitignore` del repositorio ignora `*.parquet` (también `/dataset/`, `/p10_modelado/` y `*.zip`). Sin excepción, `candidatas_test.parquet` y `prendas_min.parquet` no se subirían y la API no arrancaría en otra computadora. La excepción, al final del `.gitignore` y después de `*.parquet`, es solo para esas dos carpetas: `!api/datos/*.parquet` y `!app/datos/*.parquet`. Se probó en un repositorio de prueba: esos archivos se suben y cualquier otro `.parquet` (por ejemplo, de `dataset/`) sigue ignorado. Suman unos 3 MB a un repositorio de ~10 MB.

Durante el desarrollo, las carpetas de trabajo se llamaban `api/` (con su propia copia del modelo en `modelo/`) y `app/`; la estructura de arriba es la de entrega.

---

---

## 4. Entorno y requisitos

**Entorno usado:** conda, entorno `api_hm`, **Python 3.13**; scikit-learn **1.9.1**; pandas 3.1.1 (el de este entorno); Streamlit 1.67.0.

**Versión de Python: 3.11 o superior (probado con 3.13).** Con Python 3.10 la instalación falla: `pip install -r requirements.txt` termina con `ERROR: ... fastapi==0.163.1 Requires-Python >=3.11`. Se comprobó el 20/11/2026 en una segunda computadora con Windows que tenía solo Python 3.10. Se instaló Python 3.13.17 (con el *Python install manager*: `py install 3.13`, que puede convivir con el 3.10) y, en un entorno virtual limpio (`py -3.13 -m venv .venv`), pasaron los 7 tests, la API devolvió para el cliente de referencia las mismas 12 prendas en el mismo orden y la pantalla funcionó con "Con historial" y "Nuevo". El mínimo de 3.11 está verificado para `fastapi`; para el resto de las librerías fijadas (pandas, scikit-learn, pyarrow, streamlit) no se probó con 3.11 ni con 3.12.

**Por qué un entorno fijo (lo que más tiempo llevó).** El modelo se guardó con scikit-learn 1.9.1. Cargarlo con otra versión no siempre da error, pero **puede cambiar las listas**: con la versión 1.7.2 el solapamiento de las 12 prendas fue de ~88 % frente a la 1.9.1. Para una demo que debe ser consistente, la versión no es un detalle. La solución es un entorno dedicado (y, a futuro, Docker).

**Librerías.** `api/requirements.txt` contiene:

```
fastapi==0.163.1
uvicorn==0.54.0
httpx==0.28.1
pytest==9.2.0
pandas==3.1.1
pyarrow==26.0.1
joblib==1.6.0
scikit-learn==1.9.1
```

- **Todas las versiones están fijadas** (19/11/2026), tomadas del entorno `api_hm` donde se probó (`pip show`). La que más importa es `scikit-learn==1.9.1`, porque con otra versión las listas pueden cambiar. Antes de esa fecha, solo `scikit-learn` estaba fijada.
- `httpx` y `pytest` son para los tests.
- **La pantalla tiene su propio `app/requirements.txt`**, con las versiones exactas del entorno donde se probó:

```
streamlit==1.67.0
requests==2.34.2
pandas==3.1.1
pyarrow==26.0.1
```

  Se mantienen **separados** del `requirements.txt` general del repositorio (pensado para análisis y modelado, con versiones mínimas como `scikit-learn>=1.4`): la API exige `scikit-learn==1.9.1` exacta y mezclar los archivos afectaría los notebooks del resto del grupo. Instalación en un entorno nuevo: `python -m pip install -r requirements.txt` dentro de cada carpeta (`api` y `app`).

**Windows con PowerShell:** si `.venv\Scripts\activate` falla con "la ejecución de scripts está deshabilitada", correr antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (vale solo para esa ventana; hay que repetirlo en cada terminal nueva), o usar `cmd`.

**Internet.** Las tipografías (Cormorant Garamond y DM Sans) se cargan desde Google Fonts: sin conexión la demo funciona igual, con una tipografía genérica.

---

## 5. Puesta en marcha

Hacen falta **dos terminales abiertas a la vez**. En Windows con el entorno `api_hm`, la forma más segura es usar la ruta completa de Python (evita abrir otro entorno por error):

**Terminal 1 — API** (desde la carpeta `api`):

```powershell
& "C:\Users\flore\anaconda3\envs\api_hm\python.exe" -m uvicorn lookwise_api:app
```

`lookwise_api:app` significa "el objeto `app` del archivo `lookwise_api.py`". Con `--reload` el servidor se reinicia solo al guardar cambios (útil mientras se desarrolla). Comprobación: abrir `http://127.0.0.1:8000/salud`; debe responder `{"estado":"ok","clientes":4162}`.

**Terminal 2 — pantalla** (desde la carpeta `app`):

```powershell
& "C:\Users\flore\anaconda3\envs\api_hm\python.exe" -m streamlit run app.py --server.port 8502
```

Se abre en `http://localhost:8502`. Se usa el 8502 porque el puerto predeterminado (8501) estaba ocupado por otra aplicación.

**Para apagar:** `Ctrl+C` en cada terminal. **Orden:** primero la API y después la pantalla (si la API está apagada, la pantalla lo avisa, ver sección 7.3).

**Si la API dice `[Errno 10048] ... solo se permite un uso de cada dirección de socket`:** el puerto 8000 ya está ocupado, casi siempre por una API anterior que quedó prendida. Hay que cerrar esa terminal (o el proceso) y volver a arrancar; si no, la pantalla le hablaría a la API vieja sin avisar.

> En cualquier otro equipo, reemplazar la ruta por el `python` del entorno donde estén instaladas las librerías.

---

## 6. La API en detalle

### 6.1 El contrato

| Endpoint            | Para qué                                                                                                     | Parámetro                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `GET /salud`      | Confirma que la API está encendida (no verifica que las recomendaciones sean buenas: eso lo hacen los tests) | ninguno                        |
| `GET /recomendar` | Devuelve 12 prendas para un cliente                                                                           | `cliente=<id>` (obligatorio) |
| `GET /docs`       | Documentación interactiva (Swagger), generada sola por FastAPI                                               | —                             |

Un **endpoint** es cada dirección de la API que atiende un tipo de pedido; el **parámetro** es el dato que viaja con el pedido (acá, para quién se pide).

**Respuesta de `/recomendar`** (ejemplo real: un cliente con historial, 44 compras previas; los códigos están en orden de ranking):

```json
{
  "cliente": "00164322e9af7460e84207c8d172912a2c13da209bb0eab92f74545ba217d885",
  "etapa": "con_historial",
  "prendas": [865587001, 898918002, 896169002, 857163001, 874619001, 896152002,
              918836001, 863595006, 781613006, 920610005, 904545002, 909911001]
}
```

**Códigos de estado:**

| Código | Cuándo                                                  | Quién "falló"                                     |
| ------- | -------------------------------------------------------- | --------------------------------------------------- |
| 200     | Todo bien                                                | —                                                  |
| 404     | El cliente no existe en la lista                         | El pedido (dato inexistente)                        |
| 422     | Falta el parámetro `cliente` (lo valida FastAPI solo) | El pedido (mal armado)                              |
| 500     | Error dentro del código de la API                       | El código; la traza sale en la terminal de uvicorn |

**Cliente nuevo vs. desconocido:** un cliente *nuevo* está en la lista pero sin compras previas → recibe el baseline (200). Uno *desconocido* no está en la lista → 404. Son casos distintos de negocio y la API los distingue.

### 6.2 El código importante (`lookwise_api.py`)

**Carga única al arrancar.** El modelo y los datos se cargan **una sola vez**, al principio del archivo, no dentro de la función. Cada pedido responde en ≈1,5 ms porque no recarga nada.

```python
AQUI = Path(__file__).resolve().parent
MODELOS = AQUI.parent / "models"  # el modelo oficial: api/ y models/ quedan lado a lado en el repo
app = FastAPI()

# Se cargan UNA sola vez, al arrancar
modelo = joblib.load(MODELOS / "ranker_clasificador.joblib")
with open(MODELOS / "configuracion_modelo.json", encoding="utf-8") as f:
    config = json.load(f)
clientes = pd.read_csv(AQUI / "datos/clientes_test.csv").set_index("customer_id")
candidatas = pd.read_parquet(AQUI / "datos/candidatas_test.parquet").set_index("customer_id").sort_index()
baseline = [int(x) for x in config["baseline_optimizado"]["top12"]]
```

`Path(__file__).resolve().parent` hace que las rutas funcionen **sin importar desde qué carpeta se lance** el programa; `MODELOS` apunta a la carpeta `models/` del repositorio, hermana de `api/`. El archivo de configuración se abre con `with` para que se cierre solo. Los índices por `customer_id` (y `sort_index()` en candidatas) hacen rápida la búsqueda de un cliente.

**Las 17 variables del ranker**, en el **mismo orden con que se entrenó** el modelo (el orden importa: debe coincidir con el del entrenamiento; con otro orden el modelo recibiría cada variable en el lugar equivocado o rechazaría el pedido):

```python
COLUMNAS = ["rank_pop", "rank_edad", "rank_cocompra", "puntaje_cocompra", "ya_lo_compro",
            "ventas_7d", "ventas_30d", "tendencia", "dias_desde_primera_venta", "precio_articulo",
            "ventas_tramo_7d", "afinidad_grupo", "age", "edad_faltante", "n_compras",
            "dias_desde_ultima", "compras_por_dia_activo"]
```

- **De la prenda:** `ventas_7d`, `ventas_30d`, `tendencia`, `precio_articulo`, `dias_desde_primera_venta`, `ventas_tramo_7d`.
- **Del cruce cliente–prenda:** `rank_pop`, `rank_edad`, `rank_cocompra`, `puntaje_cocompra`, `ya_lo_compro`, `afinidad_grupo`.
- **Del cliente:** `age`, `edad_faltante`, `n_compras`, `dias_desde_ultima`, `compras_por_dia_activo`.

**Advertencia: si se reentrena el modelo de `models/`.** El ranker se entrenó con esas 17 variables en ese orden. Como la API ahora lee el modelo de `models/`, que es del grupo, alguien podría reemplazarlo:

| Qué cambia en el modelo                                          | Qué pasa                                                                                                                                                                        |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Se reentrena con las **mismas 17 variables, mismo orden**   | La API lo toma sola y sigue funcionando                                                                                                                                          |
| Cambian los nombres o el orden de las variables                   | El modelo se niega a puntuar: scikit-learn compara los nombres de las columnas con los del entrenamiento y la API responde 500 (ver el `ValueError` en la terminal de uvicorn) |
| Cambian las variables y también hay que regenerar las candidatas | Hay que actualizar `COLUMNAS` y rehacer `candidatas_test.parquet` con las variables nuevas                                                                                   |

El test `test_variables_del_modelo` compara `modelo.feature_names_in_` con `COLUMNAS` y falla apenas el modelo de `models/` deja de coincidir, antes de que nadie abra la pantalla. (Se comprobó cambiando a propósito el orden de dos columnas: el modelo rechaza los pedidos con un `ValueError`.)

**La función principal:**

```python
def recomendar(cliente):
    if cliente not in clientes.index:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if bool(clientes.at[cliente, "es_nuevo"]):
        return {"cliente": cliente, "etapa": "nuevo", "prendas": baseline}
    t = candidatas.loc[[cliente]]
    prob = modelo.predict_proba(t[COLUMNAS])[:, 1]
    orden = pd.Series(prob, index=t["article_id"].values).sort_values(ascending=False, kind="stable")
    prendas = [int(a) for a in orden.index[:12]]
    return {"cliente": cliente, "etapa": "con_historial", "prendas": prendas}
```

Las decisiones escondidas en esas líneas:

- **El 404 va antes de buscar al cliente** (*cláusula de guarda*: validar primero, procesar después). Si la verificación estuviera después de `clientes.at[...]`, el `KeyError` saltaría primero y el chequeo nunca se ejecutaría: el usuario vería un 500 (error del código) en lugar de un 404 (cliente inexistente).
- **`candidatas.loc[[cliente]]`** (doble corchete) devuelve siempre una tabla, de ~90 filas, una por prenda candidata. Con un solo corchete, si un cliente tuviera una única fila, pandas devolvería una Serie en lugar de una tabla.
- **`predict_proba(...)[:, 1]`** da el puntaje de la clase "compra". **Es un puntaje para ordenar, no una probabilidad real**: el modelo se entrenó con `class_weight: balanced`, que distorsiona la escala. Por eso en la documentación se dice *puntaje*.
- **`ascending=False`**: los puntajes más altos arriba. **`kind="stable"`**: si dos prendas empatan, siempre se mantiene el mismo orden entre ellas, para que el mismo pedido dé siempre la misma respuesta.
- **`orden.index[:12]`**: las 12 primeras. Los ids se convierten a `int` para que el JSON lleve enteros simples de Python y no tipos numéricos de NumPy.

**Los endpoints:**

```python
@app.get("/recomendar")
def endpoint_recomendar(cliente: str):
    return recomendar(cliente)

@app.get("/salud")
def salud():
    return {"estado": "ok", "clientes": int(len(clientes))}
```

`@app.get("/salud")` **registra** el endpoint: le dice a la API qué función responde a un GET en esa dirección. No es una autorización (la API no tiene login). Se separó la lógica (`recomendar`) del endpoint para poder reutilizarla o probarla por separado.

### 6.3 Cómo se arma la lista de un cliente con historial

1. **Candidatas.** Para cada cliente, `candidatas_test.parquet` guarda entre **54 y 118 prendas candidatas (promedio 93)** para los 3.725 clientes con historial. El archivo tiene 370.882 filas en total porque incluye también a los 437 clientes nuevos, que la API no usa: reciben el baseline. Provienen de **tres generadores**, según el código oficial del repositorio (`src/modelos.py`, clase `RankerSupervisado`, con `n_candidatos=40` y `dias_pares=28`): popularidad reciente (7 días), popularidad por tramo de edad (7 días) y co-compra con recompra. **Cada generador aporta sus 40 mejores prendas y las tres listas se unen**, por eso hay entre 54 y 118 candidatas por cliente y no 40 (`rank_pop`, `rank_edad` y `rank_cocompra` guardan la posición en cada lista; vale 41 si la prenda no figuraba en esa lista). *(Nota: `docs/modelado.md` dice que el ranker "ve ~40 candidatas"; 40 es el tamaño de cada lista, no del total.)*

   **El archivo lo genera el script `exportar_candidatas_api.py` ** (carpeta `src/` del repositorio), que reproduce los siguientes pasos: muestra p10 tratada (solo canal online, duplicados conservados, sin colapsar), corte el 16/09/2020 y variables calculadas solo con compras anteriores. Escribe `candidatas_test.parquet` y `clientes_test.csv` con el orden de filas del modelo oficial, que importa para los empates de puntaje (en el archivo hay clientes con empates exactos entre sus 13 primeras prendas: desempata el orden de las filas). Al final verifica contra `models/recomendaciones_semana_test.csv`. Se corre desde la raíz del repositorio y necesita la muestra p10 (`transactions.parquet`, `customers.parquet`, `articles.parquet`, que no se versiona):

   ```
   python src/exportar_candidatas_api.py --base dataset/p10 --salida api/datos
   ```
2. **Puntaje.** El modelo (`HistGradientBoostingClassifier`; `learning_rate` 0,05, `max_leaf_nodes` 15, `max_iter` 200, `l2_regularization` 1,0, `class_weight: balanced`) puntúa cada par cliente–prenda con las 17 variables.
3. **Ranking.** Se ordenan de mayor a menor puntaje y se devuelven las 12 primeras.

**Cliente nuevo:** se devuelve el `top12` guardado en `configuracion_modelo.json` (*baseline con decaimiento, vida media 3 días*): las prendas más vendidas recientemente, ponderando más las ventas de los últimos días. Es una **lista fija**, igual para todos los clientes nuevos.

**Métrica de referencia (Recall@12 en la semana de test):**

| Grupo              | Recall@12 |
| ------------------ | --------- |
| Todos los clientes | 6,95 %    |
| Con historial      | 7,53 %    |
| Nuevos             | 2,04 %    |

*Recall@12:* para cada cliente, de las prendas **distintas** que compró en la semana de test, qué fracción estaba entre las 12 recomendadas; después se promedia entre clientes. Esta definición se verificó el 19/11/2026: aplicada a `models/recomendaciones_semana_test.csv` del repositorio y a las respuestas reales del test (`test_verdad.parquet`) reproduce exactamente los tres valores de la tabla (6,95 %, 7,53 % y 2,04 %). Que el valor de los nuevos sea mucho menor es esperable: sin historial no se puede personalizar. Es justamente el argumento del sistema por etapas.

### 6.4 Consistencia con las recomendaciones oficiales del repositorio

El repositorio guarda las recomendaciones oficiales de la semana de test en `models/recomendaciones_semana_test.csv` (12 prendas por cliente, 4.162 clientes). Con las candidatas generadas por el script oficial, la API las reproduce **exactamente**:

| Comparación                                                           | Resultado                                                                       |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Script `exportar_candidatas_api.py` (verificación propia del script) | **4.162 de 4.162** clientes con las mismas 12 prendas y en el mismo orden |
| La API (`recomendar`) contra el CSV oficial, todos los clientes       | **4.162 de 4.162**                                                        |
| La API contra el CSV oficial, solo clientes con historial               | **3.725 de 3.725**                                                        |
| Los 7 tests de la API con los datos nuevos                              | 7 passed                                                                        |

Como la API devuelve las mismas listas que el CSV oficial, el Recall@12 que se muestra en la pantalla (7,53 % con historial, 2,04 % nuevos, 6,95 % todos) es el de las recomendaciones que la API sirve, y se puede afirmar que **la API muestra exactamente los resultados del modelo oficial**.

**Cómo se llegó a esto (historial).** La primera versión de `candidatas_test.parquet` se había armado en una sesión de trabajo, sin documentar sus parámetros. Con ese archivo la API rendía casi igual (Recall@12 con historial 7,61 % contra 7,53 % oficial) pero no coincidía: las 12 prendas eran las mismas en 2.400 de los 3.725 clientes con historial (64 %), el solapamiento medio era de 11,6 de 12, y para 319 clientes la lista oficial incluía prendas que no estaban entre las candidatas. Dado que el modelo oficial se generó con los duplicados conservados, se pensó que la causa pudiera ser la utilizacion de duplicados colapsados; **esa causa no se comprobó**, pero con el script oficial las diferencias desaparecieron. El modelo y la configuración eran los mismos todo el tiempo (idénticos byte a byte a los de `models/`), así que la diferencia estaba en las candidatas.

El formato del archivo nuevo es igual al anterior (mismas 19 columnas y tipos; `clientes_test.csv` idéntico), de modo que `lookwise_api.py` no necesitó cambios. El archivo pasó de 371.510 a 370.882 filas.

---

## 7. La pantalla en detalle

### 7.1 Qué ve quien usa la demo

Barra lateral, de arriba hacia abajo:

1. **Tipo de cliente:** *Con historial* (3.725 clientes) o *Nuevo* (437).
2. **Compras previas** (solo con historial): *Todas*, *Pocas (1 a 5)* → 416 clientes, *Medias (6 a 80)* → 2.374, *Muchas (81 o más)* → 935.
3. **Cliente:** el comienzo del identificador (los ids completos tienen 64 caracteres).
4. **Compras previas del cliente:** cantidad de compras anteriores.
5. **Recall@12 del modelo (test):** 7,53 % con historial, 2,04 % nuevos, con una aclaración: es el promedio del tipo de cliente, **no el acierto de ese cliente en particular**.

En el centro: una **etiqueta** con la etapa que aplicó el sistema (rosa con texto oscuro), un título descriptivo y la tabla de 12 prendas **en orden de ranking** (la fila 1 es la primera recomendación), con código, prenda, tipo, grupo y color.

### 7.2 El código importante (`app.py`)

**Cargas con caché.** Streamlit **vuelve a ejecutar todo el archivo en cada interacción**. `@st.cache_data` hace que clientes, catálogo y métricas se lean del disco una sola vez.

```python
@st.cache_data
def cargar_clientes():
    return pd.read_csv(AQUI / "datos/clientes_test.csv")

@st.cache_data
def cargar_prendas():
    return pd.read_parquet(AQUI / "datos/prendas_min.parquet").set_index("article_id")

@st.cache_data
def cargar_metricas():
    with open(AQUI / "datos/configuracion_modelo.json", encoding="utf-8") as f:
        return json.load(f)["metricas_test_recall_at_12"]
```

**Los niveles de compras previas** salen de la distribución real de los 3.725 clientes con historial (mínimo 1; percentil 10 = 5; mediana = 35; percentil 75 = 81; máximo 987), no de cortes arbitrarios:

```python
RANGOS = {
    "Todas": (1, 10**9),
    "Pocas (1 a 5)": (1, 5),
    "Medias (6 a 80)": (6, 80),
    "Muchas (81 o más)": (81, 10**9),
}
```

**El filtro** (el selector de compras solo aparece para "Con historial", porque todos los clientes nuevos tienen 0 compras y filtrar no tendría sentido):

```python
tipo = st.sidebar.radio("Tipo de cliente", ["Con historial", "Nuevo"])
filtro = clientes[clientes["es_nuevo"] == (tipo == "Nuevo")]

if tipo == "Con historial":
    nivel = st.sidebar.radio("Compras previas", list(RANGOS))
    minimo, maximo = RANGOS[nivel]
    filtro = filtro[filtro["n_compras_previas"].between(minimo, maximo)]
```

### 7.3 El pedido a la API y el manejo de errores

```python
API = "http://127.0.0.1:8000"

def pedir_recomendacion(cliente):
    try:
        r = requests.get(f"{API}/recomendar", params={"cliente": cliente}, timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar con la API. ¿Está encendida?"
    if r.status_code == 404:
        return None, "Cliente no encontrado."
    if r.status_code != 200:
        return None, f"Error de la API (código {r.status_code})."
    return r.json(), None
```

La función devuelve siempre un par `(datos, error)`: o hay datos o hay un mensaje. Así la pantalla **nunca muestra una traza técnica**: con la API apagada, aparece un cuadro rojo con "No se pudo conectar con la API. ¿Está encendida?". El `timeout=10` evita que la pantalla se quede esperando para siempre.

**La dirección de la API es configurable:**

```python
API = os.environ.get("LOOKWISE_API_URL", "http://127.0.0.1:8000")
```

Sin la variable de entorno `LOOKWISE_API_URL`, la pantalla usa la API local de siempre. La variable existe para poder correr cada pieza en un contenedor distinto (por ejemplo con Docker, donde la API no está en `127.0.0.1` sino en otro nombre, como `http://api:8000`). Se probó con la API en otro puerto (funciona) y con una dirección sin API (aparece el mensaje rojo). Si nadie usa Docker, simplemente no se usa y no cambia nada.

### 7.4 Del código de prenda a la tabla (la línea clave: `reindex`)

```python
tabla = prendas.reindex(datos["prendas"]).reset_index()
tabla.index = tabla.index + 1          # la posición empieza en 1, no en 0
tabla = tabla.rename(columns={
    "article_id": "Código",
    "prod_name": "Prenda",
    "product_type_name": "Tipo",
    "product_group_name": "Grupo",
    "colour_group_name": "Color",
})
st.dataframe(tabla, height=(len(tabla) + 1) * 35 + 3)
```

- **`reindex` y no `isin`.** La API devuelve los 12 códigos **en orden de ranking**; ese orden es el producto. `reindex(lista)` arma la tabla con las filas **exactamente en el orden de la lista**. `prendas[prendas.index.isin(lista)]` filtraría las mismas 12 prendas, pero en el **orden del catálogo**, y se perdería el ranking.
- **Riesgo de `reindex`:** si un código de la lista no está en el catálogo, **no da error**: crea una fila con celdas vacías (NaN). Hoy no ocurre: se verificó que las 15.029 prendas candidatas y las 12 del baseline están **todas** en `prendas_min.parquet` (faltan 0). Por eso `prendas_min` **debe regenerarse junto con las candidatas**.
- **`height=(len(tabla) + 1) * 35 + 3`:** cada fila mide ≈35 px (más el encabezado). Se calcula con `len(tabla)` en lugar de fijar un número, para que se vean las 12 filas sin scroll interno y se ajuste solo si la API devolviera otra cantidad.

### 7.5 La métrica en pantalla (y un detalle que dio error)

```python
clave = "Nuevos" if tipo == "Nuevo" else "Con historial"
recall = f"{metricas[clave] * 100:.2f}".replace(".", ",")
st.sidebar.metric("Recall@12 del modelo (test)", f"{recall} %")
```

El selector dice `Nuevo` (singular) y la clave del archivo JSON es `Nuevos` (plural): al usar el valor del selector como clave directamente, apareció `KeyError: 'Nuevo'`. La línea `clave = ...` traduce uno al otro. (`.replace(".", ",")` muestra el decimal con coma, como se escribe en español.)


## 8. Decisiones de diseño y alternativas descartadas

### 8.1 API

| #   | Decisión                                                                                | Por qué                                                                                                                                         | Alternativa descartada                                                      |
| --- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| A1  | Hacer una API (FastAPI + uvicorn) separada de la pantalla                                | API y Streamlit son piezas distintas; la rúbrica pide una demo estable (API o aplicación) y el profe habló de un modelo desplegado en una API | Solo un CSV precalculado: cumple en el papel, pero no hace inferencia real  |
| A2  | Contrato fijo: `GET /recomendar?cliente=<id>` → `{cliente, etapa, prendas}`         | Pantalla y API pueden avanzar y cambiar por separado                                                                                             | Que la API devuelva también nombres y colores: mezcla responsabilidades    |
| A3  | La etapa la decide el **sistema** según `es_nuevo`                              | En la tienda real el cliente no elige cuántas compras tiene                                                                                     | Un deslizador "compras que conoce el sistema" (maqueta inicial)             |
| A4  | Cliente nuevo → baseline; con historial → ranker                                       | Es el sistema por etapas del modelo final (notebook 06)                                                                                          | Un único modelo para todos                                                 |
| A5  | Decir "puntaje", no "probabilidad"                                                       | `class_weight: balanced` hace que el número sirva para ordenar, no como probabilidad                                                          | —                                                                          |
| A6  | Cargar modelo y datos una sola vez                                                       | ≈1,5 ms por pedido                                                                                                                              | Cargar dentro de la función                                                |
| A7  | Orden estable en empates (`kind="stable"`)                                             | Mismo pedido → misma respuesta                                                                                                                  | Orden por defecto                                                           |
| A8  | Guarda del 404 antes de leer al cliente                                                  | Evita el `KeyError` → 500                                                                                                                     | Dejar que falle                                                             |
| A9  | Distinguir nuevo (200) de desconocido (404)                                              | Son casos de negocio distintos                                                                                                                   | —                                                                          |
| A10 | Entorno fijo (`api_hm`, scikit-learn 1.9.1)                                            | Con otra versión las listas cambian (~88 % de solapamiento)                                                                                     | Usar el entorno base                                                        |
| A11 | 7 tests automáticos                                                                     | En segundos se sabe si se rompió el contrato                                                                                                    | Probar solo a mano                                                          |
| A12 | La API lee el modelo de `models/`, sin copia propia                                    | Una sola fuente de verdad; la copia era idéntica (0 diferencias en 4.162 clientes)                                                              | Copia dentro de `api/`: autosuficiente, pero podía quedar desactualizada |
| A13 | Test `test_variables_del_modelo`                                                       | Avisa si el modelo se reentrenó con otras variables u otro orden                                                                                | Sin test                                                                    |
| A14 | Excepción en `.gitignore` solo para `api/datos/*.parquet` y `app/datos/*.parquet` | Con 3 MB la demo corre tras clonar; no abre la puerta a otros parquet                                                                            | Pasar a CSV (más pesado); compartir los archivos por fuera del repositorio |

### 8.2 Pantalla

| #   | Decisión                                                                          | Por qué                                                                                                                                                                     | Alternativa descartada                                                                     |
| --- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| B1  | La pantalla **consulta la API**                                              | Demuestra la arquitectura pantalla → API → modelo                                                                                                                          | Leer `recomendaciones_semana_test.csv` directo (decisión inicial del 16/11, modificada) |
| B2  | Sin deslizador de compras "que conoce el sistema"                                  | Es el único elemento que no representa el funcionamiento real; además exigiría correr el modelo en vivo con datos que no están en el repositorio                         | Deslizador de la maqueta                                                                   |
| B3  | Filtro de compras previas solo para "Con historial"                                | La rúbrica pide casos comunes: pocas y muchas compras                                                                                                                       | Slider numérico libre                                                                     |
| B4  | Cortes 1–5 / 6–80 / 81+                                                          | Salen de la distribución real (p10 = 5, mediana 35, p75 = 81)                                                                                                               | Cortes arbitrarios                                                                         |
| B5  | Id abreviado + cantidad de compras                                                 | El id completo no se lee; las compras explican la recomendación                                                                                                             | Id completo                                                                                |
| B6  | Título distinto por etapa                                                         | Se entiende por qué la lista de un cliente nuevo es siempre la misma                                                                                                        | Título genérico                                                                          |
| B7  | Tabla con posición 1–12 y nombre, tipo, grupo y color                            | Son las columnas útiles para entender la recomendación                                                                                                                     | Mostrar solo ids                                                                           |
| B8  | `reindex` en lugar de `isin`                                                   | Respeta el orden del ranking                                                                                                                                                 | `isin`                                                                                   |
| B9  | Errores visibles y claros, sin trazas                                              | Una demo estable no muestra pantallas técnicas                                                                                                                              | Dejar el error de Streamlit                                                                |
| B10 | Catálogo reducido (15.029 × 5, 271 KB) en vez del original (105.542 × 25, 6 MB) | **No es por peso** (6 MB cargan al instante): solo hace falta lo que se recomienda y se muestra. App más liviana, fácil de distribuir y con menos datos expuestos    | Cargar el catálogo completo                                                               |
| B11 | `@st.cache_data`                                                                 | Streamlit re-ejecuta el archivo en cada clic                                                                                                                                 | Cargar sin caché                                                                          |
| B12 | Mostrar el Recall@12 con aclaración                                               | Honestidad sobre el desempeño; justifica el sistema por etapas (7,53 % → 2,04 % al cambiar de tipo). Riesgo: 7,5 % suena bajo sin contexto, por eso va discreto y aclarado | Pantalla sin métricas                                                                     |
| B13 | Tema propio y etiqueta de color                                                    | Identidad visual del grupo; sin blanco ni negro puros                                                                                                                        | Estilo por defecto                                                                         |
| B14 | Vocabulario "compras del cliente", no "ventas"                                     | "Ventas" suena a ventas totales de H&M                                                                                                                                       | —                                                                                         |
| B15 | Dirección de la API configurable con `LOOKWISE_API_URL`                         | Deja lista la pantalla para Docker sin cambiar nada hoy (valor por defecto igual al anterior)                                                                                | Dirección fija en el código                                                              |
| B16 | La pantalla se llama `app.py`                                                    | Coincide con `streamlit run app/app.py` del README de `app/`                                                                                                             | Mantener `app.py` y corregir el README                                                   |

---

## 9. Pruebas y verificación

### 9.1 Tests automáticos de la API (`test_lookwise_api.py`)

Usan `TestClient` de FastAPI: llaman a la API sin necesidad de levantar el servidor.

```python
from fastapi.testclient import TestClient
from lookwise_api import app

web = TestClient(app)

NUEVO = "009d1f01410c945ed5f25c733f2c8261c5f17800fab8b4c8875efee404ca59fc"
HISTORIAL = "00164322e9af7460e84207c8d172912a2c13da209bb0eab92f74545ba217d885"

def test_estabilidad():
    a = web.get("/recomendar", params={"cliente": HISTORIAL}).json()
    b = web.get("/recomendar", params={"cliente": HISTORIAL}).json()
    assert a == b

def test_cliente_inexistente():
    r = web.get("/recomendar", params={"cliente": "abc123"})
    assert r.status_code == 404
```

| Test                           | Verifica                                                                                   |
| ------------------------------ | ------------------------------------------------------------------------------------------ |
| `test_salud`                 | 200 y 4.162 clientes                                                                       |
| `test_cliente_nuevo`         | 200, etapa `nuevo`, 12 prendas                                                           |
| `test_cliente_con_historial` | 200, etapa `con_historial`, 12 prendas                                                   |
| `test_estabilidad`           | Dos pedidos iguales dan exactamente la misma respuesta                                     |
| `test_cliente_inexistente`   | 404                                                                                        |
| `test_sin_parametro`         | 422                                                                                        |
| `test_variables_del_modelo`  | Las 17 variables del modelo de `models/` coinciden, en orden, con `COLUMNAS` de la API |

Se ejecutan, desde `api`, con:

```powershell
& "C:\Users\flore\anaconda3\envs\api_hm\python.exe" -m pytest -v
```

Resultado: **7 passed**. El archivo de tests debe estar **al lado** de `lookwise_api.py`. Aparece una advertencia de `httpx`/`starlette` que es un aviso de futuras versiones, no un error.

### 9.2 Pruebas manuales

| Prueba                                  | Resultado                                                                                                                           |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| API: cliente con historial en `/docs` | 200, `con_historial`, 12 prendas                                                                                                  |
| API: el mismo cliente dos veces         | Mismas 12 prendas, mismo orden                                                                                                      |
| API: cliente nuevo                      | 200, `nuevo`, lista del baseline                                                                                                  |
| API: cliente `abc123`                 | 404 `{"detail": "Cliente no encontrado"}`                                                                                         |
| Pantalla con la API apagada             | Cuadro rojo con mensaje claro                                                                                                       |
| Pantalla con la API prendida            | Etapa + 12 prendas con nombre, tipo, grupo y color                                                                                  |
| Pantalla, "Nuevo"                       | 437 clientes; lista idéntica a la de la API para un nuevo                                                                          |
| Pantalla, "Pocas" / "Muchas"            | 416 / 935 clientes                                                                                                                  |
| Pantalla, 12 filas                      | Todas con datos completos (sin celdas vacías)                                                                                      |
| Listas entre clientes                   | Distintas: un cliente de 44 compras recibe trajes de baño, tops y cardigans; uno de 190, jeans, pantalones y ropa interior básica |

**Qué prueban y qué no:** estabilidad no es acierto. Los tests confirman que la API **funciona y es consistente**; qué tan buenas son las recomendaciones lo mide el Recall@12.

---

## 10. Casos de uso para recorrer la demo

| Caso                        | Cómo                                              | Qué debe pasar                                                                                       |
| --------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Cliente con historial       | "Con historial" → elegir cualquiera               | Etiqueta "Cliente con historial", lista personalizada                                                 |
| Pocas contra muchas compras | Comparar un cliente de "Pocas" con uno de "Muchas" | Las listas son distintas                                                                              |
| Cliente nuevo               | "Nuevo"                                            | Desaparece el selector de compras previas (todos tienen 0); la lista es la misma para cualquier nuevo |
| Consistencia                | Elegir un cliente, cambiar a otro y volver         | Misma lista y mismo orden                                                                             |
| API apagada                 | Cerrar la terminal de la API y recargar            | Mensaje rojo "No se pudo conectar con la API. ¿Está encendida?"                                     |

La API también se prueba sola en `http://127.0.0.1:8000/docs`: `GET /recomendar` → *Try it out* → pegar un `customer_id` de `clientes_test.csv` → *Execute*.

---

## 11. Errores que aparecieron y cómo se resolvieron

Documentarlos sirve para reconocerlos rápido si vuelven a pasar.

| Síntoma                                    | Causa                                                                                | Resolución                                                               |
| ------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `500 Internal Server Error` en la API     | `NameError: name '____' is not defined`: quedó un espacio en blanco sin completar | Leer la **última línea** del traceback en la terminal de uvicorn  |
| `/docs` no cargaba                        | `SyntaxError`: dos líneas se unieron en una y quedó `[:____]`                  | Separar las líneas, escribir `[:12]` y buscar `____` con Ctrl+F      |
| 500 con un cliente inventado                | `KeyError` al buscar un cliente que no existe                                      | Guarda con 404 antes de la búsqueda                                      |
| Listas de prendas distintas a las esperadas | scikit-learn 1.7.2 en lugar de 1.9.1                                                 | Entorno dedicado `api_hm`                                               |
| Streamlit abría otra aplicación           | El puerto 8501 estaba ocupado                                                        | `--server.port 8502`                                                    |
| API: `[Errno 10048]` al arrancar          | El puerto 8000 lo ocupaba una API anterior                                           | Cerrar esa terminal (o el proceso) y volver a arrancar                    |
| El tema no se aplicaba                      | `config.toml` quedó fuera de la carpeta `.streamlit/`                           | Moverlo adentro y reiniciar Streamlit                                     |
| `KeyError: 'Nuevo'` en la pantalla        | El selector dice "Nuevo" y el JSON usa "Nuevos"                                      | Traducir con `clave = "Nuevos" if tipo == "Nuevo" else "Con historial"` |
| Un cambio de código no se veía            | El archivo no estaba guardado                                                        | Ctrl+S (punto blanco en la pestaña = sin guardar) y recargar             |

**Método general:** un 500 se diagnostica siempre mirando la terminal donde corre el programa, de `Traceback` hasta la última línea. Un `KeyError: 'X'` significa "busqué la clave X y no existe": la línea que señala indica dónde.

---

## 12. Limitaciones

- La demo solo conoce a los **clientes de la semana de test (16 al 22/09/2020)**. Las recomendaciones son de esa semana, con variables **ya calculadas**; no se calculan en vivo.
- Corre en una computadora, **no en la nube**: no es un despliegue en producción: es un prototipo local, sin servidor ni contenedores.
- **Estabilidad ≠ acierto.** La API devuelve siempre lo mismo para el mismo cliente; la calidad la mide el Recall@12 (7,5 % con historial; 2,0 % nuevos).
- El puntaje del ranker **no es una probabilidad real**.
- Los clientes nuevos reciben una lista **igual para todos**: no hay personalización sin historial.
  - La tabla de clientes del dataset **no tiene género** (solo edad, estado en el club, newsletter y código postal anonimizado), así que el sistema no puede distinguir entre un cliente y una clienta nuevos. El catálogo está dominado por Ladieswear (37,6 % de los artículos), y las 12 prendas del baseline (dos vestidos, un jean, suéteres, un cardigan, pantalones) parecen de línea femenina, aunque esto último no se verificó contra el grupo de índice (`prendas_min.parquet` no lo incluye). Personalizar por edad ya se probó y no mejoró lo más vendido (hipótesis H1: 4,3 contra 4,6 aciertos cada 100 en clientes nuevos). Por eso el Recall@12 de los nuevos es bajo (2,04 %).
- **Evaluación offline:** se mide si el cliente compró lo recomendado, no si la recomendación causó la compra; los datos no registran qué prendas vio cada cliente (sesgo de exposición). Para saber el efecto real haría falta una prueba A/B.
- **Techo de candidatas:** el ranker solo puede recomendar prendas que estén entre las candidatas del cliente (≈93 en promedio para los clientes con historial), así que el Recall@12 está acotado por esa cobertura.
- Una prenda del catálogo original de H&M figura con tipo inconsistente (código `874619001`, "Marissa Hoodie (J)", tipo *Bra*, grupo *Underwear*): viene del dataset original, no de la demo.
- Un mismo modelo puede aparecer repetido en distintos colores dentro de una lista (por ejemplo, un jean en dos variantes de color): son códigos de artículo distintos.
- Los `customer_id` son identificadores anonimizados (hash) del dataset original de H&M.
- La carpeta `api/` depende de la estructura del repositorio: tiene que estar junto a `models/`; sola no arranca.
- Las fotos de las prendas no se incluyen, por derechos de imagen.

---

## 13. Mejoras a futuro

- **Versionar la ruta** (`/v1/recomendar`) para poder cambiar el formato de respuesta sin romper a quien la use.
- **Mostrar el desempeño del baseline** al lado del Recall@12 del modelo, para que el número tenga referencia (el valor sale del notebook 06).
- Calcular las variables en vivo (hoy se leen ya calculadas), para poder recomendar a clientes fuera de la semana de test.
- Una tabla "lo que compró" del cliente, con foto y color, para comparar historial y recomendación (requiere un archivo reducido nuevo y resolver el tema de derechos de imagen).
- **Capturar una señal de preferencia en la base de datos del mercado argentino** para mejorar el arranque en frío: por ejemplo, una pregunta opcional al registrarse sobre qué sección le interesa (mujer, hombre, niños, todo), o usar la sección que el visitante mira en sus primeros clics. Es preferible a pedir el género, que supone que determina lo que se compra. Es una decisión de producto y de protección de datos personales (a revisar con quien corresponda), y su efecto no se puede medir con estos datos: habría que validarlo con el piloto A/B (notebook 07), comparando el Recall@12 de los nuevos con y sin la señal.
- Sumar monitoreo semanal y la prueba A/B.

---

## 14. Glosario

| Término                              | Qué es                                                                                                                      |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **API**                         | El camino por el que la pantalla le hace un pedido al modelo y recibe la respuesta. No muestra nada por sí sola             |
| **Endpoint**                    | Cada dirección de la API que atiende un tipo de pedido (`/salud`, `/recomendar`)                                        |
| **Parámetro**                  | El dato que viaja con el pedido (acá, el identificador del cliente)                                                         |
| **FastAPI**                     | La librería de Python con que se define la API                                                                              |
| **uvicorn**                     | El servidor que pone a la API a escuchar pedidos                                                                             |
| **Streamlit**                   | La librería con que se arma la pantalla                                                                                     |
| **JSON**                        | El formato en que viaja la respuesta de la API                                                                               |
| **Etapa**                       | `nuevo` (sin compras previas) o `con_historial`                                                                          |
| **Baseline**                    | La recomendación simple de referencia: las más vendidas recientemente (con decaimiento)                                    |
| **Ranker**                      | El modelo (Gradient Boosting) que ordena las prendas candidatas de un cliente                                                |
| **Candidatas**                  | Las ~90 prendas que el ranker puntúa para cada cliente                                                                      |
| **Recall@12**                   | De lo que el cliente compró en la semana de test, qué fracción estaba entre las 12 recomendadas (promedio entre clientes) |
| **Arranque en frío**           | Recomendar a quien no tiene historial                                                                                        |
| **Contrato**                    | El acuerdo sobre cómo es el pedido y cómo es la respuesta                                                                  |
| **Estabilidad**                 | Mismo cliente, mismo modelo, mismos datos → misma lista                                                                     |
| **Caché** (`@st.cache_data`) | Guardar el resultado de una carga para no repetirla en cada interacción                                                     |
