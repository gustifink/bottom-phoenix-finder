import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test top phoenixes
        print("Testing /api/top-phoenixes...")
        response = await client.get("http://localhost:8000/api/top-phoenixes?limit=1")
        data = response.json()
        
        if data:
            token = data[0]
            print(f"\nToken: {token['symbol']}")
            print(f"Crash %: {token.get('crash_percentage', 'MISSING')}")
            print(f"Price change 24h: {token.get('price_change_24h', 'MISSING')}")
            print(f"Token age days: {token.get('token_age_days', 'MISSING')}")
            print(f"FDV: {token.get('fdv', 'MISSING')}")
            print(f"Market Cap: {token.get('market_cap', 'MISSING')}")
            
            # Test analysis endpoint
            print(f"\nTesting /api/token/{token['address']}/analysis...")
            analysis_response = await client.get(f"http://localhost:8000/api/token/{token['address']}/analysis")
            if analysis_response.status_code == 200:
                analysis = analysis_response.json()
                print(f"Analysis loaded successfully")
                print(f"Market metrics FDV: {analysis['market_metrics'].get('fdv', 'MISSING')}")
                print(f"Crash from ATH: {analysis['phoenix_indicators'].get('crash_from_ath', 'MISSING')}")
                print(f"Large transactions: {analysis['large_transactions']['total_count']} transactions")
            else:
                print(f"Analysis failed: {analysis_response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_api()) 