from setuptools import setup, find_packages

setup(
    name="trading_engine",
    version="0.1.0",
    description="Trading Engine para DEX en Solana",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "motor>=3.1.1",
        "pymongo>=4.3.3",
        "python-dotenv>=1.0.0",
        "pydantic>=1.10.7",
        "aiohttp>=3.8.4",
        "backoff>=2.2.1",
        "solana>=0.30.0",
        "solders>=0.18.0",
        "base58>=2.1.0",
    ],
    python_requires=">=3.9",
)