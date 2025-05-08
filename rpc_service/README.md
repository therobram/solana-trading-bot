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

### Comportamiento inconsistente en Docker vs Local

Si observas diferencias entre la ejecución en Docker y localmente, verifica:
1. Que estás usando el mismo archivo `.env` en ambos entornos
2. Que el Dockerfile está actualizado con los últimos cambios
3. Que has reconstruido la imagen Docker después de realizar cambios (`docker build -t solana-rpc-service .`)

## Monitorización y logs

Los logs se escriben tanto en la consola (con colores para distinguir los niveles) como en archivos en el directorio `logs/`. Los archivos de log siguen el formato `nombre-componente_YYYYMMDD.log`.

Para cambiar el nivel de verbosidad, ajusta la variable `LOG_LEVEL` en el archivo `.env`.