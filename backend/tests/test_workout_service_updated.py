"""
Unit tests for Workout Service (Updated with CRUD + Subscription Integration)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add backend directory to path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.workout.main import app, get_db
from db.db import Base
from models.workout.workout_models import WorkoutPlan, WorkoutProgress

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_workout.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def setup_teardown():
    """Fixture to setup and teardown test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestWorkoutPlanCRUD:
    """Test CRUD operations for workout plans"""
    
    @patch('services.workout.main.check_user_subscription')
    async def test_create_basic_workout_plan(self, mock_subscription, setup_teardown):
        """Test creating basic workout plan (free tier)"""
        mock_subscription.return_value = {"plan_type": "free", "is_active": True}
        
        response = client.post(
            "/workout-plans/",
            json={
                "user_id": 1,
                "plan_name": "Basic Plan",
                "goal": "weight_loss",
                "difficulty": "beginner",
                "is_personalized": False,
                "duration_weeks": 4,
                "sessions": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["difficulty"] == "beginner"
    
    @patch('services.workout.main.check_user_subscription')
    async def test_create_advanced_plan_without_premium(self, mock_subscription, setup_teardown):
        """Test that advanced plans require premium subscription"""
        mock_subscription.return_value = {"plan_type": "free", "is_active": True}
        
        response = client.post(
            "/workout-plans/",
            json={
                "user_id": 2,
                "plan_name": "Advanced Plan",
                "goal": "muscle_gain",
                "difficulty": "advanced",
                "is_personalized": False,
                "duration_weeks": 8,
                "sessions": []
            }
        )
        assert response.status_code == 403
        assert "Premium" in response.json()["detail"]
    
    @patch('services.workout.main.check_user_subscription')
    async def test_create_advanced_plan_with_premium(self, mock_subscription, setup_teardown):
        """Test that advanced plans work with premium subscription"""
        mock_subscription.return_value = {"plan_type": "premium", "is_active": True}
        
        response = client.post(
            "/workout-plans/",
            json={
                "user_id": 3,
                "plan_name": "Advanced Plan",
                "goal": "muscle_gain",
                "difficulty": "advanced",
                "is_personalized": False,
                "duration_weeks": 8,
                "sessions": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["difficulty"] == "advanced"
    
    @patch('services.workout.main.check_user_subscription')
    async def test_create_personalized_plan_without_premium(self, mock_subscription, setup_teardown):
        """Test that personalized plans require premium subscription"""
        mock_subscription.return_value = {"plan_type": "free", "is_active": True}
        
        response = client.post(
            "/workout-plans/",
            json={
                "user_id": 4,
                "plan_name": "Personalized Plan",
                "goal": "maintenance",
                "difficulty": "intermediate",
                "is_personalized": True,
                "duration_weeks": 6,
                "sessions": []
            }
        )
        assert response.status_code == 403
        assert "Personalized" in response.json()["detail"]
    
    @patch('services.workout.main.check_user_subscription')
    async def test_update_workout_plan(self, mock_subscription, setup_teardown):
        """Test updating workout plan"""
        mock_subscription.return_value = {"plan_type": "premium", "is_active": True}
        
        # Create plan
        create_response = client.post(
            "/workout-plans/",
            json={
                "user_id": 5,
                "plan_name": "Original Plan",
                "goal": "weight_loss",
                "difficulty": "beginner",
                "is_personalized": False,
                "duration_weeks": 4,
                "sessions": []
            }
        )
        plan_id = create_response.json()["plan_id"]
        
        # Update plan
        response = client.put(
            f"/workout-plans/{plan_id}",
            json={
                "user_id": 5,
                "plan_name": "Updated Plan",
                "goal": "muscle_gain",
                "difficulty": "intermediate",
                "is_personalized": True,
                "duration_weeks": 8,
                "sessions": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_name"] == "Updated Plan"
        assert data["goal"] == "muscle_gain"
    
    @patch('services.workout.main.check_user_subscription')
    async def test_delete_workout_plan(self, mock_subscription, setup_teardown):
        """Test deleting workout plan"""
        mock_subscription.return_value = {"plan_type": "premium", "is_active": True}
        
        # Create plan
        create_response = client.post(
            "/workout-plans/",
            json={
                "user_id": 6,
                "plan_name": "Plan to Delete",
                "goal": "weight_loss",
                "difficulty": "beginner",
                "is_personalized": False,
                "duration_weeks": 4,
                "sessions": []
            }
        )
        plan_id = create_response.json()["plan_id"]
        
        # Delete
        response = client.delete(f"/workout-plans/{plan_id}")
        assert response.status_code == 200
        
        # Verify deleted
        get_response = client.get(f"/workout-plans/{plan_id}")
        assert get_response.status_code == 404


class TestExerciseFiltering:
    """Test exercise listing with subscription-based filtering"""
    
    def test_list_exercises_basic(self, setup_teardown):
        """Test listing basic exercises"""
        response = client.get("/exercises/")
        assert response.status_code == 200
    
    @patch('services.workout.main.check_user_subscription')
    async def test_list_exercises_free_user(self, mock_subscription, setup_teardown):
        """Test that free users only see basic/intermediate exercises"""
        mock_subscription.return_value = {"plan_type": "free", "is_active": True}
        
        response = client.get("/exercises/?user_id=1")
        assert response.status_code == 200
        # Free tier should not include advanced
    
    @patch('services.workout.main.check_user_subscription')
    async def test_list_advanced_exercises_blocked_for_free(self, mock_subscription, setup_teardown):
        """Test that free users cannot filter by advanced difficulty"""
        mock_subscription.return_value = {"plan_type": "free", "is_active": True}
        
        response = client.get("/exercises/?user_id=2&difficulty=advanced")
        assert response.status_code == 403
    
    @patch('services.workout.main.check_user_subscription')
    async def test_list_advanced_exercises_allowed_for_premium(self, mock_subscription, setup_teardown):
        """Test that premium users can access advanced exercises"""
        mock_subscription.return_value = {"plan_type": "premium", "is_active": True}
        
        response = client.get("/exercises/?user_id=3&difficulty=advanced")
        assert response.status_code == 200


class TestProgressTracking:
    """Test progress tracking functionality"""
    
    def test_record_workout_progress(self, setup_teardown):
        """Test recording workout progress"""
        response = client.post(
            "/progress/",
            json={
                "user_id": 7,
                "session_id": 1,
                "completed_at": datetime.now().isoformat(),
                "duration_minutes": 60,
                "intensity_level": "moderate",
                "notes": "Good workout",
                "exercise_progress": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 60
        assert data["intensity_level"] == "moderate"
    
    def test_get_user_progress_history(self, setup_teardown):
        """Test retrieving user progress history"""
        user_id = 8
        
        # Record multiple progress entries
        for i in range(3):
            client.post(
                "/progress/",
                json={
                    "user_id": user_id,
                    "session_id": i + 1,
                    "completed_at": (datetime.now() - timedelta(days=i)).isoformat(),
                    "duration_minutes": 45 + (i * 5),
                    "intensity_level": "moderate",
                    "notes": f"Workout {i+1}",
                    "exercise_progress": []
                }
            )
        
        response = client.get(f"/progress/user/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_get_progress_by_date_range(self, setup_teardown):
        """Test retrieving progress within date range"""
        user_id = 9
        
        # Record progress on different dates
        for i in range(5):
            client.post(
                "/progress/",
                json={
                    "user_id": user_id,
                    "session_id": i + 1,
                    "completed_at": (datetime.now() - timedelta(days=i)).isoformat(),
                    "duration_minutes": 50,
                    "intensity_level": "moderate",
                    "notes": f"Workout {i+1}",
                    "exercise_progress": []
                }
            )
        
        # Get progress for last 2 days
        start_date = (datetime.now() - timedelta(days=2)).isoformat()
        end_date = datetime.now().isoformat()
        
        response = client.get(
            f"/progress/user/{user_id}?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        data = response.json()
        # Should return 2-3 entries (depending on time)
        assert len(data) >= 2


class TestProgressStatistics:
    """Test progress statistics calculation"""
    
    def test_get_progress_stats(self, setup_teardown):
        """Test getting progress statistics"""
        user_id = 10
        
        # Record multiple workouts
        for i in range(5):
            client.post(
                "/progress/",
                json={
                    "user_id": user_id,
                    "session_id": i + 1,
                    "completed_at": datetime.now().isoformat(),
                    "duration_minutes": 60 - (i * 5),
                    "intensity_level": "moderate",
                    "notes": f"Workout {i+1}",
                    "exercise_progress": []
                }
            )
        
        response = client.get(f"/progress/stats/user/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_workouts"] == 5
        assert data["average_duration_minutes"] > 0
    
    def test_stats_for_user_with_no_progress(self, setup_teardown):
        """Test statistics for user with no progress"""
        response = client.get("/progress/stats/user/9999")
        assert response.status_code == 200
        data = response.json()
        assert data["total_workouts"] == 0
        assert data["average_duration_minutes"] == 0


class TestSubscriptionIntegration:
    """Test Payment Service integration"""
    
    @patch('services.workout.main.check_user_subscription')
    async def test_subscription_check_timeout(self, mock_subscription, setup_teardown):
        """Test handling of subscription service timeout"""
        # Mock a timeout scenario - should default to free
        mock_subscription.side_effect = Exception("Connection timeout")
        
        response = client.post(
            "/workout-plans/",
            json={
                "user_id": 11,
                "plan_name": "Plan",
                "goal": "weight_loss",
                "difficulty": "advanced",
                "is_personalized": False,
                "duration_weeks": 4,
                "sessions": []
            }
        )
        # Should fail because subscription check couldn't be verified
        assert response.status_code == 403


class TestErrorHandling:
    """Test error handling"""
    
    def test_get_nonexistent_plan(self, setup_teardown):
        """Test getting non-existent plan"""
        response = client.get("/workout-plans/99999")
        assert response.status_code == 404
    
    @patch('services.workout.main.check_user_subscription')
    async def test_update_nonexistent_plan(self, mock_subscription, setup_teardown):
        """Test updating non-existent plan"""
        mock_subscription.return_value = {"plan_type": "premium", "is_active": True}
        
        response = client.put(
            "/workout-plans/99999",
            json={
                "user_id": 1,
                "plan_name": "Updated",
                "goal": "weight_loss",
                "difficulty": "beginner",
                "is_personalized": False,
                "duration_weeks": 4,
                "sessions": []
            }
        )
        assert response.status_code == 404
    
    def test_delete_nonexistent_plan(self, setup_teardown):
        """Test deleting non-existent plan"""
        response = client.delete("/workout-plans/99999")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
