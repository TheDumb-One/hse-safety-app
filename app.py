import streamlit as st
import pandas as pd
import plotly.express as px
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="HSE Safety Command | OIL", 
    page_icon="🛡️", 
    layout="wide"
)

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
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ OIL Safety Intelligence Platform")
st.caption("SIH26165: AI-Driven SIF Precursor Detection & Enterprise Risk Analytics")

# Secrets Management
api_key = st.secrets.get("GEMINI_API_KEY", None)

if not api_key:
    with st.sidebar:
        st.subheader("⚙️ API Configuration")
        api_key = st.text_input("Enter Gemini API Key:", type="password")

# ---------------------------------------------------------
# Pydantic Schema Definition
# ---------------------------------------------------------
class SafetyAnalysis(BaseModel):
    hazard_category: str = Field(description="Main hazard category (e.g. Gas Leak, Fall Hazard, Electrical)")
    activity: str = Field(description="Operational task performed during the incident")
    barrier_failure: str = Field(description="Safeguard or procedural safety control that failed")
    iogp_rule: str = Field(description="IOGP Rule: Working at Height, Energy Isolation, Line of Fire, Bypassing Controls, Confined Space, Hot Work, Work Authorization")
    is_sif_precursor: bool = Field(description="True if incident had serious injury or fatality potential")
    potential_consequence: str = Field(description="Worst case potential consequence")
    recommended_action: str = Field(description="Immediate corrective site action required")

# ---------------------------------------------------------
# Multimodal Ingestion Layer (Zero-Cost Ingestion)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📝 Field Input Ingestion")

tab1, tab2, tab3 = st.tabs([
    "📄 Upload PDF / Image Log", 
    "✍️ Manual Field Note", 
    "🎙️ Voice Note Recording"
])

uploaded_file = None
report_text = ""
audio_file = None

with tab1:
    uploaded_file = st.file_uploader(
        "Drop Scanned/Digital PDF Report or Field Photo", 
        type=["pdf", "png", "jpg", "jpeg"]
    )

with tab2:
    report_text = st.text_area(
        "Enter Raw Incident Log / Field Narrative:", 
        placeholder="Roughneck unclipped harness at 4m above deck while working on valve...", 
        height=100
    )

with tab3:
    audio_file = st.audio_input("Record Live Voice Field Note")

# ---------------------------------------------------------
# Core Multimodal AI Engine with Resilience / Fallback Loop
# ---------------------------------------------------------
if uploaded_file or report_text or audio_file:
    if st.button("🚀 Analyze Incident for SIF Precursors"):
        if not api_key:
            st.error("🔑 API Key missing! Add GEMINI_API_KEY to Streamlit Secrets or sidebar.")
        else:
            with st.spinner("Processing report with Cloud AI Engine..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    system_prompt = """
                    You are an expert HSE Lead Auditor at Oil India Limited (OIL).
                    Analyze this field report (text narrative, scanned PDF/Image, or voice note).
                    Extract hazards, map barrier failures strictly to IOGP Life-Saving Rules, 
                    and evaluate whether the event constitutes a Serious Injury or Fatality (SIF) Precursor.
                    """
                    
                    contents_payload = [system_prompt]

                    # Process File Uploads (Scanned PDF or Images)
                    if uploaded_file is not None:
                        contents_payload.append(
                            types.Part.from_bytes(
                                data=uploaded_file.read(), 
                                mime_type=uploaded_file.type
                            )
                        )
                    # Process Recorded Voice Audio
                    elif audio_file is not None:
                        contents_payload.append(
                            types.Part.from_bytes(
                                data=audio_file.read(), 
                                mime_type="audio/wav"
                            )
                        )
                    # Process Raw Text
                    elif report_text:
                        contents_payload.append(f"FIELD LOG TEXT:\n{report_text}")

                    # Fallback list to bypass server load issues (503 handling)
                    candidate_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
                    response = None
                    last_exception = None

                    for model_name in candidate_models:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=contents_payload,
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    response_schema=SafetyAnalysis,
                                ),
                            )
                            break  # Success: exit loop
                        except Exception as e:
                            last_exception = e
                            continue  # Retry next model on failure

                    if response is None:
                        raise last_exception

                    res = SafetyAnalysis.model_validate_json(response.text)

                    # Display Analysis Banner
                    st.markdown("---")
                    if res.is_sif_precursor:
                        st.error("🚨 **CRITICAL SIF PRECURSOR DETECTED**\n\nHigh probability of Serious Injury or Fatality!")
                    else:
                        st.success("✅ **Standard Near-Miss / Low Severity Level**")

                    # Structured Results Output
                    st.subheader("📋 Dynamic Intelligence Summary")
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
                    st.error(f"Processing Error: {str(e)}")

# ---------------------------------------------------------
# Command Center Visual Analytics
# ---------------------------------------------------------
st.markdown("---")
st.header("📊 Plant Command Center (Site Risk Analytics)")

df = pd.DataFrame({
    "Rig_Site": ["Rig Alpha", "Rig Alpha", "Rig Beta", "Plant 1", "Rig Beta", "Plant 2", "Rig Alpha", "Plant 1", "Rig Beta", "Rig Alpha"],
    "Department": ["Drilling", "Maintenance", "Drilling", "Operations", "Maintenance", "Operations", "Drilling", "Maintenance", "Logistics", "Drilling"],
    "IOGP_Rule": ["Working at Height", "Bypassing Controls", "Energy Isolation", "Line of Fire", "Working at Height", "Hot Work", "Confined Space", "Energy Isolation", "Line of Fire", "Working at Height"],
    "Barrier_Failure": ["Lapses in Tie-off", "Permit Non-compliance", "LOTO Failure", "Dropped Object", "Defective Scaffolding", "Ignition Source", "Gas Testing Absent", "Valve Leak", "Unsecured Load", "Harness Failure"],
    "Is_SIF": [True, True, True, False, True, False, True, True, False, True]
})

c_f1, c_f2 = st.columns(2)
with c_f1:
    selected_site = st.multiselect("Filter Asset Location:", options=df["Rig_Site"].unique(), default=df["Rig_Site"].unique())
with c_f2:
    sif_only = st.checkbox("Focus SIF Precursors Only", value=False)

filtered_df = df[df["Rig_Site"].isin(selected_site)]
if sif_only:
    filtered_df = filtered_df[filtered_df["Is_SIF"] == True]

m1, m2, m3 = st.columns(3)
m1.metric("Active Incident Logs", len(filtered_df))
m2.metric("Critical SIF Count", int(filtered_df["Is_SIF"].sum()), delta="Risk Level High", delta_color="inverse")
m3.metric("Top Failure Mode", filtered_df["Barrier_Failure"].mode()[0] if not filtered_df.empty else "N/A")

col_c1, col_c2 = st.columns(2)
with col_c1:
    fig_bar = px.bar(
        filtered_df, 
        x="IOGP_Rule", 
        color="Is_SIF", 
        title="IOGP Rule Breaches",
        color_discrete_map={True: "#d9534f", False: "#0066cc"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_c2:
    fig_sun = px.sunburst(
        filtered_df, 
        path=["Rig_Site", "Department", "IOGP_Rule"], 
        title="Site Risk Hierarchy",
        color="Is_SIF",
        color_discrete_map={True: "#d9534f", False: "#0066cc"}
    )
    st.plotly_chart(fig_sun, use_container_width=True)