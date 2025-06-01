from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BRSCalculator:
    """Calculate Bottom Resilience Score for tokens"""
    
    def calculate_brs(self, token_data: Dict, historical_data: Optional[Dict] = None) -> Dict:
        """
        Calculate the complete BRS score and component scores
        
        Returns dict with:
        - brs_score: Total score (0-100)
        - Component scores
        - Additional metrics
        """
        try:
            # Calculate all component scores
            holder_resilience = self._calculate_holder_resilience(token_data)
            volume_floor = self._calculate_volume_floor(token_data)
            price_recovery = self._calculate_price_recovery(token_data)
            distribution_health = self._calculate_distribution_health(token_data)
            revival_momentum = self._calculate_revival_momentum(token_data)
            smart_accumulation = self._calculate_smart_accumulation(token_data)
            
            # Calculate total BRS score
            brs_score = (
                holder_resilience +
                volume_floor +
                price_recovery +
                distribution_health +
                revival_momentum +
                smart_accumulation
            )
            
            # Additional metrics
            buy_sell_ratio = self._calculate_buy_sell_ratio(token_data)
            volume_trend = self._determine_volume_trend(token_data)
            price_trend = self._determine_price_trend(token_data)
            
            return {
                "brs_score": round(brs_score, 2),
                "holder_resilience_score": holder_resilience,
                "volume_floor_score": volume_floor,
                "price_recovery_score": price_recovery,
                "distribution_health_score": distribution_health,
                "revival_momentum_score": revival_momentum,
                "smart_accumulation_score": smart_accumulation,
                "buy_sell_ratio": buy_sell_ratio,
                "volume_trend": volume_trend,
                "price_trend": price_trend
            }
            
        except Exception as e:
            logger.error(f"Error calculating BRS: {e}")
            return {"brs_score": 0, "error": str(e)}
    
    def _calculate_holder_resilience(self, data: Dict) -> float:
        """
        Calculate holder resilience score (20 points max)
        Based on buy/sell ratio
        """
        try:
            buys = data.get("buys_24h", 0)
            sells = data.get("sells_24h", 0)
            
            if sells == 0:
                return 20.0
            
            ratio = buys / sells
            
            if ratio > 1.2:
                return 20.0
            elif ratio > 1.0:
                return 15.0
            elif ratio > 0.8:
                return 10.0
            else:
                return 5.0
                
        except Exception:
            return 5.0
    
    def _calculate_volume_floor(self, data: Dict) -> float:
        """
        Calculate volume floor score (20 points max)
        Based on 24h volume - adjusted for 50k+ volume tokens
        """
        try:
            volume_24h = data.get("volume_24h", 0)
            
            # Adjusted for higher volume requirements
            if volume_24h >= 500000:  # 500k+ volume
                return 20.0
            elif volume_24h >= 250000:  # 250k+ volume
                return 18.0
            elif volume_24h >= 100000:  # 100k+ volume
                return 15.0
            elif volume_24h >= 50000:   # 50k+ volume (minimum)
                return 12.0
            elif volume_24h >= 25000:
                return 8.0
            else:
                return 5.0
                
        except Exception:
            return 5.0
    
    def _calculate_price_recovery(self, data: Dict) -> float:
        """
        Calculate price recovery score (20 points max)
        Based on recent price movement - check multiple timeframes
        """
        try:
            price_change_24h = data.get("price_change_24h", 0)
            price_change_6h = data.get("price_change_6h", 0)
            price_change_1h = data.get("price_change_1h", 0)
            
            # Check for recovery patterns
            if price_change_1h > 5 and price_change_6h > 0:
                # Strong recent recovery
                return 20.0
            elif price_change_24h > 0:
                # Positive 24h change
                return 18.0
            elif price_change_6h > 0 and price_change_1h > -2:
                # Recent stabilization/recovery
                return 15.0
            elif price_change_24h >= -5:
                # Minimal decline
                return 12.0
            elif price_change_24h >= -10:
                # Moderate decline
                return 8.0
            else:
                # Still falling
                return 5.0
                
        except Exception:
            return 5.0
    
    def _calculate_distribution_health(self, data: Dict) -> float:
        """
        Calculate distribution health score (10 points max)
        Based on liquidity and market cap ratio
        """
        try:
            liquidity = data.get("liquidity_usd", 0)
            market_cap = data.get("market_cap", 0)
            
            # Check liquidity to market cap ratio
            if market_cap > 0:
                liq_ratio = liquidity / market_cap
                
                if liq_ratio >= 0.1:  # 10%+ liquidity/mcap ratio
                    return 10.0
                elif liq_ratio >= 0.05:  # 5%+ ratio
                    return 8.0
                elif liq_ratio >= 0.02:  # 2%+ ratio
                    return 6.0
                else:
                    return 4.0
            else:
                # Fallback to absolute liquidity
                if liquidity >= 100000:
                    return 8.0
                elif liquidity >= 50000:
                    return 6.0
                else:
                    return 3.0
                
        except Exception:
            return 3.0
    
    def _calculate_revival_momentum(self, data: Dict) -> float:
        """
        Calculate revival momentum score (15 points max)
        Based on volume trend and price stabilization
        """
        try:
            volume_24h = data.get("volume_24h", 0)
            price_change_24h = data.get("price_change_24h", 0)
            price_change_6h = data.get("price_change_6h", 0)
            buys = data.get("buys_24h", 0)
            sells = data.get("sells_24h", 0)
            
            # Strong revival signs
            if volume_24h > 100000 and price_change_6h > 0 and buys > sells:
                return 15.0
            # Good volume with stabilization
            elif volume_24h > 50000 and -5 <= price_change_24h <= 20:
                return 12.0
            # Decent activity
            elif volume_24h > 50000 or (price_change_6h > -5 and buys >= sells * 0.8):
                return 10.0
            else:
                return 5.0
                
        except Exception:
            return 5.0
    
    def _calculate_smart_accumulation(self, data: Dict) -> float:
        """
        Calculate smart accumulation score (15 points max)
        Based on buy patterns and volume distribution
        """
        try:
            buys = data.get("buys_24h", 0)
            sells = data.get("sells_24h", 0)
            volume = data.get("volume_24h", 0)
            price_change_5m = data.get("price_change_5m", 0)
            
            # Strong accumulation patterns
            if buys > sells * 1.5 and volume > 100000:
                return 15.0
            # Good accumulation with high volume
            elif buys > sells * 1.2 and volume > 50000:
                return 13.0
            # Positive buy pressure
            elif buys > sells and volume > 50000:
                return 11.0
            # Recent buying interest
            elif price_change_5m > 0 and buys > sells * 0.8:
                return 8.0
            else:
                return 5.0
                
        except Exception:
            return 5.0
    
    def _calculate_buy_sell_ratio(self, data: Dict) -> float:
        """Calculate buy/sell ratio"""
        try:
            buys = data.get("buys_24h", 0)
            sells = data.get("sells_24h", 1)  # Avoid division by zero
            return round(buys / sells, 2)
        except:
            return 1.0
    
    def _determine_volume_trend(self, data: Dict) -> str:
        """Determine volume trend based on volume levels"""
        try:
            volume_24h = data.get("volume_24h", 0)
            # Adjusted for higher volume tokens
            if volume_24h > 250000:
                return "up"
            elif volume_24h > 100000:
                return "stable"
            else:
                return "down"
        except:
            return "unknown"
    
    def _determine_price_trend(self, data: Dict) -> str:
        """Determine price trend based on multiple timeframes"""
        try:
            price_change_24h = data.get("price_change_24h", 0)
            price_change_6h = data.get("price_change_6h", 0)
            
            if price_change_6h > 5 or (price_change_24h > 0 and price_change_6h > 0):
                return "up"
            elif price_change_24h < -10 and price_change_6h < -5:
                return "down"
            else:
                return "stable"
        except:
            return "unknown"
    
    def get_score_interpretation(self, brs_score: float) -> Tuple[str, str]:
        """
        Get interpretation of BRS score
        Returns: (category, description)
        """
        if brs_score >= 80:
            return "Phoenix Rising", "Strong buy signal - high recovery potential"
        elif brs_score >= 60:
            return "Showing Life", "Add to watchlist - monitoring recommended"
        elif brs_score >= 40:
            return "Still Dormant", "Monitor only - not ready yet"
        else:
            return "Dead Token", "Avoid - low recovery probability" 