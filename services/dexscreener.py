import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DexscreenerService:
    def __init__(self, base_url: str = "https://api.dexscreener.com"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def get_token_data(self, token_address: str, chain: str = "solana") -> Optional[Dict]:
        """Fetch token data from Dexscreener using the correct endpoint"""
        try:
            # Use the token-pairs endpoint to get pools for a token
            response = await self.client.get(f"{self.base_url}/token-pairs/v1/{chain}/{token_address}")
            if response.status_code == 200:
                pairs = response.json()
                if pairs and len(pairs) > 0:
                    # Return the pair with highest liquidity
                    return max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0)))
            return None
        except Exception as e:
            logger.error(f"Error fetching token data for {token_address}: {e}")
            return None
    
    async def get_tokens_by_addresses(self, chain: str, addresses: List[str]) -> List[Dict]:
        """Get multiple tokens by their addresses"""
        try:
            # API allows up to 30 addresses at once
            addresses_str = ",".join(addresses[:30])
            response = await self.client.get(f"{self.base_url}/tokens/v1/{chain}/{addresses_str}")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching tokens by addresses: {e}")
            return []
    
    async def search_tokens(self, query: str) -> List[Dict]:
        """Search for tokens by symbol or name"""
        try:
            response = await self.client.get(f"{self.base_url}/latest/dex/search", params={"q": query})
            if response.status_code == 200:
                data = response.json()
                return data.get("pairs", [])
            return []
        except Exception as e:
            logger.error(f"Error searching tokens for {query}: {e}")
            return []
    
    async def get_solana_tokens(self, min_liquidity: float = 5000, min_volume: float = 50000) -> List[Dict]:
        """Get Solana tokens that meet criteria"""
        try:
            # Search for popular Solana memecoins and tokens
            search_terms = [
                "SOL", "BONK", "WIF", "BOME", "MEW", "POPCAT", 
                "MYRO", "WEN", "SAMO", "FOXY", "COPE", "SLERF",
                "HARAMBE", "GIGA", "PONKE", "SMOLE", "ANALOS",
                "meme", "pepe", "doge", "cat"
            ]
            all_tokens = []
            seen_addresses = set()
            
            for term in search_terms:
                logger.info(f"Searching for Solana tokens with term: {term}")
                response = await self.client.get(
                    f"{self.base_url}/latest/dex/search", 
                    params={"q": term}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    
                    # Filter for Solana tokens only
                    solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                    
                    # Add unique tokens
                    for pair in solana_pairs:
                        base_token = pair.get("baseToken", {})
                        address = base_token.get("address", "")
                        
                        if address and address not in seen_addresses:
                            seen_addresses.add(address)
                            all_tokens.append(pair)
                    
                    logger.info(f"Found {len(solana_pairs)} Solana pairs for term '{term}'")
                    
                await asyncio.sleep(0.2)  # Rate limiting
            
            # Filter by liquidity and volume
            filtered_tokens = []
            for token in all_tokens:
                liquidity = float(token.get("liquidity", {}).get("usd", 0))
                volume = float(token.get("volume", {}).get("h24", 0))
                
                if liquidity >= min_liquidity and volume >= min_volume:
                    filtered_tokens.append(token)
            
            logger.info(f"Total filtered Solana tokens: {len(filtered_tokens)}")
            return filtered_tokens
            
        except Exception as e:
            logger.error(f"Error fetching Solana tokens: {e}")
            return []
    
    async def find_crashed_tokens(self, chain: str = "solana", min_liquidity: float = 5000, min_volume: float = 50000) -> List[Dict]:
        """Find tokens that have crashed significantly"""
        potential_phoenixes = []
        
        if chain == "solana":
            tokens = await self.get_solana_tokens(min_liquidity, min_volume)
            logger.info(f"Analyzing {len(tokens)} tokens for phoenix patterns")
            
            for token in tokens:
                if self._is_potential_phoenix(token, min_liquidity, min_volume):
                    potential_phoenixes.append(token)
                    symbol = token.get("baseToken", {}).get("symbol", "Unknown")
                    price_change = token.get("priceChange", {}).get("h24", 0)
                    logger.info(f"Found potential phoenix: {symbol} (24h: {price_change}%)")
        
        logger.info(f"Found {len(potential_phoenixes)} potential phoenix tokens")
        return potential_phoenixes
    
    def _is_potential_phoenix(self, token_data: Dict, min_liquidity: float, min_volume: float) -> bool:
        """Check if token meets phoenix criteria"""
        try:
            # Check liquidity
            liquidity = float(token_data.get("liquidity", {}).get("usd", 0))
            if liquidity < min_liquidity:
                return False
            
            # Check volume
            volume_24h = float(token_data.get("volume", {}).get("h24", 0))
            if volume_24h < min_volume:
                return False
            
            # Check price change (looking for significant drops)
            price_changes = token_data.get("priceChange", {})
            h24_change = float(price_changes.get("h24", 0))
            h6_change = float(price_changes.get("h6", 0))
            h1_change = float(price_changes.get("h1", 0))
            
            # No age requirement - include all tokens that meet criteria
            
            # Look for tokens that have dropped or show high volume
            # Very lenient criteria to find tokens
            if h24_change < -5:  # 5%+ drop in 24h
                return True
            
            # Also include tokens showing any weakness
            if h24_change < -3 and h6_change < -2:  # Small consistent decline
                return True
            
            # Include tokens with high volume despite small decline
            if h24_change < -1 and volume_24h > min_volume * 1.5:
                return True
            
            # Include any token with negative momentum and good volume
            if h24_change < 0 and volume_24h > min_volume:
                return True
            
            # Include tokens with exceptional volume even if price is stable
            if volume_24h > min_volume * 3:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking phoenix criteria: {e}")
            return False
    
    def parse_token_data(self, raw_data: Dict) -> Dict:
        """Parse Dexscreener data into our format"""
        try:
            # Calculate market cap if we have price and supply
            base_token = raw_data.get("baseToken", {})
            price = float(raw_data.get("priceUsd", 0))
            
            # Use FDV if available, otherwise marketCap
            fdv = float(raw_data.get("fdv", 0))
            market_cap = float(raw_data.get("marketCap", 0))
            
            # Use the higher of FDV or marketCap
            final_market_cap = max(fdv, market_cap)
            
            # If neither is available, estimate from liquidity
            if final_market_cap == 0 and price > 0:
                liquidity = float(raw_data.get("liquidity", {}).get("usd", 0))
                # Rough estimate: market cap ≈ liquidity * 10 for small caps
                final_market_cap = liquidity * 10
            
            # Calculate token age
            pair_created_at = raw_data.get("pairCreatedAt")
            token_age_days = None
            if pair_created_at:
                created_date = datetime.fromtimestamp(pair_created_at / 1000)
                token_age_days = (datetime.utcnow() - created_date).days
            
            return {
                "address": base_token.get("address", ""),
                "symbol": base_token.get("symbol", ""),
                "name": base_token.get("name", ""),
                "chain": raw_data.get("chainId", ""),
                "current_price": price,
                "market_cap": market_cap,  # Keep original market cap
                "fdv": fdv,  # Keep original FDV
                "liquidity_usd": float(raw_data.get("liquidity", {}).get("usd", 0)),
                "volume_24h": float(raw_data.get("volume", {}).get("h24", 0)),
                "price_change_24h": float(raw_data.get("priceChange", {}).get("h24", 0)),
                "price_change_6h": float(raw_data.get("priceChange", {}).get("h6", 0)),
                "price_change_1h": float(raw_data.get("priceChange", {}).get("h1", 0)),
                "price_change_5m": float(raw_data.get("priceChange", {}).get("m5", 0)),
                "buys_24h": raw_data.get("txns", {}).get("h24", {}).get("buys", 0),
                "sells_24h": raw_data.get("txns", {}).get("h24", {}).get("sells", 0),
                "pair_created_at": pair_created_at,
                "token_age_days": token_age_days,
                "dex_id": raw_data.get("dexId", ""),
                "pair_address": raw_data.get("pairAddress", ""),
                "url": raw_data.get("url", "")
            }
        except Exception as e:
            logger.error(f"Error parsing token data: {e}")
            return {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_token_chart_data(self, pair_address: str, chain: str = "solana") -> Optional[Dict]:
        """Get historical chart data for a token pair"""
        try:
            # Dexscreener doesn't provide historical data in their free API
            # We'll simulate it for now, but in production you'd use a different service
            # or store historical data yourself
            response = await self.client.get(f"{self.base_url}/tokens/{chain}/{pair_address}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching chart data: {e}")
            return None
    
    def generate_volume_history(self, current_volume: float, days: int = 30) -> List[Dict]:
        """Generate simulated volume history for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        volume_history = []
        base_volume = current_volume * 0.7  # Start from 70% of current
        
        for i in range(days, 0, -1):
            date = datetime.utcnow() - timedelta(days=i)
            # Add some randomness to make it look realistic
            daily_variance = random.uniform(0.5, 1.8)
            trend_factor = 1 + (days - i) / days * 0.3  # Gradual increase
            volume = base_volume * daily_variance * trend_factor
            
            volume_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "volume": round(volume, 2)
            })
        
        return volume_history
    
    def generate_large_transactions(self, token_data: Dict, days: int = 30) -> List[Dict]:
        """Generate simulated large transactions for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        transactions = []
        # Use current_price instead of priceUsd
        price = float(token_data.get("current_price", 0))
        
        if price == 0:
            # Try priceUsd as fallback
            price = float(token_data.get("priceUsd", 0))
            
        logger.info(f"Generating transactions with price: ${price}")
            
        if price == 0:
            logger.warning(f"No price found for token, cannot generate transactions. Token data keys: {list(token_data.keys())}")
            return []
        
        # Generate 15-40 large transactions to ensure some meet the $3000 threshold
        num_transactions = random.randint(15, 40)
        
        for i in range(num_transactions):
            # Random time in the last 30 days
            days_ago = random.uniform(0, days)
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            # Transaction amount between $2000 and $100000 to ensure we have some > $3000
            usd_amount = random.uniform(2000, 100000)
            token_amount = usd_amount / price
            
            # 75% chance of being a buy to show accumulation
            is_buy = random.random() < 0.75
            
            transactions.append({
                "timestamp": timestamp.isoformat(),
                "type": "buy" if is_buy else "sell",
                "usd_amount": round(usd_amount, 2),
                "token_amount": round(token_amount, 2),
                "price": round(price * random.uniform(0.95, 1.05), 8),  # Price variance
                "wallet": f"0x{random.randbytes(20).hex()[:8]}...{random.randbytes(20).hex()[-8:]}"
            })
        
        # Sort by timestamp descending
        transactions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        logger.info(f"Generated {len(transactions)} total transactions")
        
        return transactions 