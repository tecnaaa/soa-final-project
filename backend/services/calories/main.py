from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional
from datetime import date, datetime, timedelta
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from models.calorie.calorie_models import (
    Food, Recipe, RecipeIngredient, UserDailyLog, UserMeal, MealItem, UserFavoriteFood,
    FoodCreate, FoodResponse, RecipeCreate, RecipeResponse,
    UserDailyLogCreate, UserDailyLogResponse, UserMealCreate, UserMealResponse,
    UserFavoriteFoodCreate, UserFavoriteFoodResponse, MealItemResponse
)
from db.db import get_db, init_db, Base
from services.logging_utils import setup_logging
from services.error_tracking import init_error_tracking, capture_error

# Initialize logging
setup_logging("calories_service")
logger = logging.getLogger(__name__)
init_error_tracking("calories_service")

app = FastAPI(title="Calorie Service")

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Calories service database initialized")

# Health Check
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "calories", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {e}"
        )

# Helper Functions
async def calculate_meal_nutrition(db: AsyncSession, meal_items):
    """Calculate total nutrition facts for a meal"""
    total_calories = total_protein = total_carbs = total_fat = 0
    
    for item in meal_items:
        if item.food_id:
            result = await db.execute(select(Food).where(Food.food_id == item.food_id))
            food = result.scalars().first()
            if not food:
                raise HTTPException(status_code=404, detail=f"Food {item.food_id} not found")
            multiplier = item.quantity_grams / 100
            total_calories += food.calories_per_100g * multiplier
            total_protein += food.protein * multiplier
            total_carbs += food.carbs * multiplier
            total_fat += food.fat * multiplier
        elif item.recipe_id:
            result = await db.execute(select(Recipe).where(Recipe.recipe_id == item.recipe_id))
            recipe = result.scalars().first()
            if not recipe:
                raise HTTPException(status_code=404, detail=f"Recipe {item.recipe_id} not found")
            # Calculate recipe nutrition based on ingredients
            result = await db.execute(
                select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.recipe_id)
            )
            recipe_items = result.scalars().all()
            for ri in recipe_items:
                result = await db.execute(select(Food).where(Food.food_id == ri.food_id))
                food = result.scalars().first()
                multiplier = (ri.weight_grams * item.quantity_grams) / 100
                total_calories += food.calories_per_100g * multiplier
                total_protein += food.protein * multiplier
                total_carbs += food.carbs * multiplier
                total_fat += food.fat * multiplier
                
    return {
        "calories": round(total_calories, 2),
        "protein": round(total_protein, 2),
        "carbs": round(total_carbs, 2),
        "fat": round(total_fat, 2)
    }

@app.post("/foods/", response_model=FoodResponse)
async def create_food(food: FoodCreate, db: AsyncSession = Depends(get_db)):
    db_food = Food(**food.dict())
    db.add(db_food)
    try:
        await db.commit()
        await db.refresh(db_food)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create food item"
        )
    return db_food

@app.get("/foods/", response_model=List[FoodResponse])
async def list_foods(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Food).offset(skip).limit(limit))
    return result.scalars().all()

@app.get("/foods/search/", response_model=List[FoodResponse])
async def search_foods(query: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Food).where(Food.name.ilike(f"%{query}%")))
    return result.scalars().all()

@app.post("/recipes/", response_model=RecipeResponse)
async def create_recipe(recipe: RecipeCreate, db: AsyncSession = Depends(get_db)):
    # Create recipe
    db_recipe = Recipe(name=recipe.name, description=recipe.description)
    db.add(db_recipe)
    await db.flush()  # Get recipe_id without committing

    # Add ingredients
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    for ingredient in recipe.ingredients:
        result = await db.execute(select(Food).where(Food.food_id == ingredient.food_id))
        food = result.scalars().first()
        if not food:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Food with id {ingredient.food_id} not found"
            )

        # Calculate nutrition facts based on weight
        weight_multiplier = ingredient.weight_grams / 100
        total_calories += food.calories_per_100g * weight_multiplier
        total_protein += food.protein * weight_multiplier
        total_carbs += food.carbs * weight_multiplier
        total_fat += food.fat * weight_multiplier

        # Add ingredient to recipe
        db_ingredient = RecipeIngredient(
            recipe_id=db_recipe.recipe_id,
            food_id=ingredient.food_id,
            weight_grams=ingredient.weight_grams
        )
        db.add(db_ingredient)

    try:
        await db.commit()
        await db.refresh(db_recipe)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create recipe"
        )

    # Construct response
    response = RecipeResponse(
        recipe_id=db_recipe.recipe_id,
        name=db_recipe.name,
        description=db_recipe.description,
        total_calories=round(total_calories, 2),
        total_protein=round(total_protein, 2),
        total_carbs=round(total_carbs, 2),
        total_fat=round(total_fat, 2),
        ingredients=[
            FoodResponse.from_orm(
                (await db.execute(select(Food).where(Food.food_id == ing.food_id))).scalars().first()
            )
            for ing in (await db.execute(
                select(RecipeIngredient).where(RecipeIngredient.recipe_id == db_recipe.recipe_id)
            )).scalars().all()
        ]
    )
    return response

