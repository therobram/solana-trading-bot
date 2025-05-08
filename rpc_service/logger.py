### 📁 rpc_service/logger.py
import logging
import sys
from datetime import datetime

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

def setup_logger(name):
    """Configura y retorna un logger con el nombre especificado"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    
    # Handler para archivo
    file_handler = logging.FileHandler(f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log')
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger