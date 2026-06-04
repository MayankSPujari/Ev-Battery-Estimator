from ml.models.registry import ModelRegistry
from ml.analytics.analyzer import analyze_scenarios
from ml.preprocessing.data_gen import generate_ev_dataset
from ml.utils import ml_logger

class MLEngineService:
    @staticmethod
    def get_metrics() -> dict:
        reg = ModelRegistry.get_regressor()
        return {
            "metrics": reg.metrics,
            "feature_importance": reg.feature_importance,
            "dataset_size": 5000,
            "feature_columns": reg.feature_cols,
        }

    @staticmethod
    def predict_range(features: dict, model_name: str) -> dict:
        import sqlite3
        import json
        from datetime import datetime
        
        reg = ModelRegistry.get_regressor()
        if model_name not in reg.models:
            raise ValueError(f"Unknown model: {model_name}. Choose from {list(reg.models.keys())}")
        result = reg.predict(features, model_name)
        all_models = reg.predict_all(features)
        
        # Phase 5: Analytics Logging to SQLite
        try:
            conn = sqlite3.connect('analytics.db')
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS predictions
                         (timestamp TEXT, model TEXT, inputs TEXT, output REAL)''')
            c.execute("INSERT INTO predictions VALUES (?, ?, ?, ?)",
                      (datetime.now().isoformat(), model_name, json.dumps(features), result["predicted_range_km"]))
            conn.commit()
            conn.close()
            ml_logger.info("Successfully recorded prediction to analytics.db")
        except Exception as e:
            ml_logger.error(f"Failed to record analytics: {e}")

        return {
            "primary": result,
            "all_models": all_models,
            "input": features,
        }

    @staticmethod
    def analyze_scenarios(features: dict) -> dict:
        reg = ModelRegistry.get_regressor()
        return analyze_scenarios(reg, features)

    @staticmethod
    def forecast_degradation(initial_capacity_kwh: float, current_cycles: int, forecast_cycles: int, avg_temp_c: float) -> dict:
        forecaster = ModelRegistry.get_forecaster()
        return forecaster.forecast(
            initial_capacity_kwh=initial_capacity_kwh,
            current_cycles=current_cycles,
            forecast_cycles=forecast_cycles,
            avg_temp=avg_temp_c,
        )

    @staticmethod
    def get_sample_data(n: int) -> list:
        df = generate_ev_dataset(n_samples=min(n, 200))
        return df.to_dict(orient="records")
