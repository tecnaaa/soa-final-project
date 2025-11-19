"""
Workout Plan Service

Handles creation and management of exercises, workout plans, and progress tracking.
Integrates with Payment Service to check user subscription level.
"""

# --- 1. Imports ---
import logging
import sys
import os
import httpx
from typing import List, Optional, AsyncGenerator
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, text, select, or_
from dotenv import load_dotenv
from services.logging_utils import setup_logging
from services.error_tracking import init_error_tracking, capture_error
from jose import jwt, JWTError

# --- 2. Path Setup & Local Imports ---
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from db.db import get_db, init_db, Base
    from models.workout.workout_models import (
        # Main Models
        WorkoutPlan, WorkoutSession, SessionExercise, Exercise,
        WorkoutProgress, ExerciseProgress,
        # Pydantic Models
        WorkoutPlanBase, WorkoutPlanCreate, WorkoutPlanResponse,
        WorkoutSessionBase, WorkoutSessionResponse,
        SessionExerciseBase, SessionExerciseResponse,
        WorkoutProgressBase, WorkoutProgressResponse,
        ExerciseProgressBase, ExerciseProgressResponse
    )
except ImportError as e:
    logging.critical(f"Import Error: {e}. Check paths and module names.")
    sys.exit(1)

# --- 3. Logging Setup ---
setup_logging("workout_service")
logger = logging.getLogger(__name__)
init_error_tracking("workout_service")
load_dotenv()

