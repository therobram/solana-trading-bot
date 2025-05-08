# 🚀 Bot de Trading para DEX en Solana

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue)](https://www.docker.com/)
[![Solana](https://img.shields.io/badge/Solana-Mainnet-orange)](https://solana.com/)

Bot profesional de trading para detección y operación automática de tokens en DEX de Solana, implementado con una arquitectura de microservicios escalable y altamente disponible.

## ✨ Características

- **Detección Automatizada**: Identificación automática de nuevos tokens mediante la API de Dexscreener
- **Estrategia Inteligente**: Inversión basada en criterios configurables (perfil, booster, volumen, pools de liquidez)
- **Gestión de Riesgo**: Venta automática cuando un token alcanza x3 de su valor inicial
- **Alta Disponibilidad**: Sistema óptimo de gestión de RPC para máxima disponibilidad y rendimiento
- **Escalabilidad**: Arquitectura de microservicios desplegable en GCP Cloud Run
- **Monitorización**: Sistema completo de logging y monitoreo de operaciones

## 🔍 Arquitectura

El proyecto está organizado en microservicios independientes que se comunican entre sí:

1. **RPC Service**: Selección óptima de endpoints RPC para Solana
   - Mide latencia real de múltiples endpoints
   - Escoge el RPC más rápido automáticamente
   - Cachea para evitar medir constantemente
   - Se adapta dinámicamente a cambios de red

2. **Token Scanner**: Detección de nuevos tokens mediante API de Dexscreener
   - Monitoreo continuo de nuevos lanzamientos
   - Análisis de liquidez y volumen
   - Filtrado por criterios configurables

3. **Trading Engine**: Análisis y ejecución de operaciones de compra/venta
   - Implementación con Jupiter API para mejores rutas de swap
   - Gestión de posiciones de trading
   - Estrategias personalizables basadas en múltiples factores

4. **API Gateway**: Interfaz unificada para todos los servicios
   - Endpoints REST para todas las funcionalidades
   - Monitoreo centralizado
   - Escalabilidad independiente de cada componente

## 📋 Requisitos

- Python 3.9+
- Docker y Docker Compose
- Cuenta de GCP (para despliegue en producción)
- Cuenta MongoDB Atlas (o MongoDB local para desarrollo)
- Wallet de Solana con fondos para operaciones

## 🛠️ Instalación

1. Clona este repositorio:
git clone https://github.com/tuusuario/solana-trading-bot.git
cd solana-trading-bot

2. Crea y configura el archivo `.env`:
cp .env.example .env
Edita el archivo `.env` con tus credenciales y configuraciones

3. Para desarrollo local, levanta los servicios con Docker Compose:
docker-compose up -d

4. Para despliegue en GCP:
Configura las variables de Terraform
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
Edita terraform.tfvars con tus valores
Construye y sube las imágenes
./scripts/build_and_push.sh
Despliega la infraestructura
./scripts/deploy.sh

## ⚙️ Configuración

### Variables de Entorno

El archivo `.env` debe contener lo siguiente:

MongoDB
MONGO_URI=mongodb://admin@mongodb:27017/trading_bot?authSource=admin

Jupiter API
JUPITER_API=https://quote-api.jup.ag

Wallet
PRIVATE_KEY_JSON=[231, 127, 214, 105, 61, 217, 17, 124, ...]

RPC Endpoints
RPC_SOLANA=https://api.mainnet-beta.solana.com
RPC_QUIKNODE=https://your-node.solana-mainnet.quiknode.pro/key
RPC_HELIUS=https://mainnet.helius-rpc.com/?api-key=key
Agrega todos tus RPC endpoints aquí

RPC Service Config
RPC_CACHE_TTL=60
RPC_TIMEOUT=10
RPC_RETRY_ATTEMPTS=3

Token Scanner Config
TOKEN_SCAN_INTERVAL=60

Trading Engine Config
MAX_DAILY_INVESTMENT=2000
POSITION_TRACKING_INTERVAL=60

Logging
LOG_LEVEL=INFO

### Estrategia de Inversión

Puedes ajustar la estrategia de inversión en el archivo `trading_engine/token_evaluator.py`:

```python
# Inversión basada en criterios específicos:
# 1 USD por cada token nuevo.
# 3 USD por cada token nuevo y con perfil.
# 5 USD por cada token nuevo, con perfil y booster activado.
# ... etc

🚦 Uso

Endpoints API

RPC Service

GET /rpc - Obtiene el RPC más rápido
GET /rpc/status - Estado de todos los RPCs configurados
POST /tx - Envía una transacción firmada

Token Scanner

GET /tokens - Lista de tokens detectados
GET /tokens/{address} - Información de un token específico
POST /scan - Ejecuta un escaneo manual

Trading Engine

POST /analyze - Analiza tokens nuevos
POST /execute - Ejecuta órdenes de compra
POST /cycle - Ejecuta ciclo completo de trading
POST /track - Verifica posiciones abiertas

API Gateway

Consolida todos los endpoints anteriores
GET /dashboard - Datos consolidados para panel de control

Interfaz Web (opcional)

Accede al panel de control: http://localhost:8080
MongoDB Express UI: http://localhost:8081

📂 Estructura del Proyecto

solana-trading-bot/
│
├── rpc_service/
│   ├── config.py           # Configuración y variables de entorno
│   ├── logger.py           # Sistema de logging personalizado
│   ├── main.py             # Aplicación FastAPI
│   ├── rpc_manager.py      # Selección y gestión de RPCs
│   ├── tx_sender.py        # Envío de transacciones
│   ├── requirements.txt    # Dependencias
│   └── Dockerfile          # Configuración para Docker
│
├── token_scanner/
│   ├── db.py               # Acceso a la base de datos
│   ├── dexscreener_client.py  # Cliente para API Dexscreener
│   ├── logger.py           # Sistema de logging
│   ├── main.py             # Aplicación FastAPI
│   ├── models.py           # Modelos de datos
│   ├── scanner.py          # Lógica de escaneo de tokens
│   ├── requirements.txt    # Dependencias
│   └── Dockerfile          # Configuración para Docker
│
├── trading_engine/
│   ├── db.py               # Acceso a la base de datos
│   ├── jupiter_client.py   # Cliente para Jupiter DEX
│   ├── logger.py           # Sistema de logging
│   ├── main.py             # Aplicación FastAPI
│   ├── models.py           # Modelos de datos
│   ├── position_tracker.py # Seguimiento de posiciones
│   ├── token_evaluator.py  # Evaluación de tokens
│   ├── trading_engine.py   # Motor principal de trading
│   ├── requirements.txt    # Dependencias
│   └── Dockerfile          # Configuración para Docker
│
├── api_gateway/
│   ├── logger.py           # Sistema de logging
│   ├── main.py             # Aplicación FastAPI (Gateway)
│   ├── requirements.txt    # Dependencias
│   └── Dockerfile          # Configuración para Docker
│
├── terraform/              # Configuración IaC para GCP
├── scripts/                # Scripts de utilidad y despliegue
├── .env.example            # Plantilla para variables de entorno
├── docker-compose.yml      # Configuración de Docker Compose
└── README.md               # Este archivo


📊 Monitorización y Mantenimiento

Logs: Disponibles en el directorio logs/
Panel de MongoDB: Accesible en http://localhost:8081 (desarrollo local)
Métricas de Cloud Run: Disponibles en GCP Console (producción)
Alertas: Configura alertas en Cloud Monitoring para ser notificado

🤝 Contribución

Haz un fork del repositorio
Crea una nueva rama (git checkout -b feature/amazing-feature)
Haz commit de tus cambios (git commit -m 'Add some amazing feature')
Haz push a la rama (git push origin feature/amazing-feature)
Abre un Pull Request

📄 Licencia

Este proyecto está bajo licencia privada. Todos los derechos reservados.

Desarrollado con ❤️ para el ecosistema Solana