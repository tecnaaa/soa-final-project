from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Coaching Service")

class Session(BaseModel):
    session_id: int
    user_id: int
    pt_id: int
    session_date_time: str
    duration_minutes: int
    session_type: str

# In-memory demo
_SESSIONS = {}

@app.get('/health')
async def health():
    return {"status":"ok"}

@app.get('/sessions', response_model=List[Session])
async def list_sessions():
    return list(_SESSIONS.values())

@app.post('/sessions', response_model=Session)
async def create_session(s: Session):
    if s.session_id in _SESSIONS:
        raise HTTPException(status_code=400, detail='session exists')
    _SESSIONS[s.session_id] = s.dict()
    return s

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8007, reload=True)
