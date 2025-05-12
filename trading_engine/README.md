# Trading Engine para DEX en Solana

![Solana](https://img.shields.io/badge/Solana-362bd9?style=for-the-badge&logo=solana&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

Motor de trading automatizado para DEX en la blockchain de Solana, que implementa estrategias de inversión basadas en criterios configurables como perfil, booster, volumen y pools de liquidez.

## Características

- Implementación como microservicio con FastAPI
- Evaluación de tokens basada en múltiples criterios
- Ejecución automática de órdenes de compra
- Seguimiento de posiciones y venta automática cuando un token alcanza un valor predefinido (ej. x3)
- Modo simulación para pruebas sin riesgo
- Modo real para operaciones en mainnet
- Integración con Jupiter DEX para las mejores rutas de swap

## Prerrequisitos

- Python 3.9+
- Docker y Docker Compose (opcional)
- MongoDB
- Wallet de Solana con fondos para operaciones reales
- RPC de Solana (para modo real)

## Estructura del Proyecto

```
trading_engine/
├── trading_engine/           # Paquete Python
│   ├── __init__.py           # Inicialización del paquete
│   ├── config.py             # Configuración y variables de entorno
│   ├── db.py                 # Capa de acceso a MongoDB
│   ├── jupiter_client.py     # Cliente para interactuar con Jupiter DEX
│   ├── logger.py             # Sistema de logging personalizado
│   ├── main.py               # Aplicación FastAPI
│   ├── models.py             # Modelos de datos
│   ├── position_tracker.py   # Seguimiento de posiciones abiertas
│   ├── solana_wrapper.py     # Wrapper para interacciones con Solana
│   ├── token_evaluator.py    # Evaluación de tokens
│   └── trading_engine.py     # Motor principal de trading
├── Dockerfile                # Configuración para contenedorización
├── docker-entrypoint.sh      # Script de entrada para Docker
├── solana-install.sh         # Instalador local de Solana
├── requirements.txt          # Dependencias Python
└── setup.py                  # Configuración de instalación
```

## Instalación y Configuración

### 1. Preparación del Entorno Local

Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/solana-trading-bot.git
cd solana-trading-bot/trading_engine
```

Crea un entorno virtual e instala las dependencias:

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -e .
```

### 2. Configuración de Variables de Entorno

Crea un archivo `.env` en el directorio raíz:

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017/trading_bot

# Jupiter API
JUPITER_API=https://quote-api.jup.ag

# Wallet (incluye los corchetes)
PRIVATE_KEY_JSON=[231, 127, 214, 105, 61, 217, 17, 124, 177, 9, 36, 20, 98, 149, 236, 22, 58, 232, 30, 140, 34, 120, 41, 63, 63, 176, 39, 58, 129, 51, 1, 37]

# RPC Endpoints
RPC_SOLANA=https://api.mainnet-beta.solana.com

# Trading Engine Config
MAX_DAILY_INVESTMENT=50
POSITION_TRACKING_INTERVAL=60

# Logging
LOG_LEVEL=INFO

# Modo de ejecución
SIMULATION_MODE=true
```

## Ejecución Local

Para ejecutar el microservicio localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
uvicorn trading_engine.main:app --reload --port 8002
```

Accede a la documentación Swagger en: http://localhost:8002/docs

## Ejecución con Docker

### Preparación para Docker

> **IMPORTANTE**: El paso más crítico es descargar el instalador de Solana localmente antes de construir la imagen Docker. Esto evita problemas de conectividad durante la construcción.

1. **Descarga el instalador de Solana localmente**:

```bash
curl -sSfL https://release.anza.xyz/stable/install -o solana-install.sh
chmod +x solana-install.sh
```

2. **Crea el archivo docker-entrypoint.sh**:

```bash
cat > docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Imprimir información sobre el modo de ejecución
echo "Iniciando Trading Engine en modo: $(if [ "$SIMULATION_MODE" = "true" ]; then echo "SIMULACIÓN"; else echo "REAL"; fi)"

# Si estamos en modo real, verificar conexión con Solana
if [ "$SIMULATION_MODE" != "true" ]; then
    echo "Verificando conexión con Solana..."
    # Asegurarse de que solana está en el PATH
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    # Verificar instalación
    which solana || echo "Solana no está en el PATH"
    solana --version || echo "Error al ejecutar solana --version"
    # Configurar RPC
    solana config set --url $RPC_SOLANA || echo "Error configurando URL de RPC Solana"
    solana cluster-version || echo "No se pudo conectar a Solana RPC, pero continuaremos de todos modos"
fi

# Iniciar la aplicación
exec uvicorn trading_engine.main:app --host 0.0.0.0 --port 8002 --reload
EOF

chmod +x docker-entrypoint.sh
```

3. **Crea el Dockerfile**:

```bash
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias (actualizado según la documentación oficial)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libudev-dev \
    libssl-dev \
    llvm \
    libclang-dev \
    protobuf-compiler \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio para logs
RUN mkdir -p logs

# Instalar Rust (necesario para algunos paquetes de Solana)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env"
ENV PATH="/root/.cargo/bin:${PATH}"

# Copiar el instalador de Solana previamente descargado
COPY solana-install.sh .

# Instalar Solana CLI usando el instalador local
RUN chmod +x solana-install.sh && \
    ./solana-install.sh && \
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH" && \
    echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc

# Configurar PATH para los siguientes comandos
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"

# Verificar instalación de Solana (con manejo de errores)
RUN ls -la /root/.local/share/solana/install/active_release/bin/ || echo "Directorio no encontrado" && \
    which solana || echo "Solana no está en el PATH" && \
    solana --version || echo "Error al ejecutar solana --version"

# Copiar requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de entrada
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Copiar código fuente
COPY . .

# Instalar el paquete en modo desarrollo
RUN pip install -e .

# Variables de entorno configurables en tiempo de ejecución
ENV ENVIRONMENT=docker
ENV SIMULATION_MODE=false

# Exponer puerto
EXPOSE 8002

# Comando de inicio
ENTRYPOINT ["/docker-entrypoint.sh"]
EOF
```

4. **Crea un archivo `.env.docker` en el directorio padre** (un nivel arriba del directorio trading_engine):

```bash
# Ubicación: ../env.docker
# MongoDB
MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/trading_bot?authSource=admin

# Jupiter API
JUPITER_API=https://quote-api.jup.ag

# Wallet (incluye los corchetes)
PRIVATE_KEY_JSON=[231, 127, 214, 105, 61, 217, 17, 124, 177, 9, 36, 20, 98, 149, 236, 22, 58, 232, 30, 140, 34, 120, 41, 63, 63, 176, 39, 58, 129, 51, 1, 37]

# RPC Endpoints
RPC_SOLANA=https://api.mainnet-beta.solana.com

# Trading Engine Config
MAX_DAILY_INVESTMENT=50
POSITION_TRACKING_INTERVAL=60

# Logging
LOG_LEVEL=INFO

# Modo de ejecución (Puedes sobreescribir esto con -e al ejecutar el contenedor)
SIMULATION_MODE=false
```

### Construir y Ejecutar la Imagen Docker

1. **Construir la imagen**:

```bash
docker build -t solana-trading-engine .
```

2. **Ejecutar el contenedor en modo simulación**:

```bash
docker run --rm -p 8002:8002 \
  --name trading-engine-simulation \
  --env-file ../.env.docker \
  -e SIMULATION_MODE=true \
  solana-trading-engine
```

3. **Ejecutar el contenedor en modo real**:

```bash
docker run --rm -p 8002:8002 \
  --name trading-engine-real \
  --env-file ../.env.docker \
  --network solana-trading-bot_trading_bot_network \
  solana-trading-engine
```

> **Nota**: Asegúrate de que `solana-trading-bot_trading_bot_network` exista o crea la red manualmente con `docker network create solana-trading-bot_trading_bot_network`.

## Ejecución con Docker Compose

El Trading Engine está diseñado para integrarse perfectamente en una arquitectura de microservicios completa para el bot de trading. Puedes desplegarlo como parte de un sistema más amplio que incluye RPC Service, Token Scanner y API Gateway.

### Preparación para Docker Compose

Antes de ejecutar el servicio con Docker Compose, asegúrate de tener toda la estructura necesaria:

1. **Estructura de directorios recomendada**:

```
solana-trading-bot/
├── api_gateway/
├── rpc_service/
├── token_scanner/
├── trading_engine/
│   ├── trading_engine/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── ... (resto de archivos)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── solana-install.sh
│   ├── requirements.txt
│   └── setup.py
├── docker-compose.yml
└── .env.docker
```

2. **Archivos necesarios para el Trading Engine**:

   - En el directorio trading_engine, asegúrate de descargar el instalador de Solana:
   ```bash
   cd trading_engine
   curl -sSfL https://release.anza.xyz/stable/install -o solana-install.sh
   chmod +x solana-install.sh
   ```

   - Crea el script de entrada `docker-entrypoint.sh` en el mismo directorio:
   ```bash
   cat > docker-entrypoint.sh << 'EOF'
   #!/bin/bash
   set -e

   # Imprimir información sobre el modo de ejecución
   echo "Iniciando Trading Engine en modo: $(if [ "$SIMULATION_MODE" = "true" ]; then echo "SIMULACIÓN"; else echo "REAL"; fi)"

   # Si estamos en modo real, verificar conexión con Solana
   if [ "$SIMULATION_MODE" != "true" ]; then
       echo "Verificando conexión con Solana..."
       # Asegurarse de que solana está en el PATH
       export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
       # Verificar instalación
       which solana || echo "Solana no está en el PATH"
       solana --version || echo "Error al ejecutar solana --version"
       # Configurar RPC
       solana config set --url $RPC_SOLANA || echo "Error configurando URL de RPC Solana"
       solana cluster-version || echo "No se pudo conectar a Solana RPC, pero continuaremos de todos modos"
   fi

   # Iniciar la aplicación
   exec uvicorn trading_engine.main:app --host 0.0.0.0 --port 8002 --reload
   EOF

   chmod +x docker-entrypoint.sh
   ```

3. **Configuración de variables de entorno**:
   
   Crea o actualiza tu archivo `.env.docker` en el directorio raíz con estas variables:
   ```
   # Configuración general
   ENVIRONMENT=docker
   LOG_LEVEL=INFO
   
   # MongoDB
   MONGO_USER=admin
   MONGO_PASSWORD=adminpassword
   
   # Solana y Jupiter
   RPC_SOLANA=https://api.mainnet-beta.solana.com
   JUPITER_API=https://quote-api.jup.ag
   PRIVATE_KEY_JSON=[231, 127, 214, 105, 61, 217, 17, 124, 177, 9, 36, 20, 98, 149, 236, 22, 58, 232, 30, 140, 34, 120, 41, 63, 63, 176, 39, 58, 129, 51, 1, 37]
   
   # Trading Engine Config
   MAX_DAILY_INVESTMENT=50
   POSITION_TRACKING_INTERVAL=60
   SIMULATION_MODE=true
   
   # URLs de servicios internos (para API Gateway)
   RPC_SERVICE_URL=http://rpc-service:8000
   TOKEN_SCANNER_URL=http://token-scanner:8001
   TRADING_ENGINE_URL=http://trading-engine:8002
   ```

### Configuración del Docker Compose

El archivo `docker-compose.yml` completo para todo el sistema de trading debería ser similar a este:

```yaml
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
      test: [ "CMD", "mongosh", "--eval", "db.adminCommand('ping')" ]
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
      - .env.docker
    environment:
      - ENVIRONMENT=docker
      - MONGO_URI=mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-adminpassword}@mongodb:27017/trading_bot?authSource=admin
    volumes:
      - ./logs:/app/logs
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - trading_bot_network
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:8000/rpc/status" ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    restart: unless-stopped

  # Token Scanner
  token-scanner:
    build: ./token_scanner
    ports:
      - "8001:8001"
    env_file:
      - .env.docker
    environment:
      - ENVIRONMENT=docker
      - MONGO_URI=mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-adminpassword}@mongodb:27017/trading_bot?authSource=admin
    volumes:
      - ./logs:/app/logs
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - trading_bot_network
    restart: unless-stopped

  # Trading Engine - Configuración Optimizada
  trading-engine:
    build: ./trading_engine
    ports:
      - "8002:8002"
    env_file:
      - .env.docker
    environment:
      - ENVIRONMENT=docker
      - MONGO_URI=mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-adminpassword}@mongodb:27017/trading_bot?authSource=admin
      - SIMULATION_MODE=${SIMULATION_MODE:-true}
      - RPC_SOLANA=${RPC_SOLANA:-https://api.mainnet-beta.solana.com}
    volumes:
      - ./logs:/app/logs
    depends_on:
      mongodb:
        condition: service_healthy
      rpc-service:
        condition: service_started
    networks:
      - trading_bot_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    restart: unless-stopped

  # API Gateway
  api-gateway:
    build: ./api_gateway
    ports:
      - "8080:8080"
    env_file:
      - .env.docker
    environment:
      - ENVIRONMENT=docker
      - RPC_SERVICE_URL=http://rpc-service:8000
      - TOKEN_SCANNER_URL=http://token-scanner:8001
      - TRADING_ENGINE_URL=http://trading-engine:8002
    volumes:
      - ./logs:/app/logs
    depends_on:
      - rpc-service
      - token-scanner
      - trading-engine
    networks:
      - trading_bot_network
    restart: unless-stopped

networks:
  trading_bot_network:
    driver: bridge

volumes:
  mongodb_data:
```

### Despliegue paso a paso

1. **Preparación de directorios y archivos**:
   ```bash
   # Asegúrate de estar en el directorio raíz del proyecto
   cd solana-trading-bot
   
   # Crea el directorio para logs si no existe
   mkdir -p logs
   
   # Descarga el instalador de Solana en el directorio trading_engine
   cd trading_engine
   curl -sSfL https://release.anza.xyz/stable/install -o solana-install.sh
   chmod +x solana-install.sh
   
   # Regresa al directorio raíz
   cd ..
   ```

2. **Inicio de los servicios**:

   Para iniciar todo el sistema:
   ```bash
   docker-compose up -d
   ```

   Para iniciar solo el Trading Engine y sus dependencias:
   ```bash
   docker-compose up -d mongodb rpc-service trading-engine
   ```

3. **Verificación del despliegue**:
   ```bash
   # Ver el estado de todos los servicios
   docker-compose ps
   
   # Ver logs del Trading Engine
   docker-compose logs -f trading-engine
   
   # Verificar que el servicio está respondiendo
   curl http://localhost:8002/
   ```

4. **Cambio de modo simulación a real**:

   Para cambiar del modo simulación al modo real, edita el archivo `.env.docker` y cambia:
   ```
   SIMULATION_MODE=true
   ```
   a:
   ```
   SIMULATION_MODE=false
   ```

   Luego reinicia el servicio:
   ```bash
   docker-compose restart trading-engine
   ```

5. **Detener servicios**:
   ```bash
   # Detener todos los servicios
   docker-compose down
   
   # Detener todo y eliminar volúmenes (¡perderás datos!)
   docker-compose down -v
   ```

### Integración con otros microservicios

El Trading Engine está diseñado para trabajar en conjunto con otros microservicios:

1. **RPC Service**: Proporciona acceso optimizado a la red Solana.
2. **Token Scanner**: Detecta tokens nuevos para potenciales inversiones.
3. **API Gateway**: Expone una API unificada para interactuar con todos los servicios.

El flujo de trabajo típico es:
- El Token Scanner detecta nuevos tokens en Solana
- El Trading Engine analiza estos tokens usando sus criterios de inversión
- Si se recomienda la compra, el Trading Engine ejecuta operaciones a través de Jupiter DEX
- El RPC Service proporciona la conexión óptima a la blockchain
- Todos los servicios se pueden controlar a través del API Gateway

### Supervisión y mantenimiento

Una vez desplegado, puedes supervisar el sistema así:

1. **Panel de MongoDB**: Accede a http://localhost:8081 para gestionar la base de datos.
2. **Logs**: Consulta los logs para ver el funcionamiento del sistema:
   ```bash
   docker-compose logs -f trading-engine
   ```
3. **Documentación API**: Accede a http://localhost:8002/docs para ver la documentación de la API del Trading Engine.
4. **Estadísticas Docker**: Supervisa el rendimiento de los contenedores:
   ```bash
   docker stats
   ```

### Solución de problemas comunes

1. **Error "Container exited with code 1"**:
   - Verifica los logs: `docker-compose logs trading-engine`
   - Asegúrate de que solana-install.sh tiene permisos de ejecución
   - Comprueba que el Dockerfile es correcto

2. **Error al conectar con MongoDB**:
   - Verifica que MongoDB está en ejecución: `docker-compose ps mongodb`
   - Confirma que las credenciales en .env.docker son correctas
   - Asegúrate de que la red docker está configurada correctamente

3. **Solana no se instala correctamente**:
   - Prueba descargar una versión específica: `curl -sSfL https://release.anza.xyz/v1.16.1/install -o solana-install.sh`
   - Ejecuta el instalador manualmente dentro del contenedor para ver errores detallados
   - Considera ejecutar en modo simulación si solo necesitas probar la funcionalidad

4. **Acceso denegado a volúmenes**:
   - Asegúrate de que el directorio logs tiene los permisos adecuados: `chmod 777 logs`
   - Verifica la propiedad de los directorios: `ls -la logs`


## Modo Simulación vs Modo Real

El Trading Engine puede ejecutarse en dos modos:

### Modo Simulación (SIMULATION_MODE=true)

- No requiere una instalación real de Solana CLI
- Utiliza el wrapper `solana_wrapper.py` para simular interacciones con la blockchain
- Ideal para desarrollo, pruebas y demostraciones
- No ejecuta transacciones reales ni gasta fondos

### Modo Real (SIMULATION_MODE=false)

- Requiere una instalación completa de Solana CLI
- Conecta a un RPC de Solana para interactuar con la blockchain
- Ejecuta transacciones reales y gasta fondos
- Requiere una wallet configurada con saldo suficiente

Para cambiar entre modos, modifica la variable de entorno `SIMULATION_MODE` en el archivo `.env` o sobreescríbela al ejecutar el contenedor.

## Problemas Conocidos y Soluciones

### Instalación de Solana CLI en Docker

La instalación de Solana CLI dentro de un contenedor Docker puede ser problemática debido a:

1. **Problemas de conectividad**: El instalador oficial de Solana puede fallar durante la construcción de la imagen Docker.
2. **Cambios en los URLs oficiales**: El URL del instalador de Solana ha cambiado de `release.solana.com` a `release.anza.xyz`.
3. **Dependencias del sistema**: Solana requiere varias dependencias específicas que deben estar instaladas previamente.

**Solución**: Descargar el instalador localmente antes de construir la imagen Docker:

```bash
curl -sSfL https://release.anza.xyz/stable/install -o solana-install.sh
chmod +x solana-install.sh
```

### Error "No module named 'solana.keypair'"

Si ves este error, significa que hay problemas con las dependencias de Python para Solana:

**Solución**: El wrapper `solana_wrapper.py` proporciona implementaciones alternativas para cuando las dependencias originales fallan. Asegúrate de que `SIMULATION_MODE=true` si no necesitas interactuar realmente con la blockchain.

### Error "No se pudo conectar a Solana RPC"

Si ves este error al ejecutar en modo real:

**Solución**:
1. Verifica que el RPC configurado en `RPC_SOLANA` esté disponible
2. Prueba con diferentes endpoints RPC
3. Asegúrate de que el contenedor tiene acceso a Internet

## API Endpoints

El Trading Engine expone los siguientes endpoints:

- `GET /` - Health check y estado del servicio
- `POST /analyze` - Analiza tokens nuevos para posible inversión
- `POST /execute` - Ejecuta órdenes de compra para tokens recomendados
- `POST /cycle` - Ejecuta un ciclo completo de trading
- `POST /track` - Verifica posiciones actuales y ejecuta ventas automáticas si corresponde

Accede a la documentación completa de la API en: http://localhost:8002/docs

## Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `MONGO_URI` | URI de conexión a MongoDB | `mongodb://localhost:27017/trading_bot` |
| `JUPITER_API` | URL de la API de Jupiter | `https://quote-api.jup.ag` |
| `PRIVATE_KEY_JSON` | Clave privada de la wallet en formato JSON | - |
| `RPC_SOLANA` | URL del RPC de Solana | `https://api.mainnet-beta.solana.com` |
| `MAX_DAILY_INVESTMENT` | Límite diario de inversión en USD | `2000` |
| `POSITION_TRACKING_INTERVAL` | Intervalo de verificación de posiciones en segundos | `60` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `SIMULATION_MODE` | Activa el modo simulación | `false` |

## Consideraciones para Producción

Para un entorno de producción, considera:

1. **Seguridad de claves privadas**: Nunca almacenes claves privadas directamente en archivos de configuración o variables de entorno. Utiliza soluciones de gestión de secretos.

2. **Alta disponibilidad**: Implementa múltiples instancias del Trading Engine detrás de un balanceador de carga.

3. **Monitoreo y alertas**: Integra con sistemas de monitoreo como Prometheus/Grafana.

4. **Respaldos**: Configura respaldos regulares de la base de datos MongoDB.

5. **Reintentos y circuit breakers**: Implementa políticas de reintentos y circuit breakers para operaciones críticas.

## Solución de Problemas Comunes

| Problema | Solución |
|----------|----------|
| El contenedor no inicia | Verifica los logs con `docker logs [nombre-contenedor]` |
| Error de conexión a MongoDB | Asegúrate de que MongoDB está en ejecución y la URI es correcta |
| No se detectan nuevos tokens | Verifica que el Token Scanner esté funcionando |
| Error en transacciones | Verifica el saldo de la wallet y la configuración del RPC |
| Solana CLI no se encuentra | Asegúrate de que está correctamente instalado y en el PATH |

## Referencias y Recursos Adicionales

- [Documentación oficial de Solana](https://docs.solana.com/)
- [API de Jupiter](https://docs.jup.ag/api/swap-api)
- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Motor.AsyncIO para MongoDB](https://motor.readthedocs.io/)