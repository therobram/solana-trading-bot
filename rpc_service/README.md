# Microservicio RPC para Solana Trading Bot

Este microservicio gestiona la conexión con distintos proveedores de RPC de Solana, seleccionando automáticamente el nodo más rápido disponible para garantizar respuestas óptimas y alta disponibilidad.

## Características

- Selección inteligente del RPC más rápido entre múltiples proveedores
- Monitorización de latencia y disponibilidad de nodos
- API REST para integración con otros microservicios
- Sistema de cacheo para evitar consultas repetidas
- Manejo de errores y reintentos automáticos
- Logging detallado con rotación de archivos

## Requisitos previos

- Python 3.9+
- pip (gestor de paquetes de Python)
- Docker (opcional, para ejecución containerizada)
- Docker Compose (opcional, para entorno de desarrollo completo)
- Variables de entorno configuradas en archivo `.env`

## Estructura del proyecto

```
rpc_service/
├── rpc_service/            # Paquete Python con código fuente
│   ├── __init__.py         # Archivo para marcar el directorio como paquete Python
│   ├── main.py             # Punto de entrada de la aplicación FastAPI
│   ├── rpc_manager.py      # Lógica de gestión de nodos RPC
│   ├── tx_sender.py        # Funcionalidad para enviar transacciones
│   ├── config.py           # Configuración y carga de variables de entorno
│   └── logger.py           # Sistema de logging personalizado
├── logs/                   # Directorio para archivos de log (creado automáticamente)
├── setup.py                # Hace instalable el paquete
├── requirements.txt        # Dependencias del proyecto
└── Dockerfile              # Configuración para contenedorización
```

## Configuración del entorno

1. Crea un archivo `.env` en la raíz del proyecto principal o en el directorio `rpc_service/` con las siguientes variables:

```env
# URLs de proveedores RPC (debes tener al menos uno)
RPC_SOLANA=https://api.mainnet-beta.solana.com
RPC_QUIKNODE=https://tu-endpoint-de-quiknode
RPC_HELIUS=https://tu-endpoint-de-helius

# Configuración opcional
RPC_CACHE_TTL=60        # Tiempo de vida en caché (segundos)
RPC_TIMEOUT=10          # Timeout para peticiones RPC (segundos)
RPC_RETRY_ATTEMPTS=3    # Número de reintentos si falla la petición
LOG_LEVEL=INFO          # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# MongoDB (para Docker Compose)
MONGO_USER=admin
MONGO_PASSWORD=adminpassword
```

## Instalación y ejecución local (sin Docker)

Sigue estos pasos para ejecutar el servicio localmente durante el desarrollo:

1. Navega al directorio del microservicio:
   ```bash
   cd rpc_service
   ```

2. Instala el paquete en modo desarrollo:
   ```bash
   pip install -e .
   ```

3. Ejecuta la aplicación con uvicorn:
   ```bash
   uvicorn rpc_service.main:app --reload
   ```

El servidor estará disponible en `http://localhost:8000`. La bandera `--reload` permite que la aplicación se reinicie automáticamente cuando detecta cambios en el código.

## Ejecución con Docker

Para ejecutar el servicio en un contenedor Docker:

1. Construye la imagen Docker:
   ```bash
   # Desde el directorio rpc_service
   docker build -t solana-rpc-service .
   ```

2. Ejecuta el contenedor:
   ```bash
   # Si el archivo .env está un nivel hacia arriba (en la raíz del proyecto)
   docker run --rm -p 8000:8000 --env-file ../.env --name rpc-service-dev solana-rpc-service
   
   # Si el archivo .env está en el mismo directorio
   docker run --rm -p 8000:8000 --env-file .env --name rpc-service-dev solana-rpc-service
   ```

Los logs del servicio se mostrarán en la consola, y el servidor estará disponible en `http://localhost:8000`.

## Ejecución con Docker Compose

Para ejecutar el microservicio junto con MongoDB y otros servicios, puedes utilizar Docker Compose. Este método es ideal para desarrollo y pruebas ya que configura automáticamente la red y dependencias entre servicios.

### Archivo docker-compose.yml

Coloca este archivo en la raíz del proyecto:

