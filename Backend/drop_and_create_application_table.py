from app.database import engine, Base
from app.models.application import Application

# Drop just the `applications` table
Application.__table__.drop(engine)

# Recreate the `applications` table with updated schema
Base.metadata.create_all(bind=engine, tables=[Application.__table__])

print("✅ Applications table dropped and recreated successfully.")
