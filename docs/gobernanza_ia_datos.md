# Gobernanza de IA y de datos: recomendador de moda para la tienda online de H&M en Argentina

Lookwise Data Lab · Nov 22, 2026

## Por qué este documento

Junto con el sistema de recomendación, Lookwise Data Lab le entrega a H&M una guía para usarlo de forma responsable. El recomendador es de riesgo bajo, pero decide qué ve cada cliente en la primera vitrina de la marca en Argentina, y lo hace con datos personales. Por eso conviene acordar las reglas antes del lanzamiento, y no después de un problema.

**Qué entendemos por gobernanza.** Es el conjunto de reglas, roles y controles que define qué datos se usan y para qué, quién aprueba los cambios del modelo, cómo se vigila que siga funcionando bien y a quién recurre un cliente si algo le parece mal. La gobernanza de datos cuida la información; la de IA, las decisiones que el sistema toma con ella; y la ética pregunta si esas decisiones son justas para todos los clientes.

**Por qué importa en este caso.**

- **Quien define la métrica define el comportamiento.** Un recomendador que solo busca aciertos tiende a mostrar siempre lo mismo.
- **Un buen promedio puede esconder grupos para los que el sistema funciona peor.** En este proyecto, quienes no compran en las líneas de mujer.
- **La vitrina es la primera impresión de la marca en un mercado nuevo.** Un error de criterio se convierte rápido en un problema de reputación.
- **Los datos de los clientes argentinos están protegidos por ley** (Ley 25.326), y entre quienes compran hay menores de edad.

**Qué le corresponde a cada parte.** H&M, como responsable de la base de datos de sus clientes, responde ante ellos y ante la autoridad de control por la finalidad, el consentimiento, la seguridad y los derechos de acceso, corrección y borrado, aunque el modelo lo construya un tercero. Lookwise Data Lab responde por lo que construye: que el modelo esté documentado, evaluado y sea reproducible, y por advertir los riesgos que encuentra. Las decisiones legales y comerciales son de H\&M; nosotros recomendamos.

El documento recorre primero cada tema con sus riesgos y lo que ya está resuelto. Al final reúne lo que encontramos y nuestras recomendaciones, separadas entre lo que haremos junto con H&M antes del lanzamiento y lo que H&M tendrá que sostener después.

## Alcance y clasificación de riesgo

El sistema es de **riesgo bajo**: ordena 12 prendas por cliente y no decide sobre créditos, empleo ni acceso a servicios. Aun así usa datos de personas y optimiza una métrica, y eso alcanza para fijar criterios explícitos.

- **Qué recomienda y a quién:** 12 prendas por cliente de la tienda online de H&M en Argentina, tanto a clientes nuevos como a clientes con historial. El proyecto empezó enfocado en los clientes nuevos (arranque en frío) y se amplió: a quien nunca compró le muestra lo más vendido de la semana y, desde la primera compra, una vitrina personalizada.
- **Qué optimiza:** Recall@12 es la métrica que decide; MAP@12, Hit Rate@12, Precision@12 y prendas distintas acompañan.
- **Efecto colateral de la métrica:** optimizar aciertos empuja hacia lo más popular. Por eso se mide también la cantidad de prendas distintas que se muestran: lo más vendido enseña las mismas 12 a todos y el modelo final recomienda 4.123 prendas distintas (hipótesis H5).
- **Por qué es riesgo bajo:** el cliente puede ignorar la recomendación y no hay una decisión automática sobre sus derechos. Pasaría a **medio** si el sistema empezara a usar datos de navegación o preferencias declaradas, que es lo que se propone para mejorar el arranque en frío.

## Gobernanza de datos

El modelo usa tres tipos de datos: del cliente, de su comportamiento de compra y del producto. El único dato personal declarado es la edad; lo que más pesa es el historial de compras.

### Qué datos usa el modelo

