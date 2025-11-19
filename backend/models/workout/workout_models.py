"""
SQLAlchemy models for the Workout service.
"""

# --- 1. Imports ---

# Standard Library
import sys
from pathlib import Path
from datetime import datetime

# Third-Party Imports
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Numeric, TIMESTAMP, Date, Text,
    Enum as SQLEnum, Float, Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, List
from pydantic import BaseModel

# --- 2. Path Setup (for local imports) ---

# Add the backend directory to the Python path for imports
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if (backend_dir not in sys.path):
    sys.path.append(backend_dir)

# --- 3. Local Application Imports ---

try:
    from db.db import Base
except ImportError:
    print(f"Error: Could not import 'Base' from db.db. Searched in: {backend_dir}")
    sys.exit(1)

# --- 4. Model Definitions ---

class Equipment(Base):
    """SQLAlchemy model for exercise equipment"""
    __tablename__ = 'equipment'
    
    equipment_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

# Simple Exercise model for workout plans
class Exercise(Base):
    """SQLAlchemy model for exercises in workout plans"""
    __tablename__ = 'exercises'
    
    exercise_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('workout_plans.plan_id'), nullable=False)
    day_of_week = Column(String(20), nullable=False)  # monday, tuesday, etc.
    exercise_name = Column(String(150), nullable=False)
    sets = Column(Integer)
    reps = Column(String(50))  # e.g., "8-12", "10 minutes"
    weight_kg = Column(Numeric(5, 2), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    plan = relationship("WorkoutPlan", back_populates="exercises")

class ExerciseSecondaryMuscle(Base):
    """Association table for exercises and their secondary muscle groups"""
    __tablename__ = 'exercise_secondary_muscles'
    
    exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'), primary_key=True)
    muscle_group_id = Column(Integer, ForeignKey('muscle_groups.muscle_group_id'), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class ExerciseEquipment(Base):
    """Association table for exercises and their required equipment"""
    __tablename__ = 'exercise_equipment'
    
    exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'), primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id'), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class ExerciseVariation(Base):
    """Model for exercise variations (easier/harder alternatives)"""
    __tablename__ = 'exercise_variations'
    
    variation_id = Column(Integer, primary_key=True)
    parent_exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'))
    variant_exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'))
    variation_type = Column(SQLEnum('easier', 'harder', 'alternative', name='variation_type'))
    created_at = Column(TIMESTAMP, server_default=func.now())

class WorkoutPlan(Base):
    """Enhanced SQLAlchemy model for workout plans"""
    __tablename__ = 'workout_plans'
    
    plan_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users_db.users.user_id"))
    plan_name = Column(String(200), nullable=False)
    is_default = Column(Boolean, default=False)
    goal = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    created_by_pt_id = Column(Integer, ForeignKey("users_db.users.user_id"), nullable=True)  # PT who created this plan
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    exercises = relationship("Exercise", back_populates="plan", cascade="all, delete-orphan")

class WorkoutSession(Base):
    """Enhanced SQLAlchemy model for workout sessions"""
    __tablename__ = 'workout_sessions'
    
    session_id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey('workout_plans.plan_id'))
    day_of_week = Column(Integer, nullable=False)  # 1-7 for Monday-Sunday
    name = Column(String(100), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    calories_target = Column(Float)
    difficulty = Column(SQLEnum('beginner', 'intermediate', 'advanced', name='session_difficulty'))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    plan = relationship("WorkoutPlan", back_populates="sessions")
    exercises = relationship("SessionExercise", back_populates="session", cascade="all, delete-orphan")
    progress = relationship("WorkoutProgress", back_populates="session")

class SessionExercise(Base):
    """Enhanced SQLAlchemy model for exercises in a session"""
    __tablename__ = 'session_exercises'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('workout_sessions.session_id'))
    exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'))
    sets = Column(Integer)
    reps = Column(String(50))  # e.g., "8-12", "AMRAP", "30 seconds"
    duration_minutes = Column(Integer)
    rest_seconds = Column(Integer)
    weight_guidance = Column(String(100))  # e.g., "70% 1RM", "Bodyweight"
    order_in_session = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    session = relationship("WorkoutSession", back_populates="exercises")
    exercise = relationship("Exercise")

