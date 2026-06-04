import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor

class EVRangeRegressor:
    """EV Range Estimator using Random Forest Regressor."""
    
    def __init__(self):
        self.models = {
            'random_forest': Pipeline([
                ('scaler', StandardScaler()),
                ('model', RandomForestRegressor(n_estimators=100, max_depth=10, n_jobs=-1))
            ])
        }
        self.feature_cols = []
        self.trained = False
        self.metrics = {}
        self.feature_importance = {}

    def train(self, df: pd.DataFrame):
        X = df.drop(columns=['actual_range_km'])
        y = df['actual_range_km']
        self.feature_cols = list(X.columns)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        for name, pipeline in self.models.items():
            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_test)
            
            self.metrics[name] = {
                'mae': round(mean_absolute_error(y_test, preds), 2),
                'rmse': round(root_mean_squared_error(y_test, preds), 2),
                'r2': round(r2_score(y_test, preds), 4)
            }
            
            # Feature importance for tree models
            model_step = pipeline.named_steps['model']
            if hasattr(model_step, 'feature_importances_'):
                importances = model_step.feature_importances_
                self.feature_importance[name] = dict(zip(self.feature_cols, [round(float(x), 4) for x in importances]))
            
        self.trained = True
        return self.metrics

    def predict(self, features: dict, model_name: str = 'random_forest') -> dict:
        if not self.trained:
            raise RuntimeError("Models must be trained or loaded before prediction.")
        if model_name not in self.models:
            model_name = 'random_forest'

        features_copy = features.copy()
        if 'interaction_temp_age' in self.feature_cols and 'interaction_temp_age' not in features_copy:
            features_copy['interaction_temp_age'] = features_copy['temperature_c'] * (features_copy['battery_age_cycles'] / 1000)
        if 'interaction_payload_grade' in self.feature_cols and 'interaction_payload_grade' not in features_copy:
            features_copy['interaction_payload_grade'] = (features_copy['payload_kg'] / 100) * features_copy['terrain_grade_pct']

        df_input = pd.DataFrame([features_copy])[self.feature_cols]
        pipeline = self.models[model_name]
        prediction = pipeline.predict(df_input)[0]

        return {
            "model_used": model_name,
            "predicted_range_km": round(float(prediction), 2)
        }
        
    def explain_prediction(self, features: dict, model_name: str = 'random_forest') -> dict:
        """Generates local SHAP explanations for the specific prediction."""
        import shap
        if model_name not in self.models:
            model_name = 'random_forest'
            
        features_copy = features.copy()
        if 'interaction_temp_age' in self.feature_cols and 'interaction_temp_age' not in features_copy:
            features_copy['interaction_temp_age'] = features_copy['temperature_c'] * (features_copy['battery_age_cycles'] / 1000)
        if 'interaction_payload_grade' in self.feature_cols and 'interaction_payload_grade' not in features_copy:
            features_copy['interaction_payload_grade'] = (features_copy['payload_kg'] / 100) * features_copy['terrain_grade_pct']

        df_input = pd.DataFrame([features_copy])[self.feature_cols]
        pipeline = self.models[model_name]
        
        # Apply scaling
        scaler = pipeline.named_steps['scaler']
        scaled_input = scaler.transform(df_input)
        
        model_step = pipeline.named_steps['model']
        
        # Compute exact SHAP values
        explainer = shap.TreeExplainer(model_step)
        shap_values = explainer.shap_values(scaled_input)
        expected_value = explainer.expected_value
        
        # Format output
        contributions = {feat: float(val) for feat, val in zip(self.feature_cols, shap_values[0])}
        
        return {
            "base_value": float(expected_value if not isinstance(expected_value, list) else expected_value[0]),
            "contributions": contributions
        }

    def predict_all(self, features: dict) -> dict:
        return {name: self.predict(features, name)["predicted_range_km"] for name in self.models}

    def save(self, filepath: str):
        state = {
            'models': self.models,
            'feature_cols': self.feature_cols,
            'trained': self.trained,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }
        joblib.dump(state, filepath)

    def load(self, filepath: str):
        state = joblib.load(filepath)
        self.models = state['models']
        self.feature_cols = state['feature_cols']
        self.trained = state['trained']
        self.metrics = state['metrics']
        self.feature_importance = state['feature_importance']