| Tipo | Variables del modelo | De dónde salen | Qué cuidar |
| --- | --- | --- | --- |
| Del cliente | Edad e indicador de edad no informada | Tabla de clientes | Es el único dato personal declarado. Se usa de tres maneras: como variable directa (importancia casi nula), para armar una de las tres listas de candidatas (lo más vendido en el tramo de edad del cliente) y para calcular las ventas de cada prenda en ese tramo, que es la séptima variable más importante de 17 |
| Del comportamiento de compra | Si ya compró la prenda, puntaje de co-compra, compras previas, días desde la última compra y frecuencia de compra | Historial de transacciones | Es dato personal: describe los hábitos de cada cliente. Es lo que más pesa: la recompra y la co-compra son las dos variables más importantes del modelo |
| Del producto | Ventas de 7 y 30 días, tendencia, días desde la primera venta, precio promedio, ventas en el tramo de edad del cliente y afinidad del cliente con la línea de la prenda | Catálogo y transacciones | No es dato personal, salvo la afinidad, que cruza la prenda con las compras del cliente. El precio está escalado y sin unidad: sirve para comparar prendas, no como precio real |

Fuente: `models/configuracion_modelo.json`, `src/features.py`, `src/modelos.py` y `reports/importancia_variables.csv`.

### Qué datos no se usan

| Dato | Por qué |
| --- | --- |
| `postal_code` | Es un hash sin significado geográfico: 82% de los códigos tiene un solo cliente y uno concentra 2.857 clientes (2,6%), probablemente un valor por defecto. Usarlo podría funcionar como proxy de una zona |
| `club_member_status`, `fashion_news_frequency` | La tabla de clientes es una foto de un solo momento y puede reflejar información posterior a la compra (*data leakage*) |
| `FN`, `Active` | 66% y 67% de vacíos, y el vacío de `Active` no se puede interpretar |
| Texto libre y fotos de las prendas | Los modelos actuales no los usan; las fotos, además, tienen derechos de imagen |

El `customer_id` se usa solo como clave y ya viene anonimizado (hash) en el dataset original.

### Qué cuidar en cada tipo de dato

- **La afinidad sigue el patrón de compra de cada cuenta.** El modelo aprende qué parte de las compras de cada cliente es de Ladieswear, Divided, Menswear, Sport o Baby/Children. Y lo tiene en cuenta: quien compra siempre ropa de mujer va a ver sobre todo ropa de mujer. Pero no es determinista: no deduce el género de la persona, sino que tiene en cuenta todas las líneas que compró. Por ejemplo, una clienta que compra sobre todo ropa de mujer y a veces ropa para sus hijos va a ver sobre todo ropa de mujer y también algo de ropa de chicos, porque las dos líneas están en su historial. Por eso se trata como una preferencia de compra, no como un dato de quién es el cliente. Es una señal legítima, porque sale de lo que el cliente eligió, pero refuerza lo que ya compra (ver Equidad y sesgos).
- **Calidad del catálogo:** 3.873 artículos (3,67%) tienen el grupo de prenda como "Unknown", 416 no tienen descripción y al menos una prenda está mal clasificada en el dataset original (un buzo con capucha registrado como corpiño). El 26,3% del catálogo no tiene ventas en el entrenamiento y no puede recomendarse hasta que se venda (cifra inflada por la muestra del 10%).
- **Calidad de las compras:** integridad completa entre tablas; el 11,96% de las compras son filas repetidas y se conservan, porque no se puede confirmar si son varias unidades, talles o devoluciones. Cada decisión está cuantificada en `reports/tratamiento_datos.csv`.
- **Trazabilidad:** muestra del 10% de clientes elegida con un hash determinístico (reproducible y anidada), corte temporal por fecha, chequeo automático de que las variables no usan información posterior al corte, semillas fijas y versiones de librerías fijadas. El código está versionado en GitHub y cada cambio lo aprueba un integrante distinto del que lo escribió.
- **Seguridad:** la API y la demo son un prototipo sin autenticación, pensado para correr en una computadora o en contenedores locales; los identificadores ya vienen anonimizados. En producción hacen falta acceso con usuario, conexión cifrada y registro de accesos.
- **Minimización:** el sistema no pide ni infiere el género. La edad como variable directa casi no aporta al ranker: conviene evaluar quitarla en el próximo reentrenamiento y medir si cambia el desempeño. El tramo de edad sí aporta, a través de las candidatas y de las ventas por tramo, así que esa parte se mantiene mientras no haya otra señal que la reemplace. Para los clientes nuevos se propone una pregunta opcional al registrarse (la sección de interés), preferible a pedir el género.
- **Menores de edad:** el dataset tiene clientes desde los 16 años, y Divided, la línea juvenil y adolescente, es la segunda en recomendaciones (25,4%). Entre los clientes de 20 años o menos, Divided es el 36,8% de sus compras. El tratamiento de sus datos se desarrolla en el marco normativo.
- **Términos de uso:** los datos son de H&M Group y se publicaron para una competencia de Kaggle, solo para uso no comercial y de investigación académica. El repositorio no los incluye ni los redistribuye. Un sistema real usaría los datos propios de H&M Argentina.

