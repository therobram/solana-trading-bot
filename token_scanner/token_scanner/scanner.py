### 📁 token_scanner/scanner.py
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

from token_scanner.logger import setup_logger
from token_scanner.models import Token, TokenStatus
from token_scanner.dexscreener_client import DexscreenerClient
from token_scanner.db import Database
from token_scanner.config import Config

logger = setup_logger("token_scanner")

class TokenScanner:
    """Clase para escanear y detectar nuevos tokens"""
    
    def __init__(self, db: Database, scan_interval: int = None):
        """
        Inicializa el scanner de tokens
        
        Args:
            db: Instancia de la base de datos
            scan_interval: Intervalo de escaneo en segundos (default: 60)
        """
        self.db = db
        self.dexscreener = DexscreenerClient()

        # Cargar configuración si no se proporciona el intervalo
        if scan_interval is None:
            Config.load_environment()
            scan_interval = Config.get_scan_interval()

        self.scan_interval = scan_interval
        self.running = False
        self.last_scan_time = None
    
    async def scan_once(self) -> List[Token]:
        """
        Realiza un escaneo único buscando tokens nuevos
        
        Returns:
            Lista de tokens nuevos encontrados
        """
        try:
            logger.info("Iniciando escaneo de tokens nuevos...")
            start_time = time.time()
            
            # Obtener tokens recientes de Dexscreener
            tokens = await self.dexscreener.get_recent_tokens(chain="solana", max_age_hours=24)
            
            new_tokens = []
            for token in tokens:
                # Verificar si el token ya existe en nuestra base de datos
                token_exists = await self.db.token_exists(token.address)
                
                if not token_exists:
                    # Obtener detalles completos
                    detailed_token = await self.dexscreener.get_token_details(token.address)
                    
                    if detailed_token:
                        # Guardar en la base de datos
                        await self.db.save_token(detailed_token)
                        new_tokens.append(detailed_token)
                        logger.info(f"Nuevo token detectado: {detailed_token.symbol} ({detailed_token.address})")
            
            elapsed = time.time() - start_time
            logger.info(f"Escaneo completado en {elapsed:.2f}s. {len(new_tokens)} nuevos tokens encontrados.")
            
            self.last_scan_time = datetime.utcnow()
            return new_tokens
            
        except Exception as e:
            logger.error(f"Error durante el escaneo: {str(e)}", exc_info=True)
            return []
    
    async def start_scanning(self):
        """Inicia el proceso de escaneo continuo"""
        if self.running:
            logger.warning("El scanner ya está en ejecución")
            return
            
        self.running = True
        logger.info(f"Iniciando scanner de tokens con intervalo de {self.scan_interval}s")
        
        try:
            while self.running:
                await self.scan_once()
                
                # Esperar para el próximo escaneo con un poco de jitter para evitar patrones predecibles
                jitter = random.uniform(0, 5)  # 0-5 segundos de jitter
                await asyncio.sleep(self.scan_interval + jitter)
        except asyncio.CancelledError:
            logger.info("Scanner detenido por solicitud")
            self.running = False
        except Exception as e:
            logger.error(f"Error en el loop de escaneo: {str(e)}", exc_info=True)
            self.running = False
    
    def stop_scanning(self):
        """Detiene el proceso de escaneo"""
        self.running = False
        logger.info("Señal de detención enviada al scanner")