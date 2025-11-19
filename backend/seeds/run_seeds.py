"""
Master Seed Runner
Runs all database seeding in sequence
Called automatically when Docker container starts
"""

import sys
import os
from pathlib import Path

# Add seeds directory to path
seeds_path = str(Path(__file__).parent)
if seeds_path not in sys.path:
    sys.path.insert(0, seeds_path)

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from seed_users import seed_users_data
from seed_workout import seed_workout_data
from seed_nutrition import seed_nutrition_data
from seed_calorie import seed_calorie_data
from seed_payment import seed_payment_data


def run_all_seeds():
    """Run all database seeds in sequence"""
    
    print("\n" + "="*60)
    print("🌱 STARTING DATABASE SEEDING...")
    print("="*60 + "\n")
    
    try:
        # Run seeds in sequence (some depend on user data)
        print("📌 Step 1: Seeding Users...")
        seed_users_data()
        
        print("\n📌 Step 2: Seeding Workout...")
        seed_workout_data()
        
        print("\n📌 Step 3: Seeding Nutrition...")
        seed_nutrition_data()
        
        print("\n📌 Step 4: Seeding Calories...")
        seed_calorie_data()
        
        print("\n📌 Step 5: Seeding Payment...")
        seed_payment_data()
        
        print("\n" + "="*60)
        print("✅ ALL DATABASE SEEDS COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as error:
        print("\n" + "="*60)
        print("❌ ERROR DURING SEEDING:")
        print(str(error))
        print("="*60 + "\n")
        import traceback
        traceback.print_exc()
        raise error


if __name__ == "__main__":
    try:
        run_all_seeds()
        print("✅ Seeding completed!")
        sys.exit(0)
    except Exception as error:
        print(f"❌ Seeding failed: {str(error)}")
        sys.exit(1)
