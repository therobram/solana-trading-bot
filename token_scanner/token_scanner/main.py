### 📁 token_scanner/main.py
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from typing import List, Optional
from datetime import datetime

from token_scanner.models import Token, TokenStatus, TokenAnalysis
from token_scanner.scanner import TokenScanner
from token_scanner.db import Database
from token_scanner.logger import setup_logger
from token_scanner.config import Config

# Cargar configuración del entorno
Config.load_environment()

# Configurar logger con el nivel adecuado
logger = setup_logger("token_scanner_api", level=Config.get_log_level())

# Inicializar componentes
mongo_uri = Config.get_mongo_uri()
db = Database(mongo_uri)
scanner = TokenScanner(db)

# Inicializar FastAPI
app = FastAPI(
    title="Token Scanner Service",
    description="Servicio para detección y análisis de nuevos tokens en Solana",
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

# Task para el scanner
scanner_task = None

@app.on_event("startup")
async def startup_event():
    global scanner_task
    logger.info("Iniciando servicio de Token Scanner")
    scanner_task = asyncio.create_task(scanner.start_scanning())

@app.on_event("shutdown")
async def shutdown_event():
    global scanner_task
    logger.info("Deteniendo servicio de Token Scanner")
    scanner.stop_scanning()
    if scanner_task:
        scanner_task.cancel()
        try:
            await scanner_task
        except asyncio.CancelledError:
            pass

@app.get("/", tags=["General"])
def root():
    """Endpoint de health check"""
    return {
        "service": "Token Scanner",
        "status": "healthy",
        "scanning": scanner.running,
        "last_scan": scanner.last_scan_time.isoformat() if scanner.last_scan_time else None
    }

@app.get("/tokens", response_model=List[Token], tags=["Tokens"])
async def get_tokens(
    status: Optional[TokenStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene la lista de tokens
    
    Args:
        status: Filtrar por estado (opcional)
        limit: Límite de resultados
        offset: Desplazamiento para paginación
    """
    try:
        if status:
            tokens = await db.get_tokens_by_status(status)
            return tokens[offset:offset+limit]
        else:
            # Implementar obtención de todos los tokens con paginación
            # (requiere método adicional en la clase Database)
            tokens = []  # Placeholder
            return tokens
    except Exception as e:
        logger.error(f"Error obteniendo tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener tokens: {str(e)}")

@app.get("/tokens/{address}", response_model=Token, tags=["Tokens"])
async def get_token(address: str = Path(..., description="Dirección del token")):
    """
    Obtiene un token específico por su dirección
    
    Args:
        address: Dirección del token
    """
    token = await db.get_token(address)
    if not token:
        raise HTTPException(status_code=404, detail=f"Token {address} no encontrado")
    return token

@app.post("/scan", response_model=List[Token], tags=["Scanner"])
async def trigger_scan():
    """Dispara un escaneo manual de tokens nuevos"""
    try:
        tokens = await scanner.scan_once()
        return tokens
    except Exception as e:
        logger.error(f"Error en escaneo manual: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en escaneo: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)