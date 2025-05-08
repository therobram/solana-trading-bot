### 📁 token_scanner/dexscreener_client.py
import aiohttp
from typing import Dict, List, Any, Optional
import asyncio
import json
import time
from datetime import datetime, timedelta
import backoff

from logger import setup_logger
from models import Token

logger = setup_logger("dexscreener_client")

class DexscreenerClient:
    """Cliente para interactuar con la API de Dexscreener"""
    
    BASE_URL = "https://api.dexscreener.com/latest"
    
    def __init__(self, rate_limit_per_min: int = 60):
        """
        Inicializa el cliente de Dexscreener
        
        Args:
            rate_limit_per_min: Límite de peticiones por minuto (por defecto 60)
        """
        self.rate_limit = rate_limit_per_min
        self.request_times = []
    
    def _check_rate_limit(self):
        """
        Verifica y espera si es necesario para respetar el rate limit
        """
        now = time.time()
        # Limpiar peticiones antiguas (más de 1 minuto)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Si estamos en el límite, esperar
        if len(self.request_times) >= self.rate_limit:
            oldest = min(self.request_times)
            sleep_time = 60 - (now - oldest)
            if sleep_time > 0:
                logger.warning(f"Rate limit alcanzado, esperando {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        # Registrar esta petición
        self.request_times.append(time.time())
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza una petición a la API de Dexscreener
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de la petición
            
        Returns:
            Respuesta de la API como diccionario
        """
        self._check_rate_limit()
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Error en petición a Dexscreener: {response.status} - {await response.text()}")
                        response.raise_for_status()
                    
                    data = await response.json()
                    return data
        except Exception as e:
            logger.error(f"Error en petición a Dexscreener: {str(e)}")
            raise
    
    async def search_tokens(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca tokens en Dexscreener
        
        Args:
            query: Consulta de búsqueda
            
        Returns:
            Lista de tokens encontrados
        """
        response = await self._make_request(f"search", {"q": query})
        return response.get("pairs", [])
    
    async def get_token_pairs(self, token_address: str) -> List[Dict[str, Any]]:
        """
        Obtiene los pares de un token
        
        Args:
            token_address: Dirección del token
            
        Returns:
            Lista de pares del token
        """
        response = await self._make_request(f"tokens/{token_address}")
        return response.get("pairs", [])
    
    async def get_recent_tokens(self, chain: str = "solana", max_age_hours: int = 24) -> List[Token]:
        """
        Obtiene tokens recientes en la cadena especificada
        
        Args:
            chain: Cadena blockchain (default: "solana")
            max_age_hours: Antigüedad máxima en horas (default: 24)
            
        Returns:
            Lista de tokens recientes como objetos Token
        """
        # Primero obtenemos los pares más recientes
        response = await self._make_request(f"pairs/{chain}")
        pairs = response.get("pairs", [])
        
        # Filtramos por fecha de creación
        min_timestamp = datetime.utcnow() - timedelta(hours=max_age_hours)
        recent_pairs = []
        
        for pair in pairs:
            # Verificar si tenemos timestamp de creación
            created_at = pair.get("pairCreatedAt")
            if not created_at:
                continue
                
            # Convertir timestamp a datetime
            try:
                pair_created_at = datetime.fromtimestamp(created_at / 1000)
                if pair_created_at >= min_timestamp:
                    recent_pairs.append(pair)
            except:
                continue
        
        # Convertir a objetos Token
        tokens = []
        for pair in recent_pairs:
            # Extraer información del token base
            base_token = pair.get("baseToken", {})
            if not base_token or not base_token.get("address"):
                continue
                
            # Crear objeto Token
            token = Token(
                address=base_token.get("address"),
                name=base_token.get("name", "Unknown"),
                symbol=base_token.get("symbol", "????"),
                network=chain,
                price_usd=float(pair.get("priceUsd", 0)),
                volume_24h=float(pair.get("volume", {}).get("h24", 0)),
                liquidity=float(pair.get("liquidity", {}).get("usd", 0)),
                has_profile=bool(base_token.get("name") and len(base_token.get("name", "")) > 0),
                created_at=datetime.fromtimestamp(pair.get("pairCreatedAt", 0) / 1000),
                metadata={
                    "pair_address": pair.get("pairAddress"),
                    "dex_id": pair.get("dexId"),
                    "url": pair.get("url"),
                    "fdv": pair.get("fdv"),
                    "price_change": pair.get("priceChange")
                }
            )
            
            # Solo agregar si no está duplicado
            if token.address not in [t.address for t in tokens]:
                tokens.append(token)
        
        logger.info(f"Se encontraron {len(tokens)} tokens recientes en {chain}")
        return tokens
    
    async def get_token_details(self, token_address: str, chain: str = "solana") -> Optional[Token]:
        """
        Obtiene detalles completos de un token
        
        Args:
            token_address: Dirección del token
            chain: Cadena blockchain (default: "solana")
            
        Returns:
            Objeto Token con detalles completos o None si no se encuentra
        """
        response = await self._make_request(f"tokens/{chain}/{token_address}")
        pairs = response.get("pairs", [])
        
        if not pairs:
            return None
            
        # Tomamos el primer par como referencia
        pair = pairs[0]
        base_token = pair.get("baseToken", {})
        
        if not base_token or not base_token.get("address"):
            return None
            
        # Crear objeto Token
        token = Token(
            address=base_token.get("address"),
            name=base_token.get("name", "Unknown"),
            symbol=base_token.get("symbol", "????"),
            network=chain,
            price_usd=float(pair.get("priceUsd", 0)),
            volume_24h=float(pair.get("volume", {}).get("h24", 0)),
            liquidity=float(pair.get("liquidity", {}).get("usd", 0)),
            has_profile=bool(base_token.get("name") and len(base_token.get("name", "")) > 0),
            liquidity_pools_count=len(pairs),
            created_at=datetime.fromtimestamp(pair.get("pairCreatedAt", 0) / 1000) if pair.get("pairCreatedAt") else datetime.utcnow(),
            metadata={
                "pairs": [{
                    "pair_address": p.get("pairAddress"),
                    "dex_id": p.get("dexId"),
                    "url": p.get("url"),
                    "liquidity_usd": p.get("liquidity", {}).get("usd", 0)
                } for p in pairs],
                "fdv": pair.get("fdv"),
                "price_change": pair.get("priceChange")
            }
        )
        
        # Comprobamos si tiene booster activo (simplificado - implementar lógica real)
        # En una implementación real, necesitarías verificar esto contra alguna fuente de datos
        token.booster_active = token.liquidity > 5000 and token.volume_24h > 5000
        
        return token