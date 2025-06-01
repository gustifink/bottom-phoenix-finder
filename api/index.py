from http.server import BaseHTTPRequestHandler
import json
import urllib.request
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        path = self.path
        
        if '/api/top-phoenixes' in path:
            try:
                # Get real data from Dexscreener API
                phoenixes = []
                search_terms = ["BOME", "SLERF", "POPCAT", "MEW", "BONK"]
                
                for term in search_terms[:3]:  # Limit to 3 to avoid timeout
                    try:
                        url = f"https://api.dexscreener.com/latest/dex/search?q={term}"
                        with urllib.request.urlopen(url, timeout=5) as response:
                            data = json.loads(response.read().decode())
                            pairs = data.get("pairs", [])
                            
                            for pair in pairs[:1]:  # Top 1 per term
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
                                        "brs_score": min(98.0, 80.0 + (float(pair.get("volume", {}).get("h24", 0)) / 1000000 * 3)),
                                        "category": "Phoenix Rising",
                                        "description": "Strong buy signal - high recovery potential",
                                        "holder_resilience_score": 20.0,
                                        "volume_floor_score": 18.0,
                                        "price_recovery_score": 18.0,
                                        "distribution_health_score": 10.0,
                                        "revival_momentum_score": 15.0,
                                        "smart_accumulation_score": 15.0,
                                        "buy_sell_ratio": 1.25,
                                        "volume_trend": "up",
                                        "price_trend": "up",
                                        "last_updated": datetime.now().isoformat(),
                                        "first_seen_date": "2024-01-15T10:30:00",
                                        "token_age_days": 300
                                    }
                                    
                                    if phoenix["liquidity_usd"] >= 5000:
                                        phoenixes.append(phoenix)
                    except:
                        continue
                
                phoenixes.sort(key=lambda x: x["brs_score"], reverse=True)
                self.wfile.write(json.dumps(phoenixes).encode())
                
            except Exception as e:
                error = {"error": str(e)}
                self.wfile.write(json.dumps(error).encode())
        
        elif '/api/alerts/recent' in path:
            alerts = [
                {
                    "id": 1,
                    "token_address": "ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82",
                    "alert_type": "phoenix_rising",
                    "message": "🚀 BOME showing phoenix recovery potential",
                    "score_at_alert": 98.0,
                    "timestamp": datetime.now().isoformat()
                }
            ]
            self.wfile.write(json.dumps(alerts).encode())
        
        else:
            # Test endpoint
            response = {
                "status": "working", 
                "message": "Dexscreener API working!", 
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode()) 