# Bottom - Solana Phoenix Token Finder

## Overview

Bottom is an advanced crypto analysis tool that identifies Solana memecoin tokens that have crashed significantly but show strong recovery potential. The system uses a proprietary Bottom Resilience Score (BRS) to evaluate tokens across 6 key metrics.

## Features

### 1. **Comprehensive Token Analysis**
- **Real-time Monitoring**: Continuously scans Solana blockchain for crashed tokens
- **BRS Scoring System**: 100-point scoring across 6 components
- **Featured Phoenix Cards**: Highlights the best opportunities with detailed metrics
- **Analysis Preview**: Shows key indicators directly in the table view

### 2. **Advanced Filtering**
- Minimum market cap filters ($500K, $1M, $5M, $10M)
- Minimum volume filters ($50K, $100K, $250K, $500K)
- BRS score filtering (All, 60+, 80+)

### 3. **Detailed Token Analysis**
When you click "Analysis" on any token, you get:
- Token age and creation date
- Market metrics (price, market cap, liquidity, volume)
- Phoenix indicators (crash %, price changes, buy/sell ratio)
- Complete BRS breakdown with explanations
- Selection reasons - why this token was chosen
- Risk factors to consider
- Trading recommendations

### 4. **Visual Indicators**
- 🔥 Extreme volume alerts (when volume > 1000% of market cap)
- 📊 High volume indicators
- 💪 Strong accumulation signals
- 💧 Deep liquidity warnings
- 🆕 New token age alerts

## BRS Scoring Components

1. **Holder Resilience (20 pts)**: Buy/sell ratio analysis
2. **Volume Floor (20 pts)**: 24h trading volume assessment
3. **Price Recovery (20 pts)**: Recent price movement patterns
4. **Distribution Health (10 pts)**: Liquidity to market cap ratio
5. **Revival Momentum (15 pts)**: Volume trends and stabilization
6. **Smart Accumulation (15 pts)**: Buyer patterns and accumulation

## Installation & Usage

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$(pwd):$PYTHONPATH
python3 app/main.py
```

### Frontend Setup
```bash
cd frontend
python3 -m http.server 8080
```

Then open http://localhost:8080 in your browser.

## Key Selection Criteria

### Primary Requirements:
- **Minimum Market Cap**: $500K (configurable)
- **Minimum Daily Volume**: $50K (configurable)
- **Liquidity**: Must have sufficient liquidity for safe entry/exit

### Phoenix Patterns:
- Significant price decline (ideally 70%+ from ATH)
- High volume relative to market cap
- More buyers than sellers (accumulation)
- Strong liquidity depth

## Example Analysis: OKCC Token

The system found OKCC (Official King Charles Coin) with these exceptional metrics:
- **Volume/Market Cap Ratio**: 4,682% (!!)
- **Liquidity/Market Cap**: 48.7%
- **Buy/Sell Ratio**: 1.12 (more buyers than sellers)
- **BRS Score**: 71/100

This demonstrates the system's ability to find tokens with extreme volume divergence - a key indicator of potential explosive moves.

## API Endpoints

- `GET /health` - Check backend status
- `GET /api/top-phoenixes` - Get top phoenix tokens
- `GET /api/token/{address}/analysis` - Get detailed token analysis
- `GET /api/alerts/recent` - Get recent phoenix alerts
- `POST /api/watchlist/add` - Add token to watchlist
- `WebSocket /ws/updates` - Real-time token updates

## Technologies Used

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Data Source**: Dexscreener API (no key required)
- **Real-time**: WebSocket for live updates

## Risk Disclaimer

This tool identifies high-risk, high-reward opportunities in the memecoin space. These are speculative investments suitable only for risk capital. Always:
- Use proper position sizing (1-2% of portfolio max)
- Set stop losses
- Take profits on the way up
- Never invest more than you can afford to lose

## Future Enhancements

- [ ] Telegram bot integration for alerts
- [ ] Historical performance tracking
- [ ] Multi-chain support (BSC, Ethereum, etc.)
- [ ] Advanced charting integration
- [ ] Community sentiment analysis
- [ ] Automated trading integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool is for informational purposes only. Always do your own research before making investment decisions. Crypto trading involves substantial risk of loss.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Dexscreener for providing free API access
- The crypto community for phoenix pattern insights
- All contributors and testers

---

Built with ❤️ for finding hidden gems at the bottom 