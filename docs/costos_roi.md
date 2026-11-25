# Costos y retorno de la inversión (ROI)

**Autor:** Lookwise Data Lab · Sistema de recomendación para clientes nuevos de H&M (e-commerce)

**Pregunta del cliente:** ¿cuánto hay que invertir en el recomendador y cuánto retorna? ¿Se recupera en 6 meses?

**Respuesta corta:**

- **Inversión:** **USD 15.000** de honorarios para construir el sistema y **USD 650 por mes** para operarlo. En el primer año, **USD 22.805** en total.
- **Retorno:** en el escenario más probable, el recomendador **se paga en el mes 3** y cierra el primer año con un **ROI de +488%**.
- **Riesgo:** en 10.000 escenarios simulados, la inversión se recupera en 6 meses en el **98%** de los casos. Solo no se recupera si el canal online es tan chico como el de una sola tienda **y** la venta extra es mínima.

El cálculo está en `src/roi.py`, la simulación en `notebooks/08_costos_roi.ipynb` y los resultados en `reports/roi_*.csv` (el archivo `roi_flujos_powerbi.csv` está listo para el dashboard).

## 1. Criterios del análisis

| Pauta                                                                          | Cómo se aplica                                                                                                                                                     |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Costos técnicos con los precios publicados de los servicios                   | Nube con precios públicos de AWS; software de código abierto                                                                                                      |
| Beneficio solo sobre el **canal online**, donde funciona el recomendador | Se usa la facturación online de H&M, no la total                                                                                                                   |
| Incluir **honorarios profesionales** con referencia norteamericana       | USD 1.500 por científico de datos por mes, durante unos 2 meses de proyecto (referencia: sueldos de EE. UU. de unos USD 160.000 al año) |
| Costos de nube con precios **publicados en la web**                      | Precio por hora publicado × horas de uso de cada servidor (sección 2)                                                                                             |
| Para el costo total, **sumar con desglose**                              | Tabla de costos separada en técnicos y honorarios, con el total                                                                                                    |
| ROI: primero el **punto de equilibrio**                                  | Sección 5.1: equilibrio operativo y de recupero                                                                                                                    |
| A partir de ese punto, **3 escenarios** (opcional)                       | Sección 5.2: pesimista, base y optimista                                                                                                                           |
| Gráficos interactivos **segmentados en Power BI** (opcional)            | `reports/roi_flujos_powerbi.csv`: flujo mes a mes por escenario, listo para filtrar                                                                               |
| Trabajar con **simulación y datos sintéticos**                         | Sección 5.3: Monte Carlo con 10.000 escenarios                                                                                                                     |

## 2. Inversión

| Tipo                          | Concepto                                                                                 | Única vez           | Por mes           |
| ----------------------------- | ---------------------------------------------------------------------------------------- | -------------------- | ----------------- |
| Técnico (nube)               | API de recomendaciones: 2 servidores m7i.large encendidos todo el día (uno de respaldo) |                      | USD 147           |
| Técnico (nube)               | Reentrenamiento semanal: 1 servidor m7i.xlarge, 10 horas por semana                      |                      | USD 9             |
| Técnico (nube)               | Monitoreo y registro de versiones del modelo: 1 servidor m7i.large                       |                      | USD 74            |
| Técnico (nube)               | Imprevistos (almacenamiento, transferencia de datos): 20%                                |                      | USD 46            |
| Técnico (software)           | Licencias: pandas, scikit-learn, FastAPI y Streamlit son de código abierto              |                      | USD 0             |
| **Subtotal técnico**   |                                                                                          |                      | **USD 275** |
| Honorarios                    | Desarrollo: 5 científicos de datos × 2 meses × USD 1.500                              | USD 15.000           |                   |
| Honorarios                    | Operación y reentrenamiento: 1 científico de datos al 25% de su tiempo                 |                      | USD 375           |
| **Subtotal honorarios** |                                                                                          | **USD 15.000** | **USD 375** |
| **Total**               |                                                                                          | **USD 15.000** | **USD 650** |

