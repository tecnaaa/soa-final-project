"""
SQLAlchemy models for the Calorie service.
"""

# --- 1. Imports ---

# Standard Library
import sys
from pathlib import Path
from typing import Optional, List
from datetime import date, datetime
from enum import Enum as PyEnum

# Third-Party Imports
from sqlalchemy import (
    Column, Integer, String, Numeric, TIMESTAMP, Float, ForeignKey, Enum
)
from sqlalchemy.sql import func
from pydantic import BaseModel

# --- 2. Path Setup (for local imports) ---

# Add the backend directory to the Python path for imports
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# --- 3. Local Application Imports ---

try:
    from db.db import Base
except ImportError:
    print(f"Error: Could not import 'Base' from db.db. Searched in: {backend_dir}")
    sys.exit(1)

# --- 4. Enums ---
class MealType(str, PyEnum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"

# --- 5. SQLAlchemy Models ---

class Food(Base):
    """
    SQLAlchemy model for the 'foods' table.
    Stores nutritional information for food items per 100g.
    """
    __tablename__ = "foods"
    
    food_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum('raw', 'cooked', name='food_type'), nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    fiber = Column(Float, default=0)
    sugar = Column(Float, default=0)
    category = Column(String(50))
    brand = Column(String(100))
    serving_size_grams = Column(Float)
    image_url = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

class Recipe(Base):
    """
    SQLAlchemy model for the 'recipes' table.
    Stores information about recipes.
    """
    __tablename__ = "recipes"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))

class RecipeIngredient(Base):
    """
    SQLAlchemy model for the 'recipe_ingredients' table.
    Stores information about ingredients in a recipe.
    """
    __tablename__ = "recipe_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id"))
    food_id = Column(Integer, ForeignKey("foods.food_id"))
    weight_grams = Column(Float, nullable=False)

class UserDailyLog(Base):
    """SQLAlchemy model for tracking daily calorie logs"""
    __tablename__ = "user_daily_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # No FK constraint to users_db
    date = Column(TIMESTAMP, nullable=False)
    target_calories = Column(Integer)
    notes = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class UserMeal(Base):
    """SQLAlchemy model for tracking individual meals"""
    __tablename__ = "user_meals"
    
    meal_id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("user_daily_logs.log_id"), nullable=False)
    meal_type = Column(Enum(MealType), nullable=False)
    meal_time = Column(TIMESTAMP, nullable=False)
    notes = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())

class MealItem(Base):
    """SQLAlchemy model for foods/recipes in a meal"""
    __tablename__ = "meal_items"
    
    item_id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("user_meals.meal_id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.food_id"))
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id"))
    quantity_grams = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class UserFavoriteFood(Base):
    """SQLAlchemy model for user's favorite foods"""
    __tablename__ = "user_favorite_foods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # No FK constraint to users_db
    food_id = Column(Integer, ForeignKey("foods.food_id"))
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id"))
    created_at = Column(TIMESTAMP, server_default=func.now())

# --- 6. Pydantic Models ---

class FoodBase(BaseModel):
    name: str
    type: str
    calories_per_100g: float
    protein: float
    carbs: float
    fat: float
    fiber: Optional[float] = 0
    sugar: Optional[float] = 0
    category: Optional[str] = None
    brand: Optional[str] = None
    serving_size_grams: Optional[float] = None
    image_url: Optional[str] = None

class FoodCreate(FoodBase):
    pass

class FoodResponse(FoodBase):
    food_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    name: str
    description: Optional[str] = None

class RecipeIngredientBase(BaseModel):
    food_id: int
    weight_grams: float

class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientBase]

class RecipeResponse(RecipeBase):
    recipe_id: int
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    ingredients: List[FoodResponse]

    class Config:
        from_attributes = True

class UserDailyLogBase(BaseModel):
    date: date
    target_calories: Optional[int] = None
    notes: Optional[str] = None

class UserDailyLogCreate(UserDailyLogBase):
    pass

class UserDailyLogResponse(UserDailyLogBase):
    log_id: int
    user_id: int
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MealItemBase(BaseModel):
    food_id: Optional[int] = None
    recipe_id: Optional[int] = None
    quantity_grams: float

class UserMealBase(BaseModel):
    meal_type: MealType
    meal_time: datetime
    notes: Optional[str] = None
    items: List[MealItemBase]

class UserMealCreate(UserMealBase):
    pass

class MealItemResponse(MealItemBase):
    item_id: int
    food: Optional[FoodResponse] = None
    recipe: Optional[RecipeResponse] = None
    calories: float
    protein: float
    carbs: float
    fat: float

    class Config:
        from_attributes = True

class UserMealResponse(UserMealBase):
    meal_id: int
    log_id: int
    items: List[MealItemResponse]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    created_at: datetime

    class Config:
        from_attributes = True

class UserFavoriteFoodBase(BaseModel):
    food_id: Optional[int] = None
    recipe_id: Optional[int] = None

class UserFavoriteFoodCreate(UserFavoriteFoodBase):
    pass

class UserFavoriteFoodResponse(UserFavoriteFoodBase):
    id: int
    user_id: int
    food: Optional[FoodResponse] = None
    recipe: Optional[RecipeResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True
