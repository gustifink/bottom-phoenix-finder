export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { url } = req;

  try {
    // Handle top-phoenixes endpoint
    if (url.includes('top-phoenixes')) {
      const phoenixes = [];
      const searchTerms = ["BOME", "SLERF", "POPCAT"];
      
      for (const term of searchTerms) {
        const response = await fetch(`https://api.dexscreener.com/latest/dex/search?q=${term}`);
        const data = await response.json();
        
        if (data.pairs && data.pairs.length > 0) {
          const pair = data.pairs[0];
          if (pair.chainId === "solana") {
            phoenixes.push({
              symbol: pair.baseToken?.symbol || term,
              name: pair.baseToken?.name || term,
              current_price: parseFloat(pair.priceUsd || 0),
              price_change_24h: parseFloat(pair.priceChange?.h24 || 0),
              volume_24h: parseFloat(pair.volume?.h24 || 0),
              market_cap: parseFloat(pair.fdv || 0),
              brs_score: 95.0,
              chain: "solana"
            });
          }
        }
      }
      
      return res.status(200).json(phoenixes);
    }

    // Handle alerts endpoint
    if (url.includes('alerts')) {
      return res.status(200).json([
        {
          id: 1,
          message: "BOME showing recovery potential",
          timestamp: new Date().toISOString()
        }
      ]);
    }

    return res.status(404).json({ error: 'Not found' });

  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
} 