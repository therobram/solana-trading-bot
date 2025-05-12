### 📁 trading_engine/jupiter_client.py
import os
from trading_engine.jupiter_client_factory import create_jupiter_client

# Reexportar la función factory como el punto de entrada principal
def JupiterClient(wallet_private_key=None, rpc_url=None):
    """
    Crear una instancia del cliente de Jupiter apropiado según configuración
    
    Args:
        wallet_private_key: Clave privada de la wallet en formato JSON (array de enteros)
        rpc_url: URL del nodo RPC Solana
        
    Returns:
        Instancia del cliente de Jupiter
    """
    return create_jupiter_client(wallet_private_key, rpc_url)