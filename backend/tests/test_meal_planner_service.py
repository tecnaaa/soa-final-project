"""
Unit tests for Meal Planner Service (Nutrition Service v2)
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

from services.nutrition.main import app, get_db
from db.db import Base
from models.nutrition.nutrition_models import MealPlan, MealRecommendation, DailyMealPlan

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_nutrition.db"
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

class TestMealPlanCreation:
    """Test cases for meal plan creation"""
    
    def test_create_meal_plan_weight_loss(self, setup_teardown):
        """Test creating weight loss meal plan"""
        response = client.post(
            "/meal-plans/",
            json={
                "user_id": 1,
                "plan_name": "Weight Loss Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "weight_loss"
        assert data["daily_calories"] == 1800
        # Weight loss: 35% protein, 40% carbs, 25% fat
        assert data["daily_protein"] > 0
        assert data["daily_carbs"] > 0
        assert data["daily_fat"] > 0

    def test_create_meal_plan_muscle_gain(self, setup_teardown):
        """Test creating muscle gain meal plan"""
        response = client.post(
            "/meal-plans/",
            json={
                "user_id": 2,
                "plan_name": "Muscle Gain Plan",
                "goal": "muscle_gain",
                "duration_days": 60
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "muscle_gain"
        assert data["daily_calories"] == 2500
        # Muscle gain should have higher carbs
        assert data["daily_carbs"] > data["daily_protein"]

    def test_create_meal_plan_maintenance(self, setup_teardown):
        """Test creating maintenance meal plan"""
        response = client.post(
            "/meal-plans/",
            json={
                "user_id": 3,
                "plan_name": "Maintenance Plan",
                "goal": "maintenance",
                "duration_days": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "maintenance"
        assert data["daily_calories"] == 2000

    def test_macro_calculation_accuracy(self, setup_teardown):
        """Test that macro targets are calculated correctly"""
        response = client.post(
            "/meal-plans/",
            json={
                "user_id": 4,
                "plan_name": "Macro Test",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        data = response.json()
        total_calories = data["daily_calories"]
        
        # Verify macro percentages
        protein_cals = data["daily_protein"] * 4
        carbs_cals = data["daily_carbs"] * 4
        fat_cals = data["daily_fat"] * 9
        
        assert abs(protein_cals / total_calories - 0.35) < 0.05
        assert abs(carbs_cals / total_calories - 0.40) < 0.05
        assert abs(fat_cals / total_calories - 0.25) < 0.05


class TestMealRecommendations:
    """Test cases for meal recommendations"""
    
    def test_add_meal_recommendation(self, setup_teardown):
        """Test adding meal recommendation to plan"""
        # Create plan first
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 5,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        
        # Add recommendation with manual nutrition info
        response = client.post(
            f"/meal-plans/{plan_id}/recommendations/",
            json={
                "meal_type": "breakfast",
                "day_of_week": "Monday",
                "food_id": 1,
                "quantity_grams": 150,
                "estimated_calories": 247.5,
                "estimated_protein": 46.5,
                "estimated_carbs": 0,
                "estimated_fat": 5.4,
                "notes": "Chicken breast"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meal_type"] == "breakfast"
        assert data["estimated_calories"] == 247.5

    def test_get_meal_recommendations(self, setup_teardown):
        """Test retrieving recommendations for a plan"""
        # Create plan and add recommendations
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 6,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        
        # Add multiple recommendations
        for meal_type in ["breakfast", "lunch", "dinner"]:
            client.post(
                f"/meal-plans/{plan_id}/recommendations/",
                json={
                    "meal_type": meal_type,
                    "day_of_week": "Any",
                    "food_id": 1,
                    "quantity_grams": 100,
                    "estimated_calories": 100,
                    "estimated_protein": 20,
                    "estimated_carbs": 0,
                    "estimated_fat": 2
                }
            )
        
        response = client.get(f"/meal-plans/{plan_id}/recommendations/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestDailyTracking:
    """Test cases for daily meal tracking"""
    
    def test_track_daily_meals(self, setup_teardown):
        """Test tracking daily meals"""
        # Create plan
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 7,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        
        # Track daily meals
        response = client.post(
            f"/meal-plans/{plan_id}/daily-tracking/",
            json={
                "date": datetime.now().isoformat(),
                "actual_calories": 1800,
                "actual_protein": 135,
                "actual_carbs": 180,
                "actual_fat": 50,
                "notes": "Good day"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["actual_calories"] == 1800
        assert data["adherence_percentage"] == 100.0  # Exactly on target

    def test_adherence_calculation(self, setup_teardown):
        """Test adherence percentage calculation"""
        # Create plan
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 8,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        plan_data = plan_response.json()
        daily_target = plan_data["daily_calories"]
        
        # Track with 80% adherence
        actual_calories = int(daily_target * 0.8)
        response = client.post(
            f"/meal-plans/{plan_id}/daily-tracking/",
            json={
                "date": datetime.now().isoformat(),
                "actual_calories": actual_calories,
                "actual_protein": 100,
                "actual_carbs": 150,
                "actual_fat": 40
            }
        )
        data = response.json()
        assert data["adherence_percentage"] == 80.0

    def test_get_daily_tracking_history(self, setup_teardown):
        """Test retrieving daily tracking history"""
        # Create plan
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 9,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        
        # Track multiple days
        for i in range(3):
            client.post(
                f"/meal-plans/{plan_id}/daily-tracking/",
                json={
                    "date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "actual_calories": 1800,
                    "actual_protein": 135,
                    "actual_carbs": 180,
                    "actual_fat": 50
                }
            )
        
        response = client.get(f"/meal-plans/{plan_id}/daily-tracking/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestMealPlanManagement:
    """Test cases for meal plan management"""
    
    def test_get_user_meal_plans(self, setup_teardown):
        """Test retrieving all meal plans for user"""
        # Create multiple plans
        for i in range(3):
            client.post(
                "/meal-plans/",
                json={
                    "user_id": 10,
                    "plan_name": f"Plan {i}",
                    "goal": "weight_loss",
                    "duration_days": 30
                }
            )
        
        response = client.get("/meal-plans/user/10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_deactivate_meal_plan(self, setup_teardown):
        """Test deactivating a meal plan"""
        # Create plan
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 11,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        
        # Deactivate
        response = client.put(f"/meal-plans/{plan_id}/deactivate")
        assert response.status_code == 200
        
        # Verify deactivated
        get_response = client.get(f"/meal-plans/{plan_id}")
        assert get_response.json()["is_active"] == 0

    def test_delete_meal_plan(self, setup_teardown):
        """Test deleting a meal plan"""
        # Create plan
        plan_response = client.post(
            "/meal-plans/",
            json={
                "user_id": 12,
                "plan_name": "Test Plan",
                "goal": "weight_loss",
                "duration_days": 30
            }
        )
        plan_id = plan_response.json()["plan_id"]
        
        # Delete
        response = client.delete(f"/meal-plans/{plan_id}")
        assert response.status_code == 200
        
        # Verify deleted
        get_response = client.get(f"/meal-plans/{plan_id}")
        assert get_response.status_code == 404


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_goal(self, setup_teardown):
        """Test invalid goal handling"""
        response = client.post(
            "/meal-plans/",
            json={
                "user_id": 13,
                "plan_name": "Invalid",
                "goal": "invalid_goal",
                "duration_days": 30
            }
        )
        assert response.status_code != 200

    def test_get_nonexistent_plan(self, setup_teardown):
        """Test getting non-existent plan"""
        response = client.get("/meal-plans/99999")
        assert response.status_code == 404

    def test_recommend_to_nonexistent_plan(self, setup_teardown):
        """Test adding recommendation to non-existent plan"""
        response = client.post(
            "/meal-plans/99999/recommendations/",
            json={
                "meal_type": "breakfast",
                "day_of_week": "Monday",
                "food_id": 1,
                "quantity_grams": 100,
                "estimated_calories": 100,
                "estimated_protein": 20,
                "estimated_carbs": 0,
                "estimated_fat": 2
            }
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
