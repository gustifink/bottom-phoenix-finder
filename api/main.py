from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bottom API working"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/health")
async def api_health():
    return {"status": "api healthy"}

@app.get("/api/test")
async def test():
    return {"message": "Test endpoint working", "data": [1, 2, 3]}

# Vercel handler
def handler(request, response):
    return app(request, response) 