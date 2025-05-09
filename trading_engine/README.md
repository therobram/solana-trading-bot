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

Crea o modifica el archivo `docker-compose.yml` en el directorio raíz del proyecto:

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
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=adminpassword
    networks:
      - trading_bot_network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped

  # Trading Engine
  trading-engine:
    build: ./trading_engine
    ports:
      - "8002:8002"
    env_file:
      - .env.docker
    environment:
      - MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/trading_bot?authSource=admin
      - SIMULATION_MODE=true
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

Para ejecutar con Docker Compose:

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f trading-engine

# Detener todos los servicios
docker-compose down
```

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