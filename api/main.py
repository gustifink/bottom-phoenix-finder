from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bottom API is working", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "bottom-api"}

@app.get("/test")
async def test():
    return {"status": "test successful", "api": "working"}

@app.get("/top-phoenixes")
async def get_phoenixes():
    """Return sample phoenix data"""
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
            "last_updated": "2025-01-02T00:00:00",
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
            "last_updated": "2025-01-02T00:00:00",
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
            "last_updated": "2025-01-02T00:00:00",
            "first_seen_date": "2024-02-10T09:45:00",
            "token_age_days": 326
        }
    ]

@app.get("/alerts/recent")
async def get_alerts():
    """Return sample alerts"""
    return [
        {
            "id": 1,
            "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "alert_type": "phoenix_rising",
            "message": "🚀 Bonk - Showing Life: High-volume memecoin showing phoenix recovery potential. BRS Score: 78.5",
            "score_at_alert": 78.5,
            "timestamp": "2025-01-01T22:00:00"
        },
        {
            "id": 2,
            "token_address": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
            "alert_type": "showing_life",
            "message": "🔥 POPCAT - Showing Life: Viral meme token with strong technical recovery signals. BRS Score: 75.8",
            "score_at_alert": 75.8,
            "timestamp": "2025-01-01T18:00:00"
        }
    ]

# Export the app for Vercel
handler = app 