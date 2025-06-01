from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import logging
import os
import sys
import traceback
import datetime

# Simple imports for Vercel environment
try:
    from models.database import init_db, get_session
    from services.token_manager import TokenManager
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import paths
    try:
        sys.path.append('.')
        sys.path.append('..')
        from models.database import init_db, get_session
        from services.token_manager import TokenManager
    except ImportError as e2:
        print(f"Second import error: {e2}")
        traceback.print_exc()
        raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bottom - Phoenix Token Finder",
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

# Initialize database with in-memory SQLite for serverless
try:
    engine = init_db("sqlite:///:memory:")
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    traceback.print_exc()
    engine = None

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

# Mock data for testing
def get_mock_phoenixes():
    """Return mock phoenix token data for testing"""
    return [
        {
            "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "symbol": "Bonk",
            "name": "Bonk",
            "chain": "solana",
            "current_price": 0.000025,
            "crash_percentage": 85.5,
            "liquidity_usd": 2500000,
            "volume_24h": 15000000,
            "market_cap": 1650000000,
            "fdv": 1650000000,
            "price_change_24h": 3.2,
            "brs_score": 78.5,
            "category": "Showing Life",
            "description": "High-volume memecoin showing phoenix recovery potential",
            "holder_resilience_score": 15.5,
            "volume_floor_score": 12.0,
            "price_recovery_score": 16.8,
            "distribution_health_score": 11.2,
            "revival_momentum_score": 13.0,
            "smart_accumulation_score": 10.0,
            "buy_sell_ratio": 1.35,
            "volume_trend": "increasing",
            "price_trend": "recovering",
            "last_updated": datetime.datetime.utcnow().isoformat(),
            "first_seen_date": "2024-01-15T10:30:00",
            "token_age_days": 352
        },
        {
            "address": "MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5",
            "symbol": "MEW",
            "name": "cat in a dogs world",
            "chain": "solana",
            "current_price": 0.0089,
            "crash_percentage": 72.1,
            "liquidity_usd": 890000,
            "volume_24h": 5200000,
            "market_cap": 295000000,
            "fdv": 295000000,
            "price_change_24h": 1.8,
            "brs_score": 72.3,
            "category": "Showing Life",
            "description": "Cat-themed token with strong community and recovery momentum",
            "holder_resilience_score": 14.2,
            "volume_floor_score": 10.8,
            "price_recovery_score": 15.1,
            "distribution_health_score": 12.5,
            "revival_momentum_score": 11.7,
            "smart_accumulation_score": 8.0,
            "buy_sell_ratio": 1.28,
            "volume_trend": "stable",
            "price_trend": "sideways",
            "last_updated": datetime.datetime.utcnow().isoformat(),
            "first_seen_date": "2024-03-20T14:15:00",
            "token_age_days": 288
        },
        {
            "address": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
            "symbol": "POPCAT",
            "name": "Popcat",
            "chain": "solana",
            "current_price": 0.385,
            "crash_percentage": 68.9,
            "liquidity_usd": 1200000,
            "volume_24h": 8500000,
            "market_cap": 373000000,
            "fdv": 373000000,
            "price_change_24h": 4.1,
            "brs_score": 75.8,
            "category": "Showing Life",
            "description": "Viral meme token with strong technical recovery signals",
            "holder_resilience_score": 16.0,
            "volume_floor_score": 11.5,
            "price_recovery_score": 17.2,
            "distribution_health_score": 10.8,
            "revival_momentum_score": 12.3,
            "smart_accumulation_score": 8.0,
            "buy_sell_ratio": 1.42,
            "volume_trend": "increasing",
            "price_trend": "bullish",
            "last_updated": datetime.datetime.utcnow().isoformat(),
            "first_seen_date": "2024-02-10T09:45:00",
            "token_age_days": 326
        }
    ]

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to Bottom - Phoenix Token Finder API",
        "docs": "/docs",
        "health": "/health",
        "status": "Mock API - Working"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "bottom-api", 
        "database": "mock",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/top-phoenixes", response_model=List[TokenResponse])
