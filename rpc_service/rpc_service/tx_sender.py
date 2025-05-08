### 📁 rpc_service/tx_sender.py
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.exceptions import SolanaRpcException
import base58
import time
from typing import Dict, Any
import asyncio
from functools import wraps
import backoff

from rpc_service.logger import setup_logger
from rpc_service.rpc_manager import get_best_rpc
from rpc_service.config import RPC_RETRY_ATTEMPTS

logger = setup_logger("tx_sender")

class TransactionError(Exception):
    """Excepción personalizada para errores de transacción"""
    pass

@backoff.on_exception(
    backoff.expo,
    (SolanaRpcException, TransactionError),
    max_tries=RPC_RETRY_ATTEMPTS,
    jitter=backoff.full_jitter
)
async def send_transaction_async(tx_data: str, opts: Dict[str, Any] = None) -> str:
    """
    Envía una transacción a la red Solana de forma asíncrona con reintento exponencial.
    
    Args:
        tx_data: Transacción codificada en base58
        opts: Opciones de envío de transacción
    
    Returns:
        Firma de la transacción (signature)
    
    Raises:
        TransactionError: Si hay un error al enviar la transacción
    """
    try:
        # Obtener el mejor RPC
        rpc_info = get_best_rpc()
        logger.info(f"Enviando transacción usando RPC: {rpc_info['rpc']}")
        
        # Crear cliente RPC
        client = Client(rpc_info['rpc'])
        
        # Convertir de base58 a bytes
        raw_tx = base58.b58decode(tx_data)
        
        # Opciones por defecto
        default_opts = {
            "skip_preflight": False,
            "preflight_commitment": "confirmed",
            "max_retries": 3
        }
        
        # Combinar con opciones proporcionadas
        if opts:
            default_opts.update(opts)
        
        # Enviar transacción
        tx_opts = TxOpts(**default_opts)
        start_time = time.time()
        response = client.send_raw_transaction(raw_tx, opts=tx_opts)
        elapsed = time.time() - start_time
        
        # Verificar respuesta
        if "result" in response:
            signature = response["result"]
            logger.info(f"Transacción enviada exitosamente en {elapsed:.2f}s. Signature: {signature}")
            return signature
        else:
            # Error en la respuesta
            error_msg = response.get("error", {}).get("message", "Error desconocido")
            logger.error(f"Error enviando transacción: {error_msg}")
            raise TransactionError(f"Error: {error_msg}")
    
    except Exception as e:
        logger.error(f"Excepción enviando transacción: {str(e)}")
        raise TransactionError(f"Error de transacción: {str(e)}")

def send_tx(tx_base58: str, opts: Dict[str, Any] = None) -> str:
    """Wrapper sincrónico para send_transaction_async"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(send_transaction_async(tx_base58, opts))
        return result
    finally:
        loop.close()