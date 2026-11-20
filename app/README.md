# Demo (Streamlit)

Pantalla de demostración del recomendador (Sprint 2). Consulta la API de [`api/`](../api/) y muestra, para un cliente de la semana de test (16 al 22/9/2020), las 12 prendas recomendadas con nombre, tipo, grupo y color, en orden de ranking.

Requiere Python 3.11 o superior y la API prendida en el puerto 8000. Desde esta carpeta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Conviene lanzarla desde `app/`: así Streamlit toma el tema visual de `.streamlit/config.toml`. Si la API no está en `http://127.0.0.1:8000`, se indica su dirección con la variable de entorno `LOOKWISE_API_URL`.

Documentación completa (arquitectura, decisiones, pruebas y limitaciones): [`docs/demo_api_streamlit.md`](../docs/demo_api_streamlit.md).
