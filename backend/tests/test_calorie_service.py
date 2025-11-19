"""
Unit tests for Calorie Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.calories.main import app, get_db
from db.db import Base
from models.calorie.calorie_models import Food, Recipe, UserDailyLog

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_calorie.db"
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

class TestFoodManagement:
    """Test cases for food management"""
    
    def test_create_food(self, setup_teardown):
        """Test creating a new food item"""
        response = client.post(
            "/foods/",
            json={
                "name": "Apple",
                "calories_per_100g": 52,
                "protein": 0.3,
                "carbs": 14,
                "fat": 0.2,
                "fiber": 2.4
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Apple"
        assert data["calories_per_100g"] == 52

    def test_get_foods_list(self, setup_teardown):
        """Test retrieving list of foods"""
        # Create some foods
        client.post("/foods/", json={
            "name": "Banana",
            "calories_per_100g": 89,
            "protein": 1.1,
            "carbs": 23,
            "fat": 0.3,
            "fiber": 2.6
        })
        
        client.post("/foods/", json={
            "name": "Orange",
            "calories_per_100g": 47,
            "protein": 0.9,
            "carbs": 12,
            "fat": 0.3,
            "fiber": 2.4
        })
        
        response = client.get("/foods/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_search_foods(self, setup_teardown):
        """Test searching foods by name"""
        # Create foods
        client.post("/foods/", json={
            "name": "Chicken Breast",
            "calories_per_100g": 165,
            "protein": 31,
            "carbs": 0,
            "fat": 3.6,
            "fiber": 0
        })
        
        response = client.get("/foods/search/?query=Chicken")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["name"] == "Chicken Breast"

    def test_search_foods_not_found(self, setup_teardown):
        """Test searching for non-existent food"""
        response = client.get("/foods/search/?query=NonexistentFood")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

class TestRecipeManagement:
    """Test cases for recipe management"""
    
    def test_create_recipe(self, setup_teardown):
        """Test creating a recipe"""
        # Create ingredients first
        rice_response = client.post("/foods/", json={
            "name": "Rice",
            "calories_per_100g": 130,
            "protein": 2.7,
            "carbs": 28,
            "fat": 0.3,
            "fiber": 0.4
        })
        rice_id = rice_response.json()["food_id"]
        
        chicken_response = client.post("/foods/", json={
            "name": "Chicken",
            "calories_per_100g": 165,
            "protein": 31,
            "carbs": 0,
            "fat": 3.6,
            "fiber": 0
        })
        chicken_id = chicken_response.json()["food_id"]
        
        # Create recipe
        response = client.post(
            "/recipes/",
            json={
                "name": "Chicken Rice",
                "description": "Simple chicken and rice dish",
                "ingredients": [
                    {"food_id": rice_id, "weight_grams": 100},
                    {"food_id": chicken_id, "weight_grams": 100}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Chicken Rice"
        assert data["total_calories"] > 0

    def test_get_recipes_list(self, setup_teardown):
        """Test retrieving recipes"""
        response = client.get("/recipes/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestDailyLogs:
    """Test cases for daily calorie logs"""
    
    def test_create_daily_log(self, setup_teardown):
        """Test creating a daily log"""
        response = client.post(
            "/logs/?user_id=1",
            json={
                "date": date.today().isoformat(),
                "goal_calories": 2000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goal_calories"] == 2000

    def test_get_daily_log(self, setup_teardown):
        """Test retrieving a daily log"""
        # Create a log first
        log_response = client.post(
            "/logs/?user_id=1",
            json={
                "date": date.today().isoformat(),
                "goal_calories": 2000
            }
        )
        log_id = log_response.json()["log_id"]
        
        response = client.get(f"/logs/{log_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["log_id"] == log_id

    def test_get_user_logs(self, setup_teardown):
        """Test retrieving user's logs"""
        # Create multiple logs
        client.post(
            "/logs/?user_id=1",
            json={
                "date": date.today().isoformat(),
                "goal_calories": 2000
            }
        )
        
        response = client.get("/logs/user/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestMealTracking:
    """Test cases for meal tracking"""
    
    def test_add_meal_to_log(self, setup_teardown):
        """Test adding a meal to a daily log"""
        # Create food
        food_response = client.post("/foods/", json={
            "name": "Egg",
            "calories_per_100g": 155,
            "protein": 13,
            "carbs": 1.1,
            "fat": 11,
            "fiber": 0
        })
        food_id = food_response.json()["food_id"]
        
        # Create log
        log_response = client.post(
            "/logs/?user_id=1",
            json={
                "date": date.today().isoformat(),
                "goal_calories": 2000
            }
        )
        log_id = log_response.json()["log_id"]
        
        # Add meal
        response = client.post(
            f"/meals/?log_id={log_id}",
            json={
                "meal_type": "breakfast",
                "meal_time": datetime.now().isoformat(),
                "notes": "Breakfast",
                "items": [
                    {
                        "food_id": food_id,
                        "recipe_id": None,
                        "quantity_grams": 100
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meal_type"] == "breakfast"
        assert data["calories"] > 0

    def test_delete_meal(self, setup_teardown):
        """Test deleting a meal"""
        # Create food and log
        food_response = client.post("/foods/", json={
            "name": "Rice",
            "calories_per_100g": 130,
            "protein": 2.7,
            "carbs": 28,
            "fat": 0.3,
            "fiber": 0.4
        })
        food_id = food_response.json()["food_id"]
        
        log_response = client.post(
            "/logs/?user_id=1",
            json={
                "date": date.today().isoformat(),
                "goal_calories": 2000
            }
        )
        log_id = log_response.json()["log_id"]
        
        # Add meal
        meal_response = client.post(
            f"/meals/?log_id={log_id}",
            json={
                "meal_type": "lunch",
                "meal_time": datetime.now().isoformat(),
                "notes": "Lunch",
                "items": [{"food_id": food_id, "recipe_id": None, "quantity_grams": 100}]
            }
        )
        meal_id = meal_response.json()["meal_id"]
        
        # Delete meal
        response = client.delete(f"/meals/{meal_id}")
        assert response.status_code == 200

class TestFavoriteFoods:
    """Test cases for favorite foods"""
    
    def test_add_favorite_food(self, setup_teardown):
        """Test adding food to favorites"""
        # Create food
        food_response = client.post("/foods/", json={
            "name": "Salmon",
            "calories_per_100g": 208,
            "protein": 25,
            "carbs": 0,
            "fat": 13,
            "fiber": 0
        })
        food_id = food_response.json()["food_id"]
        
        # Add to favorites
        response = client.post(
            "/favorites/?user_id=1",
            json={
                "food_id": food_id,
                "recipe_id": None
            }
        )
        assert response.status_code == 200

    def test_get_user_favorites(self, setup_teardown):
        """Test retrieving user's favorite foods"""
        # Create and add favorite
        food_response = client.post("/foods/", json={
            "name": "Avocado",
            "calories_per_100g": 160,
            "protein": 2,
            "carbs": 9,
            "fat": 15,
            "fiber": 7
        })
        food_id = food_response.json()["food_id"]
        
        client.post(
            "/favorites/?user_id=1",
            json={"food_id": food_id, "recipe_id": None}
        )
        
        response = client.get("/favorites/user/1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_remove_favorite(self, setup_teardown):
        """Test removing a favorite"""
        # Create and add favorite
        food_response = client.post("/foods/", json={
            "name": "Broccoli",
            "calories_per_100g": 34,
            "protein": 2.8,
            "carbs": 7,
            "fat": 0.4,
            "fiber": 2.4
        })
        food_id = food_response.json()["food_id"]
        
        fav_response = client.post(
            "/favorites/?user_id=1",
            json={"food_id": food_id, "recipe_id": None}
        )
        fav_id = fav_response.json()["id"]
        
        # Remove favorite
        response = client.delete(f"/favorites/{fav_id}")
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
