FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libudev-dev \
    libssl-dev \
    llvm \
    libclang-dev \
    protobuf-compiler \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio para logs
RUN mkdir -p logs

# Instalar Rust (necesario para algunos paquetes de Solana)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . "$HOME/.cargo/env"
ENV PATH="/root/.cargo/bin:${PATH}"

# Copiar instalador local como respaldo
COPY solana-install.sh /tmp/solana-install.sh.backup

# Intentar descargar el instalador, usar copia local si falla
RUN curl -sSfL https://release.anza.xyz/stable/install -o solana-install.sh || \
    (echo "Descarga fallida, usando copia local" && cp /tmp/solana-install.sh.backup solana-install.sh) && \
    chmod +x solana-install.sh && \
    ./solana-install.sh && \
    export PATH="/root/.local/share/solana/install/active_release/bin:$PATH" && \
    echo 'export PATH="/root/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc && \
    rm -f solana-install.sh

# Configurar PATH para los siguientes comandos
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"

# Verificar instalación de Solana (con manejo de errores)
RUN ls -la /root/.local/share/solana/install/active_release/bin/ || echo "Directorio no encontrado" && \
    which solana || echo "Solana no está en el PATH" && \
    solana --version || echo "Error al ejecutar solana --version"

# Copiar requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias Python incluyendo solana-py específicamente
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir solana==0.30.2

# Copiar el script de entrada
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Copiar código fuente
COPY . .

# Instalar el paquete en modo desarrollo
RUN pip install -e .

# Variables de entorno configurables en tiempo de ejecución
ENV ENVIRONMENT=docker
ENV SIMULATION_MODE=false

# Exponer puerto
EXPOSE 8002

# Comando de inicio
ENTRYPOINT ["/docker-entrypoint.sh"]