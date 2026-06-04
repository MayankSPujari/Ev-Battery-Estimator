import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import joblib

class BatteryDegradationForecaster:
    """
    Forecasts battery capacity over future charge cycles
    using an exponential decay + seasonal (temperature) model,
    plus a simple autoregressive sklearn layer.
    """

    def __init__(self):
        self.model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.fitted = False

    def save(self, filepath: str):
        if not self.fitted:
            raise RuntimeError("Cannot save an unfitted model.")
        state = {
            'model': self.model,
            'scaler': self.scaler,
            'fitted': self.fitted
        }
        joblib.dump(state, filepath)

    def load(self, filepath: str):
        state = joblib.load(filepath)
        self.model = state['model']
        self.scaler = state['scaler']
        self.fitted = state['fitted']

    def _generate_degradation_series(
        self, initial_capacity_kwh: float, total_cycles: int = 2000,
        avg_temp: float = 20.0, seed: int = 0
    ) -> pd.DataFrame:
        """Simulate capacity fade over charge cycles."""
        rng = np.random.default_rng(seed)
        cycles = np.arange(total_cycles)

        # Exponential capacity fade (SEI layer growth)
        alpha = 0.00003 + 0.000005 * max(0, avg_temp - 25)  # faster at high temp
        capacity = initial_capacity_kwh * np.exp(-alpha * cycles)

        # Add measurement noise
        noise = rng.normal(0, 0.05, total_cycles)
        capacity = np.clip(capacity + noise, 0, initial_capacity_kwh)

        # SOH = State of Health
        soh = (capacity / initial_capacity_kwh) * 100

        df = pd.DataFrame({'cycle': cycles, 'capacity_kwh': capacity, 'soh_pct': soh})
        return df

    def fit(self, initial_capacity_kwh: float = 75.0, avg_temp: float = 20.0):
        """Fit the autoregressive model on generic historical data to initialize the scaler and model coefficients."""
        history = self._generate_degradation_series(initial_capacity_kwh, total_cycles=500, avg_temp=avg_temp)
        window = 20
        lags = pd.DataFrame({
            f'lag_{i}': history['capacity_kwh'].shift(i) for i in range(1, window + 1)
        })
        lags['target'] = history['capacity_kwh']
        lags = lags.dropna()

        X_train = self.scaler.fit_transform(lags.drop('target', axis=1))
        y_train = lags['target'].values
        self.model.fit(X_train, y_train)
        self.fitted = True

    def forecast(
        self,
        initial_capacity_kwh: float,
        current_cycles: int,
        forecast_cycles: int = 500,
        avg_temp: float = 20.0,
    ) -> dict:
        """Forecast future capacity given current state."""
        # Generate historical series up to current
        history = self._generate_degradation_series(
            initial_capacity_kwh, total_cycles=max(current_cycles + 1, 100),
            avg_temp=avg_temp
        )

        window = 20
        if len(history) < window + 1:
            history = self._generate_degradation_series(
                initial_capacity_kwh, total_cycles=window + 50, avg_temp=avg_temp
            )

        if not self.fitted:
            # Fit on the fly if not fitted (legacy behavior fallback)
            lags = pd.DataFrame({
                f'lag_{i}': history['capacity_kwh'].shift(i) for i in range(1, window + 1)
            })
            lags['target'] = history['capacity_kwh']
            lags = lags.dropna()
            X_train = self.scaler.fit_transform(lags.drop('target', axis=1))
            y_train = lags['target'].values
            self.model.fit(X_train, y_train)
            self.fitted = True

        # Autoregressive forecast
        seed_window = history['capacity_kwh'].values[-window:].tolist()
        future_capacity = []
        for _ in range(forecast_cycles):
            x = self.scaler.transform([seed_window])
            pred = float(self.model.predict(x)[0])
            pred = max(0, pred)
            future_capacity.append(pred)
            seed_window = seed_window[1:] + [pred]

        future_cycles = list(range(current_cycles, current_cycles + forecast_cycles))
        future_soh    = [(c / initial_capacity_kwh) * 100 for c in future_capacity]

        # Find EOL (End-of-Life) at 70% SOH
        eol_cycle = None
        for i, soh in enumerate(future_soh):
            if soh < 70.0:
                eol_cycle = future_cycles[i]
                break

        return {
            'history': {
                'cycles':       history['cycle'].tolist(),
                'capacity_kwh': [round(c, 3) for c in history['capacity_kwh'].tolist()],
                'soh_pct':      [round(s, 2) for s in history['soh_pct'].tolist()],
            },
            'forecast': {
                'cycles':       future_cycles,
                'capacity_kwh': [round(c, 3) for c in future_capacity],
                'soh_pct':      [round(s, 2) for s in future_soh],
            },
            'eol_cycle':           eol_cycle,
            'current_soh_pct':     round(float((history['capacity_kwh'].iloc[-1] / initial_capacity_kwh) * 100), 2),
            'current_capacity_kwh': round(float(history['capacity_kwh'].iloc[-1]), 3),
        }
