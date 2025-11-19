"""
Seed data for Nutrition Service
Creates sample meal plans and daily meals with ingredients
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def seed_nutrition_data():
    """Seed sample nutrition data to database"""
    
    connection = None
    try:
        # Create connection - sử dụng localhost cho local development
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database='nutrition_db'
        )
        
        cursor = connection.cursor()
        print("🌱 Seeding Nutrition Database...")
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM meal_plans')
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("✅ Nutrition data already seeded, skipping...")
            cursor.close()
            return
        
        # Default meal plans cho free users (user_ids: 1-7)
        # Các user này sẽ nhận default nutrition plans
        default_plans = [
            # User 1: Tuấn - Kế hoạch giảm mỡ
            (1, 'Kế hoạch giảm mỡ - Mặc định', 2000, 150),
            # User 2: Michael - Kế hoạch duy trì
            (2, 'Kế hoạch duy trì sức khỏe - Mặc định', 2400, 160),
            # User 3: Sarah - Kế hoạch giảm mỡ
            (3, 'Kế hoạch giảm mỡ - Mặc định', 1800, 120),
            # User 4: John - Kế hoạch tăng cơ
            (4, 'Kế hoạch tăng cơ - Mặc định', 3000, 200),
            # User 5: Lisa - Kế hoạch giảm mỡ
            (5, 'Kế hoạch giảm mỡ - Mặc định', 1700, 110),
            # User 6: James - Kế hoạch tăng cơ
            (6, 'Kế hoạch tăng cơ - Mặc định', 3200, 220),
            # User 7: Emily - Kế hoạch duy trì
            (7, 'Kế hoạch duy trì sức khỏe - Mặc định', 2200, 150),
        ]
        
        # PT-created plans (created by PT user_ids: 8-11)
        pt_plans = [
            # PT Alex (ID 8) - Plans cho clients
            (2, 'Kế hoạch giảm mỡ cao cấp - Alex', 1900, 145, 8),
            (3, 'Kế hoạch cắt mỡ chuyên sâu - Alex', 1750, 130, 8),
            # PT Emma (ID 9) - Plans cho clients
            (4, 'Kế hoạch bulk lên - Emma', 3100, 210, 9),
            (5, 'Kế hoạch tái cấu trúc cơ thể - Emma', 2100, 160, 9),
            # PT David (ID 10) - Plans cho clients
            (6, 'Kế hoạch tăng cơ chuyên nghiệp - David', 3300, 230, 10),
            (7, 'Kế hoạch performance - David', 2800, 185, 10),
            # PT Sophia (ID 11) - Plans cho clients
            (1, 'Kế hoạch khỏe mạnh bền vững - Sophia', 2200, 165, 11),
        ]
        
        plan_ids = []
        
        # Insert default plans
        for plan in default_plans:
            sql = '''INSERT INTO meal_plans 
                    (user_id, plan_name, calorie_target_kcal, protein_target_g, created_by_pt_id) 
                    VALUES (%s, %s, %s, %s, %s)'''
            cursor.execute(sql, plan + (None,))
            plan_ids.append(cursor.lastrowid)
        
        # Insert PT-created plans
        for plan in pt_plans:
            sql = '''INSERT INTO meal_plans 
                    (user_id, plan_name, calorie_target_kcal, protein_target_g, created_by_pt_id) 
                    VALUES (%s, %s, %s, %s, %s)'''
            cursor.execute(sql, plan)
            plan_ids.append(cursor.lastrowid)
        
        # Sample daily meals for each plan
        daily_meals_data = [
            # Default Plan 1 (User 1) - Giảm mỡ
            (plan_ids[0], 'breakfast', '07:00:00'),
            (plan_ids[0], 'lunch', '12:00:00'),
            (plan_ids[0], 'dinner', '18:00:00'),
            (plan_ids[0], 'snack', '15:00:00'),
            # Default Plan 2 (User 2) - Duy trì
            (plan_ids[1], 'breakfast', '06:30:00'),
            (plan_ids[1], 'lunch', '12:30:00'),
            (plan_ids[1], 'dinner', '19:00:00'),
            # Default Plan 3 (User 3) - Giảm mỡ
            (plan_ids[2], 'breakfast', '07:30:00'),
            (plan_ids[2], 'lunch', '12:00:00'),
            (plan_ids[2], 'dinner', '18:30:00'),
            # Default Plan 4 (User 4) - Tăng cơ
            (plan_ids[3], 'breakfast', '06:00:00'),
            (plan_ids[3], 'lunch', '12:30:00'),
            (plan_ids[3], 'dinner', '19:30:00'),
            (plan_ids[3], 'snack', '10:00:00'),
            (plan_ids[3], 'snack', '16:00:00'),
            # Default Plan 5 (User 5) - Giảm mỡ
            (plan_ids[4], 'breakfast', '07:00:00'),
            (plan_ids[4], 'lunch', '12:00:00'),
            (plan_ids[4], 'dinner', '18:00:00'),
            # Default Plan 6 (User 6) - Tăng cơ
            (plan_ids[5], 'breakfast', '06:30:00'),
            (plan_ids[5], 'lunch', '12:00:00'),
            (plan_ids[5], 'dinner', '19:00:00'),
            (plan_ids[5], 'snack', '10:00:00'),
            (plan_ids[5], 'snack', '15:30:00'),
            # Default Plan 7 (User 7) - Duy trì
            (plan_ids[6], 'breakfast', '07:00:00'),
            (plan_ids[6], 'lunch', '12:30:00'),
            (plan_ids[6], 'dinner', '18:30:00'),
            # PT Plan 1 - Alex cho User 2
            (plan_ids[7], 'breakfast', '06:30:00'),
            (plan_ids[7], 'lunch', '12:00:00'),
            (plan_ids[7], 'dinner', '18:30:00'),
            (plan_ids[7], 'snack', '15:00:00'),
            # PT Plan 2 - Alex cho User 3
            (plan_ids[8], 'breakfast', '07:00:00'),
            (plan_ids[8], 'lunch', '12:30:00'),
            (plan_ids[8], 'dinner', '18:00:00'),
            # PT Plan 3 - Emma cho User 4
            (plan_ids[9], 'breakfast', '06:00:00'),
            (plan_ids[9], 'lunch', '12:30:00'),
            (plan_ids[9], 'dinner', '19:30:00'),
            (plan_ids[9], 'snack', '09:30:00'),
            (plan_ids[9], 'snack', '15:30:00'),
            # PT Plan 4 - Emma cho User 5
            (plan_ids[10], 'breakfast', '07:00:00'),
            (plan_ids[10], 'lunch', '12:00:00'),
            (plan_ids[10], 'dinner', '18:30:00'),
            (plan_ids[10], 'snack', '15:00:00'),
            # PT Plan 5 - David cho User 6
            (plan_ids[11], 'breakfast', '06:00:00'),
            (plan_ids[11], 'lunch', '12:30:00'),
            (plan_ids[11], 'dinner', '19:30:00'),
            (plan_ids[11], 'snack', '09:30:00'),
            (plan_ids[11], 'snack', '16:00:00'),
            # PT Plan 6 - David cho User 7
            (plan_ids[12], 'breakfast', '07:00:00'),
            (plan_ids[12], 'lunch', '12:30:00'),
            (plan_ids[12], 'dinner', '19:00:00'),
            (plan_ids[12], 'snack', '15:30:00'),
            # PT Plan 7 - Sophia cho User 1
            (plan_ids[13], 'breakfast', '07:00:00'),
            (plan_ids[13], 'lunch', '12:30:00'),
            (plan_ids[13], 'dinner', '18:30:00'),
            (plan_ids[13], 'snack', '15:00:00'),
        ]
        
        daily_meal_ids = []
        for meal in daily_meals_data:
            sql = '''INSERT INTO daily_meals 
                    (meal_plan_id, meal_type, meal_time) 
                    VALUES (%s, %s, %s)'''
            cursor.execute(sql, meal)
            daily_meal_ids.append(cursor.lastrowid)
        
        # Sample ingredients for each daily meal
        ingredients_data = [
            # Default Plan 1 Breakfast
            (daily_meal_ids[0], 'Trứng luộc', '2 quả', 155),
            (daily_meal_ids[0], 'Bánh mì ngũ cốc', '1 lát', 80),
            (daily_meal_ids[0], 'Cà chua', '1 quả', 25),
            # Default Plan 1 Lunch
            (daily_meal_ids[1], 'Ức gà nướng', '150g', 165),
            (daily_meal_ids[1], 'Cơm trắng', '150g', 195),
            (daily_meal_ids[1], 'Rau xanh luộc', '100g', 25),
            # Default Plan 1 Dinner
            (daily_meal_ids[2], 'Cá hồi nướng', '150g', 280),
            (daily_meal_ids[2], 'Khoai tây nướng', '150g', 120),
            (daily_meal_ids[2], 'Bông cải xanh', '100g', 30),
            # Default Plan 1 Snack
            (daily_meal_ids[3], 'Hạnh nhân', '30g', 180),
            (daily_meal_ids[3], 'Chuối', '1 quả', 105),
            # Default Plan 2 Breakfast
            (daily_meal_ids[4], 'Yến mạch', '50g', 190),
            (daily_meal_ids[4], 'Sữa tươi', '250ml', 160),
            (daily_meal_ids[4], 'Mật ong', '1 thìa', 65),
            (daily_meal_ids[4], 'Quả mâm xôi', '50g', 30),
            # Default Plan 2 Lunch
            (daily_meal_ids[5], 'Ức gà nướng', '180g', 198),
            (daily_meal_ids[5], 'Cơm trắng', '200g', 260),
            (daily_meal_ids[5], 'Súp rau', '200g', 50),
            # Default Plan 2 Dinner
            (daily_meal_ids[6], 'Thịt bò nướng', '170g', 300),
            (daily_meal_ids[6], 'Khoai lang nướng', '150g', 135),
            (daily_meal_ids[6], 'Bông cải xanh', '100g', 30),
            # Default Plan 3 Breakfast
            (daily_meal_ids[7], 'Trứng chiên', '1 quả', 155),
            (daily_meal_ids[7], 'Bánh mì nâu', '1 lát', 75),
            (daily_meal_ids[7], 'Cà chua', '1 quả', 25),
            # Default Plan 3 Lunch
            (daily_meal_ids[8], 'Ức gà', '120g', 132),
            (daily_meal_ids[8], 'Cơm lứt', '150g', 195),
            (daily_meal_ids[8], 'Rau xanh', '120g', 30),
            # Default Plan 3 Dinner
            (daily_meal_ids[9], 'Cá trắng nướng', '130g', 130),
            (daily_meal_ids[9], 'Khoai tây nước', '150g', 120),
            (daily_meal_ids[9], 'Bông cải', '100g', 30),
            # Default Plan 4 Breakfast (Tăng cơ)
            (daily_meal_ids[10], 'Trứng tươi', '3 quả', 210),
            (daily_meal_ids[10], 'Bánh mì', '2 lát', 160),
            (daily_meal_ids[10], 'Bơ', '1 thìa', 100),
            # Default Plan 4 Lunch
            (daily_meal_ids[11], 'Ức gà', '200g', 220),
            (daily_meal_ids[11], 'Cơm trắng', '250g', 325),
            (daily_meal_ids[11], 'Bông cải', '120g', 35),
            # Default Plan 4 Dinner
            (daily_meal_ids[12], 'Thịt bò', '200g', 350),
            (daily_meal_ids[12], 'Khoai tây', '200g', 160),
            (daily_meal_ids[12], 'Bông cải', '150g', 45),
            # Default Plan 4 Snack 1
            (daily_meal_ids[13], 'Sữa tăng cơ', '250ml', 200),
            (daily_meal_ids[13], 'Bánh quy lúa mạch', '30g', 130),
            # Default Plan 4 Snack 2
            (daily_meal_ids[14], 'Chuối', '2 quả', 210),
            (daily_meal_ids[14], 'Hạnh nhân', '40g', 240),
        ]
        
        for ingredient in ingredients_data:
            sql = '''INSERT INTO ingredients 
                    (daily_meal_id, food_name, quantity, calories) 
                    VALUES (%s, %s, %s, %s)'''
            cursor.execute(sql, ingredient)
        
        connection.commit()
        print("✅ Nutrition data seeded successfully!")
        print("\n📊 Nutrition Summary:")
        print(f"   ✓ {len(default_plans)} Default meal plans (cho free users)")
        print(f"   ✓ {len(pt_plans)} PT-created meal plans")
        print(f"   ✓ {len(daily_meals_data)} Daily meals tổng cộng")
        cursor.close()
        
    except Error as error:
        print(f"❌ Error seeding nutrition data: {str(error)}")
        raise error
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    seed_nutrition_data()
