import streamlit as st
import pandas as pd
from agents.ext_info import extract_column_info
from agents.kpi_gen import generate_kpis
from agents.viz_gen import dynamic_viz_gen_agent
from utils.doc_parser import parse_requirements_file

st.set_page_config(page_title="📊 Smart Dashboard", layout="wide")
st.title("Smart LLM-Powered Dashboard")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'])
requirements_file = st.file_uploader("Upload Requirements (TXT/DOCX)", type=['txt', 'docx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    st.success("Data Loaded Successfully")

    if requirements_file:
        requirements_text = parse_requirements_file(requirements_file)

        # Agent 1: Extract column info
        df_info = extract_column_info(df)

        # Agent 2: Generate KPIs and Insights
        kpi_text = generate_kpis(df_info)

        # Agent 3: Generate visualizations dynamically using LLM
        charts = dynamic_viz_gen_agent(df, df_info, kpi_text, requirements_text)

        themes = set(c["theme"] for c in charts)
        for theme in themes:
            st.subheader(f"📂 {theme} Charts")
            for chart in [c for c in charts if c["theme"] == theme]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.plotly_chart(chart["code"], use_container_width=True)
                with col2:
                    st.markdown(f"**{chart['title']}**")
                    st.markdown("\n".join([f"- {b}" for b in chart['bullets']]))
