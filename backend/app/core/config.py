import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY and os.getenv("TESTING") != "1":
        raise ValueError("SECRET_KEY environment variable MUST be set in production")
    elif not SECRET_KEY:
        SECRET_KEY = "test_secret_key"
        
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    TESTING: bool = os.getenv("TESTING") == "1"
    if TESTING:
        DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://shahnawaz:password@localhost:5433/construction_intel_test")
    else:
        DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://shahnawaz:password@localhost:5433/construction_intel")

    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "/tmp/construction_docs_dev")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024))) # 50 MB
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf"]

settings = Settings()