**Costo total del primer año:** USD 15.000 + 12 × USD 650 = **USD 22.805** (USD 3.305 técnicos y USD 19.500 de honorarios). Los honorarios son unos 86% del total: la nube es barata porque el modelo es liviano.

**Cómo se llega a los honorarios:** se tomó como referencia norteamericana un sueldo de unos USD 160.000 al año para un científico de datos (unos USD 13.300 por mes) y, para este proyecto, un valor de **USD 1.500 por científico de datos por mes**, durante unos **2 meses**. Con los 5 integrantes del equipo: 5 × 2 × USD 1.500 = USD 15.000.

Los precios de nube son los precios on-demand publicados por AWS para la región us-east-1 (m7i.large: USD 0,1008 por hora; m7i.xlarge: USD 0,2016 por hora).

**Plataforma de la tienda online** (referencia, aparte): una tienda tipo Shopify Plus cuesta desde USD 2.500 por mes con contrato de un año. No se suma a la inversión del recomendador, porque la tienda online existe con o sin él; se incluye en un escenario de sensibilidad (sección 6).

## 3. Facturación del canal online

Los precios del dataset están **escalados** (no son precios reales en dinero), así que no sirven para calcular facturación. Por eso se usa la **facturación pública de H&M**, solo del canal online, y se simula.

| Dato público                                               | Valor                                           |
| ----------------------------------------------------------- | ----------------------------------------------- |
| Ventas netas de H&M, año fiscal 2025                       | SEK 228.285 millones (unos USD 23.700 millones) |
| Parte online de las ventas                                  | algo más del 30%                               |
| Mercados con venta online                                   | 61                                              |
| **Facturación online de un mercado promedio de H&M** | **unos USD 9,7 millones por mes**         |

H&M Argentina es un mercado nuevo que abre con una sola tienda física, así que se supone que su canal online factura **una fracción** de un mercado promedio:

- **Mínimo, 2%** (unos USD 195.000 por mes): equivale a la venta online asociada a **una sola tienda** de H&M (ventas por tienda, unos USD 5,8 millones al año con 4.101 tiendas, combinadas con la parte online del 30%).
- **Más probable, 10%** (unos USD 973.000 por mes).
- **Máximo, 25%** (unos USD 2,4 millones por mes).

Además, el canal online arranca al 40% de su nivel y lo alcanza en 6 meses.

## 4. Beneficio

```
Beneficio mensual = facturación online × venta extra por el recomendador × margen de contribución
```

