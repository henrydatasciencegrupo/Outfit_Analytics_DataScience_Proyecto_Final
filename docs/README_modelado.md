# Lookwise Data Lab · Modelado del sistema de recomendación

Sistema de recomendación para **clientes nuevos de H&M** en e-commerce: qué 12 prendas mostrarle a cada cliente para que encuentre algo que quiera comprar.

**Autora del modelado:** Margot Huaman Quispe · **EDA y muestra:** Florencia Dinelli y María Isabel Fernández

---

## 1. Resultado en una línea

El **modelo final** casi **duplica los aciertos** de lo que se hace hoy (mostrar lo más vendido) en los clientes con historial: **13,8 vs 7,2 de cada 100**. En los clientes nuevos **nunca queda por debajo** de hoy. Además, la simulación muestra que **desde la primera compra** ya conviene personalizar.

| Tipo de cliente | Hoy: lo más vendido | Modelo final |
|---|---|---|
| Todos (4.162) | 7,0 | **12,9** |
| Con historial (3.725) | 7,2 | **13,8** |
| Nuevos (437) | 4,6 | **4,6** |

*Hit Rate@12 = clientes de cada 100 que compran al menos una de las 12 prendas recomendadas. Semana de test: 16–22/09/2020.*

---

## 2. Qué hicimos

### Datos
- **Muestra p10:** 2.226.486 compras online, 110.252 clientes y 105.542 artículos. La preparó el equipo en `notebooks/02_EDA_unificado_p10.ipynb`, con semilla fija y controles de integridad.
- **Tratamiento cuantificado** (`src/datos.py`): 8 decisiones, cada una medida. **No se borró ninguna compra real.**

| Tema | Afecta | Decisión |
|---|---|---|
| Duplicados (misma prenda, cliente y día) | 12,76% | Se conservan: son varias unidades, más demanda |
| Meses atípicos (mar–may 2020) | 14,38% | Se conservan: el test no cae en ese período |
| Precios fuera de rango (IQR) | 7,49% | Se conservan: son ventas reales |
| Clientes sin edad | 1,10% | No se imputa: forman el grupo "sin edad" |

### Cómo evaluamos
- **Partición temporal:** entrenamiento hasta el 15/09/2020, test del 16 al 22/09/2020. Simula el uso real: se recomienda con el pasado y se mide con lo que pasa después.
- **Validación:** la semana del 09 al 15/09 se usó para elegir parámetros y modelos, **sin mirar el test**.
- **Sin fuga de información:** todas las variables se calculan solo con compras anteriores a la fecha de corte, y hay un control automático.
- **Métricas** (`src/metricas.py`):

| Métrica | KPI de negocio | Pregunta |
|---|---|---|
| **MAP@12** (principal) | Experiencia | ¿Acertamos y pusimos lo correcto arriba? |
| Hit Rate@12 | Conversión | ¿Qué % de clientes compró algo de la lista? |
| Recall@12 | Productos por pedido | ¿Qué parte de su compra anticipamos? |
| Precision@12 | Uso de la vitrina | ¿Cuántos de los 12 lugares se aprovecharon? |
| Prendas distintas | Salud del catálogo | ¿A cuántas prendas damos visibilidad? |

Cada mejora se verifica con un **intervalo de confianza del 95%** (bootstrap pareado). Si no incluye el 0, la mejora es real.

### Modelos (`src/modelos.py`)

| Modelo | Tipo | Idea |
|---|---|---|
| Baseline | Referencia | Lo más vendido de los últimos 7 días (lo que se hace hoy) |
| M1 · Edad | Personalización simple | Lo más vendido en el tramo de edad del cliente |
| M2 · Co-compra | No supervisado | "Quienes compraron esto también compraron…" + recompra |
| M3 · Ranker | Supervisado | Aprende a ordenar candidatos combinando todas las señales |
| **Modelo final** | Sistema por etapas | Ranker si el cliente ya compró; lo más vendido si es nuevo |

Para el ranker se compararon **cuatro algoritmos** con los mismos datos:

| Algoritmo | MAP@12 (validación) | Segundos |
|---|---|---|
| **Regresión logística (elegido)** | **0,0323** | 2,4 |
| XGBoost | 0,0310 | 13,1 |
| LightGBM | 0,0297 | 10,5 |
| HistGradientBoosting | 0,0282 | 3,2 |

---

## 3. Qué encontramos

