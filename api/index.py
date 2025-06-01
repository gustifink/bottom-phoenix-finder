from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import List, Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_dexscreener_data():
    """Get real data from Dexscreener API"""
    phoenixes = []
    search_terms = ["BONK", "MEW", "POPCAT", "WIF", "BOME"]
    
    async with httpx.AsyncClient() as client:
        for term in search_terms:
            try:
                response = await client.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    
                    for pair in pairs[:2]:  # Take top 2 results per term
                        if pair.get("chainId") == "solana" and pair.get("baseToken"):
                            token = pair["baseToken"]
                            phoenix = {
                                "address": token.get("address", ""),
                                "symbol": token.get("symbol", ""),
                                "name": token.get("name", ""),
                                "chain": "solana",
                                "current_price": float(pair.get("priceUsd", 0)),
                                "crash_percentage": 75.0,  # Calculate this properly later
                                "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                                "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                                "market_cap": float(pair.get("marketCap", 0)),
                                "fdv": float(pair.get("fdv", 0)),
                                "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0)),
                                "brs_score": 72.5,  # Calculate this properly later
                                "category": "Showing Life",
                                "description": f"Solana token: {token.get('name', '')}",
                                "holder_resilience_score": 15.0,
                                "volume_floor_score": 12.0,
                                "price_recovery_score": 16.0,
                                "distribution_health_score": 11.0,
                                "revival_momentum_score": 13.0,
                                "smart_accumulation_score": 10.0,
                                "buy_sell_ratio": 1.25,
                                "volume_trend": "increasing",
                                "price_trend": "recovering",
                                "last_updated": "2025-01-02T00:00:00",
                                "first_seen_date": "2024-01-15T10:30:00",
                                "token_age_days": 300
                            }
                            phoenixes.append(phoenix)
                            
            except Exception as e:
                print(f"Error fetching {term}: {e}")
                continue
    
    return phoenixes

@app.get("/")
def read_root():
    return {"message": "Bottom Phoenix Finder API", "status": "working"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "bottom-api"}

@app.get("/test")
def test():
    return {"status": "working", "message": "FastAPI + Dexscreener working on Vercel"}

@app.get("/top-phoenixes")
async def get_phoenixes(
    limit: int = Query(20, description="Number of results"),
    min_score: float = Query(0, description="Minimum BRS score"),
    min_liquidity: float = Query(5000, description="Minimum liquidity")
):
    """Get real phoenix tokens from Dexscreener"""
    try:
        phoenixes = await get_dexscreener_data()
        
        # Apply filters
        filtered = [p for p in phoenixes if p["liquidity_usd"] >= min_liquidity and p["brs_score"] >= min_score]
        
        return filtered[:limit]
    except Exception as e:
        print(f"Error in get_phoenixes: {e}")
        return []

@app.get("/alerts/recent")
def get_alerts():
    return [
        {
            "id": 1,
            "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "alert_type": "phoenix_rising",
            "message": "🚀 Token showing phoenix recovery potential",
            "score_at_alert": 78.5,
            "timestamp": "2025-01-01T22:00:00"
        }
    ]

# This is for Vercel
handler = app 