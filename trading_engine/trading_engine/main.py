### 📁 trading_engine/main.py
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from typing import List, Optional
from datetime import datetime

from trading_engine.models import Token, TokenStatus, TokenAnalysis, Transaction
from trading_engine.db import Database
from trading_engine.jupiter_client import JupiterClient
from trading_engine.trading_engine import TradingEngine
from trading_engine.position_tracker import PositionTracker
from trading_engine.logger import setup_logger
from trading_engine.config import Config

# Cargar configuración del entorno
Config.load_environment()

logger = setup_logger("trading_engine_api")

# Inicializar componentes
mongo_uri = Config.get_mongo_uri()
db = Database(mongo_uri)
jupiter_client = JupiterClient()
trading_engine = TradingEngine(db, jupiter_client)

# Inicializar FastAPI
app = FastAPI(
    title="Trading Engine",
    description="Motor de trading para DEX en Solana",
    version="1.0.0",
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task para el trading engine
engine_task = None

@app.on_event("startup")
async def startup_event():
    global engine_task
    logger.info("Iniciando servicio de Trading Engine")
    await trading_engine.initialize()

@app.get("/", tags=["General"])
def root():
    """Endpoint de health check"""
    return {
        "service": "Trading Engine",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/analyze", response_model=List[TokenAnalysis], tags=["Trading"])
async def analyze_tokens():
    """Analiza tokens nuevos para posible inversión"""
    try:
        analyses = await trading_engine.analyze_tokens()
        return analyses
    except Exception as e:
        logger.error(f"Error analizando tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al analizar tokens: {str(e)}")

@app.post("/execute", response_model=List[Transaction], tags=["Trading"])
async def execute_buy_orders():
    """Ejecuta órdenes de compra para tokens recomendados"""
    try:
        transactions = await trading_engine.execute_buy_orders()
        return transactions
    except Exception as e:
        logger.error(f"Error ejecutando órdenes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al ejecutar órdenes: {str(e)}")

@app.post("/cycle", tags=["Trading"])
async def run_trading_cycle():
    """Ejecuta un ciclo completo de trading"""
    try:
        await trading_engine.run_trading_cycle()
        return {"status": "success", "message": "Ciclo de trading completado"}
    except Exception as e:
        logger.error(f"Error en ciclo de trading: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en ciclo de trading: {str(e)}")

@app.post("/track", response_model=List[Transaction], tags=["Trading"])
async def check_positions():
    """Verifica posiciones actuales y ejecuta ventas automáticas si corresponde"""
    try:
        transactions = await trading_engine.tracker.check_positions_once()
        return transactions
    except Exception as e:
        logger.error(f"Error verificando posiciones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al verificar posiciones: {str(e)}")
    
@app.post("/test-swap", tags=["Testing"])
async def test_swap():
    """Ejecuta un swap de prueba con valores mínimos"""
    try:
        # SOL a USDC con una cantidad muy pequeña (0.001 SOL = 1000000 lamports)
        signature = await trading_engine.jupiter.execute_swap(
            input_mint="So11111111111111111111111111111111111111112",  # SOL
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            amount=1000000,  # 0.001 SOL
            slippage_bps=100  # 1% slippage
        )
        
        if signature:
            return {
                "status": "success",
                "message": "Swap de prueba ejecutado correctamente",
                "signature": signature,
                "explorer_url": f"https://explorer.solana.com/tx/{signature}"
            }
        else:
            raise HTTPException(status_code=500, detail="Error ejecutando swap de prueba")
    except Exception as e:
        logger.error(f"Error en swap de prueba: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run("trading_engine.main:app", host="0.0.0.0", port=port, reload=True)