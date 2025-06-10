# Dockerfile COMPLETO, VERIFICADO Y CORRECTO
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# USA EL PUERTO 8080 DIRECTAMENTE. NO USES $PORT.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "app:app"]
