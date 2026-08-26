import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(page_title="HSE Safety Command | OIL", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.2em; font-weight: bold; background-color: #0066cc; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ OIL Safety Intelligence")
st.caption("SIH26165: AI-Driven SIF Precursor Detection & IOGP Mapping")

# ---------------------------------------------------------
# API Key Read (Streamlit Secrets or Sidebar Input)
# ---------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", None)

if not api_key:
    with st.sidebar:
        st.subheader("⚙️ API Configuration")
        api_key = st.text_input("Enter Gemini API Key:", type="password")

# ---------------------------------------------------------
# Pydantic Schema
# ---------------------------------------------------------
class SafetyAnalysis(BaseModel):
    hazard_category: str = Field(description="e.g. Gas Leak, Working at Height, Electrical, Chemical")
    activity: str = Field(description="Operational task being performed")
    barrier_failure: str = Field(description="Safeguard or administrative safety control that failed")
    iogp_rule: str = Field(description="Matching IOGP Rule: e.g. Working at Height, Energy Isolation, Line of Fire, Bypassing Controls, Confined Space")
    is_sif_precursor: bool = Field(description="True if incident had serious injury/fatality potential")
    potential_consequence: str = Field(description="Worst potential outcome")
    recommended_action: str = Field(description="Immediate site action required")

# ---------------------------------------------------------
# Ingestion Layer
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
    report_text_input = st.text_area("Enter Incident Description:", placeholder="Worker was cleaning valve on Rig 4...", height=100)
    if report_text_input:
        report_text = report_text_input

# ---------------------------------------------------------
# Processing Layer (Gemini Cloud Engine)
# ---------------------------------------------------------
if report_text:
    with st.expander("🔍 View Ingested Raw Text"):
        st.write(report_text)

    if st.button("🚀 Run Dynamic AI Risk Analysis"):
        if not api_key:
            st.error("🔑 API Key missing! Add GEMINI_API_KEY to Streamlit Secrets or sidebar.")
        else:
            with st.spinner("Analyzing incident via Cloud AI Engine..."):
                try:
                    client = genai.Client(api_key=api_key)
                    system_prompt = "You are a lead HSE safety engineer at Oil India Limited. Classify safety incidents and strictly map barrier failures to IOGP Life-Saving Rules."
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"{system_prompt}\n\nINCIDENT REPORT:\n{report_text}",
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=SafetyAnalysis,
                        ),
                    )
                    
                    res = SafetyAnalysis.model_validate_json(response.text)

                    st.markdown("---")
                    if res.is_sif_precursor:
                        st.error("🚨 **SIF PRECURSOR DETECTED**\n\nHigh risk of Serious Injury or Fatality!")
                    else:
                        st.success("✅ **Standard Incident / Low Potential Severity**")

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
                    st.error(f"AI Processing Error: {str(e)}")

# ---------------------------------------------------------
# Dashboard Metrics
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Plant Command Center (Site Metrics)")

synthetic_data = pd.DataFrame({
    "IOGP_Rule": ["Working at Height", "Bypassing Controls", "Energy Isolation", "Line of Fire", "Working at Height", "Hot Work"],
    "Is_SIF": [True, True, True, False, True, False],
    "Rig_Site": ["Rig A", "Rig B", "Plant 1", "Rig A", "Plant 2", "Rig B"]
})

m1, m2, m3 = st.columns(3)
m1.metric("Total Incident Logs", len(synthetic_data))
m2.metric("SIF Precursors", int(synthetic_data["Is_SIF"].sum()), delta="67% Risk Ratio", delta_color="inverse")
m3.metric("Sites Monitored", synthetic_data["Rig_Site"].nunique())

fig = px.bar(synthetic_data, x="IOGP_Rule", color="Is_SIF", title="Incident Trends by IOGP Rule", color_discrete_map={True: "#d9534f", False: "#0066cc"})
st.plotly_chart(fig, use_container_width=True)