"""
Database Migration Script
Creates all new tables and updates existing ones
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./goodrunss.db")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_migration():
    """Run database migration"""
    print("🔄 Starting database migration...")
    
    try:
        # Create all tables using the models
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created/updated successfully")
        
        # Add any specific migrations here
        with engine.connect() as connection:
            # Add stripe_connect_id to users table if it doesn't exist
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN stripe_connect_id VARCHAR;
                """))
                print("✅ Added stripe_connect_id to users table")
            except Exception as e:
                print(f"ℹ️ stripe_connect_id column already exists: {e}")
            
            # Add location fields to users table if they don't exist
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN latitude FLOAT;
                """))
                print("✅ Added latitude to users table")
            except Exception as e:
                print(f"ℹ️ latitude column already exists: {e}")
                
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN longitude FLOAT;
                """))
                print("✅ Added longitude to users table")
            except Exception as e:
                print(f"ℹ️ longitude column already exists: {e}")
                
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN address VARCHAR;
                """))
                print("✅ Added address to users table")
            except Exception as e:
                print(f"ℹ️ address column already exists: {e}")
            
            # Add Snapchat fields to users table if they don't exist
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN snapchat_id VARCHAR;
                """))
                print("✅ Added snapchat_id to users table")
            except Exception as e:
                print(f"ℹ️ snapchat_id column already exists: {e}")
                
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN snapchat_access_token TEXT;
                """))
                print("✅ Added snapchat_access_token to users table")
            except Exception as e:
                print(f"ℹ️ snapchat_access_token column already exists: {e}")
            
            # Add TikTok fields to users table if they don't exist
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN tiktok_id VARCHAR;
                """))
                print("✅ Added tiktok_id to users table")
            except Exception as e:
                print(f"ℹ️ tiktok_id column already exists: {e}")
                
            try:
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN tiktok_access_token TEXT;
                """))
                print("✅ Added tiktok_access_token to users table")
            except Exception as e:
                print(f"ℹ️ tiktok_access_token column already exists: {e}")
        
        print("🎉 Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()