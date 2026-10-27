from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./cv_align.db"  

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    from app.models import user, job, application, profile  # Import all models here
    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def _ensure_columns():
    """Add newly-introduced columns to existing SQLite tables.

    create_all() only creates missing tables, not missing columns, so this
    applies lightweight ALTER TABLEs for columns added after a DB was created.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "jobs" in inspector.get_table_names():
        job_columns = [c["name"] for c in inspector.get_columns("jobs")]
        if "is_open" not in job_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN is_open BOOLEAN DEFAULT 1"))