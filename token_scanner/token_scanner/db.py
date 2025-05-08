### 📁 token_scanner/db.py
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
import motor.motor_asyncio
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

from token_scanner.logger import setup_logger
from token_scanner.models import Token, TokenStatus, TokenAnalysis, Transaction
from token_scanner.config import Config

logger = setup_logger("database")

class Database:
    """Clase para interactuar con MongoDB"""
    
    def __init__(self, mongo_uri: str = None):
        """
        Inicializa la conexión a MongoDB
        
        Args:
            mongo_uri: URI de conexión a MongoDB (si es None, se toma de MONGO_URI)
        """
        if mongo_uri is None:

            Config.load_environment()
            mongo_uri = Config.get_mongo_uri()
            # mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/trading_bot")
            
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client.get_database("trading_bot")
        
        # Colecciones
        self.tokens = self.db.tokens
        self.analyses = self.db.token_analyses
        self.transactions = self.db.transactions
        
        # Inicializar índices
        asyncio.create_task(self._ensure_indexes())
    
    async def _ensure_indexes(self):
        """Crea los índices necesarios en las colecciones"""
        try:
            await self.tokens.create_index([("address", ASCENDING)], unique=True)
            await self.tokens.create_index([("created_at", DESCENDING)])
            await self.tokens.create_index([("status", ASCENDING)])
            
            await self.analyses.create_index([("token_address", ASCENDING)])
            await self.analyses.create_index([("analysis_timestamp", DESCENDING)])
            
            await self.transactions.create_index([("token_address", ASCENDING)])
            await self.transactions.create_index([("timestamp", DESCENDING)])
            
            logger.info("Índices de base de datos creados correctamente")
        except PyMongoError as e:
            logger.error(f"Error creando índices: {str(e)}")
    
    async def save_token(self, token: Token) -> str:
        """
        Guarda un token en la base de datos
        
        Args:
            token: Objeto Token a guardar
            
        Returns:
            ID del documento insertado
        """
        try:
            # Verificar si el token ya existe
            existing = await self.tokens.find_one({"address": token.address})
            
            if existing:
                # Actualizar token existente
                token.updated_at = datetime.utcnow()
                result = await self.tokens.update_one(
                    {"address": token.address},
                    {"$set": token.dict(exclude={"created_at"})}
                )
                return str(existing["_id"])
            else:
                # Insertar nuevo token
                result = await self.tokens.insert_one(token.dict())
                return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error guardando token: {str(e)}")
            raise
    
    async def token_exists(self, address: str) -> bool:
        """
        Verifica si un token existe en la base de datos
        
        Args:
            address: Dirección del token
            
        Returns:
            True si el token existe, False en caso contrario
        """
        try:
            count = await self.tokens.count_documents({"address": address})
            return count > 0
        except PyMongoError as e:
            logger.error(f"Error verificando existencia de token: {str(e)}")
            return False
    
    async def get_token(self, address: str) -> Optional[Token]:
        """
        Obtiene un token por su dirección
        
        Args:
            address: Dirección del token
            
        Returns:
            Objeto Token o None si no se encuentra
        """
        try:
            document = await self.tokens.find_one({"address": address})
            if document:
                return Token(**document)
            return None
        except PyMongoError as e:
            logger.error(f"Error obteniendo token: {str(e)}")
            return None
    
    async def get_tokens_by_status(self, status: TokenStatus) -> List[Token]:
        """
        Obtiene tokens por su estado
        
        Args:
            status: Estado de los tokens a obtener
            
        Returns:
            Lista de objetos Token
        """
        try:
            cursor = self.tokens.find({"status": status})
            tokens = []
            async for doc in cursor:
                tokens.append(Token(**doc))
            return tokens
        except PyMongoError as e:
            logger.error(f"Error obteniendo tokens por estado: {str(e)}")
            return []
    
    async def update_token_status(self, address: str, status: TokenStatus) -> bool:
        """
        Actualiza el estado de un token
        
        Args:
            address: Dirección del token
            status: Nuevo estado
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            result = await self.tokens.update_one(
                {"address": address},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error actualizando estado de token: {str(e)}")
            return False
    
    async def save_analysis(self, analysis: TokenAnalysis) -> str:
        """
        Guarda un análisis de token
        
        Args:
            analysis: Objeto TokenAnalysis a guardar
            
        Returns:
            ID del documento insertado
        """
        try:
            result = await self.analyses.insert_one(analysis.dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error guardando análisis: {str(e)}")
            raise
    
    async def get_latest_analysis(self, token_address: str) -> Optional[TokenAnalysis]:
        """
        Obtiene el análisis más reciente de un token
        
        Args:
            token_address: Dirección del token
            
        Returns:
            Objeto TokenAnalysis o None si no se encuentra
        """
        try:
            document = await self.analyses.find_one(
                {"token_address": token_address},
                sort=[("analysis_timestamp", DESCENDING)]
            )
            if document:
                return TokenAnalysis(**document)
            return None
        except PyMongoError as e:
            logger.error(f"Error obteniendo análisis: {str(e)}")
            return None
    
    async def save_transaction(self, transaction: Transaction) -> str:
        """
        Guarda una transacción
        
        Args:
            transaction: Objeto Transaction a guardar
            
        Returns:
            ID del documento insertado
        """
        try:
            result = await self.transactions.insert_one(transaction.dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error guardando transacción: {str(e)}")
            raise
    
    async def get_transactions_by_token(self, token_address: str) -> List[Transaction]:
        """
        Obtiene las transacciones de un token
        
        Args:
            token_address: Dirección del token
            
        Returns:
            Lista de objetos Transaction
        """
        try:
            cursor = self.transactions.find({"token_address": token_address})
            transactions = []
            async for doc in cursor:
                transactions.append(Transaction(**doc))
            return transactions
        except PyMongoError as e:
            logger.error(f"Error obteniendo transacciones: {str(e)}")
            return []