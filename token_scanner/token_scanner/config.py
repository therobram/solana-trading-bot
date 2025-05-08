import os
from pathlib import Path
from dotenv import load_dotenv
import sys

class Config:
    """Clase para gestionar configuración según el entorno"""
    
    @staticmethod
    def load_environment():
        """Carga el archivo .env adecuado según el entorno"""
        # Directorio base del proyecto
        base_dir = Path(__file__).resolve().parents[2]  # Suponiendo que estamos en token_scanner/token_scanner/config.py
        
        # Determinar el entorno (puedes pasarlo como argumento o detectarlo automáticamente)
        env = os.getenv("ENVIRONMENT", "local")  # Por defecto, usamos 'local'
        
        # Archivos .env a buscar, en orden de prioridad
        env_files = [
            base_dir / f".env.{env}",  # .env.local o .env.docker
            base_dir / ".env",         # .env como fallback
        ]
        
        # Intentar cargar el primer archivo que exista
        for env_file in env_files:
            if env_file.exists():
                print(f"Cargando configuración desde: {env_file}")
                load_dotenv(dotenv_path=env_file)
                return str(env_file)
        
        print("No se encontró ningún archivo .env. Usando variables de entorno del sistema.")
        return None
    
    @classmethod
    def get_mongo_uri(cls):
        """Obtiene la URI de MongoDB"""
        return os.getenv("MONGO_URI", "mongodb://localhost:27017/trading_bot")
    
    @classmethod
    def get_scan_interval(cls):
        """Obtiene el intervalo de escaneo en segundos"""
        return int(os.getenv("TOKEN_SCAN_INTERVAL", "60"))
    
    @classmethod
    def get_log_level(cls):
        """Obtiene el nivel de logging"""
        return os.getenv("LOG_LEVEL", "INFO")