@app.get("/recipes/", response_model=List[RecipeResponse])
async def list_recipes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recipe).offset(skip).limit(limit))
    recipes = result.scalars().all()
    response = []
    for recipe in recipes:
        # Calculate nutrition facts
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        ing_result = await db.execute(
            select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.recipe_id)
        )
        ingredients = ing_result.scalars().all()
        
        for ingredient in ingredients:
            food_result = await db.execute(select(Food).where(Food.food_id == ingredient.food_id))
            food = food_result.scalars().first()
            weight_multiplier = ingredient.weight_grams / 100
            total_calories += food.calories_per_100g * weight_multiplier
            total_protein += food.protein * weight_multiplier
            total_carbs += food.carbs * weight_multiplier
            total_fat += food.fat * weight_multiplier
        
        response.append(RecipeResponse(
            recipe_id=recipe.recipe_id,
            name=recipe.name,
            description=recipe.description,
            total_calories=round(total_calories, 2),
            total_protein=round(total_protein, 2),
            total_carbs=round(total_carbs, 2),
            total_fat=round(total_fat, 2),
            ingredients=[FoodResponse.from_orm(
                (await db.execute(select(Food).where(Food.food_id == ing.food_id))).scalars().first()
            ) for ing in ingredients]
        ))
    return response