async def get_top_phoenixes(
    chain: Optional[str] = Query(None, description="Filter by blockchain"),
    min_liquidity: float = Query(5000, description="Minimum liquidity in USD"),
    min_score: float = Query(0, description="Minimum BRS score"),
    limit: int = Query(20, description="Number of results to return")
):
    """Get top phoenix tokens by BRS score - Mock Data"""
    try:
        logger.info(f"Getting mock phoenixes with params: limit={limit}, min_score={min_score}")
        
        # Get mock data
        phoenixes = get_mock_phoenixes()
        
        # Apply filters
        filtered_phoenixes = [
            phoenix for phoenix in phoenixes 
            if phoenix["brs_score"] >= min_score 
            and phoenix["liquidity_usd"] >= min_liquidity
        ]
        
        # Limit results
        result = filtered_phoenixes[:limit]
        
        logger.info(f"Returning {len(result)} mock phoenix tokens")
        return result
        
    except Exception as e:
        logger.error(f"Error getting mock phoenixes: {e}")
        return []

@app.get("/token/{address}/brs")
async def get_token_brs(address: str):
    """Get detailed BRS breakdown for specific token"""
    try:
        if not engine:
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        session = get_session(engine)
        token_manager = TokenManager(session)
        
        # Update token data first
        token = await token_manager.update_token_data(address)
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        
        # Get latest BRS score
        phoenixes = await token_manager.get_top_phoenixes(limit=1, chain=token.chain)
        phoenix_data = next((p for p in phoenixes if p["address"] == address), None)
        
        session.close()
        await token_manager.cleanup()
        
        if not phoenix_data:
            raise HTTPException(status_code=404, detail="BRS data not found")
        
        return phoenix_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token BRS: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/watchlist/add")
async def add_to_watchlist(watchlist_data: WatchlistAdd):
    """Add token to personal watchlist for alerts"""
    try:
        if not engine:
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        session = get_session(engine)
        token_manager = TokenManager(session)
        
        success = await token_manager.add_to_watchlist(
            token_address=watchlist_data.token_address,
            alert_threshold=watchlist_data.alert_threshold
        )
        
        session.close()
        await token_manager.cleanup()
        
        if success:
            return {"status": "success", "message": "Token added to watchlist"}
        else:
            return {"status": "exists", "message": "Token already in watchlist"}
            
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/recent")
async def get_recent_alerts(limit: int = Query(10, description="Number of alerts to return")):
    """Get recent phoenix alerts - Mock Data"""
    try:
        alerts = [
            {
                "id": 1,
                "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "alert_type": "phoenix_rising",
                "message": "🚀 Bonk - Showing Life: High-volume memecoin showing phoenix recovery potential. BRS Score: 78.5",
                "score_at_alert": 78.5,
                "timestamp": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()
            },
            {
                "id": 2,
                "token_address": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
                "alert_type": "showing_life",
                "message": "🔥 POPCAT - Showing Life: Viral meme token with strong technical recovery signals. BRS Score: 75.8",
                "score_at_alert": 75.8,
                "timestamp": (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).isoformat()
            }
        ]
        
        return alerts[:limit]
        
    except Exception as e:
        logger.error(f"Error getting mock alerts: {e}")
        return []

@app.get("/token/{token_address}/analysis")
async def get_token_analysis(token_address: str):
    """Get detailed analysis for why a token was selected as a phoenix"""
    try:
        if not engine:
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        session = get_session(engine)
        token_manager = TokenManager(session)
        
        analysis = await token_manager.get_token_analysis(token_address)
        
        session.close()
        await token_manager.cleanup()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Token analysis not found")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token analysis: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Simplified endpoints for debugging
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "status": "API is working", 
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "message": "Mock API responding successfully"
    }

# Export the app for Vercel
handler = app 