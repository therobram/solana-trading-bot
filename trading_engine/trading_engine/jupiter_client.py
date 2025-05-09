### 📁 trading_engine/jupiter_client.py
import aiohttp
import json
import base58
from typing import Dict, Any, Optional, List
import asyncio
import backoff
import base64
import os

# Configuración de modo simulación
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

# Importaciones de Solana con manejo de errores
try:
    # Primero intentamos importar los módulos originales de Solana
    from solana.rpc.api import Client
    from solana.keypair import Keypair
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
    
    # Verificamos que podemos crear instancias básicas para confirmar que funcionan
    test_publickey = PublicKey("11111111111111111111111111111111")
    print("Usando módulos de solana-py reales")
except (ImportError, AttributeError, Exception) as e:
    # Si hay algún error, utilizamos nuestro wrapper
    print(f"Error con módulos solana-py: {str(e)}")
    print("Usando wrapper personalizado para Solana")
    from trading_engine.solana_wrapper import Client, Keypair, Transaction, PublicKey

from trading_engine.logger import setup_logger
from trading_engine.config import Config

logger = setup_logger("jupiter_client")

class JupiterClient:
    """Cliente para interactuar con Jupiter API para swaps en Solana"""
    
    QUOTE_API = "https://quote-api.jup.ag/v6/quote"
    SWAP_API = "https://quote-api.jup.ag/v6/swap"
    
    def __init__(self, wallet_private_key: str = None, rpc_url: str = None):
        """
        Inicializa el cliente de Jupiter
        
        Args:
            wallet_private_key: Clave privada de la wallet en formato JSON (array de enteros)
            rpc_url: URL del nodo RPC Solana
        """
        # Log del modo de ejecución
        if SIMULATION_MODE:
            logger.warning("Ejecutando Jupiter Client en MODO SIMULACIÓN - sin transacciones reales")
        
        # Configurar wallet
        if wallet_private_key is None:
            wallet_private_key = os.getenv("PRIVATE_KEY_JSON")
        
        if wallet_private_key:
            try:
                # Convertir de formato JSON a bytes
                secret_key = bytes(json.loads(wallet_private_key))
                self.wallet = Keypair.from_secret_key(secret_key)
                logger.info(f"Wallet configurada: {self.wallet.public_key}")
            except Exception as e:
                logger.error(f"Error configurando wallet: {str(e)}")
                self.wallet = None
        else:
            logger.warning("No se proporcionó clave privada para la wallet")
            self.wallet = None
        
        # Configurar RPC
        if rpc_url is None:
            rpc_url = os.getenv("RPC_SOLANA", "https://api.mainnet-beta.solana.com")
        self.rpc_url = rpc_url
        self.rpc_client = Client(rpc_url)
        
        # Constantes
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5
    )
    async def get_quote(
        self, 
        input_mint: str, 
        output_mint: str, 
        amount: int,
        slippage_bps: int = 50,
        swap_mode: str = "ExactIn"
    ) -> Dict[str, Any]:
        """
        Obtiene una cotización para un swap
        
        Args:
            input_mint: Dirección del token de entrada
            output_mint: Dirección del token de salida
            amount: Cantidad de tokens de entrada (en unidades menores)
            slippage_bps: Slippage máximo en basis points (1% = 100)
            swap_mode: Modo de swap ("ExactIn" o "ExactOut")
            
        Returns:
            Respuesta de la API de cotización
        """
        # Si estamos en modo simulación, devolver datos simulados
        if SIMULATION_MODE:
            logger.info(f"[SIMULACIÓN] Obteniendo cotización para {amount} de {input_mint} a {output_mint}")
            
            # Proporcionar una cotización simulada pero realista
            # Un factor de conversión aleatorio pero que parezca realista
            conversion_factor = 0.95  # Ejemplo: pérdida del 5% por slippage, etc.
            
            return {
                "inAmount": str(amount),
                "outAmount": str(int(amount * conversion_factor)),
                "otherAmountThreshold": str(int(amount * conversion_factor * (1 - slippage_bps/10000))),
                "priceImpactPct": "0.5",
                "marketInfos": [],
                "swapMode": swap_mode
            }
        
        # Código original para obtener cotización real
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": slippage_bps,
            "swapMode": swap_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.QUOTE_API, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error en Jupiter Quote API: {response.status} - {error_text}")
                        response.raise_for_status()
                    
                    data = await response.json()
                    logger.debug(f"Cotización recibida: {json.dumps(data, indent=2)}")
                    return data
        except Exception as e:
            logger.error(f"Error obteniendo cotización en Jupiter: {str(e)}")
            raise
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5
    )
    async def prepare_swap_transaction(
        self, 
        quote_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepara una transacción de swap basada en una cotización
        
        Args:
            quote_response: Respuesta de la API de cotización
            
        Returns:
            Información de la transacción
        """
        if not self.wallet:
            raise ValueError("No se ha configurado una wallet")
        
        # Si estamos en modo simulación, devolver datos simulados
        if SIMULATION_MODE:
            logger.info("[SIMULACIÓN] Preparando transacción de swap simulada")
            
            # Crear una transacción simulada en base64 (solo bytes aleatorios)
            fake_tx = base64.b64encode(os.urandom(128)).decode('utf-8')
            
            return {
                "swapTransaction": fake_tx
            }
        
        # Código original para preparar transacción real
        try:
            payload = {
                "quoteResponse": quote_response,
                "userPublicKey": str(self.wallet.public_key),
                "wrapUnwrapSOL": True  # Gestionar conversión SOL<->WSOL automáticamente
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.SWAP_API, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error en Jupiter Swap API: {response.status} - {error_text}")
                        response.raise_for_status()
                    
                    data = await response.json()
                    return data
        except Exception as e:
            logger.error(f"Error preparando transacción de swap: {str(e)}")
            raise
    
    async def execute_swap(
        self, 
        input_mint: str, 
        output_mint: str, 
        amount: int,
        slippage_bps: int = 50
    ) -> Optional[str]:
        """
        Ejecuta un swap completo (obtener cotización, preparar y enviar transacción)
        
        Args:
            input_mint: Dirección del token de entrada
            output_mint: Dirección del token de salida
            amount: Cantidad de tokens de entrada (en unidades menores)
            slippage_bps: Slippage máximo en basis points (1% = 100)
            
        Returns:
            Firma de la transacción (signature) o None si falla
        """
        try:
            logger.info(f"Iniciando swap de {amount} tokens {input_mint} → {output_mint}")
            
            # 1. Obtener cotización
            quote = await self.get_quote(input_mint, output_mint, amount, slippage_bps)
            
            if not quote or not quote.get("outAmount") or quote.get("outAmount") == "0":
                logger.error("No se pudo obtener una cotización válida")
                return None
            
            logger.info(f"Cotización: entrada={quote.get('inAmount')}, "
                       f"salida={quote.get('outAmount')}, "
                       f"precio={quote.get('priceImpactPct')}%")
            
            # 2. Preparar transacción
            swap_data = await self.prepare_swap_transaction(quote)
            
            if not swap_data or not swap_data.get("swapTransaction"):
                logger.error("No se pudo preparar la transacción de swap")
                return None
            
            # 3. Decodificar y firmar transacción
            tx_data = swap_data.get("swapTransaction")
            tx_buffer = base64.b64decode(tx_data)
            
            # Si estamos en modo simulación, generar una firma simulada
            if SIMULATION_MODE:
                logger.info("[SIMULACIÓN] Simulando firma y envío de transacción")
                signature = f"SimSignature{hash(tx_data)}"
                logger.info(f"[SIMULACIÓN] Swap ejecutado. Signature: {signature}")
                return signature
            
            # Para versioned transaction (Jupiter v6+)
            try:
                from solana.transaction import VersionedTransaction
            except ImportError:
                from trading_engine.solana_wrapper import VersionedTransaction
                
            transaction = VersionedTransaction.deserialize(tx_buffer)
            transaction.sign([self.wallet])
            
            # 4. Enviar transacción
            encoded_tx = base64.b64encode(transaction.serialize()).decode("utf-8")
            
            tx_opts = {
                "skipPreflight": True,
                "maxRetries": 3
            }
            
            response = self.rpc_client.send_raw_transaction(
                transaction.serialize(), 
                opts=tx_opts
            )
            
            if "result" in response:
                signature = response["result"]
                logger.info(f"Swap ejecutado. Signature: {signature}")
                return signature
            else:
                error = response.get("error", {}).get("message", "Error desconocido")
                logger.error(f"Error enviando transacción: {error}")
                return None
                
        except Exception as e:
            logger.error(f"Error ejecutando swap: {str(e)}", exc_info=True)
            return None
    
    async def get_token_balance(self, token_mint: str) -> Optional[int]:
        """
        Obtiene el balance de un token en la wallet
        
        Args:
            token_mint: Dirección del token
            
        Returns:
            Balance en unidades menores (lamports/decimals) o None si falla
        """
        if not self.wallet:
            raise ValueError("No se ha configurado una wallet")
        
        # Si estamos en modo simulación, devolver datos simulados
        if SIMULATION_MODE:
            logger.info(f"[SIMULACIÓN] Obteniendo balance simulado para {token_mint}")
            
            # Valores simulados para diferentes tokens
            if token_mint == self.SOL_MINT:
                return 1_000_000_000  # 1 SOL en lamports
            elif token_mint == self.USDC_MINT:
                return 1_000_000     # 1 USDC (6 decimales)
            else:
                return 1_000_000_000  # 1 unidad de token genérico (9 decimales típico)
            
        try:
            # Para SOL nativo
            if token_mint == self.SOL_MINT:
                response = self.rpc_client.get_balance(self.wallet.public_key)
                if "result" in response:
                    return response["result"]["value"]
                return None
            
            # Para SPL tokens
            try:
                from spl.token.client import Token
            except ImportError:
                logger.error("No se pudo importar spl.token.client.Token")
                return None
            
            token_client = Token(
                conn=self.rpc_client,
                pubkey=PublicKey(token_mint),
                program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
                payer=self.wallet
            )
            
            token_accounts = self.rpc_client.get_token_accounts_by_owner(
                self.wallet.public_key,
                {"mint": PublicKey(token_mint)}
            )
            
            if not token_accounts or not token_accounts.get("result") or not token_accounts["result"]["value"]:
                return 0
            
            account = token_accounts["result"]["value"][0]
            pubkey = PublicKey(account["pubkey"])
            info = token_client.get_account_info(pubkey)
            
            return info["amount"]
            
        except Exception as e:
            logger.error(f"Error obteniendo balance de token {token_mint}: {str(e)}")
            return None