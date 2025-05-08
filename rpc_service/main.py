### 📁 rpc_service/main.py
from fastapi import FastAPI, HTTPException, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time
import os
from typing import Dict, List, Any, Optional

from rpc_manager import get_best_rpc, get_all_rpc_statuses
from tx_sender import send_tx, TransactionError
from config import APP_NAME, APP_VERSION
from logger import setup_logger

logger = setup_logger("rpc_service")

# Modelos Pydantic
class TransactionRequest(BaseModel):
    tx: str = Field(..., description="Transacción codificada en base58")
    options: Optional[Dict[str, Any]] = Field(None, description="Opciones de envío de la transacción")

class TransactionResponse(BaseModel):
    signature: str
    timestamp: float

class RPCStatus(BaseModel):
    rpc: str
    latency_ms: Optional[float]
    healthy: bool

class BestRPCResponse(BaseModel):
    rpc: str
    timestamp: float

# Inicializar FastAPI
app = FastAPI(
    title=f"{APP_NAME} RPC Service",
    description="Servicio para gestión óptima de conexiones RPC a la red Solana",
    version=APP_VERSION,
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desarrollo, en producción limitar a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Manejador de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Error interno del servidor", "detail": str(exc)},
    )

# Endpoints
@app.get("/", tags=["General"])
def root():
    """Endpoint de health check"""
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "status": "healthy",
        "timestamp": time.time()
    }

@app.get("/rpc", response_model=BestRPCResponse, tags=["RPC"])
def get_fastest_rpc(force_refresh: bool = False):
    """Obtiene el RPC más rápido actualmente disponible"""
    try:
        rpc = get_best_rpc(force_refresh=force_refresh)
        return {
            "rpc": rpc,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error obteniendo el mejor RPC: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener el mejor RPC: {str(e)}")

@app.get("/rpc/status", response_model=List[RPCStatus], tags=["RPC"])
def rpc_status():
    """Obtiene el estado de todos los RPCs configurados"""
    try:
        return get_all_rpc_statuses()
    except Exception as e:
        logger.error(f"Error obteniendo estado de RPCs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de RPCs: {str(e)}")

@app.post("/tx", response_model=TransactionResponse, tags=["Transacciones"])
def send_transaction(payload: TransactionRequest = Body(...)):
    """Envía una transacción firmada a la red Solana"""
    try:
        signature = send_tx(payload.tx, payload.options)
        return {
            "signature": signature,
            "timestamp": time.time()
        }
    except TransactionError as e:
        logger.error(f"Error de transacción: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error enviando transacción: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar transacción: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)