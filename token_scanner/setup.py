from setuptools import setup, find_packages

setup(
    name="token_scanner",
    version="0.1.0",
    description="Solana Token Scanner Microservice",
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
    ],
    python_requires=">=3.9",
)