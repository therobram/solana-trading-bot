### 📁 rpc_service/config.py
import os
from dotenv import load_dotenv
from pathlib import Path
import json

# Cargar .env desde el raíz del proyecto
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# Configuración general
APP_NAME = "solana-trading-bot"
APP_VERSION = "1.0.0"

# TTL para cache de RPC en segundos
RPC_CACHE_TTL = int(os.getenv("RPC_CACHE_TTL", "60"))
RPC_TIMEOUT = int(os.getenv("RPC_TIMEOUT", "10"))  # Timeout en segundos
RPC_RETRY_ATTEMPTS = int(os.getenv("RPC_RETRY_ATTEMPTS", "3"))

# Extrae todas las variables RPC_
RPCS = [value for key, value in os.environ.items() 
       if key.startswith("RPC_") and not key in ["RPC_CACHE_TTL", "RPC_TIMEOUT", "RPC_RETRY_ATTEMPTS"]]

# Verificar que al menos existe un RPC configurado
if not RPCS:
    raise ValueError("No se encontraron URLs de RPC en las variables de entorno. Asegúrate de configurar al menos una variable RPC_*")

# Configuración de log
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")