## Equidad y sesgos

La mejora del modelo se mantiene en todos los tramos de edad con datos suficientes, pero es menor a partir de los 55 años y no está demostrada en la línea Baby/Children ni en los clientes nuevos. Se evaluó por grupos y no solo con el promedio, con el piloto A/B simulado sobre la semana de test (conversión: clientes de cada 100 que compran algo de su vitrina).

| Tramo de edad | Clientes | Con el modelo (%) | Con lo más vendido (%) | Mejora (puntos) | IC 95% | ¿Significativa? |
| --- | --- | --- | --- | --- | --- | --- |
| Menos de 25 | 1.100 | 14,80 | 6,84 | +7,96 | 4,35 a 11,57 | Sí |
| 25 a 34 | 1.291 | 15,69 | 7,32 | +8,36 | 4,92 a 11,80 | Sí |
| 35 a 44 | 462 | 14,22 | 6,09 | +8,14 | 2,68 a 13,59 | Sí |
| 45 a 54 | 775 | 12,02 | 4,74 | +7,28 | 3,46 a 11,10 | Sí |
| 55 o más | 527 | 12,13 | 7,06 | +5,07 | 0,08 a 10,07 | Sí, al límite |
| Sin edad | 7 | 20,00 | 0,00 | +20,00 | −15,06 a 55,06 | No concluyente |

La conversión del modelo va de 12,0% a 15,7% según el tramo (3,7 puntos de brecha) y la mejora, de +5,1 a +8,4 puntos. El tramo de 55 o más es el que menos gana y el que hay que mirar primero en el piloto real.

| Línea de producto | Clientes | Con el modelo (%) | Con lo más vendido (%) | Mejora (puntos) | IC 95% | ¿Significativa? |
| --- | --- | --- | --- | --- | --- | --- |
| Ladieswear | 3.213 | 12,14 | 6,95 | +5,19 | 3,18 a 7,21 | Sí |
| Divided | 1.907 | 9,45 | 2,57 | +6,87 | 4,77 a 8,97 | Sí |
| Sport | 310 | 7,06 | 0,00 | +7,06 | 3,21 a 10,91 | Sí |
| Menswear | 288 | 6,58 | 0,00 | +6,58 | 2,64 a 10,52 | Sí |
| Baby/Children | 139 | 2,70 | 0,00 | +2,70 | −0,99 a 6,40 | No concluyente |

Fuente: `reports/piloto_ab_por_edad.csv` y `reports/piloto_ab_por_linea.csv` (notebook 07). Lo más vendido casi no acierta fuera de Ladieswear y Divided: sus 12 prendas son 7 de Ladieswear (mujer) y 5 de Divided (línea juvenil y adolescente), en su mayoría femeninas. Personalizar le da acceso a quienes compran en otras líneas.

**Sesgos que aplican y cómo se atienden**