### Resultados del test (16–22/09/2020)

| Modelo | Todos | Con historial | Nuevos | MAP@12 (todos) |
|---|---|---|---|---|
| Baseline | 7,0 | 7,2 | 4,6 | 0,0083 |
| M1 · Edad | 5,4 | 5,6 | 4,3 | 0,0056 |
| M2 · Co-compra | 10,9 | 11,7 | 4,3 | 0,0311 |
| M3 · Ranker | 12,8 | 13,8 | 3,7 | 0,0332 |
| **Modelo final** | **12,9** | **13,8** | **4,6** | **0,0334** |

### Hipótesis

**Cómo leer el resultado** (criterio fijado antes de ver el test):

- ✅ **Se cumple:** el modelo mejora MAP@12 y Hit Rate@12, y el intervalo del 95% de la mejora no incluye el 0. La mejora es real.
- 🟡 **Mejora, pero no es concluyente:** el modelo mejora, pero el intervalo incluye el 0. Puede ser azar; hace falta más evidencia.
- ❌ **No se cumple:** el modelo no mejora. La hipótesis se descarta.

| # | Hipótesis | Resultado | Qué encontramos | Cómo lo resolvimos |
|---|---|---|---|---|
| H1 | La edad supera a lo más vendido en clientes nuevos | ❌ No se cumple | Con los 437 clientes nuevos, la edad acierta a 4,3 de cada 100 y lo más vendido a 4,6. La edad sola no dice qué le gusta a alguien | Para clientes nuevos usamos **lo más vendido de la semana**. Proponemos sumar datos de contexto (categoría que mira, canal, temporada) |
| H2 | El historial (co-compra) supera a la edad | ✅ Se cumple | La co-compra acierta a 11,7 de cada 100 clientes con historial; la edad, a 5,6. MAP@12 +515% | El historial pasa a ser la base de la personalización: **"quienes compraron esto también compraron…"** |
| H3 | El supervisado supera al no supervisado | 🟡 Mejora, no concluyente en MAP@12 | El ranker sube el Hit Rate de 11,7 a 13,8 (+19%), pero en MAP@12 la mejora es de +7% y el intervalo incluye el 0 | Lo elegimos igual porque **ganó en validación** con la regla fijada de antemano y el test lo confirmó. Con la regresión logística sigue siendo simple y rápido. Se confirma con una prueba A/B |
| H4 | Lo reciente (7 días) supera a lo histórico | ✅ Se cumple | En validación, la popularidad de 7 días le gana a la histórica (MAP@12 0,0073 vs 0,0048). La simulación lo confirma: con compras viejas, personalizar deja de ganar | **Lo más vendido se recalcula cada semana** y la vitrina personalizada se actualiza en cada visita |
| H5 | Personalizar reparte la visibilidad del catálogo | ✅ Se cumple | Lo más vendido muestra las mismas 12 prendas a todos; el modelo final, 9.205 prendas distintas | La personalización da salida a la **cola larga** del catálogo, que hoy no se ve |

### Simulación de clientes nuevos (`notebooks/05_simulacion_cold_start.ipynb`)

Como hay pocos clientes nuevos reales, a **3.549 clientes con historial** se les ocultó el pasado y se les dejó visibles 0, 1 o 2 compras. Las compras ocultas se borraron de toda la base para evitar fuga de información.

| Compras visibles | Lo más vendido | Mejor modelo | ¿Mejora real? |
|---|---|---|---|
| 0 | 5,9 | Ranker 7,2 | Solo en simulación: con nuevos reales gana lo más vendido |
| **1** | 5,9 | **Ranker 10,6** | ✅ Sí |
| 2 | 6,6 | Ranker 12,1 | ✅ Sí |
| Historial completo | 7,2 | Ranker 14,0 | ✅ Sí |

**Respuesta:** con 0 compras, lo más vendido; **desde la primera compra, el ranker**. Es exactamente el corte que usa el modelo final.

### Lo más importante, en simple
1. **El historial es la señal más fuerte.** Lo que más predice una compra: el puntaje de co-compra, cuántas veces compró y cuántos días pasaron desde la última compra.
2. **La edad sola no alcanza.** No le gana a lo más vendido en ningún escenario.
3. **Ganó el algoritmo más simple.** La regresión logística le ganó a XGBoost y LightGBM: las variables construidas ya capturan casi toda la señal. Es más rápida y más fácil de explicar.
4. **Lo reciente manda.** La popularidad de 7 días le gana a la histórica. En la simulación, con compras viejas personalizar deja de ganarle a lo más vendido.
5. **Personalizar da visibilidad al catálogo.** Hoy se muestran 12 prendas a todos; el modelo final muestra 9.205 distintas.

