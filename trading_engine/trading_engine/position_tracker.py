### 📁 trading_engine/position_tracker.py
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

from trading_engine.logger import setup_logger
from trading_engine.models import Token, Transaction, TokenStatus
from trading_engine.jupiter_client import JupiterClient
from trading_engine.db import Database
from trading_engine.config import Config

logger = setup_logger("position_tracker")

class PositionTracker:
    """Clase para rastrear y gestionar posiciones abiertas"""
    
    def __init__(self, db: Database, jupiter_client: JupiterClient, check_interval: int = 60):
        """
        Inicializa el rastreador de posiciones
        
        Args:
            db: Instancia de la base de datos
            jupiter_client: Cliente de Jupiter para operaciones de trading
            check_interval: Intervalo de verificación en segundos (default: 60)
        """
        self.db = db
        self.jupiter = jupiter_client
        self.check_interval = check_interval
        self.running = False
        self.last_check_time = None
        
        # Constantes
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    async def check_positions_once(self) -> List[Transaction]:
        """
        Realiza una verificación única de todas las posiciones abiertas
        
        Returns:
            Lista de transacciones de venta realizadas
        """
        try:
            logger.info("Verificando posiciones abiertas...")
            start_time = time.time()
            
            # Obtener tokens en estado BOUGHT
            tokens = await self.db.get_tokens_by_status(TokenStatus.BOUGHT)
            
            if not tokens:
                logger.info("No hay posiciones abiertas para verificar")
                return []
                
            logger.info(f"Verificando {len(tokens)} posiciones abiertas")
            
            sell_transactions = []
            for token in tokens:
                # Obtener transacciones del token para encontrar precio de entrada
                transactions = await self.db.get_transactions_by_token(token.address)
                
                # Filtrar transacciones de compra
                buy_transactions = [tx for tx in transactions if tx.transaction_type == "buy"]
                
                if not buy_transactions:
                    logger.warning(f"No se encontraron transacciones de compra para {token.symbol} ({token.address})")
                    continue
                    
                # Obtener la transacción de compra más reciente
                buy_tx = max(buy_transactions, key=lambda tx: tx.timestamp)
                
                # Obtener precio actual
                token_details = await self.db.get_token(token.address)
                current_price = token_details.price_usd if token_details else None
                
                if not current_price:
                    logger.warning(f"No se pudo obtener precio actual para {token.symbol} ({token.address})")
                    continue
                
                # Verificar si ha alcanzado x3
                entry_price = buy_tx.price_usd
                price_ratio = current_price / entry_price if entry_price > 0 else 0
                
                logger.info(f"Token {token.symbol}: Precio entrada=${entry_price:,.10f}, "
                           f"Precio actual=${current_price:,.10f}, Ratio={price_ratio:,.2f}x")
                
                # Vender si ha alcanzado x3
                if price_ratio >= 3.0:
                    logger.info(f"¡Token {token.symbol} alcanzó x3! Ejecutando venta automática")
                    
                    # Obtener balance actual del token
                    balance = await self.jupiter.get_token_balance(token.address)
                    
                    if not balance or balance == 0:
                        logger.warning(f"No hay balance disponible para vender {token.symbol}")
                        continue
                    
                    # Ejecutar venta a USDC
                    signature = await self.jupiter.execute_swap(
                        input_mint=token.address,
                        output_mint=self.USDC_MINT,
                        amount=balance,
                        slippage_bps=100  # 1% de slippage para asegurar ejecución
                    )
                    
                    if signature:
                        # Registrar transacción de venta
                        transaction = Transaction(
                            token_address=token.address,
                            transaction_type="sell",
                            amount=balance,
                            price_usd=current_price,
                            total_usd=current_price * (balance / 10**9),  # Asumiendo 9 decimales para tokens SPL
                            tx_signature=signature,
                            metadata={
                                "entry_price": entry_price,
                                "price_ratio": price_ratio,
                                "reason": "automatic_x3"
                            }
                        )
                        
                        await self.db.save_transaction(transaction)
                        
                        # Actualizar estado del token
                        await self.db.update_token_status(token.address, TokenStatus.SOLD)
                        
                        # Agregar a lista de ventas realizadas
                        sell_transactions.append(transaction)
                        
                        logger.info(f"Venta exitosa de {token.symbol}. Ganancia: {price_ratio:,.2f}x")
                    else:
                        logger.error(f"Error vendiendo token {token.symbol}")
            
            elapsed = time.time() - start_time
            logger.info(f"Verificación completada en {elapsed:.2f}s. {len(sell_transactions)} tokens vendidos.")
            
            self.last_check_time = datetime.utcnow()
            return sell_transactions
            
        except Exception as e:
            logger.error(f"Error verificando posiciones: {str(e)}", exc_info=True)
            return []
    
    async def start_tracking(self):
        """Inicia el proceso de seguimiento continuo"""
        if self.running:
            logger.warning("El tracker ya está en ejecución")
            return
            
        self.running = True
        logger.info(f"Iniciando seguimiento de posiciones con intervalo de {self.check_interval}s")
        
        try:
            while self.running:
                await self.check_positions_once()
                
                # Esperar para la próxima verificación
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Tracker detenido por solicitud")
            self.running = False
        except Exception as e:
            logger.error(f"Error en el loop de seguimiento: {str(e)}", exc_info=True)
            self.running = False
    
    def stop_tracking(self):
        """Detiene el proceso de seguimiento"""
        self.running = False
        logger.info("Señal de detención enviada al tracker")