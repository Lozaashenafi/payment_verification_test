from db.database import engine, Base
# It is very important to import your models here, 
# otherwise SQLAlchemy won't know they exist!
from db import models 

def init_database():
    print("⏳ Connecting to PostgreSQL...")
    try:
        # This command looks at all classes inheriting from 'Base' 
        # and creates the corresponding tables in Postgres.
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Failed to create tables. Error: {e}")

if __name__ == "__main__":
    init_database()