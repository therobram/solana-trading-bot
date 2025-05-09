#!/bin/bash
set -e

# Imprimir información sobre el modo de ejecución
echo "Iniciando Trading Engine en modo: $(if [ "$SIMULATION_MODE" = "true" ]; then echo "SIMULACIÓN"; else echo "REAL"; fi)"

# Si estamos en modo real, verificar conexión con Solana
if [ "$SIMULATION_MODE" != "true" ]; then
    echo "Verificando conexión con Solana..."
    # Asegurarse de que solana está en el PATH
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    # Verificar instalación
    which solana || echo "Solana no está en el PATH"
    solana --version || echo "Error al ejecutar solana --version"
    # Configurar RPC
    solana config set --url $RPC_SOLANA || echo "Error configurando URL de RPC Solana"
    solana cluster-version || echo "No se pudo conectar a Solana RPC, pero continuaremos de todos modos"
fi

# Iniciar la aplicación
exec uvicorn trading_engine.main:app --host 0.0.0.0 --port 8002 --reload