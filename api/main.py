from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
import logging
import os # Keep os for potential future environment variables, though not strictly needed now

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bottom - Phoenix Token Finder API",
    description="Find crypto tokens that have bottomed out but show recovery potential",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models (as they were in the working version)
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

# BRS Calculator - using the version that was working well
class BRSCalculator:
    def calculate_brs(self, token_data):
        try:
            holder_resilience = self._calculate_holder_resilience(token_data)
            volume_floor = self._calculate_volume_floor(token_data)
            price_recovery = self._calculate_price_recovery(token_data)
            distribution_health = self._calculate_distribution_health(token_data)
            revival_momentum = self._calculate_revival_momentum(token_data)
            smart_accumulation = self._calculate_smart_accumulation(token_data)

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
            logger.error(f"Error calculating BRS for {token_data.get('symbol')}: {e}")
            return {
                "brs_score": 30.0, # Default to a low score on error
                "holder_resilience_score": 0,
                "volume_floor_score": 0,
                "price_recovery_score": 0,
                "distribution_health_score": 0,
                "revival_momentum_score": 0,
                "smart_accumulation_score": 0
            }

    def _safe_get(self, data, key, default=0):
        return data.get(key, default) if data.get(key) is not None else default

    def _calculate_holder_resilience(self, data):
        liquidity = self._safe_get(data, "liquidity_usd")
        volume_24h = self._safe_get(data, "volume_24h")
        if liquidity > 0 and volume_24h > 0:
            ratio = volume_24h / liquidity
            return max(20, min(80, ratio * 50)) 
        return 30

    def _calculate_volume_floor(self, data):
        volume_24h = self._safe_get(data, "volume_24h")
        market_cap = self._safe_get(data, "market_cap")
        if market_cap > 0:
            volume_ratio = (volume_24h / market_cap) * 100
            return max(20, min(90, 30 + (volume_ratio * 3)))
        elif volume_24h > 50000:
            return 65
        return 25

    def _calculate_price_recovery(self, data):
        price_change_24h = self._safe_get(data, "price_change_24h")
        base_score = 40
        if price_change_24h > 0:
            base_score += min(40, price_change_24h * 2)
        elif price_change_24h < -10:
            base_score -= abs(price_change_24h)
        return max(15, min(85, base_score))

    def _calculate_distribution_health(self, data):
        liquidity = self._safe_get(data, "liquidity_usd")
        if liquidity > 100000: return 75
        if liquidity > 50000: return 60
        if liquidity > 10000: return 45
        return 30

    def _calculate_revival_momentum(self, data):
        volume_24h = self._safe_get(data, "volume_24h")
        price_change_24h = self._safe_get(data, "price_change_24h")
        score = 40
        if volume_24h > 100000: score += 20
        if price_change_24h > 5: score += 25
        elif price_change_24h > 0: score += 10
        return max(20, min(85, score))

    def _calculate_smart_accumulation(self, data):
        liquidity = self._safe_get(data, "liquidity_usd")
        volume_24h = self._safe_get(data, "volume_24h")
        score = 35
        if liquidity > 50000: score += 15
        if volume_24h > 50000: score += 20
        return max(25, min(80, score))

# Dexscreener interaction and token processing
async def fetch_live_tokens():
    tokens = []
    search_terms = [
        "SOL", "BONK", "WIF", "BOME", "MEW", "POPCAT", "MYRO", "WEN", "SAMO", 
        "FOXY", "COPE", "SLERF", "HARAMBE", "GIGA", "PONKE", "SMOLE", "ANALOS",
        "meme", "pepe", "doge", "cat"
    ]
    logger.info(f"Starting token discovery on Solana with {len(search_terms)} terms.")
    brs_calculator = BRSCalculator()

    async with httpx.AsyncClient(timeout=10.0) as client: # Added timeout
        for term in search_terms:
            try:
                logger.info(f"Searching Dexscreener for Solana tokens matching term: {term}")
                response = await client.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                data = response.json()
                pairs = data.get("pairs", [])
                solana_pairs_count = sum(1 for p in pairs if p.get('chainId') == 'solana')
                logger.info(f"Found {solana_pairs_count} Solana pairs for term '{term}'. Processing...")

                for pair_data in pairs:
                    if pair_data.get("chainId") == "solana":
                        token = process_dex_pair(pair_data, brs_calculator)
                        if token:
                            tokens.append(token)
                            logger.info(f"Processed and added token: {token['symbol']} (BRS: {token['brs_score']})")
            except httpx.HTTPStatusError as exc:
                logger.error(f"Dexscreener API error for term '{term}': {exc.response.status_code} - {exc.response.text}")
            except httpx.RequestError as exc:
                logger.error(f"Dexscreener request error for term '{term}': {exc}")
            except Exception as e:
                logger.error(f"Unexpected error fetching/processing data for term '{term}': {e}", exc_info=True)
    
    # Filter by BRS score (example: >= 60)
    phoenix_tokens = [token for token in tokens if token["brs_score"] >= 60]
    phoenix_tokens.sort(key=lambda x: x["brs_score"], reverse=True)
    
    logger.info(f"Finished discovery. Total processed Solana tokens: {len(tokens)}. Potential phoenix tokens (BRS >= 60): {len(phoenix_tokens)}.")
    return phoenix_tokens[:20] # Return top 20

