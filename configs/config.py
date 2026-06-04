import os

class Settings:
    """Basic configuration settings."""
    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ML_MODELS_DIR: str = os.path.join(PROJECT_ROOT, "ml", "saved_models")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Model filenames
    REGRESSOR_MODEL_PATH: str = os.path.join(ML_MODELS_DIR, "regressor.joblib")
    FORECASTER_MODEL_PATH: str = os.path.join(ML_MODELS_DIR, "forecaster.joblib")

settings = Settings()
