"""
Configuration Management for NutriX API
Loads configuration from environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "nutrix_db"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_TITLE: str = "NutriX API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-Powered Personalized Fitness Application API"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/nutrix.log"
    
    # Model Configuration
    MODEL_RETRAIN_THRESHOLD: int = 5
    
    # Validation Limits
    MIN_AGE: int = 10
    MAX_AGE: int = 100
    MIN_HEIGHT: float = 100.0
    MAX_HEIGHT: float = 250.0
    MIN_WEIGHT: float = 30.0
    MAX_WEIGHT: float = 300.0
    
    # Fitness Levels
    FITNESS_LEVELS: list = ["Beginner", "Intermediate", "Advanced", "Expert"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
