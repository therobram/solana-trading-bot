### 📁 token_scanner/logger.py
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

class CustomFormatter(logging.Formatter):
    """Formatter personalizado con colores y estructura profesional"""
    
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[41m\033[37m',  # White on Red
        'RESET': '\033[0m',   # Reset
    }
    
    def format(self, record):
        log_fmt = f'%(asctime)s [{self.COLORS.get(record.levelname, "")}%(levelname)s{self.COLORS["RESET"]}] '
        log_fmt += '%(name)s - %(message)s'
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logger(name, level=None):
    """Configura y retorna un logger con el nombre especificado"""
    logger = logging.getLogger(name)
    
    # Evitar configurar múltiples veces el mismo logger
    if logger.handlers:
        return logger
    
    # Usar el nivel proporcionado o por defecto obtener de las variables de entorno
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Convertir string de nivel a constante de logging
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    
    # Asegurar que el directorio de logs existe
    logs_dir = Path(__file__).resolve().parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Handler para archivo con ruta garantizada
    log_file = logs_dir / f'{name}_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.debug(f"Logger '{name}' configurado correctamente con nivel {level}")
    return logger