from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Users Service")

class User(BaseModel):
    id: int
    name: str
    email: str

# in-memory store for demo
_USERS = {1: {"id":1, "name":"Alice", "email":"alice@example.com"}}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/users", response_model=List[User])
async def list_users():
    return list(_USERS.values())

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    user = _USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="not found")
    return user

@app.post("/users", response_model=User)
async def create_user(user: User):
    if user.id in _USERS:
        raise HTTPException(status_code=400, detail="id exists")
    _USERS[user.id] = user.dict()
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
