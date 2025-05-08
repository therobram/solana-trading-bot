# test_dex_client.py
import asyncio
from token_scanner.dexscreener_client import DexscreenerClient

async def test_client():
    client = DexscreenerClient()
    
    # Probar obtener tokens impulsados
    print("Obteniendo tokens impulsados...")
    boosted = await client.get_boosted_tokens()
    print(f"Tokens impulsados: {boosted}")
    
    # Probar obtener tokens recientes
    print("Obteniendo tokens recientes...")
    tokens = await client.get_recent_tokens(chain="solana", max_age_hours=24)
    print(f"Se encontraron {len(tokens)} tokens recientes")
    
    # Mostrar detalles del primer token si hay alguno
    if tokens:
        first_token = tokens[0]
        print(f"Primer token: {first_token.name} ({first_token.symbol})")
        print(f"Dirección: {first_token.address}")
        print(f"Precio USD: ${first_token.price_usd}")
        print(f"Volumen 24h: ${first_token.volume_24h}")
        print(f"Liquidez: ${first_token.liquidity}")
        print(f"Tiene perfil: {first_token.has_profile}")
        print(f"Booster activo: {first_token.booster_active}")

if __name__ == "__main__":
    asyncio.run(test_client())