FROM python:3.11-slim

WORKDIR /app

# Copiar todo el paquete del microservicio
COPY . .

# Instalar el microservicio como paquete
RUN pip install -e .
RUN pip install -r requirements.txt

RUN mkdir -p logs

# Documentar que el servicio utiliza el puerto 8000
EXPOSE 8000

# Ejecutar la aplicación
CMD ["uvicorn", "rpc_service.main:app", "--host", "0.0.0.0", "--port", "8000"]