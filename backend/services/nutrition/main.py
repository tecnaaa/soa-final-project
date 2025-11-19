"""
Nutrition/Meal Planner Service
Handles meal plan creation and recommendations based on user goals.
Integrates with Calorie Service for food/recipe data.
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import logging
import httpx

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_
from dotenv import load_dotenv
from jose import jwt, JWTError

# Add backend to path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from models.nutrition.nutrition_models import (
    MealPlan, MealRecommendation, DailyMealPlan,
    MealPlanCreate, MealPlanResponse,
    MealRecommendationCreate, MealRecommendationResponse,
    DailyMealPlanResponse
)
from db.db import get_db, init_db, Base
from services.logging_utils import setup_logging
from services.error_tracking import init_error_tracking, capture_error

# Setup
setup_logging(service_name="nutrition_service")
logger = logging.getLogger(__name__)
init_error_tracking("nutrition_service")

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
# Payment Service URL (Để check subscription)
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8007")

app = FastAPI(title="Nutrition/Meal Planner Service")

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Nutrition service database initialized")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Calorie Service URL
CALORIE_SERVICE_URL = os.getenv("CALORIE_SERVICE_URL", "http://localhost:8005")

# --- Helper Functions ---
async def check_user_subscription(user_id: int) -> dict:
    """Check user's subscription level from Payment Service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYMENT_SERVICE_URL}/subscriptions/user/{user_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return {"plan_type": "free", "is_active": False}
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        return {"plan_type": "free", "is_active": False}

def get_current_user_role(request: Request) -> int:
    """Lấy Role ID từ token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return 1 
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role", 1)
    except Exception:
        return 1

def check_pt_permission(request: Request):
    """Dependency kiểm tra quyền PT/Admin"""
    role_id = get_current_user_role(request)
    if role_id not in [2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Chỉ Huấn luyện viên (PT) hoặc Admin mới có quyền thực hiện thao tác này."
        )
    return True

async def get_food_from_calorie_service(food_id: int) -> dict:
    """Get food details from Calorie Service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CALORIE_SERVICE_URL}/foods/{food_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Error fetching food from Calorie Service: {str(e)}")
        return None


async def get_recipe_from_calorie_service(recipe_id: int) -> dict:
    """Get recipe details from Calorie Service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CALORIE_SERVICE_URL}/recipes/{recipe_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Error fetching recipe from Calorie Service: {str(e)}")
        return None


def calculate_macro_targets(goal: str, total_calories: float) -> dict:
    """Calculate macro targets based on goal"""
    targets = {
        "weight_loss": {
            "protein_percentage": 0.35,
            "carbs_percentage": 0.40,
            "fat_percentage": 0.25
        },
        "muscle_gain": {
            "protein_percentage": 0.35,
            "carbs_percentage": 0.50,
            "fat_percentage": 0.15
        },
        "maintenance": {
            "protein_percentage": 0.30,
            "carbs_percentage": 0.45,
            "fat_percentage": 0.25
        }
    }
    
    distribution = targets.get(goal, targets["maintenance"])
    
    return {
        "protein": (total_calories * distribution["protein_percentage"]) / 4,
        "carbs": (total_calories * distribution["carbs_percentage"]) / 4,
        "fat": (total_calories * distribution["fat_percentage"]) / 9
    }


def get_recommended_calories(goal: str, user_id: int) -> float:
    """Get recommended daily calories based on goal"""
    defaults = {
        "weight_loss": 1800,
        "muscle_gain": 2500,
        "maintenance": 2000
    }
    return defaults.get(goal, 2000)


# --- API Endpoints ---

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "nutrition", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {e}"
        )


@app.post("/meal-plans/", response_model=MealPlanResponse)
async def create_meal_plan(
    plan: MealPlanCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission) # LOGIC MỚI: Chặn user thường
):
    """Create a new meal plan for user (PT/Admin Only)"""
    try:
        # Calculate macro targets based on goal
        recommended_calories = get_recommended_calories(plan.goal, plan.user_id)
        macro_targets = calculate_macro_targets(plan.goal, recommended_calories)
        
        # Create meal plan
        db_plan = MealPlan(
            user_id=plan.user_id,
            plan_name=plan.plan_name,
            goal=plan.goal,
            daily_calories=recommended_calories,
            daily_protein=macro_targets["protein"],
            daily_carbs=macro_targets["carbs"],
            daily_fat=macro_targets["fat"],
            duration_days=plan.duration_days,
            is_active=1
            # is_default=True (nếu là admin tạo template) - có thể mở rộng sau
        )
        
        db.add(db_plan)
        await db.commit()
        await db.refresh(db_plan)
        
        logger.info(f"Created meal plan {db_plan.plan_id} for user {plan.user_id}")
        return db_plan
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating meal plan: {str(e)}")
        capture_error(e, {"user_id": plan.user_id, "goal": plan.goal})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating meal plan"
        )


@app.get("/meal-plans/user/{user_id}", response_model=List[MealPlanResponse])
async def get_user_meal_plans(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all meal plans for user (Filtered by Subscription)"""
    try:
        # LOGIC MỚI: Kiểm tra subscription
        subscription = await check_user_subscription(user_id)
        plan_type = subscription.get("plan_type", "free")
        is_active_sub = subscription.get("is_active", False)
        
        if plan_type == "free" or not is_active_sub:
            # Free: Chỉ trả về plan mặc định
            logger.info(f"User {user_id} is Free. Returning default meal plans.")
            query = select(MealPlan).where(MealPlan.is_default == True)
        else:
            # Premium: Trả về plan riêng + mặc định
            logger.info(f"User {user_id} is Premium. Returning custom + default meal plans.")
            query = select(MealPlan).where(
                or_(
                    MealPlan.user_id == user_id,
                    MealPlan.is_default == True
                )
            )
            
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching meal plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching meal plans"
        )

