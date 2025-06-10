# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos y los instala
# Esto se hace por separado para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación al directorio de trabajo
COPY . .

# Expone el puerto que usará la aplicación
# Cloud Run uses the $PORT env variable, EXPOSE is more for documentation/local use
EXPOSE 8080

# Comando para correr la aplicación usando gunicorn
# Cloud Run inyectará la variable de entorno $PORT
CMD sh -c 'exec gunicorn --bind 0.0.0.0:$PORT app:app'
