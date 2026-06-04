import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys
import time
import json
import requests
from streamlit_lottie import st_lottie
import time
import json

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.config import settings
from ml.preprocessing.data_gen import generate_ev_dataset
from ml.models.registry import ModelRegistry

# Load Vehicle DB
vehicles_path = os.path.join(project_root, "configs", "vehicles.json")
with open(vehicles_path, "r") as f:
    VEHICLE_DB = json.load(f)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EV Range Pro | Premium Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Cache Lottie Animations ───────────────────────────────────────────────────
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_energy = load_lottieurl("https://lottie.host/801a61b8-6f62-4217-bfbe-ccbf02ec10ee/aDXYA7W5X3.json")

# ── Custom Premium Styling ────────────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(79, 172, 254, 0.2);
    }

    /* Gradient Buttons */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        font-weight: 800;
        letter-spacing: 1px;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6);
        color: white;
    }
    
    /* Metrics Animations */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff;
        text-shadow: 0 0 10px rgba(0,242,254,0.5);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }

    /* Sidebar Tweaks */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Custom Input styling */
    .stSlider > div[data-baseweb="slider"] > div > div > div {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
    }

</style>
""", unsafe_allow_html=True)

# ── Cache models from disk ───────────────────────────────────────────────────
@st.cache_resource(show_spinner="⚡ Initializing Neural Processors...")
def load_models():
    reg = ModelRegistry.get_regressor()
    forecaster = ModelRegistry.get_forecaster()
    return reg, reg.metrics, forecaster

try:
    regressor, model_metrics, forecaster = load_models()
except Exception as e:
    st.error(f"Failed to load models. Error: {e}")
    st.stop()

# ── State Management for History ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "current_prediction" not in st.session_state:
    st.session_state.current_prediction = None

# ── Sidebar Inputs ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h1>⚙️ Telematics Grid</h1>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    model_choice = st.selectbox(
        "🧠 Inference Engine", 
        options=list(regressor.models.keys()), 
        index=list(regressor.models.keys()).index("lightgbm") if "lightgbm" in regressor.models else 0
    )

    st.markdown("---")
    st.markdown("### 🏎️ Vehicle Selector")
    
    cat_options = ["Custom"] + list(VEHICLE_DB.keys())
    selected_cat = st.selectbox("Category", cat_options)
    
    if selected_cat != "Custom":
        brand_options = list(VEHICLE_DB[selected_cat].keys())
        selected_brand = st.selectbox("Manufacturer", brand_options)
        
        model_options = list(VEHICLE_DB[selected_cat][selected_brand].keys())
        selected_model = st.selectbox("Model", model_options)
        
        # Fetch specs
        specs = VEHICLE_DB[selected_cat][selected_brand][selected_model]
        default_capacity = specs["capacity_kwh"]
        default_payload = 150.0 if selected_cat == "Cars" else 75.0
        st.success(f"Loaded specs for {selected_brand} {selected_model}")
    else:
        default_capacity = 75.0
        default_payload = 0.0
        specs = None

    st.markdown("---")
    st.markdown("### 🔋 Battery Architecture")
    battery_capacity = st.slider("Capacity (kWh)", 2.0, 150.0, float(default_capacity), 0.5)
    soc = st.slider("Charge Level (%)", 10.0, 100.0, 80.0, 1.0)
    battery_age = st.number_input("Degradation Cycles", 0, 3000, 100, 50)

    st.markdown("---")
    st.markdown("### 🌡️ Environment Physics")
    temperature = st.slider("Ambient Temp (°C)", -20.0, 40.0, 20.0, 0.5)
    speed = st.slider("Cruising Speed (km/h)", 10.0, 130.0, 80.0, 1.0)
    wind_speed = st.slider("Headwind (km/h)", 0.0, 40.0, 0.0, 1.0)
    terrain_grade = st.slider("Elevation Grade (%)", -5.0, 5.0, 0.0, 0.5)

    st.markdown("---")
    st.markdown("### ⚖️ Auxiliary Load")
    payload = st.slider("Payload Mass (kg)", 0.0, 500.0, float(default_payload), 5.0)
    hvac = st.slider("Climate Control (kW)", 0.0, 5.0, 1.0 if selected_cat == "Cars" else 0.0, 0.1)

# ── Main Content ─────────────────────────────────────────────────────────────
st.markdown("<h1>⚡ EV Nexus Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -10px;'>Next-Generation Predictive Telemetry & Range Forecasting</p>", unsafe_allow_html=True)
st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

# Create the feature dict
features = {
    "battery_capacity_kwh": battery_capacity,
    "temperature_c": temperature,
    "speed_kmh": speed,
    "payload_kg": payload,
    "hvac_kw": hvac,
    "battery_age_cycles": battery_age,
    "soc_pct": soc,
    "terrain_grade_pct": terrain_grade,
    "wind_speed_kmh": wind_speed,
    "interaction_temp_age": temperature * (battery_age / 1000),
    "interaction_payload_grade": (payload / 100) * terrain_grade
}

# Top Stat row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <p style="color: #4facfe; margin:0; font-weight: 600;">Engine Matrix</p>
            <p style="font-size: 1.5rem; margin:0; font-weight: 800; color: white;">{model_choice.upper()}</p>
        </div>
    """, unsafe_allow_html=True)