class WorkoutProgress(Base):
    """Enhanced SQLAlchemy model for tracking workout completion"""
    __tablename__ = 'workout_progress'
    
    progress_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users_db.users.user_id"))
    session_id = Column(Integer, ForeignKey('workout_sessions.session_id'))
    completed_at = Column(TIMESTAMP, server_default=func.now())
    duration_minutes = Column(Integer)
    calories_burned = Column(Float)
    difficulty_rating = Column(Integer)  # 1-10 scale
    energy_level = Column(Integer)  # 1-10 scale
    mood = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    session = relationship("WorkoutSession", back_populates="progress")
    exercise_progress = relationship("ExerciseProgress", back_populates="workout", cascade="all, delete-orphan")

class ExerciseProgress(Base):
    """SQLAlchemy model for tracking individual exercise progress"""
    __tablename__ = 'exercise_progress'
    
    progress_id = Column(Integer, primary_key=True)
    workout_progress_id = Column(Integer, ForeignKey('workout_progress.progress_id'))
    exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'))
    sets_completed = Column(Integer)
    reps_completed = Column(String(255))  # e.g., "12,10,8"
    weight_used = Column(String(255))  # e.g., "20,20,17.5"
    duration_minutes = Column(Integer)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    workout = relationship("WorkoutProgress", back_populates="exercise_progress")
    exercise = relationship("Exercise")

# --- 5. Pydantic Models ---

class ExerciseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExerciseCategoryResponse(ExerciseCategoryBase):
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MuscleGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class MuscleGroupResponse(MuscleGroupBase):
    muscle_group_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class EquipmentBase(BaseModel):
    name: str
    description: Optional[str] = None

class EquipmentResponse(EquipmentBase):
    equipment_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    primary_muscle_group_id: int
    difficulty: str
    equipment_needed: Optional[str] = None
    calories_per_hour: Optional[float] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    instructions: Optional[str] = None
    tips: Optional[str] = None
    contraindications: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    secondary_muscle_ids: Optional[List[int]] = None
    equipment_ids: Optional[List[int]] = None

class ExerciseResponse(ExerciseBase):
    exercise_id: int
    created_at: datetime
    category: ExerciseCategoryResponse
    primary_muscle: MuscleGroupResponse
    secondary_muscles: List[MuscleGroupResponse]
    equipment: List[EquipmentResponse]

    class Config:
        from_attributes = True

class ExerciseVariationBase(BaseModel):
    parent_exercise_id: int
    variant_exercise_id: int
    variation_type: str

class ExerciseVariationResponse(ExerciseVariationBase):
    variation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SessionExerciseBase(BaseModel):
    exercise_id: int
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration_minutes: Optional[int] = None
    rest_seconds: Optional[int] = None
    weight_guidance: Optional[str] = None
    order_in_session: int
    notes: Optional[str] = None

class SessionExerciseResponse(SessionExerciseBase):
    id: int
    created_at: datetime
    exercise: ExerciseResponse

    class Config:
        from_attributes = True

class WorkoutSessionBase(BaseModel):
    name: str
    description: Optional[str] = None
    day_of_week: int
    duration_minutes: Optional[int] = None
    calories_target: Optional[float] = None
    difficulty: str
    exercises: List[SessionExerciseBase]

class WorkoutSessionResponse(WorkoutSessionBase):
    session_id: int
    plan_id: int
    created_at: datetime
    exercises: List[SessionExerciseResponse]

    class Config:
        from_attributes = True

class WorkoutPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    goal: str
    difficulty: str
    duration_weeks: int
    sessions_per_week: int
    equipment_required: Optional[str] = None
    calories_per_session: Optional[float] = None

class WorkoutPlanCreate(WorkoutPlanBase):
    user_id: int
    sessions: List[WorkoutSessionBase]

class WorkoutPlanResponse(WorkoutPlanBase):
    plan_id: int
    created_at: datetime
    updated_at: datetime
    sessions: List[WorkoutSessionResponse]

    class Config:
        from_attributes = True

class ExerciseProgressBase(BaseModel):
    exercise_id: int
    sets_completed: Optional[int] = None
    reps_completed: Optional[str] = None
    weight_used: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None

class ExerciseProgressResponse(ExerciseProgressBase):
    progress_id: int
    created_at: datetime
    exercise: ExerciseResponse

    class Config:
        from_attributes = True

class WorkoutProgressBase(BaseModel):
    user_id: int
    session_id: int
    duration_minutes: Optional[int] = None
    calories_burned: Optional[float] = None
    difficulty_rating: Optional[int] = None
    energy_level: Optional[int] = None
    mood: Optional[str] = None
    notes: Optional[str] = None
    exercise_progress: List[ExerciseProgressBase]

class WorkoutProgressResponse(WorkoutProgressBase):
    progress_id: int
    completed_at: datetime
    exercise_progress: List[ExerciseProgressResponse]

    class Config:
        from_attributes = True
