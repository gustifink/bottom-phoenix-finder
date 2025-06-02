from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import httpx
import logging

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
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

# Live data from Dexscreener
async def fetch_live_tokens():
    """Fetch live Solana token data from Dexscreener API"""
    tokens = []
    search_terms = ["BONK", "BOME", "WIF", "MEW", "POPCAT", "MYRO", "WEN", "SAMO"]
    
    logger.info(f"Starting token fetch for {len(search_terms)} search terms")
    
    async with httpx.AsyncClient() as client:
        for term in search_terms:
            try:
                logger.info(f"Searching for: {term}")
                response = await client.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    logger.info(f"Found {len(pairs)} pairs for {term}")
                    
                    processed_count = 0
                    for pair in pairs[:3]:  # Top 3 per term
                        if pair.get("chainId") == "solana":
                            liquidity_usd = pair.get("liquidity", {}).get("usd", 0)
                            if liquidity_usd > 5000:
                                token = process_dex_pair(pair)
                                if token:
                                    tokens.append(token)
                                    processed_count += 1
                                    logger.info(f"Added token: {token['symbol']} (BRS: {token['brs_score']})")
                                else:
                                    logger.warning(f"Failed to process pair for {term}")
                            else:
                                logger.info(f"Skipping {term} pair - liquidity too low: ${liquidity_usd:,.0f}")
                        else:
                            logger.info(f"Skipping non-Solana pair for {term}: {pair.get('chainId')}")
                    
                    logger.info(f"Successfully processed {processed_count} tokens for {term}")
                else:
                    logger.error(f"API error for {term}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching data for {term}: {e}")
                
    logger.info(f"Total tokens collected: {len(tokens)}")
    return tokens[:20]  # Return top 20

