import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cv_align.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 120}
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
    from app.models import user, job, application, profile, password_reset  # Import all models here
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
    if "users" in inspector.get_table_names():
        if "auth_version" not in {c["name"] for c in inspector.get_columns("users")}:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 0"))
    # Preserve older duplicates while enforcing uniqueness for every new write.
    if "applications" in inspector.get_table_names():
        with engine.begin() as conn:
            duplicates = conn.execute(text("SELECT 1 FROM applications GROUP BY user_id, job_id HAVING COUNT(*) > 1 LIMIT 1")).first()
            if not duplicates:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_application_user_job ON applications(user_id, job_id)"))
            else:
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS applications_unique_insert
                    BEFORE INSERT ON applications
                    WHEN EXISTS (
                        SELECT 1 FROM applications
                        WHERE user_id = NEW.user_id AND job_id = NEW.job_id
                    )
                    BEGIN
                        SELECT RAISE(ABORT, 'Duplicate application');
                    END
                """))
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS applications_unique_update
                    BEFORE UPDATE OF user_id, job_id ON applications
                    WHEN EXISTS (
                        SELECT 1 FROM applications
                        WHERE user_id = NEW.user_id AND job_id = NEW.job_id AND id != NEW.id
                    )
                    BEGIN
                        SELECT RAISE(ABORT, 'Duplicate application');
                    END
                """))


def lock_job(db):
    """Serialize applying and closing against the same SQLite database."""
    from sqlalchemy import text
    # All callers invoke this before their first read in the route's session.
    db.execute(text("BEGIN IMMEDIATE"))
