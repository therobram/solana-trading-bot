"""Factory para diferentes implementaciones de Jupiter Client"""
import os
import json
import base64
import base58
import logging
import aiohttp
import backoff
import asyncio
from typing import Dict, Any, Optional, List

# Intentamos importar los módulos originales de Solana
try:
    # Primero intentamos importar los módulos originales de Solana
    from solana.rpc.api import Client
    from solana.keypair import Keypair
    from solana.transaction import Transaction, VersionedTransaction
    from solana.publickey import PublicKey
    REAL_SOLANA_IMPORTS = True
    logging.info("Usando módulos de solana-py reales")
except (ImportError, AttributeError, Exception) as e:
    # Si hay algún error, utilizamos nuestro wrapper
    logging.error(f"Error con módulos solana-py: {str(e)}")
    from trading_engine.solana_wrapper import Client, Keypair, Transaction, VersionedTransaction, PublicKey
    REAL_SOLANA_IMPORTS = False
    logging.info("Usando wrapper personalizado para Solana")

# Configuración de modo simulación
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"
USE_SOLANA_CLI = os.getenv("USE_SOLANA_CLI", "false").lower() == "true"

logger = logging.getLogger("jupiter_client_factory")

class JupiterApiClient:
    """Cliente para interactuar con Jupiter API sin usar CLI de Solana"""
    
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
            transaction = VersionedTransaction.deserialize(tx_buffer)
            transaction.sign([self.wallet])
            
            # 4. Enviar transacción directamente al RPC usando REST API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_url, 
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "sendTransaction",
                        "params": [
                            base64.b64encode(transaction.serialize()).decode('utf-8'),
                            {"encoding": "base64", "skipPreflight": True, "maxRetries": 3}
                        ]
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error enviando transacción: {response.status} - {error_text}")
                        return None
                        
                    result = await response.json()
                    if "result" in result:
                        signature = result["result"]
                        logger.info(f"Swap ejecutado. Signature: {signature}")
                        return signature
                    else:
                        error = result.get("error", {}).get("message", "Error desconocido")
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
            
        # Obtener balance usando REST API
        try:
            if token_mint == self.SOL_MINT:
                # Para SOL nativo
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.rpc_url, 
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getBalance",
                            "params": [str(self.wallet.public_key)]
                        }
                    ) as response:
                        result = await response.json()
                        if "result" in result:
                            return result["result"]["value"]
                        return None
            else:
                # Para tokens SPL
                token_account_params = [
                    str(self.wallet.public_key),
                    {"mint": token_mint}
                ]
                
                # Obtener cuentas de token
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.rpc_url, 
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getTokenAccountsByOwner",
                            "params": token_account_params
                        }
                    ) as response:
                        result = await response.json()
                        
                        if not result.get("result") or not result["result"].get("value"):
                            return 0
                        
                        # Si hay cuentas, obtener el balance
                        token_accounts = result["result"]["value"]
                        if token_accounts:
                            account_pubkey = token_accounts[0]["pubkey"]
                            
                            # Obtener info de la cuenta de token
                            async with session.post(
                                self.rpc_url, 
                                json={
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "method": "getTokenAccountBalance",
                                    "params": [account_pubkey]
                                }
                            ) as balance_response:
                                balance_result = await balance_response.json()
                                if "result" in balance_result and "value" in balance_result["result"]:
                                    return int(balance_result["result"]["value"]["amount"])
                
                return 0
                
        except Exception as e:
            logger.error(f"Error obteniendo balance de token {token_mint}: {str(e)}")
            return None

class JupiterCliClient:
    """Cliente para interactuar con Jupiter usando CLI de Solana"""
    
    QUOTE_API = "https://quote-api.jup.ag/v6/quote"
    SWAP_API = "https://quote-api.jup.ag/v6/swap"
    
    def __init__(self, wallet_private_key: str = None, rpc_url: str = None):
        """
        Inicializa el cliente de Jupiter con CLI de Solana
        
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
            transaction = VersionedTransaction.deserialize(tx_buffer)
            transaction.sign([self.wallet])
            
            # 4. Enviar transacción usando el CLI de Solana
            # Guardar transacción en un archivo temporal
            tx_file = "/tmp/swap_transaction.bin"
            with open(tx_file, "wb") as f:
                f.write(transaction.serialize())
            
            # Ejecutar comando solana para enviar transacción
            try:
                result = subprocess.run(
                    ["solana", "transaction-send", tx_file, "--url", self.rpc_url, "--output", "json"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Procesar respuesta
                response_data = json.loads(result.stdout.strip())
                signature = response_data.get("signature")
                if signature:
                    logger.info(f"Swap ejecutado con CLI. Signature: {signature}")
                    return signature
                else:
                    logger.error(f"Error enviando transacción con CLI: No signature")
                    return None
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Error ejecutando comando solana: {e.stderr}")
                return None
            except Exception as e:
                logger.error(f"Error en CLI de Solana: {str(e)}")
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
                try:
                    result = subprocess.run(
                        ["solana", "balance", str(self.wallet.public_key), "--url", self.rpc_url, "--output", "json"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    balance = float(result.stdout.strip())
                    return int(balance * 1_000_000_000)  # Convertir a lamports
                except Exception as e:
                    logger.error(f"Error obteniendo balance de SOL: {str(e)}")
                    return None
            
            # Para SPL tokens
            try:
                result = subprocess.run(
                    ["spl-token", "balance", "--owner", str(self.wallet.public_key), token_mint, "--url", self.rpc_url],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # La salida es algo como "0.001 TokenSymbol"
                output = result.stdout.strip()
                amount_str = output.split()[0]  # Tomar el primer token
                
                # Determinar decimales para este token
                decimals = 6 if token_mint == self.USDC_MINT else 9  # Por defecto SPL tokens tienen 9 decimales
                
                # Convertir a unidades menores
                amount = float(amount_str)
                return int(amount * (10 ** decimals))
                
            except subprocess.CalledProcessError:
                # Si el token no existe en la wallet, devolver 0
                return 0
            except Exception as e:
                logger.error(f"Error obteniendo balance de token {token_mint}: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo balance de token {token_mint}: {str(e)}")
            return None

def create_jupiter_client(wallet_private_key=None, rpc_url=None):
    """Factory para crear el cliente apropiado según configuración"""
    use_cli = os.getenv("USE_SOLANA_CLI", "false").lower() == "true"
    
    if use_cli and not SIMULATION_MODE:
        logger.info("Usando implementación basada en CLI de Solana")
        return JupiterCliClient(wallet_private_key, rpc_url)
    else:
        logger.info("Usando implementación basada en API REST")
        return JupiterApiClient(wallet_private_key, rpc_url)