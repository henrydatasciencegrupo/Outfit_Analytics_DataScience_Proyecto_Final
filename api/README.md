# API de recomendaciones (FastAPI)

Recibe un cliente de la semana de test y devuelve las 12 prendas recomendadas: la lista fija de populares si es un cliente nuevo y el ranker (Gradient Boosting) si tiene historial. Lee el modelo y su configuración de [`models/`](../models/), por lo que esta carpeta tiene que estar junto a esa.

Requiere Python 3.11 o superior (probada con 3.13). Desde esta carpeta:

```bash
pip install -r requirements.txt
uvicorn lookwise_api:app
```

| Ruta | Para qué |
|---|---|
| `GET /salud` | Confirma que la API está encendida |
| `GET /recomendar?cliente=<id>` | Devuelve `{cliente, etapa, prendas}` con 12 códigos de prenda |
| `GET /docs` | Documentación interactiva (Swagger) |

Los 7 tests automáticos se corren con `python -m pytest` desde esta carpeta. Las versiones de las librerías están fijadas en `requirements.txt` (la clave es `scikit-learn==1.9.1`, la versión con que se guardó el modelo).

Documentación completa (contrato, decisiones, pruebas y limitaciones): [`docs/demo_api_streamlit.md`](../docs/demo_api_streamlit.md).
