import os
import pandas as pd
import streamlit as st
from datetime import datetime

# AOIs
AOIs = {
    "Component Bin": ((100, 100), (200, 200)),
    "Instruction Label": ((300, 100), (400, 200)),
    "Tool Area": ((100, 300), (200, 400)),
    "Assembly Zone": ((300, 300), (400, 400))
}

def is_in_aoi(x, y, aoi_bounds):
    (x1, y1), (x2, y2) = aoi_bounds
    return x1 <= x <= x2 and y1 <= y <= y2

def calculate_metrics(df):
    df['AOI'] = 'Outside'
    for name, bounds in AOIs.items():
        mask = df.apply(lambda row: is_in_aoi(row['x'], row['y'], bounds), axis=1)
        df.loc[mask, 'AOI'] = name

    fixation_time = df.groupby('AOI')['duration'].sum()
    total_fixation = fixation_time.sum()

    if total_fixation == 0:
        return {}

    aoi_coverage = (total_fixation - fixation_time.get('Outside', 0)) / total_fixation * 100
    avg_fixation_duration = df['duration'].mean()
    time_to_first_fixation = df[df['AOI'] == "Instruction Label"]['timestamp'].min()

    return {
        "AOI Coverage (%)": round(aoi_coverage, 2),
        "Average Fixation Duration (ms)": round(avg_fixation_duration, 2),
        "Time to First Fixation (Instruction Label, ms)": round(time_to_first_fixation, 2) if not pd.isna(time_to_first_fixation) else "N/A",
        "Efficiency Score (/100)": calculate_efficiency_score(aoi_coverage, avg_fixation_duration, time_to_first_fixation),
        "Performance Level": classify_performance(calculate_efficiency_score(aoi_coverage, avg_fixation_duration, time_to_first_fixation))
    }

def calculate_efficiency_score(coverage, avg_fix, time_to_first):
    if isinstance(time_to_first, str):
        time_to_first = 99999
    score = 0
    if coverage >= 90:
        score += 30
    if avg_fix < 200:
        score += 10
    if time_to_first < 1000:
        score += 15
    if coverage > 95:
        score += 20
    if coverage > 85 and avg_fix < 220:
        score += 25
    return score

def classify_performance(score):
    if score >= 85:
        return "Efficient"
    elif score >= 70:
        return "Acceptable"
    elif score >= 50:
        return "Needs Attention"
    else:
        return "High Risk"

# Streamlit UI
st.set_page_config(page_title="Eye-Tracking Dashboard", layout="wide")

st.markdown("""
<style>
    body {
        background-color: #0e1117;
        color: #fafafa;
    }
    .main {
        background-color: #0e1117;
    }
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #2c7be5;
        color: white;
    }
    .stSidebar {
        background-color: #161b22 !important;
        color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

st.title("\U0001F441 Eye-Tracking Worker Efficiency Dashboard")
st.markdown("""
This dashboard helps analyze and score worker focus and attention during assembly tasks using eye-tracking data.

**Upload eye-tracking CSV files**, assign a worker name, and view calculated metrics:
- Area of Interest (AOI) coverage
- Fixation metrics
- Efficiency score & attention classification
""")

st.sidebar.header("Upload Gaze Data")
worker_name = st.sidebar.text_input("Worker Name", placeholder="e.g., John Doe")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type="csv")

if uploaded_file and worker_name:
    df = pd.read_csv(uploaded_file)
    metrics = calculate_metrics(df)
    if metrics:
        st.success(f"Efficiency Report for **{worker_name}**")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Efficiency Score (/100)", value=metrics['Efficiency Score (/100)'])
            st.metric(label="Performance Level", value=metrics['Performance Level'])
        with col2:
            st.metric(label="AOI Coverage (%)", value=f"{metrics['AOI Coverage (%)']}%")
            st.metric(label="Avg. Fixation Duration", value=f"{metrics['Average Fixation Duration (ms)']} ms")
            st.metric(label="First Fixation on Instruction Label", value=f"{metrics['Time to First Fixation (Instruction Label, ms)']} ms")

        with st.expander("🔍 Detailed Metrics Table"):
            st.dataframe(pd.DataFrame([metrics], index=[worker_name]))
    else:
        st.error("The uploaded file does not contain sufficient gaze data for meaningful analysis.")
elif uploaded_file and not worker_name:
    st.sidebar.warning("Please enter the worker's name before uploading the CSV.")
