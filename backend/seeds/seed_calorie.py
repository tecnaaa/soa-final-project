"""
Seed data for Calorie Service
Creates sample foods, recipes, and recipe ingredients
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def seed_calorie_data():
    """Seed sample calorie data to database"""
    
    connection = None
    try:
        # Create connection
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database='calories_db'
        )
        
        cursor = connection.cursor()
        print("🌱 Seeding Calories Database...")
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM foods')
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("✅ Calories data already seeded, skipping...")
            cursor.close()
            return
        
        # Sample foods
        foods = [
            ('Ức gà', 165, 31, 3.6, 0),
            ('Cơm trắng', 130, 2.7, 0.3, 28),
            ('Khoai tây', 77, 2, 0.1, 17),
            ('Dầu thực vật', 884, 0, 100, 0),
            ('Bông cải xanh', 55, 4.6, 0.5, 11),
            ('Trứng luộc', 155, 13, 11, 1.1),
            ('Cá hồi', 208, 20, 13, 0),
            ('Yến mạch', 389, 17, 7, 66),
            ('Chuối', 89, 1.1, 0.3, 23),
            ('Hạnh nhân', 576, 21, 49, 22),
            ('Sữa', 61, 3.2, 3.3, 4.8),
            ('Bánh mì', 265, 9, 3.3, 49),
            ('Cà chua', 18, 0.9, 0.2, 3.9),
            ('Rau xanh', 23, 2.9, 0.4, 3.6),
            ('Thịt bò', 250, 26, 15, 0),
            ('Mật ong', 304, 0.3, 0, 82),
        ]
        
        food_ids = []
        for food in foods:
            sql = '''INSERT INTO foods 
                    (food_name, calories_kcal, protein_g, fat_g, carb_g) 
                    VALUES (%s, %s, %s, %s, %s)'''
            cursor.execute(sql, food)
            food_ids.append(cursor.lastrowid)
        
        # Sample recipes
        recipes = [
            ('Salad Ức Gà', 2, 350),
            ('Cơm Gà Rang', 1, 450),
            ('Cá Hồi Nướng với Khoai Tây', 1, 520),
            ('Trứng Cuộn Rau', 1, 280),
            ('Yến Mạch Sữa với Chuối', 1, 320),
        ]
        
        recipe_ids = []
        for recipe in recipes:
            sql = '''INSERT INTO recipes 
                    (recipe_name, total_servings, total_calories_kcal) 
                    VALUES (%s, %s, %s)'''
            cursor.execute(sql, recipe)
            recipe_ids.append(cursor.lastrowid)
        
        # Sample recipe ingredients
        recipe_ingredients = [
            # Salad Ức Gà (Recipe 1)
            (recipe_ids[0], food_ids[0], 200),  # Ức gà 200g
            (recipe_ids[0], food_ids[3], 15),   # Dầu thực vật 15g
            (recipe_ids[0], food_ids[4], 150),  # Bông cải xanh 150g
            (recipe_ids[0], food_ids[12], 100), # Cà chua 100g
            # Cơm Gà Rang (Recipe 2)
            (recipe_ids[1], food_ids[0], 200),  # Ức gà 200g
            (recipe_ids[1], food_ids[1], 300),  # Cơm trắng 300g
            (recipe_ids[1], food_ids[3], 20),   # Dầu thực vật 20g
            # Cá Hồi Nướng với Khoai Tây (Recipe 3)
            (recipe_ids[2], food_ids[6], 200),  # Cá hồi 200g
            (recipe_ids[2], food_ids[2], 200),  # Khoai tây 200g
            (recipe_ids[2], food_ids[4], 150),  # Bông cải xanh 150g
            # Trứng Cuộn Rau (Recipe 4)
            (recipe_ids[3], food_ids[5], 150),  # Trứng luộc 150g
            (recipe_ids[3], food_ids[13], 100), # Rau xanh 100g
            (recipe_ids[3], food_ids[3], 10),   # Dầu thực vật 10g
            # Yến Mạch Sữa với Chuối (Recipe 5)
            (recipe_ids[4], food_ids[7], 50),   # Yến mạch 50g
            (recipe_ids[4], food_ids[10], 200), # Sữa 200ml
            (recipe_ids[4], food_ids[8], 100),  # Chuối 100g
            (recipe_ids[4], food_ids[15], 15),  # Mật ong 15g
        ]
        
        for ingredient in recipe_ingredients:
            sql = '''INSERT INTO recipe_ingredients 
                    (recipe_id, food_id, quantity_g) 
                    VALUES (%s, %s, %s)'''
            cursor.execute(sql, ingredient)
        
        connection.commit()
        print("✅ Calories data seeded successfully!")
        cursor.close()
        
    except Error as error:
        print(f"❌ Error seeding calories data: {str(error)}")
        raise error
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    seed_calorie_data()
