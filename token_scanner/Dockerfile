FROM python:3.11-slim

WORKDIR /app

# Copiar requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Instalar el paquete en modo editable
RUN pip install -e .

# Crear directorio para logs
RUN mkdir -p logs

# Establecer variable de entorno
ENV ENVIRONMENT=docker

# Exponer puerto
EXPOSE 8001

# Comando de inicio
CMD ["uvicorn", "token_scanner.main:app", "--host", "0.0.0.0", "--port", "8001"]