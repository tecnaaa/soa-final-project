"""
Centralized Seed Manager
Orchestrates all database seeding with proper error handling and lock mechanism
Ensures seeds run only once across all services
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add paths
seeds_path = str(Path(__file__).parent)
if seeds_path not in sys.path:
    sys.path.insert(0, seeds_path)

backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import seed functions
from seed_users import seed_users_data
from seed_workout import seed_workout_data
from seed_nutrition import seed_nutrition_data
from seed_calorie import seed_calorie_data
from seed_payment import seed_payment_data


class SeedLock:
    """
    Simple lock mechanism using database to prevent concurrent seeding
    """
    def __init__(self, db_host='localhost', db_user='root', db_password='password'):
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.lock_acquired = False
    
    def acquire_lock(self, timeout=60):
        """Try to acquire lock with timeout"""
        import mysql.connector
        from mysql.connector import Error
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                connection = mysql.connector.connect(
                    host=self.db_host,
                    user=self.db_user,
                    password=self.db_password
                )
                cursor = connection.cursor()
                
                # Create seeds metadata database if not exists
                cursor.execute("""
                    CREATE DATABASE IF NOT EXISTS seeds_metadata
                    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                
                # Create lock table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS seeds_metadata.seed_lock (
                        id INT PRIMARY KEY DEFAULT 1,
                        locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        locked_by VARCHAR(255),
                        UNIQUE KEY unique_lock (id)
                    )
                """)
                
                # Try to insert lock record (will fail if already locked)
                try:
                    cursor.execute("""
                        INSERT INTO seeds_metadata.seed_lock (id, locked_by)
                        VALUES (1, %s)
                    """, (os.getenv('HOSTNAME', 'unknown'),))
                    connection.commit()
                    self.lock_acquired = True
                    logger.info("✅ Seed lock acquired")
                    cursor.close()
                    connection.close()
                    return True
                except:
                    # Lock already exists, check if it's stale
                    cursor.execute("""
                        SELECT locked_at FROM seeds_metadata.seed_lock WHERE id = 1
                    """)
                    result = cursor.fetchone()
                    if result:
                        lock_time = result[0]
                        elapsed = (datetime.now() - lock_time).total_seconds()
                        
                        # If lock is older than 5 minutes, assume it's stale
                        if elapsed > 300:
                            logger.warning("⚠️  Stale lock detected, forcing lock release")
                            cursor.execute("DELETE FROM seeds_metadata.seed_lock WHERE id = 1")
                            cursor.execute("""
                                INSERT INTO seeds_metadata.seed_lock (id, locked_by)
                                VALUES (1, %s)
                            """, (os.getenv('HOSTNAME', 'unknown'),))
                            connection.commit()
                            self.lock_acquired = True
                            logger.info("✅ Stale lock released, new lock acquired")
                            cursor.close()
                            connection.close()
                            return True
                    
                    cursor.close()
                    connection.close()
                    logger.info(f"⏳ Seed lock is held by another process, waiting... ({int(time.time() - start_time)}s/{timeout}s)")
                    time.sleep(5)
                    
            except Exception as e:
                logger.warning(f"⚠️  Failed to acquire lock: {str(e)}, retrying...")
                time.sleep(5)
        
        return False
    
    def release_lock(self):
        """Release the lock"""
        if not self.lock_acquired:
            return
        
        try:
            import mysql.connector
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password
            )
            cursor = connection.cursor()
            cursor.execute("DELETE FROM seeds_metadata.seed_lock WHERE id = 1")
            connection.commit()
            cursor.close()
            connection.close()
            logger.info("✅ Seed lock released")
        except Exception as e:
            logger.error(f"❌ Error releasing lock: {str(e)}")


class SeedManager:
    """
    Manages all database seeding operations
    """
    
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_user = os.getenv('DB_USER', 'root')
        self.db_password = os.getenv('DB_PASSWORD', 'password')
        self.lock = SeedLock(self.db_host, self.db_user, self.db_password)
        self.results: Dict[str, Tuple[bool, str]] = {}
    
    def wait_for_db(self, timeout=120):
        """Wait for MySQL database to be ready"""
        import mysql.connector
        from mysql.connector import Error
        
        logger.info("⏳ Waiting for MySQL database to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                connection = mysql.connector.connect(
                    host=self.db_host,
                    user=self.db_user,
                    password=self.db_password
                )
                connection.close()
                logger.info("✅ MySQL database is ready!")
                return True
            except Error as e:
                elapsed = int(time.time() - start_time)
                logger.info(f"⏳ MySQL not ready yet ({elapsed}s/{timeout}s): {str(e)}")
                time.sleep(5)
        
        logger.error(f"❌ Timeout waiting for MySQL after {timeout}s")
        return False
    
    def wait_for_db_schemas(self, timeout=60):
        """Wait for all database schemas to be created"""
        import mysql.connector
        from mysql.connector import Error
        
        required_dbs = ['users_db', 'workout_db', 'nutrition_db', 'calories_db', 'payment_db']
        logger.info(f"⏳ Waiting for database schemas to be created: {required_dbs}")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                connection = mysql.connector.connect(
                    host=self.db_host,
                    user=self.db_user,
                    password=self.db_password
                )
                cursor = connection.cursor()
                cursor.execute("SHOW DATABASES")
                existing_dbs = [db[0] for db in cursor.fetchall()]
                cursor.close()
                connection.close()
                
                missing_dbs = [db for db in required_dbs if db not in existing_dbs]
                
                if not missing_dbs:
                    logger.info(f"✅ All database schemas are ready!")
                    return True
                
                elapsed = int(time.time() - start_time)
                logger.info(f"⏳ Waiting for schemas ({elapsed}s/{timeout}s): {missing_dbs}")
                time.sleep(3)
                
            except Exception as e:
                logger.warning(f"⚠️  Error checking schemas: {str(e)}")
                time.sleep(3)
        
        logger.error(f"❌ Timeout waiting for schemas after {timeout}s")
        return False
    
    def run_seed(self, name: str, seed_func) -> Tuple[bool, str]:
        """Run a single seed function with error handling"""
        try:
            logger.info(f"🌱 Running seed: {name}")
            seed_func()
            logger.info(f"✅ Seed completed: {name}")
            return (True, f"Seed {name} completed successfully")
        except Exception as e:
            logger.error(f"❌ Seed failed: {name} - {str(e)}", exc_info=True)
            return (False, f"Seed {name} failed: {str(e)}")
    
    def run_all_seeds(self) -> bool:
        """
        Run all database seeds in sequence with proper ordering
        Returns True if all seeds completed (regardless of success)
        """
        
        print("\n" + "="*70)
        print("🌱 STARTING CENTRALIZED DATABASE SEEDING MANAGER")
        print("="*70 + "\n")
        
        # Step 1: Wait for database to be ready
        if not self.wait_for_db():
            logger.error("❌ Database is not ready, cannot proceed with seeding")
            return False
        
        # Step 2: Wait for schemas to be created
        if not self.wait_for_db_schemas():
            logger.error("❌ Database schemas are not ready, cannot proceed with seeding")
            return False
        
        # Step 3: Acquire lock to prevent concurrent seeding
        if not self.lock.acquire_lock():
            logger.error("❌ Could not acquire seed lock, another process might be seeding")
            return False
        
        try:
            # Step 4: Run seeds in sequence (respecting dependencies)
            seeds = [
                ("Users", seed_users_data),
                ("Workout", seed_workout_data),
                ("Nutrition", seed_nutrition_data),
                ("Calories", seed_calorie_data),
                ("Payment", seed_payment_data),
            ]
            
            success_count = 0
            for name, seed_func in seeds:
                success, message = self.run_seed(name, seed_func)
                self.results[name] = (success, message)
                if success:
                    success_count += 1
            
            # Step 5: Print summary
            print("\n" + "="*70)
            print("📊 SEEDING SUMMARY")
            print("="*70)
            for name, (success, message) in self.results.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"{status}: {message}")
            
            print("\n" + "="*70)
            if success_count == len(seeds):
                print(f"✅ ALL SEEDS COMPLETED SUCCESSFULLY ({success_count}/{len(seeds)})")
            else:
                print(f"⚠️  PARTIAL SUCCESS: {success_count}/{len(seeds)} seeds completed")
            print("="*70 + "\n")
            
            return True
            
        finally:
            # Always release lock
            self.lock.release_lock()


def run_seeds():
    """
    Main entry point for seed manager
    Can be called from Docker entrypoint or CLI
    """
    manager = SeedManager()
    try:
        manager.run_all_seeds()
        return 0
    except Exception as e:
        logger.error(f"❌ Critical error in seed manager: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = run_seeds()
    sys.exit(exit_code)
