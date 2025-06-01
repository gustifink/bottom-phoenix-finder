# Bottom - Deployment Guide

## Overview
Bottom is a Solana Phoenix Token Finder that identifies crashed memecoin tokens with recovery potential. This guide covers deployment to Vercel.

## Architecture
- **Frontend**: Vanilla HTML/CSS/JavaScript served as static files
- **Backend**: FastAPI as Vercel serverless functions
- **Database**: In-memory SQLite (resets on each function call)
- **API**: Dexscreener free API for token data

## Vercel Deployment

### Prerequisites
1. Install Vercel CLI: `npm i -g vercel`
2. Create a Vercel account
3. Install Git and initialize repository

### Setup Steps

1. **Initialize Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Deploy to Vercel**
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Set up and deploy? **Y**
   - Which scope? Choose your account
   - Link to existing project? **N**
   - Project name: `bottom-phoenix-finder`
   - In which directory is your code located? `./`
   - Want to override settings? **N**

3. **Configure Environment Variables**
   ```bash
   vercel env add DATABASE_URL
   # Enter: sqlite:///:memory:
   
   vercel env add BRS_UPDATE_INTERVAL
   # Enter: 15
   ```

4. **Deploy Production**
   ```bash
   vercel --prod
   ```

### Environment Variables
Set these in your Vercel dashboard or via CLI:

- `DATABASE_URL`: `sqlite:///:memory:` (for serverless)
- `BRS_UPDATE_INTERVAL`: `15` (minutes)
- `NODE_ENV`: `production`

### File Structure
```
/
├── api/
│   └── main.py          # Vercel serverless function
├── frontend/
│   ├── index.html       # Main frontend
│   ├── app.js          # JavaScript application
│   └── styles.css      # Styling
├── models/             # Database models
├── services/           # Business logic
├── vercel.json         # Vercel configuration
├── requirements.txt    # Python dependencies
└── README.md
```

### Features in Production
- ✅ Real-time Solana token discovery
- ✅ BRS (Bottom Recovery Score) calculation
- ✅ Responsive dark theme UI
- ✅ Token analysis with charts
- ✅ Dexscreener integration
- ✅ Large transaction tracking (simulated)

### Limitations in Serverless
- Database resets on each function call (use external DB for persistence)
- WebSocket connections not supported (polling used instead)
- Background tasks run on-demand only
- 30-second function timeout

### Monitoring & Logs
- View logs: `vercel logs your-deployment-url`
- Monitor functions in Vercel dashboard
- Check API health: `https://your-domain.vercel.app/health`

### Custom Domain (Optional)
1. Go to Vercel dashboard
2. Project Settings > Domains
3. Add your custom domain
4. Update DNS records as instructed

### Performance Tips
- API responses are cached briefly
- Token discovery happens on-demand
- Large transaction data is simulated for speed
- Frontend uses optimized loading states

### Support
For issues:
1. Check Vercel function logs
2. Verify environment variables
3. Test API endpoints individually
4. Check Dexscreener API rate limits

## Local Development
```bash
# Frontend
cd frontend && python3 -m http.server 8080

# Backend (separate terminal)
cd backend && source venv/bin/activate
export PYTHONPATH=$(pwd):$PYTHONPATH
python3 app/main.py
```

Visit: http://localhost:8080 