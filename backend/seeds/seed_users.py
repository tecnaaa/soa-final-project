"""
Seed data for Users Service
Creates sample users with different roles (user, pt, admin) for testing
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/users_db")

def seed_users_data():
    """Seed sample users to database"""
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Use synchronous engine
        db_url = DATABASE_URL
        
        # Đảm bảo chúng ta đang sử dụng driver pymysql (đồng bộ)
        if "mysql+asyncmy://" in db_url:
            db_url = db_url.replace("mysql+asyncmy://", "mysql+pymysql://")
        elif "mysql+aiomysql://" in db_url:
            db_url = db_url.replace("mysql+aiomysql://", "mysql+pymysql://")
        elif db_url.startswith("mysql://"):
            # Nếu chỉ là mysql://, SQLAlchemy có thể tự chọn driver, 
            # nhưng tốt nhất là chỉ định rõ
            db_url = db_url.replace("mysql://", "mysql+pymysql://")

        engine = create_engine(db_url, echo=False)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        print("🌱 Seeding Users Database...")
        
        # Import models
        from models.user.user_models import User, Role
        
        # Check if users already exist (excluding admin)
        user_count = session.query(User).filter(User.email != "admin@app.com").count()
        
        if user_count > 0:
            print("✅ Users already seeded, skipping...")
            session.close()
            return
        
        # Get existing roles from database
        roles = session.query(Role).all()
        role_map = {}
        
        for role in roles:
            if role.role_name == 'user':
                role_map['user'] = role.role_id
            elif role.role_name == 'pt':
                role_map['pt'] = role.role_id
            elif role.role_name == 'admin':
                role_map['admin'] = role.role_id
        
        # If roles don't exist, create them
        if not role_map:
            print("⚠️  Roles not found in database. Creating default roles...")
            
            # Create default roles
            default_roles = [
                Role(role_name='user'),
                Role(role_name='pt'),
                Role(role_name='admin')
            ]
            
            for role in default_roles:
                session.add(role)
            
            session.commit()
            
            # Get roles again
            roles = session.query(Role).all()
            for role in roles:
                if role.role_name == 'user':
                    role_map['user'] = role.role_id
                elif role.role_name == 'pt':
                    role_map['pt'] = role.role_id
                elif role.role_name == 'admin':
                    role_map['admin'] = role.role_id
            
            print("✅ Default roles created successfully")
        
        print(f"✅ Roles found: {role_map}")
        
        # Sample users data
        sample_users = [
            # Regular Users (Free Tier)
            {
                'role_id': role_map.get('user'),
                'email': 'hadgclone01@gmail.com',
                'password': 'password123',
                'first_name': 'Tuấn',
                'last_name': 'Nguyễn',
                'gender': 'nam',
                'height_cm': 180,
                'weight_kg': 75,
            },
            {
                'role_id': role_map.get('user'),
                'email': 'michael.brown@fitness.com',
                'password': 'password123',
                'first_name': 'Michael',
                'last_name': 'Brown',
                'gender': 'nam',
                'height_cm': 178,
                'weight_kg': 80,
            },
            {
                'role_id': role_map.get('user'),
                'email': 'sarah.wilson@fitness.com',
                'password': 'password123',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'gender': 'nu',
                'height_cm': 168,
                'weight_kg': 58,
            },
            {
                'role_id': role_map.get('user'),
                'email': 'john.doe@fitness.com',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                'gender': 'nam',
                'height_cm': 175,
                'weight_kg': 72,
            },
            {
                'role_id': role_map.get('user'),
                'email': 'lisa.anderson@fitness.com',
                'password': 'password123',
                'first_name': 'Lisa',
                'last_name': 'Anderson',
                'gender': 'nu',
                'height_cm': 165,
                'weight_kg': 55,
            },
            {
                'role_id': role_map.get('user'),
                'email': 'james.martin@fitness.com',
                'password': 'password123',
                'first_name': 'James',
                'last_name': 'Martin',
                'gender': 'nam',
                'height_cm': 182,
                'weight_kg': 85,
            },
            {
                'role_id': role_map.get('user'),
                'email': 'emily.taylor@fitness.com',
                'password': 'password123',
                'first_name': 'Emily',
                'last_name': 'Taylor',
                'gender': 'nu',
                'height_cm': 170,
                'weight_kg': 62,
            },
            # Personal Trainers
            {
                'role_id': role_map.get('pt'),
                'email': 'giabao14022005@gmail.com',
                'password': 'password123',
                'first_name': 'Alex',
                'last_name': 'Johnson',
                'gender': 'nam',
                'height_cm': 185,
                'weight_kg': 85,
            },
            {
                'role_id': role_map.get('pt'),
                'email': 'trainer.emma@fitness.com',
                'password': 'password123',
                'first_name': 'Emma',
                'last_name': 'Williams',
                'gender': 'nu',
                'height_cm': 170,
                'weight_kg': 62,
            },
            {
                'role_id': role_map.get('pt'),
                'email': 'coach.david@fitness.com',
                'password': 'password123',
                'first_name': 'David',
                'last_name': 'Lee',
                'gender': 'nam',
                'height_cm': 188,
                'weight_kg': 90,
            },
            {
                'role_id': role_map.get('pt'),
                'email': 'trainer.sophia@fitness.com',
                'password': 'password123',
                'first_name': 'Sophia',
                'last_name': 'Garcia',
                'gender': 'nu',
                'height_cm': 172,
                'weight_kg': 65,
            },
            # Admin
            {
                'role_id': role_map.get('admin'),
                'email': 'minhkhai3105@gmail.com',
                'password': 'password123',
                'first_name': 'Admin',
                'last_name': 'System',
                'gender': 'nam',
                'height_cm': 165,
                'weight_kg': 60,
            },
        ]
        
        # Create users
        for user_data in sample_users:
            password = user_data.pop('password')
            user = User(**user_data)
            user.password_hash = User.hash_password(password)
            session.add(user)
        
        # Commit changes
        session.commit()
        print(f"✅ {len(sample_users)} Users seeded successfully!")
        print("\n📋 Seeded Users:")
        print("\n👥 Regular Users (Free Tier):")
        print("   - hadgclone01@gmail.com (password123) [USER]")
        print("   - michael.brown@fitness.com (password123) [USER]")
        print("   - sarah.wilson@fitness.com (password123) [USER]")
        print("   - john.doe@fitness.com (password123) [USER]")
        print("   - lisa.anderson@fitness.com (password123) [USER]")
        print("   - james.martin@fitness.com (password123) [USER]")
        print("   - emily.taylor@fitness.com (password123) [USER]")
        print("\n🏋️ Personal Trainers:")
        print("   - giabao14022005@gmail.com (password123) [PT]")
        print("   - trainer.emma@fitness.com (password123) [PT]")
        print("   - coach.david@fitness.com (password123) [PT]")
        print("   - trainer.sophia@fitness.com (password123) [PT]")
        print("\n🔐 Admin:")
        print("   - minhkhai3105@gmail.com (password123) [ADMIN]")
        session.close()
            
    except Exception as error:
        print(f"❌ Error seeding users: {str(error)}")
        import traceback
        traceback.print_exc()
        raise error


if __name__ == "__main__":
    seed_users_data()
