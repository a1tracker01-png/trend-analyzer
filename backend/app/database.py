import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./roshan.db")

# Neon and cloud providers often supply URLs starting with postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLAlchemy 2.1+ defaults to psycopg (psycopg 3) for postgresql://
if DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL and "+psycopg2" not in DATABASE_URL:
    try:
        import psycopg
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        try:
            import psycopg2
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            pass

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Optimized for Neon Serverless PostgreSQL
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,  # Checks connection liveness before executing query
        "pool_recycle": 300,   # Recycle connections every 5 minutes
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def upgrade_schema_types(target_engine):
    """Safely upgrades PostgreSQL column types to TEXT to support long signed CDN URLs."""
    url_str = str(target_engine.url)
    if not url_str.startswith(("postgresql", "postgres")):
        return
    migrations = [
        "ALTER TABLE reels ALTER COLUMN permalink TYPE TEXT",
        "ALTER TABLE reels ALTER COLUMN thumbnail_url TYPE TEXT",
        "ALTER TABLE reels ALTER COLUMN video_url TYPE TEXT",
        "ALTER TABLE creators ALTER COLUMN profile_pic_url TYPE TEXT",
        "ALTER TABLE creators ALTER COLUMN profile_url TYPE TEXT",
        "ALTER TABLE creators ALTER COLUMN full_name TYPE TEXT",
        "ALTER TABLE data_sources ALTER COLUMN status_message TYPE TEXT",
        "ALTER TABLE data_sources ALTER COLUMN api_endpoint TYPE TEXT",
        "ALTER TABLE creators ADD COLUMN IF NOT EXISTS country VARCHAR(100)",
        "ALTER TABLE reels ADD COLUMN IF NOT EXISTS country VARCHAR(100)"
    ]
    with target_engine.connect() as conn:
        for q in migrations:
            try:
                conn.execute(text(q))
            except Exception:
                pass
        conn.commit()


def get_db():
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