| Supuesto                                                    | Mínimo | Más probable | Máximo | De dónde sale                                                                                                                                                                                    |
| ----------------------------------------------------------- | ------- | ------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tamaño del canal online (fracción de un mercado promedio) | 2%      | 10%           | 25%     | Sección 3                                                                                                                                                                                        |
| Venta online extra por el recomendador                      | 1%      | 3%            | 6%      | Parte de la mejora del piloto A/B (+7,6 puntos en pedidos con una prenda recomendada, (notebook 07) que es venta nueva. El máximo coincide con lo que espera la industria de la personalización |
| Margen de contribución                                     | 35%     | 45%           | 53,4%   | Margen bruto de H&M en 2025 (53,4%) menos los costos variables de vender online (pago y envío)                                                                                                   |

## 5. Resultados

### 5.1 Punto de equilibrio

Con los supuestos más probables (3% de venta extra y 45% de margen), cada USD 100 de facturación online deja USD 1,35 de beneficio gracias al recomendador.

| Punto de equilibrio                                                         | Facturación online necesaria por mes | Como % de un mercado online promedio de H&M |
| --------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------- |
| **Operativo:** el beneficio del mes cubre el costo del mes (USD 650)  | **USD 48.177**                  | 0,5%                                        |
| **Recupero en 12 meses:** cubre además los USD 15.000 del desarrollo | USD 140.769                           | 1,4%                                        |
| **Recupero en 6 meses**                                               | USD 233.362                           | 2,4%                                        |

Incluso el escenario mínimo (unos USD 195.000 por mes) supera el equilibrio operativo; lo que lo deja sin recuperar la inversión en el año es la combinación con poca venta extra (1%) y margen bajo (35%).

### 5.2 Tres escenarios a partir del punto de equilibrio

12 meses de operación:

| Escenario      | Facturación online por mes | Beneficio en 12 meses | Resultado a 12 meses   | ROI a 12 meses  | Se recupera en   |
| -------------- | --------------------------- | --------------------- | ---------------------- | --------------- | ---------------- |
| Pesimista      | USD 194.604                 | USD 6.947             | −USD 15.857           | −70%           | más de 12 meses |
| **Base** | **USD 973.018**       | **USD 133.985** | **+USD 111.180** | **+488%** | **mes 3**  |
| Optimista      | USD 2.432.545               | USD 794.975           | +USD 772.171           | +3.386%         | mes 1            |

### 5.3 Simulación con datos sintéticos (Monte Carlo)

10.000 escenarios en los que se sortean los tres supuestos con una distribución triangular (más peso en el valor más probable).

| Indicador                                                         | Valor                                                |
| ----------------------------------------------------------------- | ---------------------------------------------------- |
| Probabilidad de recuperar toda la inversión en **6 meses** | **98%**                                        |
| Probabilidad de recuperarla en **12 meses**                 | **100%** (sobre 10.000 escenarios, redondeado) |
| ROI a 12 meses: escenario mediano                                 | +621%                                                |
| ROI a 12 meses: 80% central de los escenarios                     | de +231% a +1.266%                                   |
| Mes de recupero mediano                                           | 3                                                    |

El supuesto que más mueve el resultado es el **tamaño del canal online**: más que la venta extra o el margen.

### 5.4 Datos para Power BI

`reports/roi_flujos_powerbi.csv` tiene una fila por escenario y mes (0 a 12), con y sin plataforma: facturación online, beneficio, costos, flujo neto y acumulado. Permite armar en el dashboard la curva del acumulado con un segmentador por escenario y ver en qué mes cruza el cero.

## 6. Sensibilidad: con el costo de la plataforma

Sumando USD 2.500 por mes de la tienda online, la probabilidad de recuperar la inversión baja a **87% en 6 meses** y **96% en 12 meses**.

## 7. Conclusión para el negocio

- **Cuánto invertir:** USD 15.000 una vez y USD 650 por mes; USD 22.805 en el primer año, con el desglose de la sección 2.
- **Cuánto retorna:** en el escenario más probable, el recomendador **se paga en el mes 3** y deja una ganancia de unos USD 111.000 en el primer año.
- **Punto de equilibrio:** el recomendador cubre su costo mensual desde unos USD 48.000 de venta online por mes, y recupera toda la inversión en 6 meses desde unos USD 233.000 por mes.
- **¿Se recupera en 6 meses?** **Sí, en el 98% de los escenarios simulados.**
- **El riesgo está en el volumen del canal online**, no en el costo. Por eso conviene lanzar con el **piloto A/B** (`docs/plan_validacion.md`, sección 7): mide la venta extra real con clientes de H&M Argentina y permite recalcular este ROI antes de escalar.

## 8. Limitaciones

- La facturación de Argentina se estima a partir del promedio de los mercados online de H&M; el valor real dependerá del lanzamiento.
- La venta extra sale de una simulación con datos históricos de otro mercado; el piloto A/B es la forma de medirla.
- Los honorarios usan un valor de referencia para el proyecto; con tarifas de mercado de EE. UU. más altas la inversión sube, pero en el escenario base se seguiría recuperando dentro del año.
- Los precios de nube son on-demand; con contratos de 1 a 3 años bajan entre 27% y 49%.
- No se descuenta el valor del dinero en el tiempo, porque el horizonte es de 12 meses.

## Fuentes

- H&M Group, informe anual y reporte del año fiscal 2025: ventas netas, margen bruto (53,4%), margen operativo (8,1%), 61 mercados online y 4.101 tiendas.
- Participación del canal online de H&M (algo más del 30% de las ventas): resultados del cuarto trimestre de 2025.
- Precios de AWS EC2 m7i.large y m7i.xlarge en us-east-1: calculadoras Holori y DoiT (2026).
- Precio de Shopify Plus (desde USD 2.500 por mes con contrato de un año): página de precios de Shopify, 2026.
- Tipo de cambio SEK/USD: 2026.