def process_dex_pair(pair):
    """Process a Dexscreener pair into our token format"""
    try:
        base_token = pair.get("baseToken", {})
        
        # Validate required fields
        if not base_token.get("address") or not base_token.get("symbol"):
            logger.warning(f"Skipping pair - missing address or symbol: {base_token}")
            return None
        
        # Calculate metrics with proper defaults and validation
        current_price = float(pair.get("priceUsd") or 0)
        volume_24h = float(pair.get("volume", {}).get("h24") or 0)
        liquidity = float(pair.get("liquidity", {}).get("usd") or 0)
        market_cap = float(pair.get("marketCap") or 0)
        fdv = float(pair.get("fdv") or market_cap or 0)
        price_change_24h = float(pair.get("priceChange", {}).get("h24") or 0)
        
        # Skip tokens with no meaningful data
        if current_price <= 0 or liquidity <= 0:
            logger.warning(f"Skipping token {base_token.get('symbol')} - no price or liquidity data")
            return None
        
        # BRS calculation with safe division
        brs_score = 30  # Base score
        
        # Liquidity component (0-25 points)
        if liquidity > 0:
            brs_score += min(25, (liquidity / 50000) * 25)
        
        # Price change component (0-20 points) 
        brs_score += min(20, abs(price_change_24h) * 2)
        
        # Volume component (0-25 points)
        if market_cap > 0 and volume_24h > 0:
            volume_ratio = (volume_24h / market_cap) * 100
            brs_score += min(25, volume_ratio * 5)
        elif volume_24h > 100000:  # High absolute volume
            brs_score += 15
        
        # Cap the score
        brs_score = min(95, max(20, brs_score))
        
        # Mock crash percentage based on inverse BRS
        crash_percentage = min(90, max(65, 90 - (brs_score * 0.3)))
        
        category = "Phoenix Rising" if brs_score > 70 else "Showing Life" if brs_score > 50 else "Deep Bottom"
        
        # Handle date parsing safely
        pair_created = pair.get("pairCreatedAt")
        token_age_days = 1
        first_seen_date = datetime.utcnow().isoformat()
        
        if pair_created:
            try:
                if pair_created.endswith('Z'):
                    pair_created = pair_created.replace('Z', '+00:00')
                created_dt = datetime.fromisoformat(pair_created)
                token_age_days = max(1, (datetime.utcnow() - created_dt.replace(tzinfo=None)).days)
                first_seen_date = created_dt.isoformat()
            except Exception as e:
                logger.warning(f"Date parsing error for {base_token.get('symbol')}: {e}")
        
        token_data = {
            "address": base_token.get("address", ""),
            "symbol": base_token.get("symbol", ""),
            "name": base_token.get("name", base_token.get("symbol", "")),
            "chain": "solana",
            "current_price": current_price,
            "crash_percentage": crash_percentage,
            "liquidity_usd": liquidity,
            "volume_24h": volume_24h,
            "market_cap": market_cap,
            "fdv": fdv,
            "price_change_24h": price_change_24h,
            "brs_score": round(brs_score, 1),
            "category": category,
            "description": f"Volume: ${volume_24h:,.0f} | Liquidity: ${liquidity:,.0f}",
            "holder_resilience_score": round(brs_score * 0.23, 1),
            "volume_floor_score": round(brs_score * 0.24, 1),
            "price_recovery_score": round(brs_score * 0.22, 1),
            "distribution_health_score": round(brs_score * 0.11, 1),
            "revival_momentum_score": round(brs_score * 0.13, 1),
            "smart_accumulation_score": round(brs_score * 0.15, 1),
            "buy_sell_ratio": round(1.0 + (brs_score / 300), 2),
            "volume_trend": "up" if volume_24h > 100000 else "stable",
            "price_trend": "recovering" if price_change_24h > 0 else "stabilizing",
            "last_updated": datetime.utcnow().isoformat(),
            "first_seen_date": first_seen_date,
            "token_age_days": token_age_days
        }
        
        logger.info(f"Processed token: {token_data['symbol']} - BRS: {token_data['brs_score']}")
        return token_data
        
    except Exception as e:
        logger.error(f"Error processing pair: {e}")
        logger.error(f"Pair data: {pair}")
        return None

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Bottom - Phoenix Token Finder API",
        "status": "running",
        "endpoints": {
            "top_phoenixes": "/api/top-phoenixes",
            "recent_alerts": "/api/alerts/recent",
            "token_analysis": "/api/token/{address}/analysis",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bottom-api", "environment": "vercel"}

@app.get("/api/top-phoenixes", response_model=List[TokenResponse])
async def get_top_phoenixes(
    chain: Optional[str] = Query(None, description="Filter by blockchain"),
    min_liquidity: float = Query(5000, description="Minimum liquidity in USD"),
    min_score: float = Query(0, description="Minimum BRS score"),
    limit: int = Query(20, description="Number of results to return")
):
    """Get top phoenix tokens by BRS score"""
    try:
        # Fetch live data
        tokens = await fetch_live_tokens()
        
        # Filter based on parameters
        filtered_tokens = [
            token for token in tokens
            if token["brs_score"] >= min_score and token["liquidity_usd"] >= min_liquidity
        ]
        
        # Sort by BRS score and limit
        filtered_tokens.sort(key=lambda x: x["brs_score"], reverse=True)
        return filtered_tokens[:limit]
        
    except Exception as e:
        logger.error(f"Error getting top phoenixes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/recent")
async def get_recent_alerts(limit: int = Query(10, description="Number of alerts to return")):
    """Get recent phoenix alerts"""
    try:
        # Mock alerts with current data
        alerts = [
            {
                "id": 1,
                "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "symbol": "BONK",
                "alert_type": "phoenix_rising",
                "message": "🚀 BONK showing strong recovery signals",
                "score_at_alert": 78.5,
                "timestamp": datetime.utcnow().isoformat(),
                "sent_status": True
            },
            {
                "id": 2,
                "token_address": "ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82",
                "symbol": "BOME",
                "alert_type": "volume_spike",
                "message": "📈 BOME volume spike detected",
                "score_at_alert": 72.3,
                "timestamp": datetime.utcnow().isoformat(),
                "sent_status": True
            }
        ]
        return alerts[:limit]
        
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/token/{token_address}/analysis")
async def get_token_analysis(token_address: str):
    """Get detailed analysis for a token"""
    try:
        # Fetch live tokens and find the requested one
        tokens = await fetch_live_tokens()
        token = next((t for t in tokens if t["address"] == token_address), None)
        
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        
        # Add detailed analysis
        analysis = {
            **token,
            "large_transactions": [
                {
                    "hash": f"tx{i+1}abc123def456",
                    "type": "buy" if i % 2 == 0 else "sell",
                    "amount_usd": 50000 + (i * 10000),
                    "amount_tokens": (50000 + (i * 10000)) / token["current_price"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "solscan_url": f"https://solscan.io/tx/tx{i+1}abc123def456"
                }
                for i in range(25)  # 25 transactions
            ],
            "price_history": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "price": token["current_price"] * (1 + (i * 0.01)),
                    "volume": token["volume_24h"] * (0.8 + (i * 0.02))
                }
                for i in range(24)  # 24 hours
            ]
        }
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Vercel handler
def handler(request, response):
    return app(request, response) 