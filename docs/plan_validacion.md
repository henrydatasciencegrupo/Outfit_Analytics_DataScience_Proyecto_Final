# Plan de validación y evaluación

**Autor:** Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)

Este documento reúne cómo se validó el recomendador **antes** de llevarlo a producción (evaluación *offline* con datos históricos) y cómo se propone validarlo **en** producción, con un piloto controlado antes de escalarlo a todos los clientes. Los resultados salen del notebook final, `notebooks/06_metricas_optimizacion_decisiones.ipynb`, y de los CSV de `reports/`.

## Índice

- [1. Resumen](#1-resumen)
- [2. Muestra de datos para entrenar y evaluar](#2-muestra-de-datos-para-entrenar-y-evaluar)
- [3. Protocolo de validación offline](#3-protocolo-de-validación-offline)
- [4. Métricas de evaluación](#4-métricas-de-evaluación)
- [5. Regla de decisión y significancia](#5-regla-de-decisión-y-significancia)
- [6. Resultados](#6-resultados)
- [7. Validación en producción: piloto antes de escalar](#7-validación-en-producción-piloto-antes-de-escalar)
- [8. Monitoreo después del despliegue](#8-monitoreo-después-del-despliegue)
- [9. Limitaciones y oportunidades de mejora](#9-limitaciones-y-oportunidades-de-mejora)

## 1. Resumen

| Etapa | Qué se hace | Con qué datos | Qué decide |
|---|---|---|---|
| Validación offline | Elegir baseline, hiperparámetros y modelo | Semana del 09 al 15/09/2020 | Qué modelo se usa |
| Test offline | Medir una sola vez el modelo elegido | Semana del 16 al 22/09/2020 (nunca vista) | Cuánto mejora frente a lo actual |
| Piloto en producción | Prueba A/B con un 10% de los clientes | Clientes reales del e-commerce | Si se escala al 100% |
| Monitoreo | Seguimiento semanal de métricas | Producción | Cuándo reentrenar |

**Resultado principal:** en la semana de test, el modelo final eleva el Recall@12 de los clientes con historial de **2,78% a 7,53%** (mejora de +4,75 puntos, IC 95% de +3,89 a +5,48). En clientes nuevos, el sistema usa lo más vendido y el resultado es equivalente a la referencia (sin diferencia significativa).

## 2. Muestra de datos para entrenar y evaluar

El detalle está en [`dataset.md`](dataset.md) y en `notebooks/01_muestreo_p10.ipynb`.

**Criterio de muestreo:**

- **Solo canal online** (`sales_channel_id = 2`): el sistema recomienda en e-commerce.
- **Sorteo por cliente, no por fila**, con un número fijo calculado a partir del cliente: `bucket = hash(customer_id || 'lookwise42') % 10000`. Se conserva **todo el historial online** de cada cliente elegido, para no cortar historiales.
- **p10** = clientes con `bucket < 1000` (10%): es la muestra del proyecto. **p5** = `bucket < 500` queda como respaldo.

**Qué es el hash:** una función que convierte el identificador del cliente en un número fijo. El mismo cliente da siempre el mismo número, así que la muestra se puede reproducir exactamente en cualquier computadora, sin guardar listas de clientes.

**Por qué esta muestra es válida:** reproduce la población online en compras por cliente, antigüedad de la primera compra y porcentaje de clientes sin edad (diferencias de hasta 0,16 puntos porcentuales). No es representativa en cobertura de artículos, por eso las cifras por artículo se leen como cotas.

**Cómo se escala:** las muestras están **anidadas**: la p5 está dentro de la p10 y la p10 dentro del total. Para trabajar con más datos solo se sube el umbral (`bucket < 2000` para el 20%, todos los clientes para el 100%), sin cambiar a los clientes que ya estaban. Así, los resultados de distintos tamaños son comparables.

| Muestra | Umbral | Clientes | Compras |
|---|---|---|---|
| p5 | `bucket < 500` | 55.454 | 1.122.274 |
| **p10 (proyecto)** | `bucket < 1000` | **110.252** | **2.226.486** |
| Total online | todos | 1.108.418 | 22.379.862 |

## 3. Protocolo de validación offline

**Partición temporal**, nunca al azar: se recomienda con el pasado y se mide con lo que pasa después, igual que en el uso real.

| Conjunto | Fechas | Uso |
|---|---|---|
| Entrenamiento | hasta el 08/09/2020 | Entrenar los modelos durante la selección |
| Validación | 09 al 15/09/2020 | **Todas** las decisiones: baseline, hiperparámetros, algoritmo, umbral |
| Test | 16 al 22/09/2020 | Medición **única** del modelo elegido, reentrenado hasta el 15/09 |

**Por qué así:**

- **Corte por fecha y no aleatorio:** un corte aleatorio dejaría que el modelo vea compras del futuro (*data leakage*) y el resultado sería artificialmente alto.
- **Validación separada del test:** elegir mirando el test es como ver las respuestas antes del examen.
- **Test de 7 días:** es el horizonte de una campaña semanal de e-commerce y es la misma regla que usa la evaluación original del dataset.
- **Baseline elegido en 4 semanas** (19/08 al 15/09/2020) y no en una sola: en moda la demanda cambia de una semana a otra, y elegir con una sola semana puede premiar una variante que acertó por casualidad.

**Controles contra la fuga de información:**

- Todas las variables se calculan solo con compras anteriores a la fecha de corte, con un control automático en `src/features.py`.
- En la simulación de clientes nuevos, las compras ocultas se borran de toda la base (popularidad, co-compra y entrenamiento del ranker). El control queda registrado en `reports/simulacion_control_fuga.csv`.
- De la tabla de clientes solo se usa la edad: el resto de las columnas son una foto de un único momento y podrían reflejar información posterior a las compras.

**Segmentos evaluados por separado:**

| Segmento | Clientes en el test | Por qué se separa |
|---|---|---|
| Con historial | 3.725 (89,5%) | El modelo personalizado se aplica a ellos |
| Nuevos (sin compras previas) | 437 (10,5%) | Es el foco del problema (*cold start*); un promedio general los escondería |
| Nuevos simulados | 3.549 | Clientes con historial a los que se les ocultan compras (0, 1 o 2 visibles), para tener más evidencia sobre cuándo personalizar |

## 4. Métricas de evaluación

El recomendador muestra **12 prendas** a cada cliente. Se evalúa en dos niveles.

**Nivel lista (lo que ve el cliente)**: implementadas en `src/metricas.py`.

| Métrica | Pregunta que responde | KPI de negocio | Rol |
|---|---|---|---|
| **Recall@12** | ¿Qué parte de lo que compró el cliente estaba en sus 12 recomendaciones? | Productos por pedido, conversión | **Decide** |
| Hit Rate@12 | ¿Qué % de clientes compró al menos una de las 12? | Conversión | Apoyo |
| MAP@12 | ¿Las prendas compradas aparecen arriba en la lista? | Experiencia | Desempate |
| Precision@12 | ¿Qué parte de los 12 lugares se aprovechó? | Uso de la vitrina | Apoyo |
| Prendas distintas | ¿A cuántas prendas damos visibilidad? | Salud del catálogo | Apoyo |

**Nivel par cliente–prenda (diagnóstico del ranker)**: implementadas en `src/optimizacion.py`.

| Métrica | Para qué |
|---|---|
| Accuracy y Balanced accuracy | Mostrar por qué la Accuracy no sirve en este problema |
| Recall, Precision y F1 | Cuántas compras detecta el clasificador y con cuántas falsas alarmas |
| ROC-AUC y PR-AUC | Si ordena las compras por encima de las no compras, sin depender de un umbral |

**Por qué Recall@12 decide:** mide cuántas de las compras reales habrían estado visibles en la vitrina personalizada, que es lo que más se vincula con la conversión. En los notebooks 03 a 05 se comparó con MAP@12; desde el notebook 06 decide Recall@12. **La elección del modelo no cambia con el criterio:** el ranker es el mejor en las dos métricas.

**Por qué la Accuracy no decide:** solo el **0,49%** de los pares cliente–prenda terminan en compra. Un clasificador que nunca predice compra tiene **99,5% de Accuracy y 0% de Recall**: no detecta ninguna compra. Además, el recomendador no usa un umbral: ordena por probabilidad y muestra las 12 primeras.

## 5. Regla de decisión y significancia

- **Intervalo de confianza del 95% por bootstrap pareado** (1.000 remuestreos de clientes, `src/metricas.py`): se compara a los dos modelos sobre los mismos clientes. Si el intervalo de la diferencia **no incluye el 0**, la mejora no es atribuible al azar.
- **Regla fijada antes de ver el resultado:** se elige el modelo más complejo (Gradient Boosting) solo si su mejora sobre la regresión logística es significativa. Así se evita sumar complejidad sin evidencia.
- **Criterio de las hipótesis**, también fijado de antemano: *se cumple* si mejora y el intervalo no incluye el 0; *no concluyente* si mejora pero el intervalo incluye el 0; *no se cumple* si no mejora.

## 6. Resultados

**Selección en validación** (`reports/busqueda_hiperparametros.csv`): 16 configuraciones.

| Algoritmo (mejor configuración) | Recall@12 | Hit Rate@12 | PR-AUC |
|---|---|---|---|
| Regresión logística (C=10, clases balanceadas) | 6,52% | 13,71% | 0,034 |
| **Gradient Boosting** (tasa 0,05; 15 hojas; 200 iteraciones; balanceado) | **6,92%** | **14,81%** | **0,041** |

Diferencia: **+0,40 puntos** de Recall@12, IC 95% **[+0,11; +0,68]** → significativa: se elige Gradient Boosting.

**Baseline optimizado** (`reports/baseline_optimizado_validacion.csv`): entre 9 variantes de "lo más vendido", gana la popularidad con decaimiento de 3 días (Recall@12 promedio de 2,54% en 4 semanas). La popularidad de todo el historial rinde menos de la mitad (1,13%): en moda manda lo reciente.

**Test final** (`reports/resultados_test_optimizado.csv`): Recall@12 en %.

| Modelo | Todos (4.162) | Con historial (3.725) | Nuevos (437) |
|---|---|---|---|
| Popularidad 7 días (referencia actual) | 2,71 | 2,78 | 2,07 |
| Co-compra + recompra (no supervisado) | 6,04 | 6,50 | 2,04 |
| Ranker con Gradient Boosting | 6,96 | 7,53 | 2,11 |
| **Modelo final por etapas** | **6,95** | **7,53** | **2,04** |

| Segmento | Mejora de Recall@12 | IC 95% | Conclusión |
|---|---|---|---|
| Con historial | +4,75 puntos | +3,89 a +5,48 | Mejora significativa |
| Nuevos | −0,03 puntos | −0,09 a 0,00 | Sin diferencia significativa |

El Hit Rate@12 de los clientes con historial pasa de **7,25% a 14,79%**: el doble de clientes encuentra en su vitrina al menos una prenda que termina comprando. El modelo muestra **4.123 prendas distintas**, contra 12 de lo más vendido.

**Diagnóstico del clasificador en test** (`reports/metricas_clasificacion_test.csv`):

| Umbral | Accuracy | Recall | Precision | ROC-AUC |
|---|---|---|---|---|
| Siempre "no compra" | 99,51% | 0% | 0% | 0,50 |
| 0,5 | 76,32% | 55,73% | 1,15% | 0,74 |
| Mejor F1 en validación | 98,76% | 15,27% | 8,27% | 0,74 |

Con el umbral calibrado, la Precision (8,27%) es unas **17 veces** la tasa base de compra (0,49%).

**Simulación de clientes nuevos** (`reports/simulacion_cold_start.csv`): Hit Rate@12, clientes de cada 100.

| Compras visibles | Lo más vendido | Ranker | ¿Mejora significativa? |
|---|---|---|---|
| 0 | 5,9 | 7,2 | Solo en simulación; con nuevos reales gana lo más vendido (4,6 contra 3,7) |
| 1 | 5,9 | 10,6 | Sí |
| 2 | 6,6 | 12,1 | Sí |
| Historial completo | 7,2 | 14,0 | Sí |

**Conclusión:** lo más vendido para quien nunca compró y el ranker **desde la primera compra**. Es el corte que usa el modelo final.

## 7. Validación en producción: piloto antes de escalar

La evaluación offline mide si el modelo **habría acertado** con compras pasadas. No mide si los clientes **compran más** cuando ven las recomendaciones. Para eso hace falta un piloto controlado con clientes reales antes de escalar.

**Por qué por clientes y no por tienda o zona:** el sistema es para el e-commerce, y en los datos el código postal está anonimizado (no permite agrupar zonas). La unidad del piloto es el **cliente de la web**.

### 7.1 Diseño: prueba A/B

| Elemento | Decisión |
|---|---|
| Grupo **modelo** | Ve la vitrina del modelo final por etapas |
| Grupo **control** | Ve lo más vendido (lo que hace hoy la tienda) |
| Asignación | Hash fijo por cliente: `asignar_grupo()` en `src/piloto.py`, con una sal propia (`lookwise-piloto`) |
| Tamaño inicial | 10% de los clientes en el grupo modelo |
| Duración | Mínimo 2 semanas y hasta reunir el tamaño de muestra (7.4) |

**Por qué el hash y no un sorteo cualquiera:** el mismo cliente cae siempre en el mismo grupo, aunque entre varias veces a la web, y la asignación se puede reproducir sin guardar listas. Al escalar del 10% al 20%, los clientes que ya estaban en el grupo modelo siguen ahí: la asignación es anidada, igual que la muestra p10.

**Por qué al azar y no por edad:** si el grupo modelo fueran, por ejemplo, solo clientes jóvenes, una diferencia en ventas podría deberse a la edad y no al modelo. El sorteo hace que los dos grupos sean parecidos en todo. Además, en nuestros resultados la edad sola no supera a lo más vendido (hipótesis H1) y casi no pesa en el modelo final. La edad se usa como **control**: se verifica que los dos grupos tengan un reparto de edades parecido (`balance_por_grupo()`) y los resultados se reportan por tramo de edad.

**Alcance por línea de producto (sustituto de la zona geográfica):** los datos no tienen ubicación (el código postal está anonimizado), así que no se puede empezar por una ciudad o una tienda. En su lugar, el piloto puede empezar mostrando la vitrina personalizada **solo en la sección de una línea de producto** (por ejemplo, Divided o Ladieswear) y, dentro de esa sección, repartir a los clientes al azar con el hash. Así se limita el riesgo a una parte del catálogo. Los grupos **no** se arman por línea: si el grupo modelo fueran solo clientes de una línea, la comparación quedaría sesgada por su perfil (por ejemplo, Divided concentra a los clientes más jóvenes). La línea de inicio se elige por **razones de negocio** (volumen de clientes y riesgo), no por la que mejor resultado dio en la simulación: elegirla por el resultado sería acomodar el piloto a los datos. La simulación solo se usa para verificar que el modelo no rinda peor que lo más vendido en esa línea. Como dentro de una línea hay menos clientes, **el tamaño de muestra se recalcula por línea** y el piloto puede durar más semanas; la estimación está en `reports/piloto_tamano_por_linea.csv`.

### 7.2 Simulación del piloto con la semana de test

El notebook `notebooks/07_piloto_ab_simulado.ipynb` aplica este diseño a los 4.162 clientes de la semana de test: los reparte con `asignar_grupo()`, verifica que los grupos sean comparables por edad y tipo de cliente, le muestra a cada grupo una sola vitrina (modelo final o lo más vendido de 7 días) y aplica la regla de escalado. Como hay pocos clientes, el escenario principal usa un reparto 50/50 y el reparto 10/90 se reporta como la etapa inicial real. Los resultados quedan en `reports/piloto_ab_simulado.csv`, `reports/piloto_ab_por_edad.csv` y `reports/piloto_tamano_muestra.csv`.

Es una simulación con datos históricos: muestra que el procedimiento funciona, pero no mide el efecto causal de mostrar la vitrina,  que solo puede medir el piloto real.

**Resultados de la simulación** (`reports/piloto_ab_simulado.csv`): conversión de la vitrina, en % de clientes que compraron al menos una prenda de su vitrina.

| Escenario | Segmento | Clientes modelo / control | Conversión modelo | Conversión control | Diferencia (IC 95%) | ¿Escalar? |
|---|---|---|---|---|---|---|
| 50/50 | Todos | 2.176 / 1.986 | 14,15% | 6,55% | +7,61 puntos (+5,78 a +9,43) | Sí |
| 50/50 | Con historial | 1.939 / 1.786 | 15,21% | 6,94% | +8,27 puntos (+6,28 a +10,26) | Sí |
| 50/50 | Nuevos | 237 / 200 | 5,49% | 3,00% | +2,49 puntos (−1,26 a +6,23) | No concluyente |
| 10/90 (etapa inicial) | Todos | 425 / 3.737 | 13,65% | 6,90% | +6,74 puntos (+3,38 a +10,11) | Sí |

- **Los grupos son comparables:** el hash los reparte de forma pareja por tramo de edad y por tipo de cliente.
- **La regla de escalado se cumple**, incluso en la etapa inicial del 10%: el grupo modelo convierte más del doble que el control y el intervalo no incluye el 0.
- **Clientes nuevos:** la diferencia no es significativa, como se esperaba: los dos grupos ven una vitrina de popularidad.
- **Por tramo de edad** (`reports/piloto_ab_por_edad.csv`): el grupo modelo convierte más en todos los tramos con clientes suficientes, con mejoras de +5,1 a +8,4 puntos y significativas en los cinco. El grupo "sin edad" (7 clientes) no permite conclusiones.
- **Por línea de producto** (`reports/piloto_ab_por_linea.csv`): mide en qué sección de la tienda acierta más el modelo. Sirve como control al elegir por qué línea empezar el piloto real, junto con el tamaño de muestra necesario en cada línea (`reports/piloto_tamano_por_linea.csv`).
- **Por línea de producto** (resultado): el modelo acierta más que lo más vendido en las cinco líneas y la mejora es significativa en cuatro.

| Línea | Clientes que compraron en la línea | Acierto modelo | Acierto control | Diferencia (IC 95%) |
|---|---|---|---|---|
| Ladieswear | 3.213 | 12,14% | 6,95% | +5,19 puntos (+3,18 a +7,21) |
| Divided | 1.907 | 9,45% | 2,57% | +6,87 puntos (+4,77 a +8,97) |
| Sport | 310 | 7,06% | 0,00% | +7,06 puntos (+3,21 a +10,91) |
| Menswear | 288 | 6,58% | 0,00% | +6,58 puntos (+2,64 a +10,52) |
| Baby/Children | 139 | 2,70% | 0,00% | +2,70 puntos (−0,99 a +6,40), no concluyente |

  En Sport, Menswear y Baby/Children lo más vendido acierta 0% porque sus 12 prendas no incluyen ninguna de esas líneas: la vitrina general deja fuera secciones enteras de la tienda, y el modelo sí las cubre.

- **Tamaño de muestra por línea** (`reports/piloto_tamano_por_linea.csv`), con el 10% de los clientes en el grupo modelo y los clientes de la población online estimados a partir de la muestra p10:

| Línea | Clientes por semana (estimado) | Clientes por grupo para +1 punto | Semanas para +1 punto | Semanas para +2 puntos |
|---|---|---|---|---|
| Ladieswear | 32.130 | 10.824 | 3,4 | 0,9 |
| Divided | 19.070 | 4.674 | 2,5 | 0,7 |
| Sport | 3.100 | 1.553 | 5,0 | 1,9 |
| Menswear | 2.880 | 1.553 | 5,4 | 2,0 |
| Baby/Children | 1.390 | 1.553 | 11,2 | 4,2 |

  Para las líneas con 0% de acierto en el control se usa una tasa base mínima de 0,5% en el cálculo. **Lectura para elegir la línea de inicio:** Ladieswear y Divided son las que juntan la muestra más rápido (2 a 4 semanas para detectar una mejora de 1 punto). Ladieswear es la línea más grande de la tienda, así que un error ahí afecta más venta; Divided tiene volumen suficiente con menos riesgo, por lo que es una buena candidata para empezar. La decisión final corresponde a H&M, con estos criterios.
- **Recall@12:** pasa de 2,44% en el control a 7,16% en el grupo modelo (+4,72 puntos, IC 95% de +3,72 a +5,76).

### 7.3 Métricas del piloto

| Tipo | Métrica | Cómo se mide en producción |
|---|---|---|
| **Principal** | Conversión de la vitrina | % de clientes que compran al menos una prenda recomendada (equivalente a Hit Rate@12) |
| Secundaria | Prendas por pedido | Prendas compradas por pedido y % que venía de la vitrina (equivalente a Recall@12) |
| Secundaria | Clics en la vitrina | % de clientes que hacen clic en alguna recomendación |
| Secundaria | Ingreso por cliente | Ventas por cliente en el período |
| Resguardo | Diversidad del catálogo | Prendas distintas mostradas |
| Resguardo | Tiempo de respuesta | Que la vitrina cargue rápido |
| Resguardo | Devoluciones | Que no aumenten en el grupo modelo |

Los resultados se reportan **por separado** para clientes nuevos y con historial, igual que en la evaluación offline.

### 7.4 Tamaño de muestra

Con `tamano_muestra()` de `src/piloto.py` (prueba de dos proporciones, 95% de confianza y 80% de potencia), tomando como base el Hit Rate@12 de la referencia actual en el test (6,97%):

| Mejora mínima que se quiere detectar | Clientes por grupo |
|---|---|
| +0,5 puntos (de 6,97% a 7,47%) | 42.061 |
| +1 punto (de 6,97% a 7,97%) | 10.850 |
| +2 puntos (de 6,97% a 8,97%) | 2.878 |

Offline, la mejora observada fue mucho mayor (de 6,97% a 13,70% en todos los clientes), así que con unos **11.000 clientes por grupo** el piloto alcanza para detectar incluso una mejora de 1 punto. Con el grupo modelo en el 10%, el piloto dura hasta que ese grupo reúna esa cantidad de clientes, y como mínimo dos semanas para incluir distintos días de la semana.

### 7.5 Regla de escalado

| Etapa | % en el grupo modelo | Pasa a la siguiente si… |
|---|---|---|
| 1 | 10% | La conversión del grupo modelo es mayor y el IC 95% de la diferencia no incluye el 0 (`comparar_grupos()`), sin deterioro de las métricas de resguardo |
| 2 | 20% | Se mantiene el resultado de la etapa 1 |
| 3 | 50% | Se mantiene el resultado |
| 4 | 100% | Despliegue completo; el control pasa a ser un 5% fijo para seguir midiendo |

**Se detiene el piloto** si la conversión del grupo modelo es significativamente menor, si aumentan las devoluciones o si el tiempo de respuesta afecta la navegación.

## 8. Monitoreo después del despliegue

- **Cada semana:** Recall@12, Hit Rate@12 y prendas distintas, por segmento (nuevos y con historial), comparados con el grupo de control.
- **Recalcular lo más vendido cada semana**, con decaimiento de 3 días: lo reciente es lo que predice.
- **Reentrenar el ranker** si la mejora sobre el control cae por debajo de la mitad de la observada en el piloto durante dos semanas seguidas, o al cambiar de temporada.
- **Registrar cada entrenamiento** (parámetros, muestra usada y métricas) en MLflow, para comparar versiones y volver a una anterior si hace falta.

## 9. Limitaciones y oportunidades de mejora

| Limitación | Efecto | Mejora propuesta |
|---|---|---|
| Evaluación offline: solo se registran compras, no lo que vio cada cliente | No mide el efecto causal de mostrar la vitrina | Piloto A/B (sección 7) |
| Una sola semana de test | El resultado puede depender de esa semana | Validar en varias semanas y en el piloto |
| Las candidatas del ranker contienen alrededor del 12% de las compras | Ningún modelo puede recomendar lo que no está entre las candidatas | Ampliar la generación de candidatas (prendas similares por atributos) |
| Clientes nuevos: sin historial no hay señal | El modelo no supera a lo más vendido | Sumar contexto de la visita: categoría que mira, canal de llegada, temporada |
| Datos de un mercado del hemisferio norte | La estacionalidad está invertida respecto de Argentina | Invertir o ignorar la estacionalidad; reentrenar con datos locales desde el lanzamiento |
| Muestra del 10% de los clientes | Las cifras por artículo están infladas | Escalar la muestra subiendo el umbral del hash |
| Hiperparámetros elegidos en una semana de validación | Posible ajuste a esa semana | Validación en varias semanas; el orden de los modelos se mantuvo en test |
| Prendas nuevas sin ventas | No entran en co-compra ni en popularidad | Modelo de contenido con los atributos del catálogo |
