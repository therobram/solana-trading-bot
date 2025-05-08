### 📁 rpc_service/rpc_manager.py
from solana.rpc.api import Client
import time
import random
from functools import lru_cache
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
import json

from rpc_service.config import RPCS, RPC_CACHE_TTL, RPC_TIMEOUT, RPC_RETRY_ATTEMPTS
from rpc_service.logger import setup_logger

logger = setup_logger("rpc_manager")

# Cache con TTL implementado como clase
class RPCCache:
    def __init__(self, ttl: int):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            # Expirado, eliminar
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        self.cache.clear()

# Instancia de cache
cache = RPCCache(RPC_CACHE_TTL)

async def measure_rpc_health(rpc_url: str) -> Tuple[str, float, bool]:
    """Mide la latencia de un RPC de forma asíncrona"""
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                rpc_url,
                json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                timeout=aiohttp.ClientTimeout(total=RPC_TIMEOUT)
            ) as response:
                result = await response.json()
                latency = time.time() - start_time
                is_healthy = response.status == 200 and result.get("result") == "ok"
                return rpc_url, latency, is_healthy
    except Exception as e:
        logger.warning(f"Error midiendo latencia de {rpc_url}: {str(e)}")
        return rpc_url, float("inf"), False

async def check_all_rpcs() -> List[Dict]:
    """Verifica la salud de todos los RPCs de forma concurrente"""
    tasks = [measure_rpc_health(rpc) for rpc in RPCS]
    results = await asyncio.gather(*tasks)
    
    # Formatear resultados
    statuses = []
    for rpc_url, latency, is_healthy in results:
        statuses.append({
            "rpc": rpc_url,
            "latency_ms": round(latency * 1000, 2) if latency < float("inf") else None,
            "healthy": is_healthy
        })
    return statuses

def get_best_rpc(force_refresh=False) -> dict:
    """
    Obtiene el mejor RPC basado en latencia, con soporte para cache
    
    Args:
        force_refresh (bool): Forzar actualización ignorando cache
        
    Returns:
        dict: Diccionario con información del mejor RPC: {"rpc": url, "latency_ms": valor}
    """
    if not force_refresh:
        cached_rpc = cache.get("best_rpc")
        if cached_rpc:
            logger.debug(f"Usando RPC cacheado: {cached_rpc['rpc']} ({cached_rpc['latency_ms']}ms)")
            return cached_rpc
    
    # Necesitamos refrescar
    logger.info("Buscando el mejor RPC disponible...")
    
    # Ejecutar el loop de eventos para la verificación asíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    statuses = loop.run_until_complete(check_all_rpcs())
    loop.close()
    
    # Filtrar solo los RPCs saludables
    healthy_rpcs = [status for status in statuses if status["healthy"]]
    
    if not healthy_rpcs:
        logger.warning("No hay RPCs saludables disponibles. Intentando con cualquiera...")
        # Crear un diccionario de fallback con un RPC aleatorio
        fallback_rpc = random.choice(RPCS)
        return {
            "rpc": fallback_rpc,
            "latency_ms": None,
            "healthy": False
        }
    
    # Ordenar por latencia y seleccionar el mejor
    best_rpc = min(healthy_rpcs, key=lambda x: x["latency_ms"])
    logger.info(f"Mejor RPC seleccionado: {best_rpc['rpc']} ({best_rpc['latency_ms']}ms)")
    
    # Actualizar cache
    cache.set("best_rpc", best_rpc)
    return best_rpc

def get_all_rpc_statuses() -> List[Dict]:
    """Retorna el estado actual de todos los RPCs"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    statuses = loop.run_until_complete(check_all_rpcs())
    loop.close()
    return statuses