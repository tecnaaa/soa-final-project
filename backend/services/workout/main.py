from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Workout Service")

class Exercise(BaseModel):
    exercise_id: int
    plan_id: int
    day_of_week: str
    exercise_name: str
    sets: int
    reps: str
    weight_kg: Optional[float] = None

class Plan(BaseModel):
    plan_id: int
    user_id: int
    plan_name: str
    goal: Optional[str] = None
    start_date: Optional[str] = None
    created_by_pt_id: Optional[int] = None

class Progress(BaseModel):
    progress_id: int
    plan_id: int
    user_id: int
    exercise_id: Optional[int] = None
    date_recorded: Optional[str] = None

# In-memory stores for demo
_PLANS = {1: {"plan_id":1, "user_id":1, "plan_name":"Strength 8 weeks", "goal":"Tăng cơ"}}
_EXERCISES = {1: {"exercise_id":1, "plan_id":1, "day_of_week":"Thứ 2", "exercise_name":"Squat", "sets":4, "reps":"6-8", "weight_kg":80}}
_PROGRESS = {}

@app.get('/health')
async def health():
    return {"status":"ok"}

@app.get('/plans', response_model=List[Plan])
async def list_plans():
    return list(_PLANS.values())

@app.get('/plans/{plan_id}', response_model=Plan)
async def get_plan(plan_id: int):
    p = _PLANS.get(plan_id)
    if not p:
        raise HTTPException(status_code=404, detail='not found')
    return p

@app.post('/plans', response_model=Plan)
async def create_plan(plan: Plan):
    if plan.plan_id in _PLANS:
        raise HTTPException(status_code=400, detail='plan exists')
    _PLANS[plan.plan_id] = plan.dict()
    return plan

@app.get('/plans/{plan_id}/exercises', response_model=List[Exercise])
async def list_exercises(plan_id: int):
    return [e for e in _EXERCISES.values() if e['plan_id'] == plan_id]

@app.post('/exercises', response_model=Exercise)
async def create_exercise(ex: Exercise):
    if ex.exercise_id in _EXERCISES:
        raise HTTPException(status_code=400, detail='exercise exists')
    _EXERCISES[ex.exercise_id] = ex.dict()
    return ex

@app.post('/progress', response_model=Progress)
async def record_progress(p: Progress):
    if p.progress_id in _PROGRESS:
        raise HTTPException(status_code=400, detail='progress exists')
    _PROGRESS[p.progress_id] = p.dict()
    return p

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8005, reload=True)
