import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
from pydantic import BaseModel, Field
from openai import OpenAI

# ---------------------------------------------------------
# Page Configuration & Mobile UI Enhancements
# ---------------------------------------------------------
st.set_page_config(
    page_title="HSE Safety Command | OIL",
    page_icon="🛡️",
    layout="centered"
)

# Custom CSS for Mobile Touch Targets & Alert Cards
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.2em; 
        font-weight: bold; 
        background-color: #0066cc;
        color: white;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #0066cc;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .sif-card {
        background-color: #fff3f3;
        border-left: 5px solid #d9534f;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ OIL Safety Intelligence")
st.caption("SIH26165: AI-Driven SIF Precursor Detection & IOGP Mapping")

# ---------------------------------------------------------
# API Key Management (Streamlit Secrets or Local Input)
# ---------------------------------------------------------
api_key = st.secrets.get("OPENAI_API_KEY", None)

if not api_key:
    with st.sidebar:
        st.subheader("⚙️ Settings")
        api_key = st.text_input("Enter OpenAI API Key:", type="password")

# ---------------------------------------------------------
# Pydantic Data Schema (IOGP Life-Saving Rules Aligned)
# ---------------------------------------------------------
class SafetyAnalysis(BaseModel):
    hazard_category: str = Field(description="Type of hazard, e.g., Gas/Pressure Leak, Working at Height, Electrical, Line of Fire, Toxic Chemical")
    activity: str = Field(description="Operational task actively being performed during incident")
    barrier_failure: str = Field(description="Safeguard or administrative safety control that failed or was absent")
    iogp_rule: str = Field(description="Strictly match to one of the 9 IOGP Life-Saving Rules: Bypassing Safety Controls, Confined Space, Driving, Energy Isolation, Hot Work, Line of Fire, Safe Mechanical Lifting, Work Authorization, or Working at Height")
    is_sif_precursor: bool = Field(description="True if incident had potential for Serious Injury or Fatality")
    potential_consequence: str = Field(description="Worst-case outcome if no intervention occurred")
    recommended_action: str = Field(description="Immediate operational action required on site")

# ---------------------------------------------------------
# Step 1 & 2: Data Ingestion (Text Input or PDF File)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📝 Field Report Ingestion")

tab1, tab2 = st.tabs(["📄 Upload PDF Report", "✍️ Manual Field Note"])
report_text = ""

with tab1:
    uploaded_file = st.file_uploader("Drop Incident PDF Report", type=["pdf"])
    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            report_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        st.success("PDF Extracted Successfully!")

with tab2:
    report_text_input = st.text_area(
        "Enter Unstructured Incident Description:",
        placeholder="Worker unclipped safety harness at 4 meters on Rig 3 to reach crossbeam...",
        height=100
    )
    if report_text_input:
        report_text = report_text_input

# ---------------------------------------------------------
# Steps 3, 4 & 5: AI Engine Execution & Parsing
# ---------------------------------------------------------
if report_text:
    with st.expander("🔍 View Ingested Raw Text"):
        st.write(report_text)

    if st.button("🚀 Run SIF Risk Analysis"):
        if not api_key:
            st.error("🔑 OpenAI API Key required! Add it to Streamlit secrets or sidebar.")
        else:
            with st.spinner("Analyzing incident against IOGP standards..."):
                try:
                    client = OpenAI(api_key=api_key)
                    response = client.beta.chat.completions.parse(
                        model="gpt-4o-2024-08-06",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a lead HSE engineer at Oil India Limited (OIL). Analyze safety reports and strictly map findings to IOGP Life-Saving Rules."
                            },
                            {"role": "user", "content": report_text}
                        ],
                        response_format=SafetyAnalysis
                    )
                    res = response.choices[0].message.parsed

                    st.markdown("---")
                    
                    # High Risk Flag (SIF Precursor Alert)
                    if res.is_sif_precursor:
                        st.error("🚨 **SIF PRECURSOR DETECTED**\n\nHigh risk of Serious Injury or Fatality!")
                    else:
                        st.success("✅ **Standard Near-Miss / Low Potential Severity**")

                    # Structured Report Summary
                    st.subheader("📋 Parsed Intelligence Summary")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Hazard Category:**\n`{res.hazard_category}`")
                        st.markdown(f"**Activity:**\n`{res.activity}`")
                        st.markdown(f"**Barrier Failure:**\n`{res.barrier_failure}`")

                    with col2:
                        st.markdown(f"**IOGP Rule Triggered:**\n🚨 `{res.iogp_rule}`")
                        st.markdown(f"**Potential Consequence:**\n`{res.potential_consequence}`")

                    st.info(f"💡 **Recommended Action:** {res.recommended_action}")

                except Exception as e:
                    st.error(f"Analysis Error: {str(e)}")

# ---------------------------------------------------------
# Step 6: Command Center Analytics (Simulated Site Trends)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Plant Command Center (Site Metrics)")

# Synthetic Incident Log matching OIL requirements
synthetic_data = pd.DataFrame({
    "IOGP_Rule": [
        "Working at Height", "Bypassing Safety Controls", "Energy Isolation", 
        "Line of Fire", "Working at Height", "Hot Work", "Confined Space",
        "Working at Height", "Line of Fire", "Energy Isolation"
    ],
    "Is_SIF": [True, True, True, False, True, False, True, True, False, True],
    "Rig_Site": ["Rig A", "Rig B", "Plant 1", "Rig A", "Plant 2", "Rig B", "Plant 1", "Rig A", "Plant 2", "Rig B"]
})

# SIF vs Non-SIF Metrics
sif_count = int(synthetic_data["Is_SIF"].sum())
total_count = len(synthetic_data)

m1, m2, m3 = st.columns(3)
m1.metric("Total Incident Logs", total_count)
m2.metric("SIF Precursors Detected", sif_count, delta=f"{(sif_count/total_count)*100:.0f}% Risk Ratio", delta_color="inverse")
m3.metric("Active Sites Monitored", synthetic_data["Rig_Site"].nunique())

# Chart: Top Triggered IOGP Rules
fig = px.bar(
    synthetic_data, 
    x="IOGP_Rule", 
    color="Is_SIF", 
    title="Incident Frequency by IOGP Rule",
    labels={"IOGP_Rule": "IOGP Rule", "count": "Incidents", "Is_SIF": "SIF Potential"},
    color_discrete_map={True: "#d9534f", False: "#0066cc"}
)
st.plotly_chart(fig, use_container_width=True)