---

## 4. Qué pasó en el camino (decisiones y ajustes)

| Situación | Qué hicimos | Por qué |
|---|---|---|
| El ranker con HistGradientBoosting quedaba 10% debajo de la co-compra en MAP@12 | Comparamos 4 algoritmos; ganó la regresión logística y el ranker pasó a ser el mejor | Elegir el algoritmo con evidencia, no por fama |
| El ranker ganador era peor que hoy en clientes nuevos (3,7 vs 4,6) | Modelo final por etapas: ranker para quien ya compró, lo más vendido para nuevos | Que ningún grupo quede peor que hoy |
| Con 437 clientes nuevos ninguna diferencia era concluyente | Simulación de clientes nuevos con 3.549 clientes (propuesta del equipo) | Más evidencia para fijar cuándo personalizar |
| En la simulación, el ranker ganaba con 0 compras pero no con nuevos reales | Para 0 compras manda la evidencia real; la simulación decide 1 y 2 compras | Los simulados eran compradores frecuentes, no nuevos |
| El ranker armaba recomendaciones de a un cliente (muy lento) | Se arman en bloque | De más de 40 minutos a pocos minutos |

---

## 5. Recomendaciones para H&M

1. **Implementar el modelo final por etapas:** lo más vendido de la semana para quien nunca compró y el ranker desde la primera compra.
2. **Actualizar la vitrina personalizada en cada visita.** Lo reciente es lo que predice.
3. **Recalcular "lo más vendido" cada semana**, no con todo el historial.
4. **Mostrar "quienes compraron esto también compraron…"** en la página de producto y en el carrito: la co-compra es la señal más fuerte.
5. **No personalizar solo por edad.** No supera a lo más vendido.
6. **Para clientes que vuelven tras mucho tiempo**, combinar sus compras viejas con lo más vendido.
7. **Aprovechar la cola larga:** pasar de 12 a más de 9.000 prendas visibles ayuda a vender stock que hoy no se ve.
8. **Validar con una prueba A/B** antes de llevarlo a toda la tienda, midiendo conversión (Hit Rate) y productos por pedido.
9. **Para clientes nuevos, sumar información de contexto** (categoría que mira, canal de llegada, temporada), porque la edad sola no alcanza.
10. **Monitorear las métricas cada semana** y reentrenar si caen.

### Próximos pasos del proyecto
- Demo en Streamlit: elegir un cliente y ver sus 12 recomendaciones.
- Dashboard en Power BI con los CSV de `reports/`.
- Registro de cada corrida en MLflow y automatización con GitHub Actions.
- Análisis de costos y retorno de la inversión (objetivo: recuperarla en 6 meses o menos).
- Modelo de contenido para prendas nuevas, que todavía no tienen ventas.

---

## 6. Estructura y cómo reproducir

```
notebooks/
├── muestreo_p10_documentado.ipynb   # Muestra p10 (Flor e Isa)
├── 02_EDA_unificado_p10.ipynb       # EDA del equipo (Flor e Isa)
├── 03_baseline.ipynb                # Baseline: lo más vendido
├── 04_pipeline_modelos.ipynb        # Tratamiento, features, modelos, comparación y ganador
└── 05_simulacion_cold_start.ipynb   # Simulación: desde cuántas compras personalizar
src/
├── datos.py                         # Carga, verificación y tratamiento
├── features.py                      # Pipeline de features sin fuga de información
├── metricas.py                      # Métricas e intervalo de confianza
├── modelos.py                       # Baseline, M1, M2, M3 y modelo final
├── simulacion.py                    # Reglas y funciones de la simulación
└── pipeline.py                      # Ejecución de punta a punta
reports/                             # CSV de resultados y gráficos (insumo de Power BI)
docs/README_modelado.md              # Este documento
```

```
pip install -r requirements.txt
python src/pipeline.py --base <carpeta_p10> --salida reports
```

O abrir los notebooks, cambiar `BASE` por la carpeta local de la muestra p10 y ejecutar **Run All**. Los datos no se suben al repositorio: están en el Drive del equipo.
