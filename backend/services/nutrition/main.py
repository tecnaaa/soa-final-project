from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Nutrition Service")

class Meal(BaseModel):
    id: int
    name: str
    calories: int

_MEALS = {1: {"id":1, "name":"Oatmeal", "calories":150}}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/meals", response_model=List[Meal])
async def list_meals():
    return list(_MEALS.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
