import json
import requests
from datetime import datetime

def handler(event, context):
    """Simple serverless function that calls Dexscreener API"""
    
    # Enable CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    path = event.get('path', '')
    
    if path == '/api/top-phoenixes':
        try:
            # Call Dexscreener API directly - same as working local version
            search_terms = ["BONK", "MEW", "POPCAT", "WIF", "BOME", "SLERF"]
            phoenixes = []
            
            for term in search_terms:
                try:
                    response = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])
                        
                        for pair in pairs[:2]:  # Top 2 per term
                            if pair.get("chainId") == "solana" and pair.get("baseToken"):
                                token = pair["baseToken"]
                                
                                phoenix = {
                                    "address": token.get("address", ""),
                                    "symbol": token.get("symbol", ""),
                                    "name": token.get("name", ""),
                                    "chain": "solana",
                                    "current_price": float(pair.get("priceUsd", 0)),
                                    "crash_percentage": 75.0,
                                    "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                                    "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                                    "market_cap": float(pair.get("marketCap", 0)),
                                    "fdv": float(pair.get("fdv", 0)),
                                    "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0)),
                                    "brs_score": min(95.0, 70.0 + (float(pair.get("volume", {}).get("h24", 0)) / 1000000 * 5)),
                                    "category": "Phoenix Rising",
                                    "description": f"Solana token showing recovery potential",
                                    "holder_resilience_score": 15.0,
                                    "volume_floor_score": 12.0,
                                    "price_recovery_score": 16.0,
                                    "distribution_health_score": 11.0,
                                    "revival_momentum_score": 13.0,
                                    "smart_accumulation_score": 10.0,
                                    "buy_sell_ratio": 1.25,
                                    "volume_trend": "increasing",
                                    "price_trend": "recovering",
                                    "last_updated": datetime.now().isoformat(),
                                    "first_seen_date": "2024-01-15T10:30:00",
                                    "token_age_days": 300
                                }
                                
                                # Only add if it has decent liquidity
                                if phoenix["liquidity_usd"] >= 5000:
                                    phoenixes.append(phoenix)
                                
                except Exception as e:
                    print(f"Error with {term}: {e}")
                    continue
            
            # Sort by BRS score
            phoenixes.sort(key=lambda x: x["brs_score"], reverse=True)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(phoenixes[:20])
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({"error": str(e)})
            }
    
    elif path == '/api/alerts/recent':
        alerts = [
            {
                "id": 1,
                "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "alert_type": "phoenix_rising",
                "message": "🚀 Token showing phoenix recovery potential",
                "score_at_alert": 78.5,
                "timestamp": datetime.now().isoformat()
            }
        ]
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(alerts)
        }
    
    elif path == '/api/test':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({"status": "working", "message": "Simple Dexscreener API working!"})
        }
    
    else:
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({"error": "Not found"})
        } 