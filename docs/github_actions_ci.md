# Integración continua con GitHub Actions

## Objetivo

Se implementó un flujo de integración continua (CI)
para validar automáticamente componentes del proyecto
Lookwise Data Lab.

## Herramientas

- GitHub Actions
- Python 3.13
- pytest
- FastAPI
- Streamlit

## Archivo de configuración

.github/workflows/ci.yml

## Eventos que ejecutan el workflow

- Push a main y rama-nacho.
- Pull request hacia main.
- Ejecución manual desde GitHub Actions.

## Validaciones automáticas

### FastAPI

1. Instalación de dependencias.
2. Verificación de archivos del modelo y datos demo.
3. Validación de sintaxis Python.
4. Ejecución de siete pruebas automatizadas.

### Streamlit

1. Validación de sintaxis Python.
2. Verificación de archivos necesarios para la demo.

## Ejecutar las pruebas localmente

Desde la raíz del repositorio:

    python -m pip install -r api/requirements.txt
    python -m compileall -q api src
    python -m py_compile app/app.py
    cd api
    python -m pytest test_lookwise_api.py -v

## Limitaciones

Este workflow no reentrena el modelo ni ejecuta
la aplicación Streamlit completa.

El entrenamiento depende de los datos de modelado,
que no se incluyen en el repositorio.

La validación actual utiliza el modelo entrenado
y los datos reducidos de la demo.

## Próximas mejoras

- Validación de contenedores Docker.
- Pruebas de integración API-Streamlit.
- Seguimiento de experimentos con MLflow.