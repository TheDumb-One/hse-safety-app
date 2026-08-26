import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Setup & Mobile CSS
# ---------------------------------------------------------
st.set_page_config(page_title="HSE Safety Command | OIL", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.2em; font-weight: bold; background-color: #0066cc; color: white; }
    .card { background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid #0066cc; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ OIL Safety Intelligence Platform")
st.caption("SIH26165: SIF Precursor Detection & Enterprise Risk Analytics")

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

if report_text:
    if st.button("🚀 Run Dynamic AI Risk Analysis"):
        if not api_key:
            st.error("🔑 API Key missing! Add GEMINI_API_KEY to Streamlit Secrets or sidebar.")
        else:
            with st.spinner("Analyzing incident via Cloud AI Engine..."):
                try:
                    client = genai.Client(api_key=api_key)
                    system_prompt = "You are a lead HSE safety engineer at Oil India Limited. Classify safety incidents and strictly map barrier failures to IOGP Life-Saving Rules."
                    
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
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
# Enhanced Plant Command Center (Narrow Down Risk)
# ---------------------------------------------------------
st.markdown("---")
st.header("📊 Plant Command Center & SIF Risk Matrix")

# Rich Operational Dataset
df = pd.DataFrame({
    "Rig_Site": ["Rig Alpha", "Rig Alpha", "Rig Beta", "Plant 1", "Rig Beta", "Plant 2", "Rig Alpha", "Plant 1", "Rig Beta", "Rig Alpha"],
    "Department": ["Drilling", "Maintenance", "Drilling", "Operations", "Maintenance", "Operations", "Drilling", "Maintenance", "Logistics", "Drilling"],
    "IOGP_Rule": ["Working at Height", "Bypassing Controls", "Energy Isolation", "Line of Fire", "Working at Height", "Hot Work", "Confined Space", "Energy Isolation", "Line of Fire", "Working at Height"],
    "Barrier_Failure": ["Lapses in Tie-off", "Permit Non-compliance", "LOTO Failure", "Dropped Object", "Defective Scaffolding", "Ignition Source", "Gas Testing Absent", "Valve Leak", "Unsecured Load", "Harness Failure"],
    "Is_SIF": [True, True, True, False, True, False, True, True, False, True],
    "Shift": ["Night", "Day", "Day", "Night", "Day", "Night", "Day", "Night", "Day", "Night"]
})

# Sidebar / Top Slicers for Risk Narrowing
st.subheader("🎯 Narrow Down Site Risk Factors")
c_f1, c_f2, c_f3 = st.columns(3)

with c_f1:
    selected_site = st.multiselect("Filter by Asset / Site:", options=df["Rig_Site"].unique(), default=df["Rig_Site"].unique())
with c_f2:
    selected_dept = st.multiselect("Filter by Operating Dept:", options=df["Department"].unique(), default=df["Department"].unique())
with c_f3:
    sif_only = st.checkbox("Show SIF Precursors Only", value=False)

# Filter Data Dynamic Update
filtered_df = df[(df["Rig_Site"].isin(selected_site)) & (df["Department"].isin(selected_dept))]
if sif_only:
    filtered_df = filtered_df[filtered_df["Is_SIF"] == True]

# Executive Key Metrics
total_incidents = len(filtered_df)
sif_incidents = int(filtered_df["Is_SIF"].sum())
sif_rate = (sif_incidents / total_incidents * 100) if total_incidents > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Active Filtered Logs", total_incidents)
m2.metric("Critical SIF Precursors", sif_incidents, delta=f"{sif_rate:.1f}% Risk Ratio", delta_color="inverse")
m3.metric("Primary High-Risk Site", filtered_df["Rig_Site"].mode()[0] if not filtered_df.empty else "N/A")
m4.metric("Top Failed Barrier", filtered_df["Barrier_Failure"].mode()[0] if not filtered_df.empty else "N/A")

# Detailed Visual Analytics
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_iogp = px.bar(
        filtered_df,
        x="IOGP_Rule",
        color="Is_SIF",
        title="<b>Incident Concentration by IOGP Rule</b>",
        labels={"Is_SIF": "SIF Potential", "IOGP_Rule": "IOGP Life-Saving Rule"},
        color_discrete_map={True: "#d9534f", False: "#0066cc"}
    )
    st.plotly_chart(fig_iogp, use_container_width=True)

with col_chart2:
    fig_dept = px.sunburst(
        filtered_df,
        path=["Rig_Site", "Department", "IOGP_Rule"],
        title="<b>Risk Hierarchy: Site ➔ Department ➔ Rule</b>",
        color="Is_SIF",
        color_discrete_map={True: "#d9534f", False: "#0066cc"}
    )
    st.plotly_chart(fig_dept, use_container_width=True)

# Granular Data View
with st.expander("📋 View Narrowed Incident Audit Log"):
    st.dataframe(filtered_df, use_container_width=True)