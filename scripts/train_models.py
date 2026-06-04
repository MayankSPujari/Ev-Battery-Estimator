import os
import sys

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.config import settings
from ml.utils import ml_logger
from ml.preprocessing.data_gen import generate_ev_dataset
from ml.models.regressor import EVRangeRegressor
from ml.forecasting.forecaster import BatteryDegradationForecaster

def main():
    ml_logger.info("⚡ Starting offline model training...")

    # Ensure models directory exists
    os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)

    ml_logger.info("⚡ Generating synthetic EV dataset (5000 samples)...")
    df = generate_ev_dataset(n_samples=5000)

    ml_logger.info("⚡ Training Regressor models...")
    regressor = EVRangeRegressor()
    metrics = regressor.train(df)
    ml_logger.info(f"Regressor metrics: {metrics}")
    regressor.save(settings.REGRESSOR_MODEL_PATH)
    ml_logger.info(f"✅ Regressor models saved to {settings.REGRESSOR_MODEL_PATH}")

    ml_logger.info("⚡ Training Forecaster model...")
    forecaster = BatteryDegradationForecaster()
    forecaster.fit()
    forecaster.save(settings.FORECASTER_MODEL_PATH)
    ml_logger.info(f"✅ Forecaster model saved to {settings.FORECASTER_MODEL_PATH}")

    ml_logger.info("🎉 All models trained and saved successfully.")

if __name__ == "__main__":
    main()
