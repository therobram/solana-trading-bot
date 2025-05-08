### 📁 api_gateway/main.py
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import Dict, Any
import time

from logger import setup_logger

logger = setup_logger("api_gateway")

# Configuración de servicios
RPC_SERVICE_URL = os.getenv("RPC_SERVICE_URL", "http://rpc-service:8000")
TOKEN_SCANNER_URL = os.getenv("TOKEN_SCANNER_URL", "http://token-scanner:8001")
TRADING_ENGINE_URL = os.getenv("TRADING_ENGINE_URL", "http://trading-engine:8002")

# Inicializar FastAPI
app = FastAPI(
    title="Solana Trading Bot API Gateway",
    description="API Gateway para el bot de trading de Solana",
    version="1.0.0"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente HTTP
@app.on_event("startup")
async def startup_event():
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.http_client.aclose()

# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Función para proxy de requests
async def proxy_request(
    client: httpx.AsyncClient,
    method: str,
    service_url: str,
    path: str,
    params: Dict = None,
    data: Any = None,
    json: Any = None,
    headers: Dict = None
) -> httpx.Response:
    url = f"{service_url}{path}"
    
    try:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers
        )
        return response
    except httpx.RequestError as e:
        logger.error(f"Error de conexión: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Servicio no disponible: {str(e)}")

# Endpoint de estado
@app.get("/", tags=["General"])
async def root():
    """Endpoint de health check"""
    return {
        "service": "Solana Trading Bot API Gateway",
        "status": "healthy",
        "timestamp": time.time()
    }

# Routes para RPC Service
@app.get("/rpc", tags=["RPC Service"])
async def get_best_rpc(request: Request):
    """Obtiene el RPC más rápido"""
    response = await proxy_request(
        client=app.state.http_client,
        method="GET",
        service_url=RPC_SERVICE_URL,
        path="/rpc"
    )
    return response.json()

@app.get("/rpc/status", tags=["RPC Service"])
async def get_rpc_status(request: Request):
    """Obtiene el estado de todos los RPCs"""
    response = await proxy_request(
        client=app.state.http_client,
        method="GET",
        service_url=RPC_SERVICE_URL,
        path="/rpc/status"
    )
    return response.json()

@app.post("/tx", tags=["RPC Service"])
async def send_transaction(request: Request):
    """Envía una transacción a la red Solana"""
    json_data = await request.json()
    response = await proxy_request(
        client=app.state.http_client,
        method="POST",
        service_url=RPC_SERVICE_URL,
        path="/tx",
        json=json_data
    )
    return response.json()

# Routes para Token Scanner
@app.get("/tokens", tags=["Token Scanner"])
async def get_tokens(request: Request):
    """Obtiene lista de tokens"""
    params = dict(request.query_params)
    response = await proxy_request(
        client=app.state.http_client,
        method="GET",
        service_url=TOKEN_SCANNER_URL,
        path="/tokens",
        params=params
    )
    return response.json()

@app.get("/tokens/{address}", tags=["Token Scanner"])
async def get_token(address: str, request: Request):
    """Obtiene un token específico"""
    response = await proxy_request(
        client=app.state.http_client,
        method="GET",
        service_url=TOKEN_SCANNER_URL,
        path=f"/tokens/{address}"
    )
    return response.json()

@app.post("/scan", tags=["Token Scanner"])
async def trigger_scan(request: Request):
    """Dispara un escaneo manual de tokens"""
    response = await proxy_request(
        client=app.state.http_client,
        method="POST",
        service_url=TOKEN_SCANNER_URL,
        path="/scan"
    )
    return response.json()

# Routes para Trading Engine
@app.post("/analyze", tags=["Trading Engine"])
async def analyze_tokens(request: Request):
    """Analiza tokens nuevos"""
    response = await proxy_request(
        client=app.state.http_client,
        method="POST",
        service_url=TRADING_ENGINE_URL,
        path="/analyze"
    )
    return response.json()

@app.post("/execute", tags=["Trading Engine"])
async def execute_buy_orders(request: Request):
    """Ejecuta órdenes de compra"""
    response = await proxy_request(
        client=app.state.http_client,
        method="POST",
        service_url=TRADING_ENGINE_URL,
        path="/execute"
    )
    return response.json()

@app.post("/cycle", tags=["Trading Engine"])
async def run_trading_cycle(request: Request):
    """Ejecuta un ciclo completo de trading"""
    response = await proxy_request(
        client=app.state.http_client,
        method="POST",
        service_url=TRADING_ENGINE_URL,
        path="/cycle"
    )
    return response.json()

@app.post("/track", tags=["Trading Engine"])
async def check_positions(request: Request):
    """Verifica posiciones abiertas"""
    response = await proxy_request(
        client=app.state.http_client,
        method="POST",
        service_url=TRADING_ENGINE_URL,
        path="/track"
    )
    return response.json()

# Endpoint de dashboard 
@app.get("/dashboard", tags=["Dashboard"])
async def get_dashboard_data(request: Request):
    """Obtiene datos consolidados para el dashboard"""
    try:
        # Obtener datos de múltiples servicios en paralelo
        tokens_task = proxy_request(
            client=app.state.http_client,
            method="GET",
            service_url=TOKEN_SCANNER_URL,
            path="/tokens"
        )
        
        rpc_status_task = proxy_request(
            client=app.state.http_client,
            method="GET",
            service_url=RPC_SERVICE_URL,
            path="/rpc/status"
        )
        
        # Esperar todos los resultados
        tokens_response, rpc_status_response = await asyncio.gather(
            tokens_task, rpc_status_task
        )
        
        # Consolidar datos
        return {
            "tokens": tokens_response.json(),
            "rpc_status": rpc_status_response.json(),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos del dashboard: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)