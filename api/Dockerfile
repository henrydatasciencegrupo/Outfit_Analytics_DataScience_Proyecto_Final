
FROM python:3.13-slim

WORKDIR /proyecto

COPY api/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY api/ /proyecto/api/
COPY models/ /proyecto/models/

WORKDIR /proyecto/api

EXPOSE 8000

CMD ["uvicorn", "lookwise_api:app", "--host", "0.0.0.0", "--port", "8000"]