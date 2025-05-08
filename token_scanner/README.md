# Microservicio Token Scanner para Solana Trading Bot

Este microservicio se encarga de detectar y registrar tokens nuevos en la red Solana, utilizando la API de DexScreener para identificar oportunidades de inversión.

## Características

- Detección automática de tokens nuevos en la blockchain Solana
- Análisis básico de tokens detectados (perfil, booster, liquidez, etc.)
- API REST para consultar tokens y ejecutar escaneos manuales
- Intervalos de escaneo configurables
- Almacenamiento de datos en MongoDB
- Sistema de logging detallado

## Requisitos previos

- Python 3.9+
- pip (gestor de paquetes de Python)
- MongoDB (local o en Docker)
- Variables de entorno configuradas en archivo `.env` o `.env.docker`
- Docker (opcional, para ejecución containerizada)
- Docker Compose (opcional, para entorno de desarrollo completo)

## Estructura del proyecto

```
token_scanner/
├── token_scanner/            # Paquete Python con código fuente
│   ├── __init__.py           # Archivo para marcar el directorio como paquete Python
│   ├── main.py               # Punto de entrada de la aplicación FastAPI
│   ├── models.py             # Modelos de datos
│   ├── scanner.py            # Lógica principal de escaneo de tokens
│   ├── dexscreener_client.py # Cliente para API de DexScreener
│   ├── db.py                 # Capa de acceso a MongoDB
│   ├── config.py             # Configuración y carga de variables de entorno
│   └── logger.py             # Sistema de logging personalizado
├── logs/                     # Directorio para archivos de log
├── setup.py                  # Para instalación como paquete
├── requirements.txt          # Dependencias del proyecto
└── Dockerfile                # Configuración para contenedorización
```

## Métodos de ejecución

### 1. Ejecución local (sin Docker)

Sigue estos pasos para ejecutar el servicio directamente en tu máquina:

#### Configuración del entorno

1. Asegúrate de tener MongoDB ejecutándose localmente (o en Docker):
   ```bash
   # Si usas Docker para MongoDB
   docker-compose up -d mongodb mongo-express
   ```

2. Prepara el entorno de ejecución:
   ```bash
   # Navega al directorio del microservicio
   cd token_scanner
   
   # Instala el paquete en modo desarrollo
   pip install -e .
   ```

#### Ejecución

```bash
# Define la variable de entorno (opcional)
export ENVIRONMENT=local

# Inicia el servicio usando uvicorn
uvicorn token_scanner.main:app --reload --port 8001
```

El servicio estará disponible en http://localhost:8001, y se reiniciará automáticamente cuando detecte cambios en el código.

### 2. Ejecución con Dockerfile

#### Construir la imagen

```bash
# En el directorio token_scanner
docker build -t solana-token-scanner .
```

#### Ejecutar el contenedor

```bash
# Si está ejecutándose en la misma red que MongoDB
docker run --rm -p 8001:8001 \
  --name token-scanner-container \
  --env-file ../.env.docker \
  --network solana-trading-bot_trading_bot_network \
  solana-token-scanner
```

Este comando:
- Expone el puerto 8001 del contenedor al puerto 8001 de tu máquina
- Nombra el contenedor como "token-scanner-container"
- Usa las variables de entorno definidas en `.env.docker`
- Conecta el contenedor a la red de Docker donde se encuentra MongoDB
- Elimina automáticamente el contenedor cuando se detenga (`--rm`)

### 3. Ejecución con Docker Compose

Docker Compose facilita la ejecución de múltiples servicios interconectados, ideal para probar el Token Scanner junto con MongoDB y otros microservicios.

#### Iniciar solo MongoDB y Token Scanner

```bash
# Reconstruir la imagen para asegurar cambios recientes
docker-compose build token-scanner

# Iniciar servicios
docker-compose up -d mongodb token-scanner
```

Este comando inicia los contenedores en modo detached (segundo plano).

#### Verificar logs

```bash
# Ver logs en tiempo real
docker-compose logs -f token-scanner
```

#### Detener servicios

```bash
# Detener solo Token Scanner
docker-compose stop token-scanner

# Detener todos los servicios
docker-compose down
```

## API Endpoints

Accede a la documentación Swagger en http://localhost:8001/docs para ver y probar todos los endpoints disponibles.

### Endpoints principales

- `GET /` - Health check y estado del servicio
- `GET /tokens` - Lista tokens detectados (filtrable por estado)
- `GET /tokens/{address}` - Información detallada de un token específico
- `POST /scan` - Inicia un escaneo manual de tokens nuevos

## Configuración

El Token Scanner se configura mediante variables de entorno, que pueden ser proporcionadas a través de archivos `.env` o `.env.docker`:

```
# MongoDB
MONGO_URI=mongodb://admin:adminpassword@localhost:27017/trading_bot?authSource=admin

# Token Scanner
TOKEN_SCAN_INTERVAL=60  # Intervalo de escaneo en segundos

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Para Docker, la URI de MongoDB debe ser:
```
MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/trading_bot?authSource=admin
```

## Solución de problemas comunes

### Error "No module named 'token_scanner'"

Asegúrate de haber instalado el paquete en modo desarrollo con `pip install -e .` cuando ejecutes localmente.

### Error de conexión a MongoDB

Verifica:
- Que MongoDB esté en ejecución
- Que la URI de MongoDB sea correcta para el entorno (localhost para local, mongodb para Docker)
- Que las credenciales sean correctas

### No se detectan tokens nuevos

- Verifica los logs para errores de comunicación con la API de DexScreener
- Asegúrate que estás conectado a internet y no hay restricciones de red
- Confirma que el cliente DexScreener esté utilizando los endpoints correctos

## Comandos útiles

### Verificar estado de los contenedores

```bash
docker-compose ps
```

### Entrar al contenedor para depuración

```bash
docker-compose exec token-scanner bash
```

### Ver tokens en MongoDB Express

Accede a http://localhost:8081 y navega a la base de datos `trading_bot` y la colección `tokens`.

## Integración con otros microservicios

El Token Scanner está diseñado para integrarse con:
- **RPC Service** - Para acceso optimizado a la blockchain Solana
- **Trading Engine** - Para analizar y operar con los tokens detectados
- **API Gateway** - Para proporcionar una interfaz unificada a todos los servicios