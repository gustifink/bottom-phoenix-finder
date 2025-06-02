from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Bottom - Phoenix Token Finder API",
        "status": "running",
        "endpoints": {
            "top_phoenixes": "/api/top-phoenixes",
            "recent_alerts": "/api/alerts/recent",
            "token_analysis": "/api/token/{address}/analysis",
            "health": "/api/health"
        }
    }

@app.get("/api")
async def api_root():
    return {
        "message": "Bottom API",
        "status": "healthy",
        "version": "1.0.0"
    }

# Export the app for Vercel
def handler(request, response):
    return app(request, response) 