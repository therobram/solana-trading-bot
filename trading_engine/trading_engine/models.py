### 📁 trading_engine/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import enum

class TokenStatus(str, enum.Enum):
    """Estado del token"""
    NEW = "new"
    ANALYZED = "analyzed"
    BOUGHT = "bought"
    SOLD = "sold"
    REJECTED = "rejected"

class Token(BaseModel):
    """Modelo para un token detectado"""
    address: str = Field(..., description="Dirección del contrato del token")
    name: str
    symbol: str
    network: str = Field(default="solana")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    has_profile: bool = False
    booster_active: bool = False
    liquidity: float = 0
    volume_24h: float = 0
    price_usd: float = 0
    liquidity_pools_count: int = 0
    status: TokenStatus = TokenStatus.NEW
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TokenAnalysis(BaseModel):
    """Modelo para el análisis de un token"""
    token_address: str
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    investment_score: float
    investment_amount: float
    buy_recommendation: bool
    reasons: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Transaction(BaseModel):
    """Modelo para transacciones de trading"""
    token_address: str
    transaction_type: str  # "buy" o "sell"
    amount: float
    price_usd: float
    total_usd: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tx_signature: str
    status: str = "completed"
    metadata: Dict[str, Any] = Field(default_factory=dict)