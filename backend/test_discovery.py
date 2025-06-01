import asyncio
import sys
sys.path.append('.')

from services.dexscreener import DexscreenerService
import logging

logging.basicConfig(level=logging.INFO)

async def test_discovery():
    service = DexscreenerService()
    try:
        print("Testing token discovery...")
        tokens = await service.find_crashed_tokens(
            chain="solana",
            min_liquidity=5000,
            min_volume=50000
        )
        
        print(f"\nFound {len(tokens)} potential phoenix tokens:")
        for i, token in enumerate(tokens[:5]):  # Show first 5
            base = token.get("baseToken", {})
            print(f"\n{i+1}. {base.get('symbol', 'Unknown')} ({base.get('name', 'Unknown')})")
            print(f"   Address: {base.get('address', 'Unknown')}")
            print(f"   24h Change: {token.get('priceChange', {}).get('h24', 0):.2f}%")
            print(f"   Liquidity: ${token.get('liquidity', {}).get('usd', 0):,.0f}")
            print(f"   Volume: ${token.get('volume', {}).get('h24', 0):,.0f}")
            print(f"   Market Cap: ${token.get('marketCap', 0):,.0f}")
            
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_discovery()) 