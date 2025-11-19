"""
Seed data for Workout Service
Creates sample workout plans and exercises
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def seed_workout_data():
    """Seed sample workout data to database"""
    
    connection = None
    try:
        # Create connection
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database='workout_db'
        )
        
        cursor = connection.cursor()
        print("🌱 Seeding Workout Database...")
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM workout_plans')
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("✅ Workout data already seeded, skipping...")
            cursor.close()
            return
        
        # Default workout plans for free users (user_ids: 1-7)
        default_plans = [
            (1, 'Beginner Full Body - Default', 'Basic full body routine for beginners', '2025-01-01', None),
            (2, 'Weight Loss Program - Default', 'Cardio and strength mix for fat loss', '2025-01-01', None),
            (3, 'Weight Loss Program - Default', 'Cardio and strength mix for fat loss', '2025-01-01', None),
            (4, 'Muscle Gain Program - Default', 'Progressive strength training', '2025-01-01', None),
            (5, 'Weight Loss Program - Default', 'Cardio and strength mix for fat loss', '2025-01-01', None),
            (6, 'Muscle Gain Program - Default', 'Progressive strength training', '2025-01-01', None),
            (7, 'Beginner Full Body - Default', 'Basic full body routine for beginners', '2025-01-01', None),
        ]
        
        # PT-created plans
        pt_plans = [
            (2, 'Advanced Fat Loss - Alex', 'Advanced fat loss program', '2025-01-01', 8),
            (3, 'Intense Cardio Bootcamp - Alex', 'High intensity cardio bootcamp', '2025-01-01', 8),
            (4, 'Professional Muscle Building - Emma', 'Professional muscle building', '2025-01-01', 9),
            (5, 'Body Transformation - Emma', 'Complete body transformation', '2025-01-01', 9),
            (6, 'Elite Strength Program - David', 'Elite strength program', '2025-01-01', 10),
            (7, 'Athletic Performance - David', 'Athletic performance training', '2025-01-01', 10),
            (1, 'Sustainable Fitness - Sophia', 'Sustainable fitness routine', '2025-01-01', 11),
        ]
        
        plan_ids = []
        
        # Insert default plans
        for plan in default_plans:
            sql = '''INSERT INTO workout_plans 
                    (user_id, plan_name, goal, start_date, created_by_pt_id) 
                    VALUES (%s, %s, %s, %s, %s)'''
            cursor.execute(sql, plan)
            plan_ids.append(cursor.lastrowid)
        
        # Insert PT-created plans
        for plan in pt_plans:
            sql = '''INSERT INTO workout_plans 
                    (user_id, plan_name, goal, start_date, created_by_pt_id) 
                    VALUES (%s, %s, %s, %s, %s)'''
            cursor.execute(sql, plan)
            plan_ids.append(cursor.lastrowid)
        
        # Sample exercises for each plan
        exercises_data = [
            # Plan 1 (Beginner)
            (plan_ids[0], 'monday', 'Squat', 3, '8-12', 20.00),
            (plan_ids[0], 'tuesday', 'Push-up', 3, '10-15', None),
            (plan_ids[0], 'wednesday', 'Deadlift', 3, '5-8', 30.00),
            (plan_ids[0], 'thursday', 'Bench Press', 3, '8-12', 25.00),
            (plan_ids[0], 'friday', 'Pull-ups', 3, '5-10', None),
            (plan_ids[0], 'saturday', 'Planks', 3, '30-60s', None),
            # Plan 2 (Weight Loss)
            (plan_ids[1], 'monday', 'Running', 1, '30 min', None),
            (plan_ids[1], 'tuesday', 'Burpees', 4, '20', None),
            (plan_ids[1], 'wednesday', 'Jump Rope', 1, '10 min', None),
            (plan_ids[1], 'thursday', 'Mountain Climbers', 3, '20', None),
            (plan_ids[1], 'friday', 'Cycling', 1, '45 min', None),
            (plan_ids[1], 'saturday', 'Boxing', 3, '15 min', None),
            # Plan 3 (Weight Loss)
            (plan_ids[2], 'monday', 'HIIT Training', 1, '20 min', None),
            (plan_ids[2], 'tuesday', 'Swimming', 1, '30 min', None),
            (plan_ids[2], 'wednesday', 'Jump Rope', 1, '10 min', None),
            (plan_ids[2], 'thursday', 'Running', 1, '25 min', None),
            (plan_ids[2], 'friday', 'Elliptical', 1, '35 min', None),
            # Plan 4 (Muscle Gain)
            (plan_ids[3], 'monday', 'Barbell Squat', 4, '6-8', 50.00),
            (plan_ids[3], 'tuesday', 'Bench Press Heavy', 4, '6-8', 40.00),
            (plan_ids[3], 'wednesday', 'Deadlift Heavy', 3, '3-5', 60.00),
            (plan_ids[3], 'thursday', 'Overhead Press', 3, '8-10', 25.00),
            (plan_ids[3], 'friday', 'Rows', 4, '8-10', 30.00),
            (plan_ids[3], 'saturday', 'Leg Press', 3, '10-12', 80.00),
            # Plan 5 (Weight Loss)
            (plan_ids[4], 'monday', 'Zumba', 1, '45 min', None),
            (plan_ids[4], 'tuesday', 'Spinning', 1, '30 min', None),
            (plan_ids[4], 'wednesday', 'Aerobics', 1, '40 min', None),
            (plan_ids[4], 'thursday', 'Running', 1, '30 min', None),
            (plan_ids[4], 'friday', 'Dance Cardio', 1, '35 min', None),
            # Plan 6 (Muscle Gain)
            (plan_ids[5], 'monday', 'Squat', 5, '5-8', 60.00),
            (plan_ids[5], 'tuesday', 'Incline Bench Press', 4, '6-8', 35.00),
            (plan_ids[5], 'wednesday', 'Deadlift', 4, '5-6', 70.00),
            (plan_ids[5], 'thursday', 'Pull-ups', 5, '8-12', None),
            (plan_ids[5], 'friday', 'Leg Curl', 4, '8-10', 40.00),
            (plan_ids[5], 'saturday', 'Cable Flyes', 4, '10-12', 30.00),
            # Plan 7 (Beginner)
            (plan_ids[6], 'monday', 'Squat', 3, '10-15', 15.00),
            (plan_ids[6], 'tuesday', 'Dumbbell Push-ups', 3, '12-15', None),
            (plan_ids[6], 'wednesday', 'Romanian Deadlift', 3, '8-10', 20.00),
            (plan_ids[6], 'thursday', 'Dumbbell Bench Press', 3, '10-12', 15.00),
            (plan_ids[6], 'friday', 'Assisted Pull-ups', 3, '8-12', None),
            (plan_ids[6], 'saturday', 'Wall Planks', 3, '45-60s', None),
            # PT Plan 1 - Advanced Fat Loss
            (plan_ids[7], 'monday', 'HIIT Running', 1, '25 min', None),
            (plan_ids[7], 'tuesday', 'Circuit Training', 4, '15', None),
            (plan_ids[7], 'wednesday', 'Swimming', 1, '35 min', None),
            (plan_ids[7], 'thursday', 'Boxing', 3, '20 min', None),
            (plan_ids[7], 'friday', 'Stair Climbing', 1, '25 min', None),
            (plan_ids[7], 'saturday', 'Crossfit WOD', 1, '30 min', None),
            # PT Plan 2 - Intense Cardio
            (plan_ids[8], 'monday', 'Tabata Training', 1, '20 min', None),
            (plan_ids[8], 'tuesday', 'Rope Climbing', 5, '10', None),
            (plan_ids[8], 'wednesday', 'Battle Ropes', 4, '30s', None),
            (plan_ids[8], 'thursday', 'Sprint Intervals', 1, '25 min', None),
            (plan_ids[8], 'friday', 'Circuit Bootcamp', 4, '20', None),
            # PT Plan 3 - Professional Muscle Building
            (plan_ids[9], 'monday', 'Barbell Squat', 5, '5-6', 70.00),
            (plan_ids[9], 'tuesday', 'Incline Barbell Press', 5, '5-6', 45.00),
            (plan_ids[9], 'wednesday', 'Deadlift Variation', 4, '3-5', 80.00),
            (plan_ids[9], 'thursday', 'Weighted Pull-ups', 5, '6-8', None),
            (plan_ids[9], 'friday', 'Leg Extension', 4, '8-10', 50.00),
            (plan_ids[9], 'saturday', 'Chest Flyes', 4, '10-12', 25.00),
            # PT Plan 4 - Body Transformation
            (plan_ids[10], 'monday', 'Full Body HIIT', 1, '30 min', None),
            (plan_ids[10], 'tuesday', 'Strength Training', 4, '12', 25.00),
            (plan_ids[10], 'wednesday', 'Cardio Mix', 1, '35 min', None),
            (plan_ids[10], 'thursday', 'Circuit Training', 4, '15', None),
            (plan_ids[10], 'friday', 'Yoga Flow', 1, '45 min', None),
            # PT Plan 5 - Elite Strength
            (plan_ids[11], 'monday', 'Barbell Squat', 6, '3-5', 80.00),
            (plan_ids[11], 'tuesday', 'Bench Press', 6, '3-5', 50.00),
            (plan_ids[11], 'wednesday', 'Deadlift', 5, '1-3', 100.00),
            (plan_ids[11], 'thursday', 'Overhead Press', 5, '5-8', 30.00),
            (plan_ids[11], 'friday', 'Barbell Rows', 5, '5-8', 45.00),
            (plan_ids[11], 'saturday', 'Front Squat', 4, '6-8', 50.00),
            # PT Plan 6 - Athletic Performance
            (plan_ids[12], 'monday', 'Plyometrics', 1, '30 min', None),
            (plan_ids[12], 'tuesday', 'Agility Training', 1, '30 min', None),
            (plan_ids[12], 'wednesday', 'Strength Power', 4, '12', 35.00),
            (plan_ids[12], 'thursday', 'Speed Work', 1, '25 min', None),
            (plan_ids[12], 'friday', 'Conditioning', 1, '35 min', None),
            # PT Plan 7 - Sustainable Fitness
            (plan_ids[13], 'monday', 'Functional Training', 3, '12', 15.00),
            (plan_ids[13], 'tuesday', 'Pilates', 1, '50 min', None),
            (plan_ids[13], 'wednesday', 'Walking', 1, '45 min', None),
            (plan_ids[13], 'thursday', 'Yoga', 1, '60 min', None),
            (plan_ids[13], 'friday', 'Light Cardio', 1, '30 min', None),
            (plan_ids[13], 'saturday', 'Stretching', 1, '30 min', None),
        ]
        
        for exercise in exercises_data:
            sql = '''INSERT INTO exercises 
                    (plan_id, day_of_week, exercise_name, sets, reps, weight_kg) 
                    VALUES (%s, %s, %s, %s, %s, %s)'''
            cursor.execute(sql, exercise)
        
        connection.commit()
        print("✅ Workout data seeded successfully!")
        print("\n📊 Workout Summary:")
        print(f"   ✓ {len(default_plans)} Default workout plans (for free users)")
        print(f"   ✓ {len(pt_plans)} PT-created workout plans")
        print(f"   ✓ {len(exercises_data)} Exercises total")
        cursor.close()
        
    except Error as error:
        print(f"❌ Error seeding workout data: {str(error)}")
        raise error
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    seed_workout_data()