@app.get("/meal-plans/{plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific meal plan with recommendations"""
    try:
        result = await db.execute(
            select(MealPlan).where(MealPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching meal plan"
        )


@app.post("/meal-plans/{plan_id}/recommendations/", response_model=MealRecommendationResponse)
async def add_meal_recommendation(
    plan_id: int,
    recommendation: MealRecommendationCreate,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """Add meal recommendation to plan"""
    try:
        # Verify plan exists
        result = await db.execute(
            select(MealPlan).where(MealPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        # Fetch nutrition info from Calorie Service if not provided
        estimated_calories = recommendation.estimated_calories
        estimated_protein = recommendation.estimated_protein
        estimated_carbs = recommendation.estimated_carbs
        estimated_fat = recommendation.estimated_fat
        
        if estimated_calories is None and recommendation.food_id:
            # Get food from Calorie Service
            food_data = await get_food_from_calorie_service(recommendation.food_id)
            if food_data:
                estimated_calories = food_data.get("calories_per_100g", 0) * recommendation.quantity_grams / 100
                estimated_protein = food_data.get("protein", 0) * recommendation.quantity_grams / 100
                estimated_carbs = food_data.get("carbs", 0) * recommendation.quantity_grams / 100
                estimated_fat = food_data.get("fat", 0) * recommendation.quantity_grams / 100
        
        elif estimated_calories is None and recommendation.recipe_id:
            # Get recipe from Calorie Service
            recipe_data = await get_recipe_from_calorie_service(recommendation.recipe_id)
            if recipe_data:
                estimated_calories = recipe_data.get("total_calories", 0)
                estimated_protein = recipe_data.get("total_protein", 0)
                estimated_carbs = recipe_data.get("total_carbs", 0)
                estimated_fat = recipe_data.get("total_fat", 0)
        
        # Create recommendation
        db_recommendation = MealRecommendation(
            plan_id=plan_id,
            meal_type=recommendation.meal_type,
            day_of_week=recommendation.day_of_week,
            food_id=recommendation.food_id,
            recipe_id=recommendation.recipe_id,
            quantity_grams=recommendation.quantity_grams,
            estimated_calories=estimated_calories,
            estimated_protein=estimated_protein,
            estimated_carbs=estimated_carbs,
            estimated_fat=estimated_fat,
            notes=recommendation.notes
        )
        
        db.add(db_recommendation)
        await db.commit()
        await db.refresh(db_recommendation)
        
        logger.info(f"Added recommendation {db_recommendation.recommendation_id} to plan {plan_id}")
        return db_recommendation
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding recommendation: {str(e)}")
        capture_error(e, {"plan_id": plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding recommendation"
        )


@app.get("/meal-plans/{plan_id}/recommendations/", response_model=List[MealRecommendationResponse])
async def get_meal_recommendations(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all recommendations for a meal plan"""
    try:
        result = await db.execute(
            select(MealRecommendation).where(
                MealRecommendation.plan_id == plan_id
            )
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching recommendations"
        )


@app.post("/meal-plans/{plan_id}/daily-tracking/", response_model=DailyMealPlanResponse)
async def track_daily_meals(
    plan_id: int,
    daily_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Track actual daily meals consumed"""
    try:
        result = await db.execute(
            select(MealPlan).where(MealPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        # Create daily tracking
        db_daily = DailyMealPlan(
            plan_id=plan_id,
            date=daily_data.get("date", datetime.now()),
            actual_calories=daily_data.get("actual_calories", 0),
            actual_protein=daily_data.get("actual_protein", 0),
            actual_carbs=daily_data.get("actual_carbs", 0),
            actual_fat=daily_data.get("actual_fat", 0),
            notes=daily_data.get("notes")
        )
        
        # Calculate adherence
        if plan.daily_calories > 0:
            adherence = (db_daily.actual_calories / plan.daily_calories) * 100
            db_daily.adherence_percentage = min(adherence, 150)
        
        db.add(db_daily)
        await db.commit()
        await db.refresh(db_daily)
        
        logger.info(f"Tracked daily meals for plan {plan_id}")
        return db_daily
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error tracking daily meals: {str(e)}")
        capture_error(e, {"plan_id": plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error tracking daily meals"
        )


@app.get("/meal-plans/{plan_id}/daily-tracking/", response_model=List[DailyMealPlanResponse])
async def get_daily_tracking(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get daily tracking history for meal plan"""
    try:
        result = await db.execute(
            select(DailyMealPlan).where(
                DailyMealPlan.plan_id == plan_id
            ).order_by(DailyMealPlan.date.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching daily tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching daily tracking"
        )


@app.put("/meal-plans/{plan_id}/deactivate")
async def deactivate_meal_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a meal plan"""
    try:
        result = await db.execute(
            select(MealPlan).where(MealPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        plan.is_active = 0
        await db.commit()
        
        logger.info(f"Deactivated meal plan {plan_id}")
        return {"message": "Meal plan deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deactivating meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating meal plan"
        )


@app.delete("/meal-plans/{plan_id}")
async def delete_meal_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a meal plan"""
    try:
        result = await db.execute(
            select(MealPlan).where(MealPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        await db.delete(plan)
        await db.commit()
        
        logger.info(f"Deleted meal plan {plan_id}")
        return {"message": "Meal plan deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting meal plan"
        )


@app.post("/meal-plans/{plan_id}/daily-meals/", response_model=dict)
async def add_daily_meal(
    plan_id: int,
    daily_meal_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)  # ✅ CHỈ PT/ADMIN MỚI ĐƯỢC
):
    """
    Thêm bữa ăn hàng ngày vào meal plan
    
    Only PT/Admin can add meals to plans.
    Free users CANNOT create/add meals.
    
    Parameters:
    - plan_id: ID của meal plan
    - daily_meal_data: {
        "meal_type": "breakfast|lunch|dinner|snack",
        "meal_time": "07:00:00",
        "ingredients": [
            {"food_name": "Trứng luộc", "quantity": "2 quả"},
            {"food_name": "Bánh mì", "quantity": "1 lát"}
        ]
      }
    """
    try:
        # Kiểm tra meal plan tồn tại
        result = await db.execute(
            select(MealPlan).where(MealPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        # Lấy role từ token
        role_id = get_current_user_role(request)
        logger.info(f"User (role={role_id}) adding daily meal to plan {plan_id}")
        
        # Tạo daily meal record
        from models.nutrition.nutrition_models import DailyMeal  # Nếu model này tồn tại
        
        db_daily_meal = DailyMeal(
            meal_plan_id=plan_id,
            meal_type=daily_meal_data.get("meal_type"),
            meal_time=daily_meal_data.get("meal_time")
        )
        
        db.add(db_daily_meal)
        await db.flush()
        
        # Thêm ingredients
        ingredients_list = daily_meal_data.get("ingredients", [])
        for ingredient_data in ingredients_list:
            from models.nutrition.nutrition_models import Ingredient
            
            ingredient = Ingredient(
                daily_meal_id=db_daily_meal.daily_meal_id,
                food_name=ingredient_data.get("food_name"),
                quantity=ingredient_data.get("quantity"),
                calories=ingredient_data.get("calories")
            )
            db.add(ingredient)
        
        await db.commit()
        logger.info(f"✅ Added daily meal {db_daily_meal.daily_meal_id} by PT/Admin (role={role_id})")
        
        return {
            "status": "success",
            "message": "Daily meal added successfully",
            "daily_meal_id": db_daily_meal.daily_meal_id,
            "meal_type": db_daily_meal.meal_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error adding daily meal: {str(e)}")
        capture_error(e, {"plan_id": plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding daily meal"
        )


@app.delete("/daily-meals/{daily_meal_id}")
async def delete_daily_meal(
    daily_meal_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)  # ✅ CHỈ PT/ADMIN MỚI ĐƯỢC
):
    """
    Xóa bữa ăn hàng ngày
    Only PT/Admin can delete meals.
    """
    try:
        from models.nutrition.nutrition_models import DailyMeal
        
        result = await db.execute(
            select(DailyMeal).where(DailyMeal.daily_meal_id == daily_meal_id)
        )
        daily_meal = result.scalars().first()
        
        if not daily_meal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily meal not found"
            )
        
        role_id = get_current_user_role(request)
        logger.info(f"User (role={role_id}) deleting daily meal {daily_meal_id}")
        
        await db.delete(daily_meal)
        await db.commit()
        
        logger.info(f"✅ Deleted daily meal {daily_meal_id} by PT/Admin (role={role_id})")
        return {"message": "Daily meal deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting daily meal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting daily meal"
        )


@app.put("/daily-meals/{daily_meal_id}")
async def update_daily_meal(
    daily_meal_id: int,
    meal_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)  # ✅ CHỈ PT/ADMIN MỚI ĐƯỢC
):
    """
    Cập nhật bữa ăn hàng ngày
    Only PT/Admin can update meals.
    """
    try:
        from models.nutrition.nutrition_models import DailyMeal
        
        result = await db.execute(
            select(DailyMeal).where(DailyMeal.daily_meal_id == daily_meal_id)
        )
        daily_meal = result.scalars().first()
        
        if not daily_meal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily meal not found"
            )
        
        role_id = get_current_user_role(request)
        logger.info(f"User (role={role_id}) updating daily meal {daily_meal_id}")
        
        # Cập nhật fields
        if "meal_time" in meal_data:
            daily_meal.meal_time = meal_data["meal_time"]
        
        await db.commit()
        logger.info(f"✅ Updated daily meal {daily_meal_id} by PT/Admin (role={role_id})")
        
        return {
            "status": "success",
            "message": "Daily meal updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating daily meal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating daily meal"
        )


# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Nutrition/Meal Planner Service...")
    uvicorn.run(app, host="0.0.0.0", port=8004)
