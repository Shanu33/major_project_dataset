# SECURITY NOTE: The PostgreSQL user provided in DATABASE_URL MUST NOT be a SUPERUSER in production.
# Provide a least-privilege role that only has access to its own database.
# Triggers execute securely without needing superuser.
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
