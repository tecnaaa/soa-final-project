"""Auth service

Notes:
- Corresponding tables: uses `users` for authentication (no separate auth table in this scaffold).
- This service provides token generation in the demo (dummy tokens). Replace with JWT or OAuth2 in production.
- Data store: in-memory / demo only. Add DB and secure secret management for production.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Auth Service")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Login Authentication
@app.post("/token", response_model=Token)
async def login(username: str, password: str):
    # Dummy auth - replace with real verification
    if not username:
        raise HTTPException(status_code=400, detail="username required")
    return {"access_token": f"token-for-{username}", "token_type": "bearer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
