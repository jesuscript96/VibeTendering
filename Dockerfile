# Dockerfile COMPLETO Y CORRECTO
# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación al directorio de trabajo
COPY . .

# ¡ESTA ES LA LÍNEA CRUCIAL Y CORRECTA!
# Usa el formato "exec" (con corchetes) y escribe el puerto 8080 directamente.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
