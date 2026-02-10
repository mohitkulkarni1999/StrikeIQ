"""
Simple test for OAuth callback
"""

from fastapi import FastAPI, Query, HTTPException
import httpx
import os

app = FastAPI()

@app.get("/test/auth")
async def test_auth():
    """Test OAuth endpoint"""
    return {
        "message": "OAuth test endpoint",
        "api_key": os.getenv("UPSTOX_API_KEY", "not_set"),
        "redirect_uri": os.getenv("UPSTOX_REDIRECT_URI", "not_set")
    }

@app.post("/test/callback")
async def test_callback(code: str = Query(None)):
    """Test OAuth callback"""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code required")
    
    return {
        "message": "Callback received",
        "code": code,
        "code_length": len(code) if code else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
