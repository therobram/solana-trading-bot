### 📁 trading_engine/trading_engine.py
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

from logger import setup_logger
from models import Token, TokenStatus, TokenAnalysis, Transaction
from jupiter_client import JupiterClient
from token_evaluator import TokenEvaluator
from position_tracker import PositionTracker
from db import Database

logger = setup_logger("trading_engine")

class TradingEngine:
    """Motor principal de trading"""
    
    def __init__(self, db: Database, jupiter_client: JupiterClient):
        """
        Inicializa el motor de trading
        
        Args:
            db: Instancia de la base de datos
            jupiter_client: Cliente de Jupiter para operaciones de trading
        """
        self.db = db
        self.jupiter = jupiter_client
        self.evaluator = TokenEvaluator()
        self.tracker = PositionTracker(db, jupiter_client)
        
        # Constantes
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        # Configuración
        self.max_daily_investment = Decimal("2000.0")  # Límite diario de inversión (USD)
        self.position_tracking_enabled = True
    
    async def initialize(self):
        """Inicializa el motor de trading"""
        logger.info("Inicializando motor de trading...")
        
        # Verificar USDC disponible
        usdc_balance = await self.jupiter.get_token_balance(self.USDC_MINT)
        if usdc_balance is not None:
            logger.info(f"Balance USDC disponible: {usdc_balance / 10**6:,.2f} USDC")
        else:
            logger.warning("No se pudo verificar el balance de USDC")
        
        # Iniciar tracker de posiciones
        if self.position_tracking_enabled:
            asyncio.create_task(self.tracker.start_tracking())
    
    async def analyze_tokens(self):
        """
        Analiza tokens nuevos y los evalúa para posible inversión
        
        Returns:
            Lista de análisis realizados
        """
        # Obtener tokens nuevos sin analizar
        tokens = await self.db.get_tokens_by_status(TokenStatus.NEW)
        
        if not tokens:
            logger.info("No hay tokens nuevos para analizar")
            return []
        
        logger.info(f"Analizando {len(tokens)} tokens nuevos")
        
        analyses = []
        for token in tokens:
            # Evaluar token
            analysis = self.evaluator.evaluate_token(token)
            
            # Guardar análisis en la base de datos
            analysis_id = await self.db.save_analysis(analysis)
            
            # Actualizar estado del token
            await self.db.update_token_status(token.address, TokenStatus.ANALYZED)
            
            # Agregar a la lista de análisis
            analyses.append(analysis)
            
            logger.info(f"Token {token.symbol} analizado: "
                       f"Score={analysis.investment_score:,.1f}, "
                       f"Recomendación: {'COMPRAR' if analysis.buy_recommendation else 'NO COMPRAR'}, "
                       f"Monto=${analysis.investment_amount:,.2f}")
        
        return analyses
    
    async def execute_buy_orders(self):
        """
        Ejecuta órdenes de compra para tokens analizados y recomendados
        
        Returns:
            Lista de transacciones realizadas
        """
        # Obtener tokens analizados
        tokens = await self.db.get_tokens_by_status(TokenStatus.ANALYZED)
        
        if not tokens:
            logger.info("No hay tokens analizados para ejecutar órdenes")
            return []
        
        logger.info(f"Procesando {len(tokens)} tokens analizados para posibles órdenes")
        
        # Obtener total ya invertido hoy
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        
        # TODO: Implementar consulta para obtener total invertido hoy
        daily_invested = Decimal("0.0")  # Placeholder
        
        transactions = []
        for token in tokens:
            # Obtener análisis más reciente
            analysis = await self.db.get_latest_analysis(token.address)
            
            if not analysis:
                logger.warning(f"No se encontró análisis para {token.symbol} ({token.address})")
                continue
            
            # Verificar si hay recomendación de compra
            if not analysis.buy_recommendation:
                logger.info(f"Token {token.symbol} no recomendado para compra")
                continue
            
            # Verificar límite diario
            investment_amount = Decimal(str(analysis.investment_amount))
            if daily_invested + investment_amount > self.max_daily_investment:
                logger.warning(f"Límite diario de inversión alcanzado (${daily_invested:,.2f}/{self.max_daily_investment:,.2f})")
                break
            
            # Verificar disponibilidad de USDC
            usdc_balance = await self.jupiter.get_token_balance(self.USDC_MINT)
            if usdc_balance is None or usdc_balance < (investment_amount * 10**6):
                logger.warning(f"USDC insuficiente para comprar {token.symbol}. "
                              f"Requerido: ${investment_amount:,.2f}, "
                              f"Disponible: ${(usdc_balance or 0) / 10**6:,.2f}")
                continue
            
            # Ejecutar compra
            logger.info(f"Ejecutando orden de compra para {token.symbol}. "
                       f"Monto: ${investment_amount:,.2f} USDC")
            
            # Convertir a unidades de token (USDC tiene 6 decimales)
            usdc_amount = int(investment_amount * 10**6)
            
            signature = await self.jupiter.execute_swap(
                input_mint=self.USDC_MINT,
                output_mint=token.address,
                amount=usdc_amount,
                slippage_bps=100  # 1% de slippage para asegurar ejecución
            )
            
            if signature:
                # Registrar transacción
                transaction = Transaction(
                    token_address=token.address,
                    transaction_type="buy",
                    amount=usdc_amount,
                    price_usd=token.price_usd,
                    total_usd=float(investment_amount),
                    tx_signature=signature,
                    metadata={
                        "analysis_score": analysis.investment_score,
                        "reasons": analysis.reasons
                    }
                )
                
                await self.db.save_transaction(transaction)
                
                # Actualizar estado del token
                await self.db.update_token_status(token.address, TokenStatus.BOUGHT)
                
                # Actualizar total invertido hoy
                daily_invested += investment_amount
                
                # Agregar a lista de transacciones
                transactions.append(transaction)
                
                logger.info(f"Compra exitosa de {token.symbol}. Signature: {signature}")
            else:
                logger.error(f"Error comprando token {token.symbol}")
        
        logger.info(f"Proceso de ejecución de órdenes finalizado. {len(transactions)} transacciones realizadas.")
        return transactions
    
    async def run_trading_cycle(self):
        """Ejecuta un ciclo completo de trading"""
        try:
            logger.info("Iniciando ciclo de trading")
            
            # 1. Analizar tokens
            await self.analyze_tokens()
            
            # 2. Ejecutar órdenes de compra
            await self.execute_buy_orders()
            
            # 3. El seguimiento de posiciones se ejecuta en un proceso separado
            
            logger.info("Ciclo de trading completado")
            
        except Exception as e:
            logger.error(f"Error en ciclo de trading: {str(e)}", exc_info=True)