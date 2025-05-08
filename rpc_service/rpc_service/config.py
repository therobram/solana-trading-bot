### 📁 rpc_service/config.py
import os
from dotenv import load_dotenv
from pathlib import Path
import json
import sys

# Lista de posibles ubicaciones para el archivo .env
env_paths = [
    Path(__file__).resolve().parents[1] / ".env",  # /rpc_service/.env
    Path(__file__).resolve().parents[2] / ".env",  # /solana-trading-bot/.env
    Path.cwd() / ".env",                           # Directorio de trabajo actual
    Path.cwd().parent / ".env",                    # Un nivel arriba del directorio de trabajo
]

# Intentar cargar desde cada ubicación posible
env_loaded = False
tried_paths = []

for env_path in env_paths:
    tried_paths.append(str(env_path))
    if env_path.exists():
        print(f"Cargando variables de entorno desde: {env_path}")
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        break

if not env_loaded:
    print(f"ADVERTENCIA: No se encontró ningún archivo .env en las rutas intentadas: {tried_paths}")

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
    # Obtener información de diagnóstico para mejorar el mensaje de error
    env_vars = [f"{k}={v[:10]}..." if len(v) > 15 else f"{k}={v}" 
                for k, v in os.environ.items() if k.startswith("RPC_")]
    
    error_msg = (
        "No se encontraron URLs de RPC en las variables de entorno.\n"
        f"Variables encontradas con prefijo RPC_: {env_vars or 'ninguna'}\n"
        f"Rutas de archivos .env intentadas: {tried_paths}\n"
        "Asegúrate de configurar al menos una variable RPC_* (como RPC_SOLANA, RPC_HELIUS, etc.)"
    )
    raise ValueError(error_msg)

# Configuración de log
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")