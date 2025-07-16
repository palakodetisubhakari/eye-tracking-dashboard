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
st.set_page_config(page_title="Eye-Tracking Dashboard", layout="centered")
st.title("\U0001F441 Eye-Tracking Worker Efficiency Dashboard")
st.markdown("""
Upload eye-tracking **CSV** files and assign a worker name. The system calculates:
- AOI (Area of Interest) coverage
- Fixation metrics
- Efficiency score & classification
""")

st.sidebar.header("Upload CSV")
worker_name = st.sidebar.text_input("Enter Worker Name")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

if uploaded_file and worker_name:
    df = pd.read_csv(uploaded_file)
    metrics = calculate_metrics(df)
    if metrics:
        st.success(f"Metrics calculated for **{worker_name}**")

        with st.expander("📊 Worker Metrics"):
            st.dataframe(pd.DataFrame([metrics], index=[worker_name]))

        st.markdown(f"### Performance Summary for `{worker_name}`")
        st.metric(label="Efficiency Score", value=metrics['Efficiency Score (/100)'])
        st.metric(label="Performance Level", value=metrics['Performance Level'])
        st.metric(label="AOI Coverage", value=f"{metrics['AOI Coverage (%)']}%")
        st.metric(label="Average Fixation Duration", value=f"{metrics['Average Fixation Duration (ms)']} ms")
        st.metric(label="Time to First Fixation", value=f"{metrics['Time to First Fixation (Instruction Label, ms)']} ms")
    else:
        st.warning("CSV does not contain enough valid gaze data.")
elif uploaded_file and not worker_name:
    st.sidebar.warning("Please enter a worker name before uploading.")
