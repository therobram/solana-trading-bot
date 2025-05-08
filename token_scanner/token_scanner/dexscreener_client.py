### 📁 token_scanner/token_scanner/dexscreener_client.py
import aiohttp
from typing import Dict, List, Any, Optional
import asyncio
import json
import time
from datetime import datetime, timedelta
import backoff

from token_scanner.logger import setup_logger
from token_scanner.models import Token

logger = setup_logger("dexscreener_client")

class DexscreenerClient:
    """Cliente para interactuar con la API de Dexscreener"""
    
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
    async def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza una petición a la API de Dexscreener
        
        Args:
            url: URL completa de la API
            params: Parámetros de la petición
            
        Returns:
            Respuesta de la API como diccionario
        """
        self._check_rate_limit()
        
        try:
            logger.debug(f"Haciendo petición a {url} con parámetros: {params}")
            
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
    
    async def get_token_profiles(self) -> Dict[str, Any]:
        """
        Obtiene los perfiles de tokens más recientes
        
        Returns:
            Perfiles de tokens más recientes
        """
        url = "https://api.dexscreener.com/token-profiles/latest/v1"
        return await self._make_request(url)
    
    async def get_boosted_tokens(self) -> Dict[str, Any]:
        """
        Obtiene los tokens impulsados más recientes
        
        Returns:
            Tokens impulsados más recientes
        """
        url = "https://api.dexscreener.com/token-boosts/latest/v1"
        return await self._make_request(url)
    
    async def get_top_boosted_tokens(self) -> Dict[str, Any]:
        """
        Obtiene los tokens con más impulsos activos
        
        Returns:
            Tokens con más impulsos activos
        """
        url = "https://api.dexscreener.com/token-boosts/top/v1"
        return await self._make_request(url)
    
    async def get_token_orders(self, chain_id: str, token_address: str) -> List[Dict[str, Any]]:
        """
        Verifica órdenes pagadas de un token
        
        Args:
            chain_id: ID de la cadena (ej: "solana")
            token_address: Dirección del token
            
        Returns:
            Lista de órdenes pagadas
        """
        url = f"https://api.dexscreener.com/orders/v1/{chain_id}/{token_address}"
        return await self._make_request(url)
    
    async def get_pair(self, chain_id: str, pair_id: str) -> Dict[str, Any]:
        """
        Obtiene un par específico por su ID
        
        Args:
            chain_id: ID de la cadena (ej: "solana")
            pair_id: ID del par
            
        Returns:
            Información del par
        """
        url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_id}"
        return await self._make_request(url)
    
    async def search_pairs(self, query: str) -> Dict[str, Any]:
        """
        Busca pares que coincidan con la consulta
        
        Args:
            query: Consulta de búsqueda
            
        Returns:
            Pares encontrados
        """
        url = "https://api.dexscreener.com/latest/dex/search"
        params = {"q": query}
        return await self._make_request(url, params)
    
    async def get_token_pairs(self, chain_id: str, token_address: str) -> List[Dict[str, Any]]:
        """
        Obtiene los pools de una dirección de token dada
        
        Args:
            chain_id: ID de la cadena (ej: "solana")
            token_address: Dirección del token
            
        Returns:
            Lista de pools del token
        """
        url = f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
        return await self._make_request(url)
    
    async def get_tokens(self, chain_id: str, token_addresses: str) -> List[Dict[str, Any]]:
        """
        Obtiene uno o varios pares por dirección de token
        
        Args:
            chain_id: ID de la cadena (ej: "solana")
            token_addresses: Direcciones de tokens separadas por comas (max 30)
            
        Returns:
            Lista de información de tokens
        """
        url = f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_addresses}"
        return await self._make_request(url)
    
    async def get_recent_tokens(self, chain: str = "solana", max_age_hours: int = 24) -> List[Token]:
        """
        Obtiene tokens recientes en la cadena especificada
        
        Args:
            chain: Cadena blockchain (default: "solana")
            max_age_hours: Antigüedad máxima en horas (default: 24)
            
        Returns:
            Lista de tokens recientes como objetos Token
        """
        # Intentar obtener tokens recientes de diferentes maneras:
        
        # 1. Primero, intentar con los tokens impulsados recientemente
        tokens = []
        
        try:
            # Obtener tokens con boost
            boosted_tokens = await self.get_boosted_tokens()
            
            if isinstance(boosted_tokens, dict) and boosted_tokens.get("chainId") == chain:
                # Si es un solo token
                token_data = boosted_tokens
                token = Token(
                    address=token_data.get("tokenAddress", ""),
                    name="Unknown",  # Los datos no incluyen nombre
                    symbol="Unknown",  # Los datos no incluyen símbolo
                    network=chain,
                    price_usd=0,  # No disponible directamente
                    has_profile=True,  # Tiene perfil si está impulsado
                    booster_active=True,  # Tiene booster si está en esta lista
                    created_at=datetime.utcnow(),  # No hay timestamp disponible
                    metadata={
                        "icon": token_data.get("icon"),
                        "header": token_data.get("header"),
                        "description": token_data.get("description"),
                        "links": token_data.get("links", []),
                        "amount": token_data.get("amount"),
                        "totalAmount": token_data.get("totalAmount")
                    }
                )
                tokens.append(token)
            elif isinstance(boosted_tokens, list):
                # Si es una lista de tokens
                for token_data in boosted_tokens:
                    if token_data.get("chainId") == chain:
                        token = Token(
                            address=token_data.get("tokenAddress", ""),
                            name="Unknown",
                            symbol="Unknown",
                            network=chain,
                            price_usd=0,
                            has_profile=True,
                            booster_active=True,
                            created_at=datetime.utcnow(),
                            metadata={
                                "icon": token_data.get("icon"),
                                "header": token_data.get("header"),
                                "description": token_data.get("description"),
                                "links": token_data.get("links", []),
                                "amount": token_data.get("amount"),
                                "totalAmount": token_data.get("totalAmount")
                            }
                        )
                        tokens.append(token)
        except Exception as e:
            logger.warning(f"Error obteniendo tokens impulsados: {str(e)}")
        
        # 2. Si no hay tokens impulsados, buscar pares recientes usando la búsqueda
        if not tokens:
            try:
                # Buscar pares recientes
                search_result = await self.search_pairs(chain)
                pairs = search_result.get("pairs", [])
                
                # Filtrar por fecha de creación
                min_timestamp = datetime.utcnow() - timedelta(hours=max_age_hours)
                recent_pairs = []
                
                for pair in pairs:
                    if pair.get("chainId") != chain:
                        continue
                        
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
            except Exception as e:
                logger.warning(f"Error buscando pares recientes: {str(e)}")
        
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
        try:
            # Obtener pares del token
            pairs = await self.get_token_pairs(chain, token_address)
            
            if not pairs:
                return None
                
            # Tomamos el primer par como referencia
            pair = pairs[0] if isinstance(pairs, list) else pairs
            
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
                liquidity_pools_count=len(pairs) if isinstance(pairs, list) else 1,
                created_at=datetime.fromtimestamp(pair.get("pairCreatedAt", 0) / 1000) if pair.get("pairCreatedAt") else datetime.utcnow(),
                metadata={
                    "pairs": [{
                        "pair_address": p.get("pairAddress"),
                        "dex_id": p.get("dexId"),
                        "url": p.get("url"),
                        "liquidity_usd": p.get("liquidity", {}).get("usd", 0)
                    } for p in (pairs if isinstance(pairs, list) else [pairs])],
                    "fdv": pair.get("fdv"),
                    "price_change": pair.get("priceChange")
                }
            )
            
            # Comprobar si tiene booster activo
            try:
                # Intentar obtener información de impulsos
                boosts = await self.get_token_orders(chain, token_address)
                token.booster_active = bool(boosts and len(boosts) > 0)
            except:
                # Si falla, verificar según criterios secundarios
                token.booster_active = token.liquidity > 5000 and token.volume_24h > 5000
            
            return token
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del token {token_address}: {str(e)}")
            return None