- **De datos:** Ladieswear es el 37,6% del catálogo y el 64,1% de las compras de la muestra (dashboard, pestaña Categorías), y es la línea más comprada en todos los tramos de edad. Se reportan los resultados por línea y se propone un modelo de contenido para prendas sin ventas.
- **De selección:** los datos solo registran lo que se compró, no lo que cada cliente vio. Solo un piloto A/B real mide el efecto causal.
- **De contexto:** los datos vienen de un mercado del hemisferio norte; la estacionalidad está invertida respecto de Argentina. Se reentrena con datos locales desde el lanzamiento.
- **De objetivo:** se compensa con la métrica de prendas distintas (sección anterior).
- **Círculo de retroalimentación:** el recomendador influye en lo que se compra y después se reentrena con eso. Por eso el piloto mantiene un grupo de control, que queda en 5% fijo aun con el despliegue completo.
- **De refuerzo:** las dos señales que más pesan son la recompra y la co-compra, y la afinidad premia la línea que el cliente ya compra. El modelo tiende a mostrar más de lo mismo: muestra 4.123 prendas distintas en total, pero cada cliente ve sobre todo su propio estilo. Se atiende con el selector de sección, un mínimo de prendas por línea y el monitoreo de diversidad.

**Hasta dónde llega este análisis.** El dataset no tiene género ni otros datos sensibles, así que la equidad se revisó con lo que hay: tramos de edad y líneas de producto. Se midió si la mejora del modelo frente a lo más vendido se mantiene en cada grupo, pero no se aplicaron métricas formales de equidad, como comparar la tasa de aciertos entre grupos con una herramienta especializada (por ejemplo, Fairlearn). Con datos locales y la sección de interés declarada por el cliente, conviene sumarlas al monitoreo.

## Transparencia y explicabilidad

Hoy la explicación está resuelta para H&M y para el equipo técnico, pero no para el cliente final: es la brecha principal de esta sección.

| Audiencia | Qué necesita | Qué hay hoy |
| --- | --- | --- |
| Dirección de H&M | Riesgos, impacto y criterios de aprobación | Resumen ejecutivo; plan de validación con regla de escalado por etapas |
| Negocio (e-commerce, merchandising) | Lógica general, variables que más pesan y cómo usar el resultado | `docs/modelado.md`; señales más importantes: recompra, co-compra y recencia del cliente; la demo muestra qué etapa aplicó el sistema |
| Equipo técnico | Versión de datos y modelo, métricas y pruebas | Notebooks, `models/configuracion_modelo.json` (variables, hiperparámetros, fecha de corte), `reports/`; registro de cada entrenamiento en MLflow |
| Cliente de la tienda | Por qué ve esas prendas y cómo desactivar la personalización | No existe todavía |

**Propuesta para el cliente:** una leyenda corta en las recomendaciones basadas en su historial (por ejemplo, "te mostramos esto porque compraste X"), un aviso de que la vitrina está personalizada y una opción para pasar a ver lo más vendido.

**Límites que hay que decir con honestidad:** el puntaje del ranker ordena las prendas pero no es una probabilidad real de compra, con clientes nuevos el sistema no personaliza (muestra la misma lista a todos), y el Gradient Boosting elegido es menos transparente que una regresión logística. Se eligió porque mejoró el Recall@12 de forma significativa, y la importancia de variables compensa en parte esa pérdida.

## Monitoreo y degradación del modelo

El plan de validación ya define el seguimiento semanal del desempeño; este documento suma tres indicadores de gobernanza (diversidad, brecha por grupo y cambio en los datos de entrada). Una moda con temporadas y un mercado nuevo hacen que el modelo pueda perder precisión sin que nadie lo note.