with c2:
    energy_density = round(battery_capacity * (soc/100), 1)
    st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <p style="color: #4facfe; margin:0; font-weight: 600;">Active Energy</p>
            <p style="font-size: 1.5rem; margin:0; font-weight: 800; color: white;">{energy_density} kWh</p>
        </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <p style="color: #4facfe; margin:0; font-weight: 600;">Ambient Force</p>
            <p style="font-size: 1.5rem; margin:0; font-weight: 800; color: white;">{temperature}°C</p>
        </div>
    """, unsafe_allow_html=True)
with c4:
    drag = round(0.5 * (speed / 100) ** 2 + 0.1 * (wind_speed / 50), 2)
    st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <p style="color: #4facfe; margin:0; font-weight: 600;">Aero Drag Coef</p>
            <p style="font-size: 1.5rem; margin:0; font-weight: 800; color: white;">{drag}</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

# ── Tabs Setup ────────────────────────────────────────────────────────────────
tab_inference, tab_explain, tab_compare = st.tabs(["🛰️ Inference Telemetry", "🧠 AI Explainability (SHAP)", "🏎️ Vehicle Comparison"])

with tab_inference:
    # ── Prediction Action ─────────────────────────────────────────────────────────
    col1, col2 = st.columns([1.2, 2])

    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🛰️ Neural Inference</h3>", unsafe_allow_html=True)
        
        if st.button("INITIALIZE PREDICTION SEQUENCE 🚀", type="primary"):
            with st.spinner("Quantum routing through inference mesh..."):
                time.sleep(0.5) # Premium feel animation delay
                res = regressor.predict(features, model_choice)
                st.session_state.current_prediction = res["predicted_range_km"]
                
                # Fetch SHAP explanation seamlessly
                if model_choice in ['xgboost', 'lightgbm', 'random_forest', 'catboost', 'gradient_boosting']:
                    st.session_state.current_explanation = regressor.explain_prediction(features, model_choice)
                else:
                    st.session_state.current_explanation = None
                
                # Save to history
                st.session_state.history.append({
                    "Model": model_choice,
                    "Capacity": battery_capacity,
                    "SOC": soc,
                    "Temp": temperature,
                    "Speed": speed,
                    "Range (km)": st.session_state.current_prediction
                })

        if st.session_state.current_prediction is not None:
            val = st.session_state.current_prediction
            
            # Determine color gradient based on range
            if val < 150: bar_color = "red"
            elif val < 300: bar_color = "yellow"
            else: bar_color = "#00f2fe"

            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val,
                number = {'suffix': " km", 'font': {'size': 50, 'color': 'white'}},
                title = {'text': "Estimated Operational Range", 'font': {'color': '#94a3b8'}},
                gauge = {
                    'axis': {'range': [None, 600], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': bar_color},
                    'bgcolor': "rgba(255,255,255,0.05)",
                    'borderwidth': 0,
                    'bordercolor': "rgba(0,0,0,0)",
                    'steps': [
                        {'range': [0, 150], 'color': "rgba(231, 76, 60, 0.2)"},
                        {'range': [150, 300], 'color': "rgba(241, 196, 15, 0.2)"},
                        {'range': [300, 600], 'color': "rgba(0, 242, 254, 0.1)"}
                    ],
                    'threshold' : {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': val}
                }
            ))
            
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "white", 'family': "Inter"},
                height=300,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Awaiting telemetry input...")
            
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📊 Session History</h3>", unsafe_allow_html=True)
        if len(st.session_state.history) > 0:
            df_history = pd.DataFrame(st.session_state.history)
            
            # Style the dataframe
            st.dataframe(
                df_history.style.background_gradient(cmap='Blues', subset=['Range (km)']),
                use_container_width=True,
                height=280
            )
        else:
            st.markdown("<p style='color: #94a3b8;'>No scenarios simulated yet in this session.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Forecaster & Energy Flow ──────────────────────────────────────────────────
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🔮 Long-Term Degradation Matrix</h3>", unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        f_cycles = st.number_input("Simulate Future Cycles", 100, 5000, 1000, 100)
        if st.button("Execute Time Jump", type="secondary"):
            with st.spinner("Simulating electrochemical decay..."):
                time.sleep(0.4)
                f_res = forecaster.forecast(battery_capacity, battery_age, f_cycles, temperature)
                diff = round(f_res['forecast_capacity_kwh'] - battery_capacity, 2)
                
                st.markdown(f"""
                    <div style="margin-top: 15px;">
                        <p style="color: #94a3b8; margin:0;">Projected Max Capacity</p>
                        <p style="font-size: 2rem; margin:0; font-weight: 800; color: #f1c40f;">{f_res['forecast_capacity_kwh']} kWh</p>
                        <p style="color: #e74c3c; margin:0; font-weight: 600;">{diff} kWh Loss over {f_cycles} cycles</p>
                    </div>
                """, unsafe_allow_html=True)
            
    with f_col2:
        if model_choice in model_metrics:
            m = model_metrics[model_choice]
            st.markdown(f"""
                <div>
                    <p style="color: #4facfe; margin:0; font-weight: 600; font-size: 1.1rem;">Model Diagnostics: {model_choice}</p>
                    <div style="margin-top: 10px;">
                        <p style="margin: 5px 0;"><strong>Mean Abs Error:</strong> <span style="color: #2ecc71;">{m['mae']} km</span></p>
                        <p style="margin: 5px 0;"><strong>Root Mean Sq:</strong> <span style="color: #f1c40f;">{m['rmse']} km</span></p>
                        <p style="margin: 5px 0;"><strong>R² Confidence:</strong> <span style="color: #00f2fe;">{m['r2']}</span></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with f_col3:
        # A pseudo-animated charging indicator using markdown/html
        st.markdown("""
            <div style="text-align: right; padding-right: 20px;">
                <p style="color: #94a3b8; margin-bottom: 5px; font-weight: 600;">System Status</p>
                <div style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #2ecc71; box-shadow: 0 0 15px #2ecc71; animation: pulse 1.5s infinite;"></div>
                <span style="color: #2ecc71; margin-left: 8px; font-weight: 800;">ONLINE</span>
                <p style="color: #4facfe; margin-top: 10px; font-size: 0.9rem;">Mesh Nodes: Connected</p>
                <p style="color: #4facfe; margin-top: 0px; font-size: 0.9rem;">Artifacts: Verified</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with tab_explain:
    st.markdown("<h3>🔍 Local Prediction Reasoning (SHAP)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Understanding exactly *why* the AI estimated this range.</p>", unsafe_allow_html=True)
    
    if st.session_state.current_prediction is None:
        st.info("Execute a prediction sequence in the Telemetry tab first.")
    elif getattr(st.session_state, 'current_explanation', None) is None or 'error' in st.session_state.current_explanation:
        st.warning("SHAP Explanations are only available for tree-based engines (XGBoost, LightGBM, Random Forest, CatBoost).")
    else:
        exp = st.session_state.current_explanation
        base_val = exp["base_value"]
        conts = exp["contributions"]
        
        # Sort contributions by absolute magnitude
        sorted_conts = sorted(conts.items(), key=lambda x: abs(x[1]), reverse=True)
        # Keep top 6 and group the rest
        top_conts = sorted_conts[:6]
        other_sum = sum(v for k, v in sorted_conts[6:])
        
        labels = ["Base Fleet Average"] + [k.replace('_', ' ').title() for k, v in top_conts] + ["Other Factors", "Final Prediction"]
        values = [base_val] + [v for k, v in top_conts] + [other_sum, st.session_state.current_prediction]
        measures = ["absolute"] + ["relative"] * 6 + ["relative", "total"]
        
        colors = ["#94a3b8"] + ["#2ecc71" if v > 0 else "#e74c3c" for k, v in top_conts] + ["#f1c40f", "#00f2fe"]
        
        fig_waterfall = go.Figure(go.Waterfall(
            name = "Prediction Force Plot",
            orientation = "v",
            measure = measures,
            x = labels,
            textposition = "outside",
            text = [f"{v:+.1f}" if m == "relative" else f"{v:.1f}" for v, m in zip(values, measures)],
            y = values,
            connector = {"line": {"color": "rgba(255,255,255,0.2)"}},
            decreasing = {"marker": {"color": "#e74c3c"}},
            increasing = {"marker": {"color": "#2ecc71"}},
            totals = {"marker": {"color": "#00f2fe"}},
        ))
        
        fig_waterfall.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={'color': "white", 'family': "Inter"},
            title="Prediction Waterfall",
            waterfallgap=0.3
        )
        
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Global Feature Importance
        st.markdown("<h3>🌍 Global Intelligence Ranking</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8;'>Which features influence the model the most universally.</p>", unsafe_allow_html=True)
        
        if hasattr(regressor, 'feature_importance') and model_choice in regressor.feature_importance:
            feat_imp = regressor.feature_importance[model_choice]
            sorted_imp = sorted(feat_imp.items(), key=lambda x: x[1])
            
            fig_bar = go.Figure(go.Bar(
                x=[v for k, v in sorted_imp],
                y=[k.replace('_', ' ').title() for k, v in sorted_imp],
                orientation='h',
                marker=dict(
                    color=[v for k, v in sorted_imp],
                    colorscale='Blues',
                    showscale=False
                )
            ))
            
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "white", 'family': "Inter"},
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

with tab_compare:
    st.markdown("<h3>🏎️ Vehicle Matrix Comparison</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Compare real-world EVs head-to-head.</p>", unsafe_allow_html=True)
    
    # Flatten the vehicle DB for easy selection
    flat_vehicles = {}
    for cat, brands in VEHICLE_DB.items():
        for brand, models in brands.items():
            for model_name, specs in models.items():
                flat_vehicles[f"{brand} {model_name}"] = specs
                
    comp_col1, comp_col2 = st.columns(2)
    
    def get_image_for_vehicle(vehicle_str):
        if "Model" in vehicle_str or "Ioniq" in vehicle_str or "EV6" in vehicle_str or "Nexon" in vehicle_str or "ZS" in vehicle_str or "Atto" in vehicle_str or "XUV" in vehicle_str or "i4" in vehicle_str or "EQS" in vehicle_str or "Taycan" in vehicle_str:
            return "assets/vehicles/cars/default.png"
        elif "F77" in vehicle_str or "Rorr" in vehicle_str:
            return "assets/vehicles/motorcycles/default.png"
        else:
            return "assets/vehicles/scooters/default.png"
    
    with comp_col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        v1 = st.selectbox("Select Vehicle 1", list(flat_vehicles.keys()), index=0)
        s1 = flat_vehicles[v1]
        
        img1 = get_image_for_vehicle(v1)
        if os.path.exists(img1):
            st.image(img1, use_container_width=True)
            
        st.markdown(f"<h4 style='color: #4facfe;'>{v1}</h4>", unsafe_allow_html=True)
        st.write(f"**Battery Capacity**: {s1['capacity_kwh']} kWh")
        st.write(f"**Efficiency**: {s1['efficiency_wh_km']} Wh/km")
        st.write(f"**Top Speed**: {s1['top_speed_kmh']} km/h")
        st.write(f"**Base Price**: ${s1['price']}")
        
        # Calculate theoretical Max Range (Capacity / Efficiency)
        r1 = (s1['capacity_kwh'] * 1000) / s1['efficiency_wh_km']
        st.markdown(f"<p style='color: #2ecc71; font-size: 1.2rem; font-weight: bold;'>Theoretical Max Range: {round(r1)} km</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with comp_col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        v2 = st.selectbox("Select Vehicle 2", list(flat_vehicles.keys()), index=len(flat_vehicles)-1)
        s2 = flat_vehicles[v2]
        
        img2 = get_image_for_vehicle(v2)
        if os.path.exists(img2):
            st.image(img2, use_container_width=True)
            
        st.markdown(f"<h4 style='color: #4facfe;'>{v2}</h4>", unsafe_allow_html=True)
        st.write(f"**Battery Capacity**: {s2['capacity_kwh']} kWh")
        st.write(f"**Efficiency**: {s2['efficiency_wh_km']} Wh/km")
        st.write(f"**Top Speed**: {s2['top_speed_kmh']} km/h")
        st.write(f"**Base Price**: ${s2['price']}")
        
        r2 = (s2['capacity_kwh'] * 1000) / s2['efficiency_wh_km']
        st.markdown(f"<p style='color: #2ecc71; font-size: 1.2rem; font-weight: bold;'>Theoretical Max Range: {round(r2)} km</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Comparison Chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    fig_comp = go.Figure(data=[
        go.Bar(name='Efficiency (Wh/km)', x=[v1, v2], y=[s1['efficiency_wh_km'], s2['efficiency_wh_km']], marker_color='#4facfe'),
        go.Bar(name='Capacity (kWh)', x=[v1, v2], y=[s1['capacity_kwh'], s2['capacity_kwh']], marker_color='#f1c40f')
    ])
    fig_comp.update_layout(
        barmode='group',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Inter"},
        title="Efficiency vs Capacity Analysis"
    )
    st.plotly_chart(fig_comp, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