```yaml
version: '3.8'

services:
  # MongoDB
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER:-admin}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD:-adminpassword}
    networks:
      - trading_bot_network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped

  # Mongo Express (UI para MongoDB)
  mongo-express:
    image: mongo-express
    ports:
      - "8081:8081"
    environment:
      - ME_CONFIG_MONGODB_ADMINUSERNAME=${MONGO_USER:-admin}
      - ME_CONFIG_MONGODB_ADMINPASSWORD=${MONGO_PASSWORD:-adminpassword}
      - ME_CONFIG_MONGODB_SERVER=mongodb
      - ME_CONFIG_BASICAUTH_USERNAME=${MONGO_USER:-admin}
      - ME_CONFIG_BASICAUTH_PASSWORD=${MONGO_PASSWORD:-adminpassword}
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - trading_bot_network
    restart: unless-stopped

  # RPC Service
  rpc-service:
    build: ./rpc_service
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - MONGO_URI=mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-adminpassword}@mongodb:27017/trading_bot?authSource=admin
    volumes:
      - ./logs:/app/logs
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - trading_bot_network
    restart: unless-stopped

networks:
  trading_bot_network:
    driver: bridge

volumes:
  mongodb_data:
```

### Pasos para ejecutar con Docker Compose

1. **Preparación**: Asegúrate de tener el archivo `.env` en la raíz del proyecto con todas las variables necesarias.

2. **Crear el directorio de logs**:
   ```bash
   mkdir -p logs
   ```

3. **Construir y levantar todos los servicios**:
   ```bash
   # Desde la raíz del proyecto
   docker-compose build
   docker-compose up -d
   ```

4. **Para solo levantar el RPC Service con MongoDB**:
   ```bash
   docker-compose up -d mongodb mongo-express rpc-service
   ```

5. **Verificar que los servicios están funcionando**:
   ```bash
   # Ver el estado de todos los servicios
   docker-compose ps
   
   # Ver logs del RPC Service
   docker-compose logs rpc-service
   
   # Ver logs en tiempo real
   docker-compose logs -f
   ```

### Acceso a los servicios

- **RPC Service API**: http://localhost:8000
- **Mongo Express (UI para MongoDB)**: http://localhost:8081
  - Usuario: el valor de MONGO_USER (por defecto "admin")
  - Contraseña: el valor de MONGO_PASSWORD (por defecto "adminpassword")

### Detener los servicios

```bash
# Detener todos los servicios pero mantener los volúmenes
docker-compose down

# Detener y eliminar volúmenes (perderás datos de MongoDB)
docker-compose down -v
```

## Endpoints API

### `GET /rpc`

Devuelve la URL del RPC más rápido disponible en ese momento.

**Respuesta de ejemplo:**
```json
{
  "rpc": "https://api.mainnet-beta.solana.com"
}
```

### `GET /rpc/status`

Devuelve el estado de todos los RPC configurados con sus latencias.

**Respuesta de ejemplo:**
```json
[
  {
    "rpc": "https://api.mainnet-beta.solana.com",
    "latency_ms": 234.56,
    "healthy": true
  },
  {
    "rpc": "https://other-node.solana.com",
    "latency_ms": null,
    "healthy": false
  }
]
```

### `POST /send-tx`

Envía una transacción firmada a la blockchain de Solana.

**Cuerpo de la petición:**
```json
{
  "tx": "base58_encoded_transaction_here"
}
```

**Respuesta de ejemplo:**
```json
{
  "signature": "transaction_signature_here"
}
```

## Solución de problemas comunes

### Error "No se encontraron URLs de RPC"

Verifica que tu archivo `.env` contiene al menos una variable con el prefijo `RPC_` (excepto las de configuración como `RPC_CACHE_TTL`). Asegúrate también de que el archivo `.env` está siendo cargado correctamente.

### Error al crear archivos de log

El sistema intentará crear automáticamente un directorio `logs/` si no existe. Si encuentras errores relacionados con permisos, verifica que el usuario que ejecuta la aplicación tiene permisos de escritura en el directorio.

### MongoDB o Mongo Express no funcionan

Si tienes problemas accediendo a MongoDB o Mongo Express:

1. Verifica que las credenciales en `.env` coinciden con las que estás usando para acceder
2. Revisa los logs con `docker-compose logs mongodb` o `docker-compose logs mongo-express`
3. Asegúrate de que los servicios están funcionando con `docker-compose ps`
4. Si cambias las credenciales en `.env`, debes reiniciar los servicios con `docker-compose down` y `docker-compose up -d`

### Comportamiento inconsistente en Docker vs Local

Si observas diferencias entre la ejecución en Docker y localmente, verifica:
1. Que estás usando el mismo archivo `.env` en ambos entornos
2. Que el Dockerfile está actualizado con los últimos cambios
3. Que has reconstruido la imagen Docker después de realizar cambios (`docker build -t solana-rpc-service .`)

## Monitorización y logs

Los logs se escriben tanto en la consola (con colores para distinguir los niveles) como en archivos en el directorio `logs/`. Los archivos de log siguen el formato `nombre-componente_YYYYMMDD.log`.

Para cambiar el nivel de verbosidad, ajusta la variable `LOG_LEVEL` en el archivo `.env`.