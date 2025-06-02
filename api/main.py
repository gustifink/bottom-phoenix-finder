from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import logging
import os
import sys

# Add the backend directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from models.database import init_db, get_session
    from services.token_manager import TokenManager
except ImportError:
    # Fallback for development
    import sqlite3
    from datetime import datetime

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
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class WatchlistAdd(BaseModel):
    token_address: str
    alert_threshold: float = 80.0

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

# Mock data for demo (since we can't run the full backend in serverless)
MOCK_PHOENIX_TOKENS = [
    {
        "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "symbol": "BONK",
        "name": "Bonk",
        "chain": "solana",
        "current_price": 0.00001687,
        "crash_percentage": 75.0,
        "liquidity_usd": 2500000,
        "volume_24h": 8500000,
        "market_cap": 1300000000,
        "fdv": 1500000000,
        "price_change_24h": 2.9,
        "brs_score": 78.5,
        "category": "Phoenix Rising",
        "description": "Strong accumulation pattern with high volume",
        "holder_resilience_score": 18.0,
        "volume_floor_score": 19.0,
        "price_recovery_score": 17.0,
        "distribution_health_score": 8.5,
        "revival_momentum_score": 13.0,
        "smart_accumulation_score": 12.0,
        "buy_sell_ratio": 1.25,
        "volume_trend": "up",
        "price_trend": "recovering",
        "last_updated": datetime.utcnow().isoformat(),
        "first_seen_date": "2023-12-28T00:00:00",
        "token_age_days": 444
    },
    {
        "address": "ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82",
        "symbol": "BOME",
        "name": "Book of Meme",
        "chain": "solana",
        "current_price": 0.0089,
        "crash_percentage": 85.0,
        "liquidity_usd": 1800000,
        "volume_24h": 5200000,
        "market_cap": 130000000,
        "fdv": 133000000,
        "price_change_24h": 3.74,
        "brs_score": 72.3,
        "category": "Showing Life",
        "description": "Recent volume spike with buyer interest",
        "holder_resilience_score": 16.0,
        "volume_floor_score": 18.0,
        "price_recovery_score": 15.0,
        "distribution_health_score": 7.8,
        "revival_momentum_score": 11.5,
        "smart_accumulation_score": 11.0,
        "buy_sell_ratio": 1.18,
        "volume_trend": "up",
        "price_trend": "stabilizing",
        "last_updated": datetime.utcnow().isoformat(),
        "first_seen_date": "2024-03-15T00:00:00",
        "token_age_days": 175
    }
]

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to Bottom - Phoenix Token Finder API",
        "docs": "/docs",
        "health": "/health"
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
        # Filter mock data based on parameters
        filtered_tokens = [
            token for token in MOCK_PHOENIX_TOKENS
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
        # Mock alerts
        alerts = [
            {
                "id": 1,
                "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "symbol": "BONK",
                "alert_type": "phoenix_rising",
                "message": "🚀 BONK - Phoenix Rising: Strong accumulation pattern. BRS Score: 78.5",
                "score_at_alert": 78.5,
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
        # Find token in mock data
        token = next((t for t in MOCK_PHOENIX_TOKENS if t["address"] == token_address), None)
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        
        # Generate mock analysis
        analysis = {
            "token_info": {
                "symbol": token["symbol"],
                "name": token["name"],
                "address": token["address"],
                "chain": token["chain"],
                "token_age_days": token["token_age_days"],
                "first_seen": token["first_seen_date"],
                "dexscreener_url": f"https://dexscreener.com/{token['chain']}/{token['address']}"
            },
            "market_metrics": {
                "current_price": token["current_price"],
                "market_cap": token["market_cap"],
                "fdv": token["fdv"],
                "liquidity_usd": token["liquidity_usd"],
                "volume_24h": token["volume_24h"],
                "liquidity_to_mcap_ratio": (token["liquidity_usd"] / token["market_cap"] * 100),
                "volume_to_mcap_ratio": (token["volume_24h"] / token["market_cap"] * 100)
            },
            "phoenix_indicators": {
                "crash_from_ath": token["crash_percentage"],
                "price_change_24h": token["price_change_24h"],
                "price_change_6h": 1.2,
                "price_change_1h": 0.5,
                "buy_sell_ratio": token["buy_sell_ratio"],
                "buys_24h": 450,
                "sells_24h": 360
            },
            "volume_history": [
                {"date": f"2024-{i:02d}-01", "volume": token["volume_24h"] * (0.8 + i * 0.1)}
                for i in range(1, 31)
            ],
            "large_transactions": {
                "total_count": 25,
                "total_volume": 250000,
                "transactions": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "buy",
                        "usd_amount": 15000,
                        "token_amount": 889000,
                        "price": token["current_price"],
                        "wallet": "0xabc...def"
                    }
                ] * 25
            },
            "brs_analysis": {
                "total_score": token["brs_score"],
                "category": token["category"],
                "interpretation": token["description"],
                "score_breakdown": {
                    "holder_resilience": {
                        "score": token["holder_resilience_score"],
                        "max_score": 20,
                        "percentage": (token["holder_resilience_score"] / 20 * 100),
                        "explanation": f"Strong holder confidence with buy/sell ratio of {token['buy_sell_ratio']:.2f}"
                    },
                    "volume_floor": {
                        "score": token["volume_floor_score"],
                        "max_score": 20,
                        "percentage": (token["volume_floor_score"] / 20 * 100),
                        "explanation": f"Exceptional volume of ${token['volume_24h']:,.0f} indicates high market interest"
                    },
                    "price_recovery": {
                        "score": token["price_recovery_score"],
                        "max_score": 20,
                        "percentage": (token["price_recovery_score"] / 20 * 100),
                        "explanation": f"Positive momentum with {token['price_change_24h']:.1f}% gain in 24h"
                    },
                    "distribution_health": {
                        "score": token["distribution_health_score"],
                        "max_score": 10,
                        "percentage": (token["distribution_health_score"] / 10 * 100),
                        "explanation": f"Good liquidity ratio reduces manipulation risk"
                    },
                    "revival_momentum": {
                        "score": token["revival_momentum_score"],
                        "max_score": 15,
                        "percentage": (token["revival_momentum_score"] / 15 * 100),
                        "explanation": f"Strong revival momentum with ${token['volume_24h']:,.0f} volume"
                    },
                    "smart_accumulation": {
                        "score": token["smart_accumulation_score"],
                        "max_score": 15,
                        "percentage": (token["smart_accumulation_score"] / 15 * 100),
                        "explanation": f"Heavy accumulation pattern with strong buying pressure"
                    }
                }
            },
            "selection_reasons": [
                f"✓ Crashed {token['crash_percentage']:.1f}% from ATH - meets phoenix crash criteria",
                f"✓ 24h volume of ${token['volume_24h']:,.0f} exceeds minimum requirement",
                f"✓ Market cap of ${token['market_cap']:,.0f} meets minimum size requirement",
                f"✓ Buy/sell ratio of {token['buy_sell_ratio']:.2f} shows accumulation",
                f"✓ BRS score of {token['brs_score']:.1f} indicates strong phoenix potential"
            ],
            "risk_factors": [
                "⚠️ High volatility expected in memecoin markets",
                "⚠️ Regulatory uncertainty around memecoins",
                "⚠️ Market sentiment can change rapidly"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/add")
async def add_to_watchlist(watchlist_data: WatchlistAdd):
    """Add token to personal watchlist for alerts"""
    try:
        # Mock response
        return {"status": "success", "message": "Token added to watchlist"}
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Vercel handler
def handler(request, response):
    return app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 