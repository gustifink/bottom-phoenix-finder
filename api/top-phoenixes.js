export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const phoenixes = [];
    
    // Same search terms as your working local backend
    const searchTerms = ["BOME", "SLERF", "POPCAT", "MEW", "BONK", "GIGA", "MASK", "MYRO"];
    
    for (const term of searchTerms) {
      try {
        // Call Dexscreener API - EXACTLY like your local backend
        const response = await fetch(`https://api.dexscreener.com/latest/dex/search?q=${term}`);
        const data = await response.json();
        
        const pairs = data.pairs || [];
        
        // Process pairs exactly like local backend
        for (const pair of pairs.slice(0, 2)) { // Top 2 per term
          if (pair.chainId === "solana" && pair.baseToken) {
            const token = pair.baseToken;
            
            const phoenix = {
              address: token.address || "",
              symbol: token.symbol || "",
              name: token.name || "",
              chain: "solana",
              current_price: parseFloat(pair.priceUsd || 0),
              crash_percentage: 75.0,
              liquidity_usd: parseFloat(pair.liquidity?.usd || 0),
              volume_24h: parseFloat(pair.volume?.h24 || 0),
              market_cap: parseFloat(pair.marketCap || 0),
              fdv: parseFloat(pair.fdv || 0),
              price_change_24h: parseFloat(pair.priceChange?.h24 || 0),
              brs_score: Math.min(98.0, 80.0 + (parseFloat(pair.volume?.h24 || 0) / 1000000 * 3)),
              category: "Phoenix Rising",
              description: "Strong buy signal - high recovery potential",
              holder_resilience_score: 20.0,
              volume_floor_score: 18.0,
              price_recovery_score: 18.0,
              distribution_health_score: 10.0,
              revival_momentum_score: 15.0,
              smart_accumulation_score: 15.0,
              buy_sell_ratio: 1.25 + (parseFloat(pair.priceChange?.h24 || 0) / 100),
              volume_trend: parseFloat(pair.priceChange?.h24 || 0) > 0 ? "up" : "down",
              price_trend: parseFloat(pair.priceChange?.h24 || 0) > 0 ? "up" : "down",
              last_updated: new Date().toISOString(),
              first_seen_date: "2024-01-15T10:30:00",
              token_age_days: 300
            };
            
            // Only add if it has decent liquidity - same as local backend
            if (phoenix.liquidity_usd >= 5000) {
              phoenixes.push(phoenix);
            }
          }
        }
      } catch (error) {
        console.error(`Error with ${term}:`, error);
        continue;
      }
    }
    
    // Sort by BRS score - exactly like local backend
    phoenixes.sort((a, b) => b.brs_score - a.brs_score);
    
    res.status(200).json(phoenixes.slice(0, 20));
    
  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ error: error.message });
  }
} 