"""
Application configuration using Pydantic settings.
Enhanced for FitGen AI with ML support.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "nutrix"  # Changed from "nutrix" for clarity
    MONGO_TIMEOUT_MS: int = 5000
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "fitgen_ai.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # ML Model Configuration
    ML_MODELS_DIR: str = "models"
    ML_INSIGHTS_DIR: str = "insights"
    ML_TRAINING_DATA_MIN_SESSIONS: int = 10
    ML_RETRAIN_FREQUENCY_DAYS: int = 7
    
    # Workout Generation Settings
    MIN_WORKOUT_DURATION: int = 15  # minutes
    MAX_WORKOUT_DURATION: int = 120  # minutes
    DEFAULT_REST_BETWEEN_SETS: int = 60  # seconds
    
    # Safety Settings
    MAX_VOLUME_INCREASE_PER_WEEK: float = 0.15  # 15% max increase
    DELOAD_FREQUENCY_WEEKS: int = 4
    HIGH_RPE_THRESHOLD: float = 8.5
    
    # Analytics Settings
    ANALYTICS_RETENTION_DAYS: int = 365
    TREND_ANALYSIS_MIN_SESSIONS: int = 5
    PLATEAU_DETECTION_WEEKS: int = 3
    
    # Export Settings
    EXPORT_DIR: str = "exports"
    EXPORT_FORMATS: list = ["csv", "json", "txt"]
    
    # Cache Settings (for future optimization)
    CACHE_ENABLED: bool = False
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Feature Flags (for gradual rollout)
    ENABLE_ML_FEATURES: bool = True
    ENABLE_EXERCISE_RECOMMENDATIONS: bool = True
    ENABLE_INJURY_PREDICTION: bool = True
    ENABLE_PLATEAU_DETECTION: bool = True
    ENABLE_VISUALIZATIONS: bool = True
    
    # Rate Limiting (for API - future use)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Data Validation
    BMI_MIN: float = 10.0
    BMI_MAX: float = 60.0
    AGE_MIN: int = 13
    AGE_MAX: int = 100
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 30
    AUTO_LOGOUT_ENABLED: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # Allow extra fields in case of environment variables
        extra = "ignore"


# Create settings instance
settings = Settings()


# Create necessary directories on import
def _ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        settings.ML_MODELS_DIR,
        settings.ML_INSIGHTS_DIR,
        settings.EXPORT_DIR,
        "logs"  # For log files
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Initialize directories
_ensure_directories()
