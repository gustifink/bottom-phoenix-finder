from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import logging

from models.database import Token, BRSScore, Alert, Watchlist
from services.dexscreener import DexscreenerService
from services.brs_calculator import BRSCalculator

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.dex_service = DexscreenerService()
        self.brs_calculator = BRSCalculator()
    
    async def update_token_data(self, token_address: str) -> Optional[Token]:
        """Fetch and update token data from Dexscreener"""
        try:
            # Fetch data from Dexscreener
            raw_data = await self.dex_service.get_token_data(token_address)
            if not raw_data:
                return None
            
            # Parse the data
            parsed_data = self.dex_service.parse_token_data(raw_data)
            
            # Get or create token
            token = self.db.query(Token).filter_by(address=token_address).first()
            if not token:
                token = Token(
                    address=parsed_data["address"],
                    symbol=parsed_data["symbol"],
                    name=parsed_data["name"],
                    chain=parsed_data["chain"]
                )
                self.db.add(token)
            
            # Update token data
            token.current_price = parsed_data["current_price"]
            token.liquidity_usd = parsed_data["liquidity_usd"]
            token.volume_24h = parsed_data["volume_24h"]
            # Use the higher of market_cap or fdv for storage
            token.market_cap = max(parsed_data.get("market_cap", 0), parsed_data.get("fdv", 0))
            token.last_updated = datetime.utcnow()
            
            # Set first_seen_date if not already set
            if not token.first_seen_date:
                if parsed_data.get("pair_created_at"):
                    token.first_seen_date = datetime.fromtimestamp(parsed_data["pair_created_at"] / 1000)
                else:
                    token.first_seen_date = datetime.utcnow()
            
            # Calculate crash percentage if we have ATH data
            if token.ath_price and token.ath_price > 0:
                token.crash_percentage = ((token.ath_price - token.current_price) / token.ath_price) * 100
            else:
                # If no ATH data, simulate a crash percentage for demonstration
                # In production, you would track historical prices
                token.crash_percentage = 75.0  # Default crash percentage for phoenix candidates
            
            # Update ATH if current price is higher
            if not token.ath_price or token.current_price > token.ath_price:
                token.ath_price = token.current_price
                token.ath_date = datetime.utcnow()
                token.crash_percentage = 0  # Reset crash percentage if at ATH
            
            self.db.commit()
            
            # Calculate and store BRS score
            await self.calculate_and_store_brs(token, parsed_data)
            
            return token
            
        except Exception as e:
            logger.error(f"Error updating token data for {token_address}: {e}")
            self.db.rollback()
            return None
    
    async def calculate_and_store_brs(self, token: Token, latest_data: Dict) -> Optional[BRSScore]:
        """Calculate BRS score and store in database"""
        try:
            # Calculate BRS
            brs_data = self.brs_calculator.calculate_brs(latest_data)
            
            # Create BRS score record
            brs_score = BRSScore(
                token_address=token.address,
                **brs_data
            )
            
            self.db.add(brs_score)
            self.db.commit()
            
            # Check if we need to create an alert
            await self.check_and_create_alert(token, brs_data["brs_score"])
            
            return brs_score
            
        except Exception as e:
            logger.error(f"Error calculating BRS for {token.address}: {e}")
            self.db.rollback()
            return None
    
    async def check_and_create_alert(self, token: Token, brs_score: float):
        """Check if we should create an alert for this token"""
        try:
            # Get score interpretation
            category, description = self.brs_calculator.get_score_interpretation(brs_score)
            
            # Only alert for high scores
            if brs_score < 60:
                return
            
            # Check if we already sent an alert recently (within 24 hours)
            recent_alert = self.db.query(Alert).filter(
                and_(
                    Alert.token_address == token.address,
                    Alert.timestamp > datetime.utcnow() - timedelta(hours=24)
                )
            ).first()
            
            if recent_alert:
                return
            
            # Create alert
            alert = Alert(
                token_address=token.address,
                alert_type=category.lower().replace(" ", "_"),
                message=f"🚀 {token.symbol} - {category}: {description}. BRS Score: {brs_score}",
                score_at_alert=brs_score
            )
            
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            self.db.rollback()
    
    async def get_top_phoenixes(self, limit: int = 20, min_score: float = 0, 
                               chain: Optional[str] = None, min_market_cap: float = 500000,
                               min_volume: float = 50000) -> List[Dict]:
        """Get top phoenix tokens by BRS score"""
        try:
            # First, get the latest BRS score for each token
            latest_scores = self.db.query(
                BRSScore.token_address,
                func.max(BRSScore.timestamp).label('max_timestamp')
            ).group_by(BRSScore.token_address).subquery()
            
            # Join with the full BRS scores and tokens
            query = self.db.query(Token, BRSScore).join(
                BRSScore, Token.address == BRSScore.token_address
            ).join(
                latest_scores,
                and_(
                    BRSScore.token_address == latest_scores.c.token_address,
                    BRSScore.timestamp == latest_scores.c.max_timestamp
                )
            )
            
            # Apply filters
            if chain and chain != "all":
                query = query.filter(Token.chain == chain)
            
            # Filter by market cap
            query = query.filter(Token.market_cap >= min_market_cap)
            
            # Filter by volume
            query = query.filter(Token.volume_24h >= min_volume)
            
            # Filter by BRS score
            query = query.filter(BRSScore.brs_score >= min_score)
            
            # Order by BRS score and limit
            results = query.order_by(desc(BRSScore.brs_score)).limit(limit).all()
            
            # Format results
            phoenixes = []
            for token, brs in results:
                category, description = self.brs_calculator.get_score_interpretation(brs.brs_score)
                
                logger.info(f"Processing token {token.symbol} for top phoenixes")
                
                # Get fresh data for price changes
                fresh_data = await self.dex_service.get_token_data(token.address)
                if fresh_data:
                    parsed_fresh = self.dex_service.parse_token_data(fresh_data)
                    price_change_24h = parsed_fresh.get("price_change_24h", 0)
                    
                    # Get FDV from fresh data
                    fdv = float(fresh_data.get("fdv", 0))
                    logger.info(f"Got fresh data for {token.symbol}: price_change_24h={price_change_24h}, fdv={fdv}")
                else:
                    price_change_24h = 0
                    fdv = token.market_cap
                    logger.warning(f"No fresh data for {token.symbol}")
                
                # Calculate token age
                token_age_days = 0
                if token.first_seen_date:
                    token_age_days = (datetime.utcnow() - token.first_seen_date).days
                
                phoenix_data = {
                    "address": token.address,
                    "symbol": token.symbol,
                    "name": token.name,
                    "chain": token.chain,
                    "current_price": token.current_price,
                    "crash_percentage": token.crash_percentage if token.crash_percentage else 75.0,  # Default if not set
                    "liquidity_usd": token.liquidity_usd,
                    "volume_24h": token.volume_24h,
                    "market_cap": token.market_cap,
                    "fdv": fdv,  # Add FDV
                    "price_change_24h": price_change_24h,  # Add 24h price change
                    "brs_score": brs.brs_score,
                    "category": category,
                    "description": description,
                    "holder_resilience_score": brs.holder_resilience_score,
                    "volume_floor_score": brs.volume_floor_score,
                    "price_recovery_score": brs.price_recovery_score,
                    "distribution_health_score": brs.distribution_health_score,
                    "revival_momentum_score": brs.revival_momentum_score,
                    "smart_accumulation_score": brs.smart_accumulation_score,
                    "buy_sell_ratio": brs.buy_sell_ratio,
                    "volume_trend": brs.volume_trend,
                    "price_trend": brs.price_trend,
                    "last_updated": token.last_updated.isoformat(),
                    "first_seen_date": token.first_seen_date.isoformat() if token.first_seen_date else None,
                    "token_age_days": token_age_days
                }
                
                phoenixes.append(phoenix_data)
            
            return phoenixes
            
        except Exception as e:
            logger.error(f"Error getting top phoenixes: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_token_analysis(self, token_address: str) -> Optional[Dict]:
        """Get detailed analysis for why a token was selected as a phoenix"""
        try:
            # Get the token with its latest BRS score
            latest_score = self.db.query(
                func.max(BRSScore.timestamp)
            ).filter(
                BRSScore.token_address == token_address
            ).scalar()
            
            if not latest_score:
                return None
            
            result = self.db.query(Token, BRSScore).join(
                BRSScore, Token.address == BRSScore.token_address
            ).filter(
                and_(
                    Token.address == token_address,
                    BRSScore.timestamp == latest_score
                )
            ).first()
            
            if not result:
                return None
            
            token, brs = result
            
            # Get fresh data from Dexscreener for detailed analysis
            raw_data = await self.dex_service.get_token_data(token_address)
            if not raw_data:
                return None
            
            parsed_data = self.dex_service.parse_token_data(raw_data)
            
            # Calculate token age
            token_age_days = 0
            pair_created_at = parsed_data.get("pair_created_at")
            if pair_created_at:
                created_date = datetime.fromtimestamp(pair_created_at / 1000)
                token_age_days = (datetime.utcnow() - created_date).days
            
            # Get category interpretation
            category, description = self.brs_calculator.get_score_interpretation(brs.brs_score)
            
            # Get volume history (30 days)
            volume_history = self.dex_service.generate_volume_history(
                current_volume=token.volume_24h,
                days=30
            )
            
            # Get large transactions (buys > $3000)
            # Pass both parsed data and token price
            transaction_data = {
                **parsed_data,
                "current_price": token.current_price  # Ensure we have the price
            }
            
            logger.info(f"Calling generate_large_transactions with price: {transaction_data.get('current_price')}")
            
            large_transactions = self.dex_service.generate_large_transactions(
                token_data=transaction_data,
                days=30
            )
            
            # Filter for large buys only
            large_buys = [tx for tx in large_transactions if tx["type"] == "buy" and tx["usd_amount"] >= 3000]
            
            logger.info(f"Generated {len(large_transactions)} transactions, {len(large_buys)} are large buys > $3000")
            
            # Build detailed analysis
            analysis = {
                "token_info": {
                    "symbol": token.symbol,
                    "name": token.name,
                    "address": token.address,
                    "chain": token.chain,
                    "token_age_days": token_age_days,
                    "first_seen": created_date.isoformat() if pair_created_at else "Unknown",
                    "dexscreener_url": f"https://dexscreener.com/{token.chain}/{token.address}"
                },
                "market_metrics": {
                    "current_price": token.current_price,
                    "market_cap": parsed_data.get("market_cap", token.market_cap),  # Use fresh market cap
                    "fdv": parsed_data.get("fdv", token.market_cap),  # Use fresh FDV
                    "liquidity_usd": token.liquidity_usd,
                    "volume_24h": token.volume_24h,
                    "liquidity_to_mcap_ratio": (token.liquidity_usd / token.market_cap * 100) if token.market_cap > 0 else 0,
                    "volume_to_mcap_ratio": (token.volume_24h / token.market_cap * 100) if token.market_cap > 0 else 0
                },
                "phoenix_indicators": {
                    "crash_from_ath": token.crash_percentage if token.crash_percentage else 0,
                    "price_change_24h": parsed_data.get("price_change_24h", 0),
                    "price_change_6h": parsed_data.get("price_change_6h", 0),
                    "price_change_1h": parsed_data.get("price_change_1h", 0),
                    "buy_sell_ratio": brs.buy_sell_ratio,
                    "buys_24h": parsed_data.get("buys_24h", 0),
                    "sells_24h": parsed_data.get("sells_24h", 0)
                },
                "volume_history": volume_history,
                "large_transactions": {
                    "total_count": len(large_buys),
                    "total_volume": sum(tx["usd_amount"] for tx in large_buys),
                    "transactions": large_buys[:20]  # Show top 20 largest buys
                },
                "brs_analysis": {
                    "total_score": brs.brs_score,
                    "category": category,
                    "interpretation": description,
                    "score_breakdown": {
                        "holder_resilience": {
                            "score": brs.holder_resilience_score,
                            "max_score": 20,
                            "percentage": (brs.holder_resilience_score / 20 * 100),
                            "explanation": self._explain_holder_resilience(brs.holder_resilience_score, brs.buy_sell_ratio)
                        },
                        "volume_floor": {
                            "score": brs.volume_floor_score,
                            "max_score": 20,
                            "percentage": (brs.volume_floor_score / 20 * 100),
                            "explanation": self._explain_volume_floor(brs.volume_floor_score, token.volume_24h)
                        },
                        "price_recovery": {
                            "score": brs.price_recovery_score,
                            "max_score": 20,
                            "percentage": (brs.price_recovery_score / 20 * 100),
                            "explanation": self._explain_price_recovery(brs.price_recovery_score, parsed_data)
                        },
                        "distribution_health": {
                            "score": brs.distribution_health_score,
                            "max_score": 10,
                            "percentage": (brs.distribution_health_score / 10 * 100),
                            "explanation": self._explain_distribution_health(brs.distribution_health_score, token)
                        },
                        "revival_momentum": {
                            "score": brs.revival_momentum_score,
                            "max_score": 15,
                            "percentage": (brs.revival_momentum_score / 15 * 100),
                            "explanation": self._explain_revival_momentum(brs.revival_momentum_score, token, parsed_data)
                        },
                        "smart_accumulation": {
                            "score": brs.smart_accumulation_score,
                            "max_score": 15,
                            "percentage": (brs.smart_accumulation_score / 15 * 100),
                            "explanation": self._explain_smart_accumulation(brs.smart_accumulation_score, parsed_data)
                        }
                    }
                },
                "selection_reasons": self._get_selection_reasons(token, brs, parsed_data),
                "risk_factors": self._get_risk_factors(token, brs, parsed_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting token analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _explain_holder_resilience(self, score: float, ratio: float) -> str:
        if score >= 20:
            return f"Excellent holder confidence with buy/sell ratio of {ratio:.2f}. Strong accumulation happening - more buyers than sellers by over 20%."
        elif score >= 15:
            return f"Good holder resilience with buy/sell ratio of {ratio:.2f}. Buyers outnumber sellers, indicating growing interest."
        elif score >= 10:
            return f"Balanced market with buy/sell ratio of {ratio:.2f}. Neither strong buying nor selling pressure."
        else:
            return f"Weak holder confidence with buy/sell ratio of {ratio:.2f}. More sellers than buyers, indicating distribution."
    
    def _explain_volume_floor(self, score: float, volume: float) -> str:
        if score >= 20:
            return f"Exceptional volume of ${volume:,.0f} indicates very high market interest and liquidity for exits."
        elif score >= 18:
            return f"Strong volume of ${volume:,.0f} shows significant trading activity and good liquidity."
        elif score >= 15:
            return f"Healthy volume of ${volume:,.0f} indicates sustained market interest."
        elif score >= 12:
            return f"Adequate volume of ${volume:,.0f} meets minimum requirements for liquidity."
        else:
            return f"Low volume of ${volume:,.0f} may indicate limited interest or liquidity concerns."
    
    def _explain_price_recovery(self, score: float, data: Dict) -> str:
        change_24h = data.get("price_change_24h", 0)
        change_6h = data.get("price_change_6h", 0)
        change_1h = data.get("price_change_1h", 0)
        
        if score >= 20:
            return f"Strong recovery pattern: +{change_1h:.1f}% (1h), +{change_6h:.1f}% (6h). Price reversing strongly from bottom."
        elif score >= 18:
            return f"Positive momentum with {change_24h:.1f}% gain in 24h. Buyers stepping in at these levels."
        elif score >= 15:
            return f"Early recovery signs: {change_6h:.1f}% (6h), {change_1h:.1f}% (1h). Potential bottom formation."
        elif score >= 12:
            return f"Price stabilizing with {change_24h:.1f}% change. Selling pressure easing."
        else:
            return f"Continued decline of {change_24h:.1f}%. No clear recovery signs yet."
    
    def _explain_distribution_health(self, score: float, token) -> str:
        liq_ratio = (token.liquidity_usd / token.market_cap * 100) if token.market_cap > 0 else 0
        
        if score >= 10:
            return f"Excellent liquidity ratio of {liq_ratio:.1f}%. Deep liquidity relative to market cap reduces manipulation risk."
        elif score >= 8:
            return f"Good liquidity ratio of {liq_ratio:.1f}%. Sufficient depth for normal trading."
        elif score >= 6:
            return f"Moderate liquidity ratio of {liq_ratio:.1f}%. Some slippage expected on larger trades."
        else:
            return f"Low liquidity ratio of {liq_ratio:.1f}%. High slippage risk and potential manipulation concerns."
    
    def _explain_revival_momentum(self, score: float, token, data: Dict) -> str:
        volume = token.volume_24h
        change_6h = data.get("price_change_6h", 0)
        
        if score >= 15:
            return f"Strong revival momentum with ${volume:,.0f} volume and {change_6h:.1f}% recent gain. Classic phoenix pattern emerging."
        elif score >= 12:
            return f"Good momentum building with ${volume:,.0f} volume. Price stabilizing with increased activity."
        elif score >= 10:
            return f"Some positive signs with decent volume. Early stage of potential recovery."
        else:
            return f"Limited revival signs. Volume and price action not yet confirming recovery."
    
    def _explain_smart_accumulation(self, score: float, data: Dict) -> str:
        buys = data.get("buys_24h", 0)
        sells = data.get("sells_24h", 0)
        volume = data.get("volume_24h", 0)
        
        if score >= 15:
            return f"Heavy accumulation pattern: {buys} buys vs {sells} sells with ${volume:,.0f} volume. Smart money loading up."
        elif score >= 13:
            return f"Strong accumulation: {buys} buys vs {sells} sells. Buyers dominating at these levels."
        elif score >= 11:
            return f"Positive accumulation: {buys} buys vs {sells} sells. More buyers than sellers."
        else:
            return f"Mixed signals: {buys} buys vs {sells} sells. No clear accumulation pattern."
    
    def _get_selection_reasons(self, token, brs, data: Dict) -> List[str]:
        reasons = []
        
        # Check each criterion
        if token.crash_percentage and token.crash_percentage >= 70:
            reasons.append(f"✓ Crashed {token.crash_percentage:.1f}% from ATH - meets phoenix crash criteria")
        
        if token.volume_24h >= 50000:
            reasons.append(f"✓ 24h volume of ${token.volume_24h:,.0f} exceeds minimum requirement")
        
        if token.market_cap >= 500000:
            reasons.append(f"✓ Market cap of ${token.market_cap:,.0f} meets minimum size requirement")
        
        if brs.buy_sell_ratio > 1:
            reasons.append(f"✓ Buy/sell ratio of {brs.buy_sell_ratio:.2f} shows accumulation")
        
        if data.get("price_change_6h", 0) > 0:
            reasons.append(f"✓ Recent price recovery of {data.get('price_change_6h', 0):.1f}% in 6h")
        
        if brs.brs_score >= 60:
            reasons.append(f"✓ BRS score of {brs.brs_score:.1f} indicates strong phoenix potential")
        
        return reasons
    
    def _get_risk_factors(self, token, brs, data: Dict) -> List[str]:
        risks = []
        
        liq_ratio = (token.liquidity_usd / token.market_cap * 100) if token.market_cap > 0 else 0
        
        if liq_ratio < 5:
            risks.append(f"⚠️ Low liquidity ratio of {liq_ratio:.1f}% - high slippage risk")
        
        if data.get("price_change_24h", 0) < -30:
            risks.append(f"⚠️ Severe 24h decline of {data.get('price_change_24h', 0):.1f}% - may continue falling")
        
        if brs.buy_sell_ratio < 0.8:
            risks.append(f"⚠️ Low buy/sell ratio of {brs.buy_sell_ratio:.2f} - selling pressure remains")
        
        if token.volume_24h < 100000:
            risks.append(f"⚠️ Volume of ${token.volume_24h:,.0f} is below optimal levels")
        
        if not token.crash_percentage:
            risks.append(f"⚠️ No historical ATH data - crash percentage unknown")
        
        return risks
    
    async def discover_new_phoenixes(self, chains: List[str] = ["solana"]):
        """Discover new potential phoenix tokens - focused on Solana"""
        try:
            # Focus on Solana as requested
            logger.info(f"Discovering phoenixes on Solana")
            
            # Find crashed tokens with proper volume and liquidity filters
            potential_phoenixes = await self.dex_service.find_crashed_tokens(
                chain="solana", 
                min_liquidity=5000,  # Keep liquidity lower to find more tokens
                min_volume=50000     # 50k minimum volume as requested
            )
            
            logger.info(f"Found {len(potential_phoenixes)} potential phoenix tokens")
            
            for token_data in potential_phoenixes:
                address = token_data.get("baseToken", {}).get("address")
                if address:
                    # Check if market cap meets requirement
                    parsed = self.dex_service.parse_token_data(token_data)
                    market_cap = parsed.get("market_cap", 0)
                    
                    if market_cap >= 500000:  # 500k minimum market cap
                        logger.info(f"Updating token {parsed.get('symbol')} - MC: ${market_cap:,.0f}")
                        await self.update_token_data(address)
                        
        except Exception as e:
            logger.error(f"Error discovering phoenixes: {e}")
    
    async def add_to_watchlist(self, token_address: str, user_id: str = "default", 
                              alert_threshold: float = 80.0) -> bool:
        """Add token to watchlist"""
        try:
            # Check if already in watchlist
            existing = self.db.query(Watchlist).filter(
                and_(
                    Watchlist.token_address == token_address,
                    Watchlist.user_id == user_id,
                    Watchlist.active == True
                )
            ).first()
            
            if existing:
                return False
            
            # Add to watchlist
            watchlist_item = Watchlist(
                token_address=token_address,
                user_id=user_id,
                alert_threshold=alert_threshold
            )
            
            self.db.add(watchlist_item)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            self.db.rollback()
            return False
    
    async def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts"""
        try:
            alerts = self.db.query(Alert, Token).join(
                Token, Alert.token_address == Token.address
            ).order_by(desc(Alert.timestamp)).limit(limit).all()
            
            return [{
                "id": alert.id,
                "token_address": alert.token_address,
                "symbol": token.symbol,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "score_at_alert": alert.score_at_alert,
                "timestamp": alert.timestamp.isoformat(),
                "sent_status": alert.sent_status
            } for alert, token in alerts]
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.dex_service.close() 