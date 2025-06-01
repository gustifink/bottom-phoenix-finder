from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import logging
import os
import sys

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from models.database import init_db, get_session
from services.token_manager import TokenManager

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
engine = init_db("sqlite:///:memory:")

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
    return {"status": "healthy", "service": "bottom-api"}

@app.get("/api/top-phoenixes", response_model=List[TokenResponse])
async def get_top_phoenixes(
    chain: Optional[str] = Query(None, description="Filter by blockchain (ethereum/bsc/polygon/all)"),
    min_liquidity: float = Query(5000, description="Minimum liquidity in USD"),
    min_score: float = Query(0, description="Minimum BRS score"),
    limit: int = Query(20, description="Number of results to return")
):
    """Get top phoenix tokens by BRS score"""
    try:
        session = get_session(engine)
        token_manager = TokenManager(session)
        
        # For serverless, we'll discover tokens on-demand
        await token_manager.discover_new_phoenixes(["solana"])
        
        phoenixes = await token_manager.get_top_phoenixes(
            limit=limit,
            min_score=min_score,
            chain=chain
        )
        
        session.close()
        await token_manager.cleanup()
        
        return phoenixes
        
    except Exception as e:
        logger.error(f"Error getting top phoenixes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/token/{address}/brs")
async def get_token_brs(address: str):
    """Get detailed BRS breakdown for specific token"""
    try:
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/add")
async def add_to_watchlist(watchlist_data: WatchlistAdd):
    """Add token to personal watchlist for alerts"""
    try:
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/recent")
async def get_recent_alerts(limit: int = Query(10, description="Number of alerts to return")):
    """Get recent phoenix alerts"""
    try:
        session = get_session(engine)
        token_manager = TokenManager(session)
        
        alerts = await token_manager.get_recent_alerts(limit=limit)
        
        session.close()
        await token_manager.cleanup()
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/token/{token_address}/analysis")
async def get_token_analysis(token_address: str):
    """Get detailed analysis for why a token was selected as a phoenix"""
    try:
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
        raise HTTPException(status_code=500, detail=str(e))

# Export the app for Vercel
handler = app 