from ml.models.regressor import EVRangeRegressor

def analyze_scenarios(regressor: EVRangeRegressor, base_features: dict) -> dict:
    """Run 'what-if' scenarios by varying one factor at a time."""
    scenarios = {}

    # Temperature sweep
    temps = list(range(-20, 46, 5))
    temp_ranges = []
    for t in temps:
        f = {**base_features, 'temperature_c': t}
        temp_ranges.append(regressor.predict(f)['predicted_range_km'])
    scenarios['temperature_sweep'] = {'temperatures': temps, 'ranges': temp_ranges}

    # Speed sweep
    speeds = list(range(20, 131, 10))
    speed_ranges = []
    for s in speeds:
        f = {**base_features, 'speed_kmh': s}
        speed_ranges.append(regressor.predict(f)['predicted_range_km'])
    scenarios['speed_sweep'] = {'speeds': speeds, 'ranges': speed_ranges}

    # SOC sweep
    socs = list(range(20, 101, 5))
    soc_ranges = []
    for soc in socs:
        f = {**base_features, 'soc_pct': soc}
        soc_ranges.append(regressor.predict(f)['predicted_range_km'])
    scenarios['soc_sweep'] = {'soc_pcts': socs, 'ranges': soc_ranges}

    return scenarios
