### 📁 trading_engine/token_evaluator.py
from typing import Dict, List, Tuple, Any, Optional
from models import Token, TokenAnalysis

class TokenEvaluator:
    """Clase para evaluar tokens y determinar decisiones de inversión"""
    
    def __init__(self):
        """Inicializa el evaluador de tokens"""
        pass
    
    def evaluate_token(self, token: Token) -> TokenAnalysis:
        """
        Evalúa un token y determina si se debe invertir
        
        Args:
            token: Objeto Token a evaluar
            
        Returns:
            Objeto TokenAnalysis con el resultado de la evaluación
        """
        # Inicializar análisis
        analysis = TokenAnalysis(
            token_address=token.address,
            investment_score=0.0,
            investment_amount=0.0,
            buy_recommendation=False,
            reasons=[]
        )
        
        # Determinar monto de inversión base según criterios
        amount = self._determine_investment_amount(token)
        analysis.investment_amount = amount
        
        # Calcular score de inversión (0-100)
        score = self._calculate_investment_score(token)
        analysis.investment_score = score
        
        # Determinar recomendación de compra
        analysis.buy_recommendation = amount > 0 and score >= 50  # Umbral de 50 puntos
        
        # Agregar razones
        reasons = self._explain_decision(token, amount, score)
        analysis.reasons = reasons
        
        return analysis
    
    def _determine_investment_amount(self, token: Token) -> float:
        """
        Determina la cantidad a invertir basado en los criterios
        
        Args:
            token: Objeto Token a evaluar
            
        Returns:
            Cantidad en USD a invertir
        """
        # Implementar lógica según los criterios especificados
        
        # Base: token nuevo
        amount = 1.0
        
        # Con perfil
        if token.has_profile:
            amount = 3.0
        
        # Con perfil y booster
        if token.has_profile and token.booster_active:
            amount = 5.0
        
        # Criterios adicionales para montos mayores
        if (token.has_profile and 
            token.booster_active and 
            token.volume_24h >= 10000 and 
            token.liquidity >= 10000):
            
            # Evaluar pools de liquidez
            if token.liquidity_pools_count == 2:
                amount = 15.0
            elif token.liquidity_pools_count > 2:
                amount = 20.0
            else:
                amount = 10.0
        
        return amount
    
    def _calculate_investment_score(self, token: Token) -> float:
        """
        Calcula un score de inversión (0-100) basado en múltiples factores
        
        Args:
            token: Objeto Token a evaluar
            
        Returns:
            Score de inversión (0-100)
        """
        score = 0.0
        
        # Factores de evaluación con sus pesos
        factors = {
            "profile": 15,           # Tiene perfil (15 puntos)
            "booster": 15,           # Tiene booster (15 puntos)
            "liquidity": 20,         # Liquidez (hasta 20 puntos)
            "volume": 20,            # Volumen (hasta 20 puntos)
            "liquidity_pools": 15,   # Pools de liquidez (hasta 15 puntos)
            "price_change": 15       # Cambio de precio (hasta 15 puntos)
        }
        
        # Evaluar perfil
        if token.has_profile:
            score += factors["profile"]
            
        # Evaluar booster
        if token.booster_active:
            score += factors["booster"]
            
        # Evaluar liquidez (máx 20 puntos)
        # 0 puntos si < 1000 USD
        # 10 puntos si entre 1000 y 10000 USD
        # 20 puntos si >= 10000 USD
        if token.liquidity >= 10000:
            score += factors["liquidity"]
        elif token.liquidity >= 1000:
            score += factors["liquidity"] * 0.5
            
        # Evaluar volumen (máx 20 puntos)
        # 0 puntos si < 1000 USD
        # 10 puntos si entre 1000 y 10000 USD
        # 20 puntos si >= 10000 USD
        if token.volume_24h >= 10000:
            score += factors["volume"]
        elif token.volume_24h >= 1000:
            score += factors["volume"] * 0.5
            
        # Evaluar pools de liquidez
        # 5 puntos por 1 pool, 10 por 2 pools, 15 por 3+ pools
        pools_count = token.liquidity_pools_count
        if pools_count >= 3:
            score += factors["liquidity_pools"]
        elif pools_count == 2:
            score += factors["liquidity_pools"] * (2/3)
        elif pools_count == 1:
            score += factors["liquidity_pools"] * (1/3)
            
        # Evaluar cambio de precio (si está disponible)
        price_change = token.metadata.get("price_change", {}).get("h24", 0)
        if price_change is not None:
            # Preferimos tokens con tendencia alcista moderada
            # Máximo puntaje para cambios entre 5% y 20%
            if 5 <= price_change <= 20:
                score += factors["price_change"]
            elif 0 < price_change < 5:
                score += factors["price_change"] * 0.7
            elif 20 < price_change <= 50:
                score += factors["price_change"] * 0.5
            elif price_change > 50:
                score += factors["price_change"] * 0.3  # Podría ser bomba y dump
        
        return min(100, score)  # Limitar a 100 puntos máximo
    
    def _explain_decision(self, token: Token, amount: float, score: float) -> List[str]:
        """
        Explica las razones detrás de la decisión de inversión
        
        Args:
            token: Objeto Token evaluado
            amount: Monto de inversión calculado
            score: Score de inversión calculado
            
        Returns:
            Lista de razones explicando la decisión
        """
        reasons = []
        
        # Explicar factores base
        if token.has_profile:
            reasons.append("El token tiene perfil verificado (+)")
        else:
            reasons.append("El token no tiene perfil verificado (-)")
            
        if token.booster_active:
            reasons.append("El token tiene booster activo (+)")
        else:
            reasons.append("El token no tiene booster activo (-)")
            
        # Explicar liquidez
        if token.liquidity >= 10000:
            reasons.append(f"Alta liquidez: ${token.liquidity:,.2f} (+)")
        elif token.liquidity >= 1000:
            reasons.append(f"Liquidez moderada: ${token.liquidity:,.2f} (±)")
        else:
            reasons.append(f"Baja liquidez: ${token.liquidity:,.2f} (-)")
            
        # Explicar volumen
        if token.volume_24h >= 10000:
            reasons.append(f"Alto volumen 24h: ${token.volume_24h:,.2f} (+)")
        elif token.volume_24h >= 1000:
            reasons.append(f"Volumen 24h moderado: ${token.volume_24h:,.2f} (±)")
        else:
            reasons.append(f"Bajo volumen 24h: ${token.volume_24h:,.2f} (-)")
            
        # Explicar pools de liquidez
        if token.liquidity_pools_count >= 3:
            reasons.append(f"Múltiples pools de liquidez: {token.liquidity_pools_count} (+)")
        elif token.liquidity_pools_count == 2:
            reasons.append(f"Dos pools de liquidez (±)")
        elif token.liquidity_pools_count == 1:
            reasons.append(f"Solo un pool de liquidez (-)")
        else:
            reasons.append(f"No se encontraron pools de liquidez (-)")
            
        # Explicar decisión final
        if amount > 0 and score >= 50:
            reasons.append(f"Recomendación: COMPRAR ${amount:,.2f} - Score: {score:.1f}/100")
        else:
            reasons.append(f"Recomendación: NO COMPRAR - Score: {score:.1f}/100")
            
        return reasons