| Qué se vigila | Indicador | Alerta | Estado |
| --- | --- | --- | --- |
| Desempeño por segmento | Recall@12 y Hit Rate@12 de clientes nuevos y con historial, contra el grupo de control, cada semana | La mejora cae por debajo de la mitad de la observada en el piloto durante dos semanas seguidas: se reentrena | En el plan de validación |
| Lo más vendido | Se recalcula cada semana con decaimiento de 3 días | No aplica | En el plan de validación |
| Cambio de temporada | Calendario de temporadas y picos de demanda (Black Friday, Navidad) | Se reentrena al cambiar de temporada y se revisa cada pico | Temporada en el plan; picos, propuesto aquí |
| Diversidad | Prendas distintas recomendadas por semana | Caída frente a lo observado en el piloto (umbral a definir con H&M) | Propuesto aquí |
| Brecha por grupo | Mejora sobre el control por tramo de edad y por línea | Un tramo o línea deja de tener mejora significativa (umbral a definir con H&M) | Propuesto aquí |
| Datos de entrada | Edad de los clientes, reparto de compras por línea y proporción de prendas sin ventas, comparados cada semana con los datos de entrenamiento | Prueba de cambio de distribución: Kolmogorov-Smirnov para la edad y chi-cuadrado para el reparto por línea (o el índice de estabilidad poblacional, PSI); umbral a definir con H&M | Propuesto aquí |
| Registro de versiones | Parámetros, muestra y métricas de cada entrenamiento en MLflow | Poder volver a una versión anterior | En el pipeline (MLflow) |

**Dos tipos de desfase.** Si cambian los datos de entrada (por ejemplo, el perfil de edad de los clientes argentinos frente al del dataset), hay *data drift*. Si cambia la relación entre lo que se ve y lo que se compra (una tendencia, una temporada), hay *concept drift*. El segundo es el más probable en moda. El data drift se detecta con pruebas estadísticas sobre los datos de entrada; el concept drift, con la caída del desempeño frente al grupo de control.

**Reentrenamiento.** El ranker se reentrena cuando salta la alerta o cambia la temporada; el costo estimado asume un reentrenamiento semanal en la nube, que cubre ambos casos. Como los datos vienen de un mercado del hemisferio norte, desde el lanzamiento conviene reentrenar con datos locales.

**Monitorear no es vigilar:** todos los indicadores son por segmento, no siguen a una persona en particular.

## Supervisión humana y responsables

El modelo solo propone un orden de prendas; las decisiones que cambian el sistema las toman personas. La matriz es una propuesta, porque los roles dependen de la organización de H&M.

| Rol | Responsabilidad | Propuesta de quién |
| --- | --- | --- |
| Responsable de los datos | Calidad, finalidad y conservación de los datos de clientes; atiende pedidos de acceso, corrección y baja | Área de datos y privacidad de H&M Argentina |
| Responsable del modelo | Versiones, reentrenamiento, métricas y alertas | Lookwise Data Lab, en la implementación y en la operación: un científico de datos al 25% de su tiempo, contemplado en los costos. H&M designa una contraparte en su equipo de datos |
| Negocio | Aprueba cada etapa del piloto y define reglas comerciales (stock, exclusiones de prendas) | E-commerce y merchandising de H&M |
| Control independiente | Revisa los resultados y los cambios sin haberlos construido | Un par técnico distinto de quien desarrolla; en el proyecto, cada cambio en GitHub lo aprueba otro integrante |

**Decisiones que requieren revisión humana**

- Pasar a la etapa siguiente del piloto (10%, 20%, 50% y 100% de los clientes) o detenerlo: el plan fija la regla, pero la aprueba una persona.
- Cambiar las variables del modelo, sobre todo si se suma una variable personal o declarada por el cliente.
- Excluir o forzar prendas (stock, devoluciones, productos sensibles).
- Resolver reclamos de clientes sobre lo que se les muestra o sobre sus datos.

## Marco normativo y de referencia

