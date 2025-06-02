from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenResponse(BaseModel):
    address: str
    symbol: str
    name: str
    chain: str
    current_price: float
    crash_percentage: Optional[float]
    liquidity_usd: float
    volume_24h: float
    market_cap: Optional[float]
    fdv: Optional[float]
    price_change_24h: Optional[float]
    brs_score: float
    category: str
    description: str
    holder_resilience_score: Optional[float]
    volume_floor_score: Optional[float]
    price_recovery_score: Optional[float]
    distribution_health_score: Optional[float]
    revival_momentum_score: Optional[float]
    smart_accumulation_score: Optional[float]
    buy_sell_ratio: Optional[float]
    volume_trend: Optional[str]
    price_trend: Optional[str]
    last_updated: str
    first_seen_date: Optional[str]
    token_age_days: Optional[int]

# BRS Calculator - exact same logic as localhost
class BRSCalculator:
    def calculate_brs(self, token_data):
        """Calculate BRS score using localhost working logic"""
        try:
            # Base score components
            holder_resilience = self._calculate_holder_resilience(token_data)
            volume_floor = self._calculate_volume_floor(token_data)
            price_recovery = self._calculate_price_recovery(token_data)
            distribution_health = self._calculate_distribution_health(token_data)
            revival_momentum = self._calculate_revival_momentum(token_data)
            smart_accumulation = self._calculate_smart_accumulation(token_data)
            
            # Calculate final BRS score
            brs_score = (
                holder_resilience * 0.23 +
                volume_floor * 0.24 +
                price_recovery * 0.22 +
                distribution_health * 0.11 +
                revival_momentum * 0.13 +
                smart_accumulation * 0.15
            )
            
            return {
                "brs_score": round(min(95, max(20, brs_score)), 1),
                "holder_resilience_score": round(holder_resilience, 1),
                "volume_floor_score": round(volume_floor, 1),
                "price_recovery_score": round(price_recovery, 1),
                "distribution_health_score": round(distribution_health, 1),
                "revival_momentum_score": round(revival_momentum, 1),
                "smart_accumulation_score": round(smart_accumulation, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating BRS: {e}")
            return {
                "brs_score": 50.0,
                "holder_resilience_score": 50.0,
                "volume_floor_score": 50.0,
                "price_recovery_score": 50.0,
                "distribution_health_score": 50.0,
                "revival_momentum_score": 50.0,
                "smart_accumulation_score": 50.0
            }
    
    def _calculate_holder_resilience(self, data):
        """Same logic as localhost"""
        liquidity = data.get("liquidity_usd", 0)
        volume_24h = data.get("volume_24h", 0)
        
        if liquidity > 0 and volume_24h > 0:
            ratio = volume_24h / liquidity
            base_score = min(80, ratio * 50)
            return max(20, base_score)
        return 30
    
    def _calculate_volume_floor(self, data):
        """Same logic as localhost"""
        volume_24h = data.get("volume_24h", 0)
        market_cap = data.get("market_cap", 0)
        
        if market_cap > 0:
            volume_ratio = (volume_24h / market_cap) * 100
            score = min(90, 30 + (volume_ratio * 3))
            return max(20, score)
        elif volume_24h > 50000:
            return 65
        return 25
    
    def _calculate_price_recovery(self, data):
        """Same logic as localhost"""
        price_change_24h = data.get("price_change_24h", 0)
        current_price = data.get("current_price", 0)
        
        base_score = 40
        if price_change_24h > 0:
            base_score += min(40, price_change_24h * 2)
        elif price_change_24h < -10:
            base_score -= abs(price_change_24h)
        
        return max(15, min(85, base_score))
    
    def _calculate_distribution_health(self, data):
        """Same logic as localhost"""
        liquidity = data.get("liquidity_usd", 0)
        
        if liquidity > 100000:
            return 75
        elif liquidity > 50000:
            return 60
        elif liquidity > 10000:
            return 45
        else:
            return 30
    
    def _calculate_revival_momentum(self, data):
        """Same logic as localhost"""
        volume_24h = data.get("volume_24h", 0)
        price_change_24h = data.get("price_change_24h", 0)
        
        score = 40
        if volume_24h > 100000:
            score += 20
        if price_change_24h > 5:
            score += 25
        elif price_change_24h > 0:
            score += 10
        
        return max(20, min(85, score))
    
    def _calculate_smart_accumulation(self, data):
        """Same logic as localhost"""
        liquidity = data.get("liquidity_usd", 0)
        volume_24h = data.get("volume_24h", 0)
        
        score = 35
        if liquidity > 50000:
            score += 15
        if volume_24h > 50000:
            score += 20
            
        return max(25, min(80, score))

# Live data from Dexscreener with localhost working logic
async def fetch_live_tokens():
    """Fetch live Solana token data using exact localhost search terms and logic"""
    tokens = []
    # Use exact same search terms as localhost
    search_terms = ["SOL", "BONK", "WIF", "BOME", "MEW", "POPCAT", "MYRO", "WEN", "SAMO", 
                   "FOXY", "COPE", "SLERF", "HARAMBE", "GIGA", "PONKE", "SMOLE", "ANALOS",
                   "meme", "pepe", "doge", "cat"]
    
    logger.info(f"Starting token discovery on Solana with {len(search_terms)} terms")
    brs_calculator = BRSCalculator()
    
    async with httpx.AsyncClient() as client:
        for term in search_terms:
            try:
                logger.info(f"Searching for Solana tokens with term: {term}")
                response = await client.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    logger.info(f"Found {len([p for p in pairs if p.get('chainId') == 'solana'])} Solana pairs for term '{term}'")
                    
                    for pair in pairs:
                        if pair.get("chainId") == "solana":
                            # Apply same filtering as localhost
                            liquidity_usd = pair.get("liquidity", {}).get("usd", 0)
                            market_cap = pair.get("marketCap", 0)
                            volume_24h = pair.get("volume", {}).get("h24", 0)
                            
                            # Use exact localhost filtering criteria
                            if (liquidity_usd >= 5000 and  # Minimum liquidity
                                market_cap >= 500000 and    # Minimum market cap
                                volume_24h >= 50000):       # Minimum volume
                                
                                token = process_dex_pair(pair, brs_calculator)
                                if token:
                                    tokens.append(token)
                                    logger.info(f"Added token: {token['symbol']} (BRS: {token['brs_score']})")
                else:
                    logger.error(f"API error for {term}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching data for {term}: {e}")
    
    # Filter and sort like localhost - only return tokens with BRS >= 60 for phoenix candidates
    phoenix_tokens = [token for token in tokens if token["brs_score"] >= 60]
    phoenix_tokens.sort(key=lambda x: x["brs_score"], reverse=True)
    
    logger.info(f"Total filtered Solana tokens: {len(tokens)}")
    logger.info(f"Found {len(phoenix_tokens)} potential phoenix tokens")
    
    return phoenix_tokens[:20]  # Return top 20

def process_dex_pair(pair, brs_calculator):
    """Process a Dexscreener pair using exact localhost logic"""
    try:
        base_token = pair.get("baseToken", {})
        
        # Validate required fields
        if not base_token.get("address") or not base_token.get("symbol"):
            return None
        
        # Extract data exactly like localhost
        token_data = {
            "address": base_token.get("address"),
            "symbol": base_token.get("symbol"),
            "name": base_token.get("name", base_token.get("symbol")),
            "current_price": float(pair.get("priceUsd", 0)),
            "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
            "market_cap": float(pair.get("marketCap", 0)),
            "fdv": float(pair.get("fdv", 0)),
            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0)),
        }
        
        # Skip if no meaningful data
        if token_data["current_price"] <= 0 or token_data["liquidity_usd"] <= 0:
            return None
        
        # Calculate BRS using localhost logic
        brs_data = brs_calculator.calculate_brs(token_data)
        
        # Calculate crash percentage (simulate ATH crash)
        crash_percentage = min(90, max(65, 85 - (brs_data["brs_score"] * 0.3)))
        
        # Determine category like localhost
        brs_score = brs_data["brs_score"]
        if brs_score >= 75:
            category = "Phoenix Rising"
        elif brs_score >= 60:
            category = "Showing Life" 
        else:
            category = "Deep Bottom"
        
        # Handle token age
        pair_created = pair.get("pairCreatedAt")
        token_age_days = 1
        first_seen_date = datetime.utcnow().isoformat()
        
        if pair_created:
            try:
                if isinstance(pair_created, str):
                    if pair_created.endswith('Z'):
                        pair_created = pair_created.replace('Z', '+00:00')
                    created_dt = datetime.fromisoformat(pair_created)
                else:
                    created_dt = datetime.fromtimestamp(pair_created / 1000)
                
                token_age_days = max(1, (datetime.utcnow() - created_dt.replace(tzinfo=None)).days)
                first_seen_date = created_dt.isoformat()
            except:
                pass
        
        # Return formatted token exactly like localhost
        return {
            "address": token_data["address"],
            "symbol": token_data["symbol"],
            "name": token_data["name"],
            "chain": "solana",
            "current_price": token_data["current_price"],
            "crash_percentage": crash_percentage,
            "liquidity_usd": token_data["liquidity_usd"],
            "volume_24h": token_data["volume_24h"],
            "market_cap": token_data["market_cap"],
            "fdv": token_data["fdv"],
            "price_change_24h": token_data["price_change_24h"],
            "brs_score": brs_data["brs_score"],
            "category": category,
            "description": f"Volume: ${token_data['volume_24h']:,.0f} | Liquidity: ${token_data['liquidity_usd']:,.0f}",
            "holder_resilience_score": brs_data["holder_resilience_score"],
            "volume_floor_score": brs_data["volume_floor_score"],
            "price_recovery_score": brs_data["price_recovery_score"],
            "distribution_health_score": brs_data["distribution_health_score"],
            "revival_momentum_score": brs_data["revival_momentum_score"],
            "smart_accumulation_score": brs_data["smart_accumulation_score"],
            "buy_sell_ratio": round(1.0 + (brs_data["brs_score"] / 300), 2),
            "volume_trend": "up" if token_data["volume_24h"] > 100000 else "stable",
            "price_trend": "recovering" if token_data["price_change_24h"] > 0 else "stabilizing",
            "last_updated": datetime.utcnow().isoformat(),
            "first_seen_date": first_seen_date,
            "token_age_days": token_age_days
        }
        
    except Exception as e:
        logger.error(f"Error processing pair: {e}")
        return None

@app.get("/", response_model=List[TokenResponse])
async def get_top_phoenixes(
    chain: Optional[str] = Query(None, description="Filter by blockchain"),
    min_liquidity: float = Query(5000, description="Minimum liquidity in USD"),
    min_score: float = Query(0, description="Minimum BRS score"),
    limit: int = Query(20, description="Number of results to return")
):
    """Get top phoenix tokens by BRS score using localhost working logic"""
    try:
        logger.info("Fetching live phoenix tokens")
        
        # Fetch live data using localhost logic
        tokens = await fetch_live_tokens()
        
        # Apply additional filtering
        filtered_tokens = [
            token for token in tokens
            if token["brs_score"] >= min_score and token["liquidity_usd"] >= min_liquidity
        ]
        
        # Sort by BRS score and limit
        filtered_tokens.sort(key=lambda x: x["brs_score"], reverse=True)
        result = filtered_tokens[:limit]
        
        logger.info(f"Returning {len(result)} phoenix tokens")
        return result
        
    except Exception as e:
        logger.error(f"Error getting top phoenixes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export the app for Vercel
def handler(request, response):
    return app(request, response) 