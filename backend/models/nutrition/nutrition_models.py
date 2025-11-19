"""
SQLAlchemy models for the Meal Planner service.
Handles meal plan creation and recommendations based on user goals.
"""

# --- 1. Imports ---
import sys
from pathlib import Path
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, TIMESTAMP, Text,
    Enum as SQLEnum, JSON
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime

# --- 2. Path Setup ---
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# --- 3. Local Imports ---
try:
    from db.db import Base
except ImportError:
    print(f"Error: Could not import 'Base' from db.db. Searched in: {backend_dir}")
    sys.exit(1)

# --- 4. Model Definitions ---

class MealPlan(Base):
    """
    Meal plan created for a user based on their goal.
    References foods/recipes from Calorie Service.
    """
    __tablename__ = 'meal_plans'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }

    plan_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    plan_name = Column(String(255), nullable=False)
    goal = Column(
        SQLEnum('weight_loss', 'muscle_gain', 'maintenance', name='nutrition_goal_enum', native_enum=False),
        nullable=False
    )
    daily_calories = Column(Float, nullable=False)
    daily_protein = Column(Float, nullable=False)
    daily_carbs = Column(Float, nullable=False)
    daily_fat = Column(Float, nullable=False)
    duration_days = Column(Integer, default=30)
    is_active = Column(Integer, default=1)
    created_by_pt_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)  # PT who created this plan
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    meal_recommendations = relationship("MealRecommendation", back_populates="meal_plan", cascade="all, delete-orphan")
    daily_meals = relationship("DailyMealPlan", back_populates="meal_plan", cascade="all, delete-orphan")


class MealRecommendation(Base):
    """
    Recommended meals for a meal plan.
    Each recommendation includes food_id/recipe_id from Calorie Service.
    """
    __tablename__ = 'meal_recommendations'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }

    recommendation_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("meal_plans.plan_id"), nullable=False)
    meal_type = Column(
        SQLEnum('breakfast', 'lunch', 'dinner', 'snack', name='meal_type_enum', native_enum=False),
        nullable=False
    )
    day_of_week = Column(String(10))  # Monday, Tuesday, etc. or 'Any'
    
    # References to Calorie Service
    food_id = Column(Integer, nullable=True)  # For single food items
    recipe_id = Column(Integer, nullable=True)  # For recipes
    quantity_grams = Column(Float, nullable=False)
    
    # Nutritional info (cached from Calorie Service)
    estimated_calories = Column(Float)
    estimated_protein = Column(Float)
    estimated_carbs = Column(Float)
    estimated_fat = Column(Float)
    
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meal_recommendations")


class DailyMealPlan(Base):
    """
    User's actual daily meal intake based on meal plan.
    Tracks what they actually eat vs what was recommended.
    """
    __tablename__ = 'daily_meal_plans'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }

    daily_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("meal_plans.plan_id"), nullable=False)
    date = Column(TIMESTAMP, nullable=False)
    
    # Actual nutrition consumed
    actual_calories = Column(Float, default=0)
    actual_protein = Column(Float, default=0)
    actual_carbs = Column(Float, default=0)
    actual_fat = Column(Float, default=0)
    
    # Adherence tracking
    adherence_percentage = Column(Float, default=0)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="daily_meals")


# --- 5. Pydantic Models ---

class MealRecommendationCreate(BaseModel):
    meal_type: str
    day_of_week: str
    food_id: Optional[int] = None
    recipe_id: Optional[int] = None
    quantity_grams: float
    estimated_calories: Optional[float] = None
    estimated_protein: Optional[float] = None
    estimated_carbs: Optional[float] = None
    estimated_fat: Optional[float] = None
    notes: Optional[str] = None


class MealRecommendationResponse(MealRecommendationCreate):
    recommendation_id: int
    plan_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MealPlanCreate(BaseModel):
    user_id: int
    plan_name: str
    goal: str  # weight_loss, muscle_gain, maintenance
    duration_days: int = 30


class MealPlanResponse(MealPlanCreate):
    plan_id: int
    daily_calories: float
    daily_protein: float
    daily_carbs: float
    daily_fat: float
    is_active: int
    created_at: datetime
    meal_recommendations: List[MealRecommendationResponse] = []

    class Config:
        from_attributes = True


class DailyMealPlanResponse(BaseModel):
    daily_id: int
    plan_id: int
    date: datetime
    actual_calories: float
    actual_protein: float
    actual_carbs: float
    actual_fat: float
    adherence_percentage: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True
