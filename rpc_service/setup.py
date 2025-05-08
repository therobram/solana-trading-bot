from setuptools import setup, find_packages

setup(
    name="rpc_service",
    version="0.1.0",
    description="Solana RPC Service Microservice",
    author="Tu Nombre",
    author_email="tu@email.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "solana>=0.30.0",
        "solders>=0.18.0",
        "base58>=2.1.0",
        "python-dotenv>=1.0.0",
        "backoff>=2.2.1",
        "aiohttp>=3.8.4",
    ],
    python_requires=">=3.9",
)