La norma que H&M tiene que cumplir en Argentina para este sistema es la [Ley 25.326 de Protección de los Datos Personales](https://www.argentina.gob.ar/normativa/nacional/ley-25326-2000-64790/actualizacion) y su [decreto reglamentario 1558/2001](https://www.argentina.gob.ar/normativa/nacional/70368/actualizacion). Esta tabla traduce sus artículos al caso; es una lectura del equipo, no asesoramiento legal.

| Artículo | Qué establece | Qué implica para el recomendador |
| --- | --- | --- |
| 4 | Los datos deben ser adecuados, pertinentes y no excesivos para su finalidad, no usarse para fines incompatibles y destruirse cuando dejen de ser necesarios | Solo se usa la edad; no se piden ni infieren otros datos. Hay que fijar cuánto tiempo se conserva el historial de compras |
| 5 | El tratamiento requiere consentimiento libre, expreso e informado, con excepciones como las relaciones contractuales | Definir con asesoría legal la base para usar el historial de compras y para la pregunta de preferencias al registrarse |
| 6 | Antes de recabar datos hay que informar finalidad, destinatarios, si responder es voluntario y las consecuencias | La pregunta de preferencias debe ser opcional y explicar para qué se usa |
| 7 | Nadie puede ser obligado a dar datos sensibles; su tratamiento está muy limitado | El sistema no recolecta datos sensibles |
| 9 | El responsable adopta medidas técnicas y organizativas de seguridad y confidencialidad | La demo es un prototipo sin autenticación, con identificadores anonimizados y un catálogo reducido; en producción hacen falta acceso con usuario, conexión cifrada y registro de accesos |
| 14 a 16 | El titular puede acceder a sus datos (respuesta en 10 días corridos) y pedir su rectificación o supresión (5 días hábiles) | Hace falta un procedimiento para que un cliente consulte, corrija o borre su historial, y para excluirlo del reentrenamiento |

Si el cliente no recibe respuesta, puede denunciar ante la [Agencia de Acceso a la Información Pública](https://www.argentina.gob.ar/aaip/datospersonales/derechos) o iniciar un hábeas data.

**Menores de edad.** La Ley 25.326 no prohíbe tratar datos de menores: hoy no los distingue de los adultos. Se aplican el Código Civil y Comercial, que considera menores a quienes no cumplieron 18 años y adolescentes a partir de los 13, y la Ley 26.061 de protección integral de niñas, niños y adolescentes. Hay proyectos para sumar reglas específicas (por ejemplo, consentimiento válido desde los 16 años y, por debajo, el de padres o tutores), pero no son ley. Como Divided está dirigida a adolescentes, recomendamos un estándar de cuidado mayor: pedirles solo los datos necesarios, no usar su edad para segmentar más allá de la vitrina y definir con el área legal cómo se obtiene su consentimiento.

**Inteligencia artificial.** No encontramos una ley nacional específica de IA vigente; en 2026 hay proyectos presentados en el Congreso (por ejemplo, [uno de presupuestos mínimos para el desarrollo de la IA](https://rest.hcdn.gob.ar/web/proyectos/289500/adjuntos/104100)). Conviene confirmar el estado antes de la entrega final y antes de cualquier lanzamiento.

**Marcos de referencia internacionales**, usados como guía y sin certificación:

- **OECD, principios de IA:** el porqué (transparencia, equidad, responsabilidad).
- **NIST AI RMF:** cómo evaluar y gestionar los riesgos del sistema.
- **ISO/IEC 42001:** cómo operar y auditar un sistema de gestión de IA (política, controles y mejora continua).

## Resumen: qué está resuelto y qué falta antes del lanzamiento

De diez riesgos identificados, cuatro tienen medida y evidencia en el repositorio, dos están diseñados o planificados sin ejecutar y cuatro quedan pendientes para H&M.

| Riesgo | Medida | Evidencia en el repositorio | Estado |
| --- | --- | --- | --- |
| Datos personales | Solo se usa la edad; sin código postal ni datos del club | `docs/controles_integridad.md`, `models/configuracion_modelo.json` | Resuelto |
| Fuga de información | Corte temporal por fecha y chequeo de variables | `src/features.py` (`chequeo_sin_leakage`), `docs/plan_validacion.md` | Resuelto |
| Sesgo por edad y línea | Evaluación por grupos con intervalos de confianza | `reports/piloto_ab_por_edad.csv`, `reports/piloto_ab_por_linea.csv` | Resuelto en simulación; falta el piloto real |
| Popularidad y visibilidad del catálogo | Métrica de prendas distintas (H5) | `docs/modelado.md` | Resuelto |
| Efecto causal desconocido | Piloto A/B con regla de escalado y control fijo de 5% | `docs/plan_validacion.md`, `notebooks/07_piloto_ab_simulado.ipynb` | Diseñado, sin ejecutar |
| Seguimiento del modelo | Indicadores semanales y alertas | `docs/plan_validacion.md`, sección 8 | En el plan y en MLflow |
| Explicación al cliente | Leyenda de motivo, aviso de personalización y opción de salida | Propuesta en este documento | Pendiente |
| Base legal y conservación | Consentimiento, finalidad, plazo de conservación y derechos del titular (Ley 25.326) | Propuesta en este documento | Pendiente con asesoría legal |
| Clientes menores de 18 años | Revisar el tratamiento de datos de menores (el dataset incluye desde 16 años) | Propuesta en este documento | Pendiente con asesoría legal |
| Estacionalidad invertida | Reentrenar con datos locales desde el lanzamiento | `docs/plan_validacion.md`, sección 9 | Pendiente de datos locales |

## Lo que encontramos

El sistema funciona con los datos disponibles, pero esos datos describen poco a los clientes y vienen de otro mercado.

**1. Casi no hay datos de los clientes.** La tabla de clientes tiene siete columnas: un identificador anonimizado y seis datos (edad, código postal anonimizado, estado en el club, frecuencia de newsletter y dos indicadores de comunicación). Solo la edad entra al modelo, y pesa poco frente al historial, así que todo lo que el sistema sabe de una persona sale de lo que ya compró. Por eso con clientes nuevos no personaliza y empata con lo más vendido.

**2. No se sabe el género de quien compra, y la vitrina inicial es casi toda de mujer.** Las 12 prendas de lo más vendido, que es lo que ve todo cliente nuevo, son 7 de Ladieswear (la línea de mujer) y 5 de Divided (la línea juvenil y adolescente): vestidos, jeans *mom* y suéteres, ninguna de Menswear, Sport ni Baby/Children. En las listas que el modelo armó para los 4.162 clientes de la semana de test, 95,2% de las prendas son de esas dos líneas (69,8% y 25,4%), y Menswear baja de 4,4% de las compras de la muestra a 1,4% de las recomendaciones: el modelo acentúa la concentración que ya había. Un cliente varón, o quien busca ropa para chicos, ve una vitrina pensada para otro público; en el piloto simulado, lo más vendido acierta 0% en Menswear, Sport y Baby/Children. Además, Divided está dirigida a adolescentes y el dataset tiene clientes desde los 16 años: hay menores entre quienes compran y reciben recomendaciones.

**3. La cultura de compra de Argentina es distinta.** Los datos vienen de un mercado que el dataset no revela, con estacionalidad del hemisferio norte. Además cambian el calendario comercial (por ejemplo, Hot Sale y Cyber Monday), el clima, los talles, el poder adquisitivo y la forma de comprar. Estas diferencias son ejemplos del equipo, no se midieron con estos datos.

**4. Los datos son de hace seis años y abarcan la pandemia.** Van de septiembre de 2018 a septiembre de 2020, y el lanzamiento sería en 2027: las tendencias, los precios y los hábitos de compra online cambiaron desde entonces. Además, marzo a mayo de 2020 (14,4% de las compras de la muestra) coinciden con el cierre de tiendas por la pandemia: en abril no hay ventas en tienda y la venta online tiene su pico. Esos meses se conservaron en el entrenamiento, porque quitarlos eliminaba datos recientes, y la semana de prueba (septiembre de 2020) no cae en ellos; aun así, el modelo aprendió en parte de un comportamiento atípico. Por eso los resultados validan el método, no las prendas concretas que recomendaría hoy, y el modelo debe reentrenarse con datos de H&M Argentina desde el lanzamiento.

**Cómo leer las cifras de este proyecto:** son una evaluación *offline* sobre el 10% de los clientes de otro mercado. Sirven para elegir el modelo y justificar un piloto, no para prometer un resultado.

## Nuestras recomendaciones

Separamos lo que proponemos hacer junto con H&M antes del lanzamiento de lo que H&M tendrá que sostener una vez que el sistema esté funcionando.

### Antes del lanzamiento: lo que haremos con H&M

Estas decisiones no las puede tomar la consultora sola: necesitamos validarlas con las áreas de H&M que tienen el conocimiento o la responsabilidad.

| Tema | Qué proponemos | Con quién de H&M |
| --- | --- | --- |
| Vitrina para clientes nuevos | Sumar un selector de sección visible (mujer, hombre, niños, todo), armar lo más vendido por línea y fijar un mínimo de prendas de cada línea | E-commerce y merchandising de H&M Argentina |
| Datos personales y consentimiento | Revisar la base legal para usar el historial de compras, el texto de la pregunta opcional de preferencias y el plazo de conservación de los datos | Área legal y de protección de datos |
| Clientes menores de 18 años | Definir cómo se tratan sus datos y si se personaliza para ellos; revisar si conviene que el piloto empiece por Divided | Área legal y de protección de datos, junto con e-commerce |
| Mercado argentino | Contrastar calendario comercial, temporadas, talles y precios con los supuestos del modelo | Marketing y equipo comercial local |
| Explicación al cliente | Diseñar la leyenda de motivo ("te mostramos esto porque compraste X"), el aviso de personalización y la opción de salida | Producto digital y UX |
| Monitoreo y responsables | Fijar los umbrales de alerta y nombrar al responsable de los datos, al del modelo y al control independiente | Tecnología y datos, y dirección de e-commerce |
| Piloto A/B | Acordar quién aprueba cada etapa y en qué casos se detiene | Dirección de e-commerce |
| Datos personales en el modelo | Evaluar quitar la edad como variable directa del ranker (su importancia es casi nula) y medir si cambia el desempeño; el tramo de edad se mantiene porque aporta a las candidatas | Tecnología y datos |

### Después del lanzamiento: lo que H&M tendrá que sostener

- **Responsables con nombre y apellido:** quien responde por los datos, quien responde por el modelo y un control independiente, distinto de quien lo desarrolla.
- **Derechos de los clientes:** un procedimiento para responder pedidos de acceso (10 días corridos) y de corrección o borrado (5 días hábiles), y para excluir del reentrenamiento a quien lo pida.
- **Pedir solo lo necesario:** señales voluntarias y explicadas; no inferir el género ni recolectar datos "por si acaso".
- **Datos locales:** reentrenar con compras argentinas y revisar si las conclusiones de este proyecto se mantienen.
- **Monitoreo por grupo:** mirar edad, línea de producto y clientes nuevos, no solo el promedio, y revisar los picos de demanda (Hot Sale, Cyber Monday, Navidad).
- **Grupo de control fijo de 5%:** permite medir el efecto real del sistema y cortar el círculo de retroalimentación.
- **Regulación y auditoría:** seguir los proyectos de ley de IA y la actualización de la Ley 25.326, y que el control independiente revise el sistema con un marco de referencia (NIST AI RMF o ISO/IEC 42001) cada vez que cambien el modelo, los datos que usa o la normativa. Esta revisión no reemplaza el monitoreo semanal del desempeño: mira si las reglas, los roles y los derechos de los clientes se siguen cumpliendo.

## Fuentes

- [Ley 25.326 de Protección de los Datos Personales](https://www.argentina.gob.ar/normativa/nacional/ley-25326-2000-64790/actualizacion) y [decreto reglamentario 1558/2001](https://www.argentina.gob.ar/normativa/nacional/70368/actualizacion), consultados el 22/11/2026.
- [Derechos del titular de datos personales (AAIP)](https://www.argentina.gob.ar/aaip/datospersonales/derechos).
- [Reglas de la competencia H&M Personalized Fashion Recommendations (Kaggle)](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations), origen y condiciones de uso de los datos.
- Evidencia del proyecto: repositorio de Lookwise Data Lab (`docs/`, `models/`, `notebooks/`, `reports/`).
- Marcos de referencia: OECD, NIST AI RMF, ISO/IEC 42001.
