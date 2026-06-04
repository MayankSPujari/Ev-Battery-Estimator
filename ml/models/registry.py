import os
import joblib
from configs.config import settings
from ml.utils import ml_logger

class ModelRegistry:
    """Enterprise model registry for loading and tracking cached artifacts."""
    _models = {}

    @classmethod
    def load_model(cls, model_id: str, path: str, model_class):
        """Lazy load a model and cache it in memory."""
        if model_id not in cls._models:
            ml_logger.info(f"Loading {model_id} from {path}...")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model artifact not found at {path}. Have you run scripts/train_models.py?")
            instance = model_class()
            instance.load(path)
            cls._models[model_id] = instance
        return cls._models[model_id]

    @classmethod
    def get_regressor(cls):
        from ml.models.regressor import EVRangeRegressor
        return cls.load_model("regressor", settings.REGRESSOR_MODEL_PATH, EVRangeRegressor)

    @classmethod
    def get_forecaster(cls):
        from ml.forecasting.forecaster import BatteryDegradationForecaster
        return cls.load_model("forecaster", settings.FORECASTER_MODEL_PATH, BatteryDegradationForecaster)
