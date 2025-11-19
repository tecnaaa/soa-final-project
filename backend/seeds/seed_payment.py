"""
Seed data for Payment Service
Creates sample subscription packages
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def seed_payment_data():
    """Seed sample payment data to database"""
    
    connection = None
    try:
        # Create connection
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database='payment_db'
        )
        
        cursor = connection.cursor()
        print("🌱 Seeding Payment Database...")
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM subscriptions')
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("✅ Payment data already seeded, skipping...")
            cursor.close()
            return
        
        # Sample subscription packages
        subscriptions = [
            ('Gói 1 tháng', 99000, 30),
            ('Gói 3 tháng', 249000, 90),
            ('Gói 6 tháng', 449000, 180),
            ('Gói 1 năm', 799000, 365),
        ]
        
        for subscription in subscriptions:
            sql = '''INSERT INTO subscriptions 
                    (subscription_name, price, duration_days) 
                    VALUES (%s, %s, %s)'''
            cursor.execute(sql, subscription)
        
        connection.commit()
        print("✅ Payment data seeded successfully!")
        cursor.close()
        
    except Error as error:
        print(f"❌ Error seeding payment data: {str(error)}")
        raise error
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    seed_payment_data()