# --- 4. FastAPI Application Setup ---
app = FastAPI(
    title="Workout Service",
    description="Service for managing exercises, workout plans, and progress tracking",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Workout service database initialized")

# Payment Service URL
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

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
            # Default to free tier if not found
            return {"plan_type": "free", "is_active": False}
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        return {"plan_type": "free", "is_active": False}


def check_subscription_for_feature(subscription: dict, feature: str) -> bool:
    """
    Check if user's subscription allows access to feature
    feature: 'advanced_plans', 'personalization', 'pt_customization'
    """
    plan_type = subscription.get("plan_type", "free")
    is_active = subscription.get("is_active", False)
    
    if not is_active:
        # Free tier logic fallback
        if plan_type == "free":
            return False
        return False
    
    feature_access = {
        "advanced_plans": {"free": False, "premium": True, "coaching": True},
        "personalization": {"free": False, "premium": True, "coaching": True},
        "pt_customization": {"free": False, "premium": False, "coaching": True},
        "basic": {"free": True, "premium": True, "coaching": True}
    }
    
    return feature_access.get(feature, {}).get(plan_type, False)

def get_current_user_role(request: Request) -> int:
    """Lấy Role ID từ token trong header Authorization"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # Nếu không có header, giả sử là user thường (role_id=1) hoặc guest
        return 1 
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        # Giả sử payload có chứa 'role' (role_id)
        return payload.get("role", 1)
    except Exception:
        return 1

def check_pt_permission(request: Request):
    """
    Dependency để kiểm tra quyền PT hoặc Admin.
    Chặn nếu user thường cố tình tạo nội dung.
    """
    role_id = get_current_user_role(request)
    # Giả sử: 1=User, 2=PT, 3=Admin
    if role_id not in [2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Chỉ Huấn luyện viên (PT) hoặc Admin mới có quyền thực hiện thao tác này."
        )
    return True


# --- 5. API Endpoints ---

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "workout", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {e}"
        )

# Workout Plan Endpoints
@app.post("/workout-plans/", response_model=WorkoutPlanResponse)
async def create_workout_plan(
    plan: WorkoutPlanCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """Create a new workout plan (Only PT/Admin)"""
    try:
        plan_data = plan.dict(exclude={'sessions'})
        db_plan = WorkoutPlan(**plan_data)
        db.add(db_plan)
        await db.flush()
        
        # Create sessions and exercises
        for session_data in plan.sessions:
            session = WorkoutSession(
                plan_id=db_plan.plan_id,
                **session_data.dict(exclude={'exercises'})
            )
            db.add(session)
            await db.flush()
            
            # Add exercises to session
            for ex_data in session_data.exercises:
                session_exercise = SessionExercise(
                    session_id=session.session_id,
                    **ex_data.dict()
                )
                db.add(session_exercise)
        
        await db.commit()
        await db.refresh(db_plan)
        
        logger.info(f"Created workout plan {db_plan.plan_id} by PT/Admin for user {plan.user_id}")
        return db_plan
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating workout plan: {str(e)}")
        capture_error(e, {"user_id": plan.user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating workout plan"
        )

@app.get("/workout-plans/{plan_id}", response_model=WorkoutPlanResponse)
async def get_workout_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkoutPlan).where(WorkoutPlan.plan_id == plan_id)
    )
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    return plan

@app.get("/workout-plans/user/{user_id}", response_model=List[WorkoutPlanResponse])
async def get_user_workout_plans(
    user_id: int,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get user's workout plans (filtered by subscription)"""
    subscription = await check_user_subscription(user_id)
    plan_type = subscription.get("plan_type", "free")
    is_active_sub = subscription.get("is_active", False)

    if plan_type == "free" or not is_active_sub:
        logger.info(f"User {user_id} is Free. Returning default plans.")
        query = select(WorkoutPlan).where(WorkoutPlan.is_default == True)
    else:
        logger.info(f"User {user_id} is Premium. Returning custom + default plans.")
        query = select(WorkoutPlan).where(
            or_(
                WorkoutPlan.user_id == user_id,
                WorkoutPlan.is_default == True
            )
        )
        
    result = await db.execute(query)
    return result.scalars().all()

@app.put("/workout-plans/{plan_id}", response_model=WorkoutPlanResponse)
async def update_workout_plan(
    plan_id: int,
    updated_plan: WorkoutPlanCreate,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """Update existing workout plan (PT/Admin Only)"""
    try:
        result = await db.execute(
            select(WorkoutPlan).where(WorkoutPlan.plan_id == plan_id)
        )
        db_plan = result.scalars().first()
        
        if not db_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout plan not found"
            )
        
        db_plan.plan_name = updated_plan.plan_name
        db_plan.goal = updated_plan.goal
        
        await db.commit()
        await db.refresh(db_plan)
        
        logger.info(f"Updated workout plan {plan_id}")
        return db_plan
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating workout plan: {str(e)}")
        capture_error(e, {"plan_id": plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating workout plan"
        )

@app.delete("/workout-plans/{plan_id}")
async def delete_workout_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """Delete a workout plan (PT/Admin Only)"""
    try:
        result = await db.execute(
            select(WorkoutPlan).where(WorkoutPlan.plan_id == plan_id)
        )
        db_plan = result.scalars().first()
        
        if not db_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout plan not found"
            )
        
        await db.delete(db_plan)
        await db.commit()
        
        logger.info(f"Deleted workout plan {plan_id}")
        return {"message": "Workout plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting workout plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting workout plan"
        )

# Exercise Endpoints
@app.post("/workout-plans/{plan_id}/exercises/", response_model=dict)
async def add_exercise_to_plan(
    plan_id: int,
    exercise_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """
    Thêm bài tập vào workout plan
    
    Only PT/Admin can add exercises to plans.
    Free users CANNOT create/add exercises.
    
    Parameters:
    - plan_id: ID của workout plan
    - exercise_data: {
        "day_of_week": "monday|tuesday|...",
        "exercise_name": "Squat",
        "sets": 3,
        "reps": "8-12",
        "weight_kg": 50.0
      }
    """
    try:
        result = await db.execute(
            select(WorkoutPlan).where(WorkoutPlan.plan_id == plan_id)
        )
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout plan not found"
            )
        
        role_id = get_current_user_role(request)
        logger.info(f"User (role={role_id}) adding exercise to plan {plan_id}")
        
        db_exercise = Exercise(
            plan_id=plan_id,
            day_of_week=exercise_data.get("day_of_week"),
            exercise_name=exercise_data.get("exercise_name"),
            sets=exercise_data.get("sets"),
            reps=exercise_data.get("reps"),
            weight_kg=exercise_data.get("weight_kg")
        )
        
        db.add(db_exercise)
        await db.commit()
        await db.refresh(db_exercise)
        
        logger.info(f"✅ Added exercise {db_exercise.exercise_id} to plan {plan_id} by PT/Admin (role={role_id})")
        
        return {
            "status": "success",
            "message": "Exercise added successfully",
            "exercise_id": db_exercise.exercise_id,
            "exercise_name": db_exercise.exercise_name,
            "day_of_week": db_exercise.day_of_week
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error adding exercise: {str(e)}")
        capture_error(e, {"plan_id": plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding exercise"
        )

@app.delete("/exercises/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """
    Xóa bài tập khỏi workout plan
    Only PT/Admin can delete exercises.
    """
    try:
        result = await db.execute(
            select(Exercise).where(Exercise.exercise_id == exercise_id)
        )
        exercise = result.scalars().first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        role_id = get_current_user_role(request)
        logger.info(f"User (role={role_id}) deleting exercise {exercise_id}")
        
        await db.delete(exercise)
        await db.commit()
        
        logger.info(f"✅ Deleted exercise {exercise_id} by PT/Admin (role={role_id})")
        return {"message": "Exercise deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting exercise: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting exercise"
        )

@app.put("/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: int,
    exercise_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _permission: bool = Depends(check_pt_permission)
):
    """
    Cập nhật bài tập trong workout plan
    Only PT/Admin can update exercises.
    """
    try:
        result = await db.execute(
            select(Exercise).where(Exercise.exercise_id == exercise_id)
        )
        exercise = result.scalars().first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        role_id = get_current_user_role(request)
        logger.info(f"User (role={role_id}) updating exercise {exercise_id}")
        
        updatable_fields = ['sets', 'reps', 'weight_kg', 'exercise_name']
        for field in updatable_fields:
            if field in exercise_data:
                setattr(exercise, field, exercise_data[field])
        
        await db.commit()
        await db.refresh(exercise)
        
        logger.info(f"✅ Updated exercise {exercise_id} by PT/Admin (role={role_id})")
        
        return {
            "status": "success",
            "message": "Exercise updated successfully",
            "exercise": {
                "exercise_id": exercise.exercise_id,
                "exercise_name": exercise.exercise_name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight_kg": exercise.weight_kg
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating exercise: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating exercise"
        )

@app.get("/workout-plans/{plan_id}/exercises/", response_model=List[dict])
async def get_plan_exercises(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách exercises trong workout plan
    Can be accessed by anyone (for viewing)
    """
    try:
        result = await db.execute(
            select(Exercise).where(Exercise.plan_id == plan_id)
        )
        exercises = result.scalars().all()
        
        return [
            {
                "exercise_id": ex.exercise_id,
                "exercise_name": ex.exercise_name,
                "day_of_week": ex.day_of_week,
                "sets": ex.sets,
                "reps": ex.reps,
                "weight_kg": ex.weight_kg
            }
            for ex in exercises
        ]
    except Exception as e:
        logger.error(f"Error fetching exercises: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching exercises"
        )

# Progress Tracking Endpoints
@app.post("/progress/", response_model=WorkoutProgressResponse)
async def record_workout_progress(
    progress: WorkoutProgressBase,
    db: AsyncSession = Depends(get_db)
):
    """Record workout progress (Allowed for all users)"""
    try:
        progress_data = progress.dict(exclude={'exercise_progress'})
        db_progress = WorkoutProgress(**progress_data)
        db.add(db_progress)
        await db.flush()
        
        for ex_progress in progress.exercise_progress:
            db_ex_progress = ExerciseProgress(
                workout_progress_id=db_progress.progress_id,
                **ex_progress.dict()
            )
            db.add(db_ex_progress)
        
        await db.commit()
        await db.refresh(db_progress)
        
        logger.info(f"Recorded progress for user {progress.user_id}")
        return db_progress
    except Exception as e:
        await db.rollback()
        logger.error(f"Error recording progress: {str(e)}")
        capture_error(e, {"user_id": progress.user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording progress"
        )

@app.get("/progress/user/{user_id}", response_model=List[WorkoutProgressResponse])
async def get_user_progress(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get user's workout progress history"""
    try:
        query = select(WorkoutProgress).where(WorkoutProgress.user_id == user_id)
        
        if start_date and end_date:
            query = query.where(and_(
                WorkoutProgress.completed_at >= start_date,
                WorkoutProgress.completed_at <= end_date
            ))
        
        result = await db.execute(query.order_by(WorkoutProgress.completed_at.desc()))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching progress"
        )

@app.get("/progress/session/{session_id}", response_model=List[WorkoutProgressResponse])
async def get_session_progress(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkoutProgress).where(
            WorkoutProgress.session_id == session_id
        ).order_by(WorkoutProgress.completed_at.desc())
    )
    return result.scalars().all()

@app.get("/progress/stats/user/{user_id}")
async def get_user_progress_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's progress statistics"""
    try:
        total_result = await db.execute(
            select(func.count(WorkoutProgress.progress_id)).where(
                WorkoutProgress.user_id == user_id
            )
        )
        total_workouts = total_result.scalar() or 0
        
        avg_result = await db.execute(
            select(func.avg(WorkoutProgress.duration_minutes)).where(
                WorkoutProgress.user_id == user_id
            )
        )
        avg_duration = avg_result.scalar() or 0
        
        return {
            "user_id": user_id,
            "total_workouts": total_workouts,
            "average_duration_minutes": float(avg_duration),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating statistics"
        )

# --- 6. Main Entry Point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)