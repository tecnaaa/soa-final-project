from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Calories Service")

class Food(BaseModel):
    food_id: int
    food_name: str
    calories_kcal: float
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carb_g: Optional[float] = None

class RecipeIngredient(BaseModel):
    recipe_ingredient_id: int
    recipe_id: int
    food_id: int
    quantity_g: float

class Recipe(BaseModel):
    recipe_id: int
    recipe_name: str
    total_servings: int
    total_calories_kcal: Optional[float] = None

# In-memory demo
_FOODS = {1: {"food_id":1, "food_name":"Ức gà", "calories_kcal":165.0, "protein_g":31.0}}
_RECIPES = {}
_RECIPE_ING = {}

@app.get('/health')
async def health():
    return {"status":"ok"}

@app.get('/foods', response_model=List[Food])
async def list_foods():
    return list(_FOODS.values())

@app.post('/foods', response_model=Food)
async def create_food(f: Food):
    if f.food_id in _FOODS:
        raise HTTPException(status_code=400, detail='food exists')
    _FOODS[f.food_id] = f.dict()
    return f

@app.get('/recipes', response_model=List[Recipe])
async def list_recipes():
    return list(_RECIPES.values())

@app.post('/recipes', response_model=Recipe)
async def create_recipe(r: Recipe):
    if r.recipe_id in _RECIPES:
        raise HTTPException(status_code=400, detail='recipe exists')
    _RECIPES[r.recipe_id] = r.dict()
    return r

@app.post('/recipe-ingredients', response_model=RecipeIngredient)
async def create_recipe_ing(ri: RecipeIngredient):
    if ri.recipe_ingredient_id in _RECIPE_ING:
        raise HTTPException(status_code=400, detail='exists')
    _RECIPE_ING[ri.recipe_ingredient_id] = ri.dict()
    return ri

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8006, reload=True)
