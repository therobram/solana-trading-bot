### 📁 trading_engine/main.py
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from typing import List, Optional
from datetime import datetime

from models import Token, TokenStatus, TokenAnalysis, Transaction
from db import Database
from jupiter_client import JupiterClient
from trading_engine import TradingEngine
from position_tracker import PositionTracker
from logger import setup_logger

logger = setup_logger("trading_engine_api")

# Inicializar componentes
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/trading_bot")
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)