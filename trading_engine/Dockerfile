FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias (actualizado según la documentación oficial)
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

# Copiar el instalador de Solana previamente descargado
COPY solana-install.sh .

# Instalar Solana CLI usando el instalador local
RUN chmod +x solana-install.sh && \
    ./solana-install.sh && \
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH" && \
    echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc

# Configurar PATH para los siguientes comandos
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"

# Verificar instalación de Solana (con manejo de errores)
RUN ls -la /root/.local/share/solana/install/active_release/bin/ || echo "Directorio no encontrado" && \
    which solana || echo "Solana no está en el PATH" && \
    solana --version || echo "Error al ejecutar solana --version"

# Copiar requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

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