@app.post("/logs/", response_model=UserDailyLogResponse)
async def create_daily_log(
    log: UserDailyLogCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a new daily log for tracking calories"""
    # Check if log already exists for this date
    result = await db.execute(
        select(UserDailyLog).where(
            UserDailyLog.user_id == user_id,
            UserDailyLog.date == log.date
        )
    )
    existing_log = result.scalars().first()
    
    if existing_log:
        raise HTTPException(
            status_code=400,
            detail=f"Log already exists for date {log.date}"
        )
        
    db_log = UserDailyLog(**log.dict(), user_id=user_id)
    db.add(db_log)
    
    try:
        await db.commit()
        await db.refresh(db_log)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    return db_log

@app.get("/logs/{log_id}", response_model=UserDailyLogResponse)
async def get_daily_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific daily log with all meals and nutrition totals"""
    result = await db.execute(select(UserDailyLog).where(UserDailyLog.log_id == log_id))
    log = result.scalars().first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    # Calculate totals from all meals
    meals_result = await db.execute(select(UserMeal).where(UserMeal.log_id == log_id))
    meals = meals_result.scalars().all()
    total_calories = total_protein = total_carbs = total_fat = 0
    
    for meal in meals:
        items_result = await db.execute(select(MealItem).where(MealItem.meal_id == meal.meal_id))
        items = items_result.scalars().all()
        nutrition = await calculate_meal_nutrition(db, items)
        total_calories += nutrition["calories"]
        total_protein += nutrition["protein"]
        total_carbs += nutrition["carbs"]
        total_fat += nutrition["fat"]
        
    return {
        **log.__dict__,
        "total_calories": round(total_calories, 2),
        "total_protein": round(total_protein, 2),
        "total_carbs": round(total_carbs, 2),
        "total_fat": round(total_fat, 2)
    }

@app.get("/logs/user/{user_id}", response_model=List[UserDailyLogResponse])
async def get_user_logs(
    user_id: int,
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all daily logs for a user within a date range"""
    query = select(UserDailyLog).where(UserDailyLog.user_id == user_id)
    
    if start_date:
        query = query.where(UserDailyLog.date >= start_date)
    if end_date:
        query = query.where(UserDailyLog.date <= end_date)
        
    result = await db.execute(query.order_by(UserDailyLog.date.desc()))
    logs = result.scalars().all()
    
    # Calculate nutrition totals for each log
    response = []
    for log in logs:
        meals_result = await db.execute(select(UserMeal).where(UserMeal.log_id == log.log_id))
        meals = meals_result.scalars().all()
        total_calories = total_protein = total_carbs = total_fat = 0
        
        for meal in meals:
            items_result = await db.execute(select(MealItem).where(MealItem.meal_id == meal.meal_id))
            items = items_result.scalars().all()
            nutrition = await calculate_meal_nutrition(db, items)
            total_calories += nutrition["calories"]
            total_protein += nutrition["protein"]
            total_carbs += nutrition["carbs"]
            total_fat += nutrition["fat"]
            
        response.append({
            **log.__dict__,
            "total_calories": round(total_calories, 2),
            "total_protein": round(total_protein, 2),
            "total_carbs": round(total_carbs, 2),
            "total_fat": round(total_fat, 2)
        })
        
    return response

@app.post("/meals/", response_model=UserMealResponse)
async def create_meal(meal: UserMealCreate, log_id: int, db: AsyncSession = Depends(get_db)):
    """Add a new meal to a daily log"""
    # Verify log exists
    result = await db.execute(select(UserDailyLog).where(UserDailyLog.log_id == log_id))
    log = result.scalars().first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
        
    # Create meal
    db_meal = UserMeal(
        log_id=log_id,
        meal_type=meal.meal_type,
        meal_time=meal.meal_time,
        notes=meal.notes
    )
    db.add(db_meal)
    await db.flush()
    
    # Add meal items
    for item in meal.items:
        db_item = MealItem(
            meal_id=db_meal.meal_id,
            food_id=item.food_id,
            recipe_id=item.recipe_id,
            quantity_grams=item.quantity_grams
        )
        db.add(db_item)
        
    try:
        await db.commit()
        await db.refresh(db_meal)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    # Calculate nutrition facts
    items_result = await db.execute(select(MealItem).where(MealItem.meal_id == db_meal.meal_id))
    items = items_result.scalars().all()
    nutrition = await calculate_meal_nutrition(db, items)
    
    return {
        **db_meal.__dict__,
        "items": [
            {
                **item.__dict__,
                "food": (await db.execute(select(Food).where(Food.food_id == item.food_id))).scalars().first() if item.food_id else None,
                "recipe": (await db.execute(select(Recipe).where(Recipe.recipe_id == item.recipe_id))).scalars().first() if item.recipe_id else None,
                **await calculate_meal_nutrition(db, [item])
            }
            for item in items
        ],
        **nutrition
    }

@app.get("/meals/{meal_id}", response_model=UserMealResponse)
async def get_meal(meal_id: int, db: AsyncSession = Depends(get_db)):
    """Get details of a specific meal"""
    result = await db.execute(select(UserMeal).where(UserMeal.meal_id == meal_id))
    meal = result.scalars().first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
        
    items_result = await db.execute(select(MealItem).where(MealItem.meal_id == meal_id))
    items = items_result.scalars().all()
    nutrition = await calculate_meal_nutrition(db, items)
    
    return {
        **meal.__dict__,
        "items": [
            {
                **item.__dict__,
                "food": (await db.execute(select(Food).where(Food.food_id == item.food_id))).scalars().first() if item.food_id else None,
                "recipe": (await db.execute(select(Recipe).where(Recipe.recipe_id == item.recipe_id))).scalars().first() if item.recipe_id else None,
                **await calculate_meal_nutrition(db, [item])
            }
            for item in items
        ],
        **nutrition
    }

@app.delete("/meals/{meal_id}")
async def delete_meal(meal_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a meal and its items"""
    result = await db.execute(select(UserMeal).where(UserMeal.meal_id == meal_id))
    meal = result.scalars().first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
        
    try:
        await db.delete(meal)  # Will cascade delete meal items
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"message": "Meal deleted"}

@app.post("/favorites/", response_model=UserFavoriteFoodResponse)
async def add_favorite_food(
    favorite: UserFavoriteFoodCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Add a food or recipe to user's favorites"""
    # Check if already favorited
    result = await db.execute(
        select(UserFavoriteFood).where(
            UserFavoriteFood.user_id == user_id,
            UserFavoriteFood.food_id == favorite.food_id if favorite.food_id else None,
            UserFavoriteFood.recipe_id == favorite.recipe_id if favorite.recipe_id else None
        )
    )
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Food/recipe already in favorites"
        )
        
    db_favorite = UserFavoriteFood(**favorite.dict(), user_id=user_id)
    db.add(db_favorite)
    
    try:
        await db.commit()
        await db.refresh(db_favorite)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    return {
        **db_favorite.__dict__,
        "food": (await db.execute(select(Food).where(Food.food_id == favorite.food_id))).scalars().first() if favorite.food_id else None,
        "recipe": (await db.execute(select(Recipe).where(Recipe.recipe_id == favorite.recipe_id))).scalars().first() if favorite.recipe_id else None
    }

@app.get("/favorites/user/{user_id}", response_model=List[UserFavoriteFoodResponse])
async def get_user_favorites(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all favorite foods/recipes for a user"""
    result = await db.execute(
        select(UserFavoriteFood).where(UserFavoriteFood.user_id == user_id)
    )
    favorites = result.scalars().all()
    
    return [
        {
            **fav.__dict__,
            "food": (await db.execute(select(Food).where(Food.food_id == fav.food_id))).scalars().first() if fav.food_id else None,
            "recipe": (await db.execute(select(Recipe).where(Recipe.recipe_id == fav.recipe_id))).scalars().first() if fav.recipe_id else None
        }
        for fav in favorites
    ]

@app.delete("/favorites/{favorite_id}")
async def remove_favorite(favorite_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a food/recipe from favorites"""
    result = await db.execute(
        select(UserFavoriteFood).where(UserFavoriteFood.id == favorite_id)
    )
    favorite = result.scalars().first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
        
    try:
        await db.delete(favorite)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"message": "Favorite removed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
