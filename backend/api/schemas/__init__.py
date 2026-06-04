from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    temperature_c:         float = Field(20.0,  ge=-30, le=55,   description="Ambient temperature °C")
    speed_kmh:             float = Field(80.0,  ge=0,   le=200,  description="Average speed km/h")
    payload_kg:            float = Field(0.0,   ge=0,   le=1000, description="Extra payload kg")
    hvac_kw:               float = Field(1.0,   ge=0,   le=10,   description="HVAC power draw kW")
    battery_age_cycles:    int   = Field(100,   ge=0,   le=3000, description="Charge cycles completed")
    soc_pct:               float = Field(80.0,  ge=1,   le=100,  description="State of charge %")
    terrain_grade_pct:     float = Field(0.0,   ge=-15, le=15,   description="Road grade %")
    wind_speed_kmh:        float = Field(0.0,   ge=0,   le=100,  description="Headwind km/h")
    battery_capacity_kwh:  float = Field(75.0,  ge=10,  le=200,  description="Nominal battery capacity kWh")
    model_name:            str   = Field("random_forest", description="ML model to use")


class ForecastRequest(BaseModel):
    initial_capacity_kwh: float = Field(75.0, ge=10, le=200)
    current_cycles:       int   = Field(500,  ge=0,  le=3000)
    forecast_cycles:      int   = Field(500,  ge=50, le=2000)
    avg_temp_c:           float = Field(20.0, ge=-20, le=50)
