import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpc_service.rpc_manager import get_best_rpc, get_all_rpc_statuses
import time

def test_rpc_endpoints():
    print("Probando todos los endpoints RPC...")
    
    statuses = get_all_rpc_statuses()
    healthy_count = 0
    
    print("\n=== Estado de los RPC endpoints ===")
    for status in statuses:
        health_status = "✅ ONLINE" if status["healthy"] else "❌ OFFLINE"
        latency = f"{status['latency_ms']}ms" if status["latency_ms"] else "N/A"
        print(f"{health_status} - Latencia: {latency} - {status['rpc']}")
        
        if status["healthy"]:
            healthy_count += 1
    
    print(f"\nEndpoints disponibles: {healthy_count}/{len(statuses)}")
    
    if healthy_count > 0:
        print("\n=== Probando selección del mejor RPC ===")
        best_rpc = get_best_rpc()
        print(f"✅ Mejor RPC seleccionado: {best_rpc["rpc"]}")
        return True
    else:
        print("❌ No hay RPC endpoints disponibles")
        return False

if __name__ == "__main__":
    test_rpc_endpoints()