def process_dex_pair(pair_data, brs_calculator):
    try:
        base_token = pair_data.get("baseToken", {})
        if not base_token.get("address") or not base_token.get("symbol"):
            logger.warning(f"Skipping pair due to missing baseToken address or symbol: {pair_data.get('pairAddress')}")
            return None

        # Basic data extraction
        token_metrics = {
            "address": base_token.get("address"),
            "symbol": base_token.get("symbol"),
            "name": base_token.get("name", base_token.get("symbol")),
            "current_price": float(pair_data.get("priceUsd", 0)),
            "liquidity_usd": float(pair_data.get("liquidity", {}).get("usd", 0)),
            "volume_24h": float(pair_data.get("volume", {}).get("h24", 0)),
            "market_cap": float(pair_data.get("marketCap", 0)),
            "fdv": float(pair_data.get("fdv", 0)),
            "price_change_24h": float(pair_data.get("priceChange", {}).get("h24", 0)),
        }

        # Apply crucial pre-BRS filters (as from localhost logic)
        if not (token_metrics["liquidity_usd"] >= 5000 and \
                token_metrics["market_cap"] >= 100000 and \
                token_metrics["volume_24h"] >= 10000 and \
                token_metrics["current_price"] > 0):
            # logger.info(f"Token {token_metrics['symbol']} filtered out by pre-BRS criteria.")
            return None

        brs_components = brs_calculator.calculate_brs(token_metrics)
        brs_score = brs_components["brs_score"]

        # Determine category based on BRS score
        if brs_score >= 75: category = "Phoenix Rising"
        elif brs_score >= 60: category = "Showing Life"
        else: category = "Deep Bottom" # Could be filtered out later if not desired
        
        # Crash percentage (example logic)
        crash_percentage = min(90, max(60, 80 - (brs_score * 0.25)))

        # Token Age
        first_seen_date_str = datetime.utcnow().isoformat() + "Z"
        token_age_days = 0
        pair_created_at_timestamp = pair_data.get("pairCreatedAt")
        if pair_created_at_timestamp:
            try:
                # Assuming timestamp is in milliseconds
                created_dt = datetime.utcfromtimestamp(pair_created_at_timestamp / 1000)
                first_seen_date_str = created_dt.isoformat() + "Z"
                token_age_days = (datetime.utcnow() - created_dt).days
            except Exception as e:
                logger.warning(f"Could not parse pairCreatedAt for {token_metrics['symbol']}: {pair_created_at_timestamp}. Error: {e}")

        return {
            **token_metrics, # Includes address, symbol, name, price, liq, vol, mc, fdv, price_change
            "chain": "solana",
            "brs_score": brs_score,
            "category": category,
            "description": f"MC: ${token_metrics['market_cap']:,.0f} | Vol: ${token_metrics['volume_24h']:,.0f} | Liq: ${token_metrics['liquidity_usd']:,.0f}",
            "crash_percentage": crash_percentage,
            "holder_resilience_score": brs_components["holder_resilience_score"],
            "volume_floor_score": brs_components["volume_floor_score"],
            "price_recovery_score": brs_components["price_recovery_score"],
            "distribution_health_score": brs_components["distribution_health_score"],
            "revival_momentum_score": brs_components["revival_momentum_score"],
            "smart_accumulation_score": brs_components["smart_accumulation_score"],
            "buy_sell_ratio": round(1.0 + (brs_score / 250), 2), # Example
            "volume_trend": "up" if token_metrics["volume_24h"] > 150000 else "stable", # Example
            "price_trend": "recovering" if token_metrics["price_change_24h"] > 2 else "stabilizing", # Example
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "first_seen_date": first_seen_date_str,
            "token_age_days": token_age_days,
        }
    except Exception as e:
        logger.error(f"Error processing Dexscreener pair {pair_data.get('pairAddress')}: {e}", exc_info=True)
        return None

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Bottom - Phoenix Token Finder API",
        "status": "running",
        "endpoints": {
            "top_phoenixes": "/api/top-phoenixes",
            "health": "/api/health",
            "test": "/api/test"
        }
    }

@app.get("/api/health")
async def api_health():
    logger.info("Health check endpoint called.")
    return {"status": "API healthy", "version": app.version, "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/test")
async def api_test():
    logger.info("Test endpoint called.")
    return {"message": "Test endpoint working!", "data": [1, 2, 3, 4, 5]}

@app.get("/api/top-phoenixes", response_model=List[TokenResponse])
async def get_top_phoenixes_endpoint(
    # Query parameters can be added here if needed, e.g., min_brs, min_liquidity
    limit: int = Query(20, ge=1, le=100)
):
    logger.info(f"Top phoenixes endpoint called with limit: {limit}")
    try:
        tokens = await fetch_live_tokens()
        logger.info(f"Fetched {len(tokens)} tokens before applying limit.")
        return tokens[:limit]
    except Exception as e:
        logger.error(f"Error in /api/top-phoenixes endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching token data.")

# Vercel handler (standard for FastAPI on Vercel)
def handler(request, response):
    return app(request, response) 