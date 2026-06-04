import numpy as np
import pandas as pd
from ml.utils import ml_logger

def generate_ev_dataset(n_samples: int = 5000) -> pd.DataFrame:
    """Generates synthetic EV dataset with enhanced feature engineering."""
    np.random.seed(42)
    
    # Base features: Expanded to support 2-wheelers (2-10 kWh) and cars (30-150 kWh)
    battery_capacity_kwh = np.random.uniform(2, 150, n_samples)
    temperature_c = np.random.uniform(-20, 40, n_samples)
    speed_kmh = np.random.uniform(10, 130, n_samples)
    payload_kg = np.random.uniform(0, 800, n_samples)
    hvac_kw = np.where(temperature_c < 10, np.random.uniform(1, 5, n_samples),
                       np.where(temperature_c > 25, np.random.uniform(1, 4, n_samples),
                                np.random.uniform(0, 1, n_samples)))
    battery_age_cycles = np.random.randint(0, 2000, n_samples)
    soc_pct = np.random.uniform(10, 100, n_samples)
    terrain_grade_pct = np.random.uniform(-5, 5, n_samples)
    wind_speed_kmh = np.random.uniform(0, 40, n_samples)

    # Feature Engineering (Interaction Terms)
    degradation_factor = 1.0 - (battery_age_cycles / 5000) * 0.2
    temp_efficiency = np.where(temperature_c < 0, 0.7, 
                               np.where(temperature_c > 35, 0.85, 1.0))
    aero_drag = 0.5 * (speed_kmh / 100) ** 2 + 0.1 * (wind_speed_kmh / 50)
    
    # Calculate Range
    base_range = (battery_capacity_kwh * 6.5) * (soc_pct / 100.0)
    actual_range = base_range * degradation_factor * temp_efficiency
    
    # Reductions
    actual_range -= aero_drag * 15
    actual_range -= (payload_kg / 100) * 2.5
    actual_range -= hvac_kw * 4.0
    actual_range -= terrain_grade_pct * 3.0
    
    # Ensure positive
    actual_range = np.maximum(actual_range, 5.0)

    # Add Gaussian noise
    actual_range += np.random.normal(0, 3.0, n_samples)

    df = pd.DataFrame({
        'battery_capacity_kwh': battery_capacity_kwh,
        'temperature_c': temperature_c,
        'speed_kmh': speed_kmh,
        'payload_kg': payload_kg,
        'hvac_kw': hvac_kw,
        'battery_age_cycles': battery_age_cycles,
        'soc_pct': soc_pct,
        'terrain_grade_pct': terrain_grade_pct,
        'wind_speed_kmh': wind_speed_kmh,
        'interaction_temp_age': temperature_c * (battery_age_cycles / 1000),
        'interaction_payload_grade': (payload_kg / 100) * terrain_grade_pct,
        'actual_range_km': actual_range
    })
    
    ml_logger.info(f"Generated {n_samples} synthetic EV samples with enhanced interactions.")
    return df
