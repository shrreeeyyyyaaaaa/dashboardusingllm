import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import docx
import os

# ------------------ Config ------------------
from openai import OpenAI

# Initialize client
client = OpenAI(api_key="OPENAI_API_KEY")

# Use new format
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Generate charts based on this data..."},
    ],
    temperature=0.7
)

generated_text = response.choices[0].message.content


# ------------------ File Readers ------------------
def read_requirements(file):
    if file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    return ""

def read_data(file):
    if file.name.endswith(".csv"):
        try:
            return pd.read_csv(file)
        except UnicodeDecodeError:
            # Fallback encodings
            try:
                return pd.read_csv(file, encoding='ISO-8859-1')
            except Exception as e:
                st.error("❌ Failed to read CSV file. Try saving it as UTF-8 or upload as Excel.")
                raise e
    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    return pd.DataFrame()

# ------------------ Helper: Column Summarizer ------------------
def summarize_dataframe(df):
    desc = df.describe(include="all").transpose().fillna("")
    lines = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        summary = desc.loc[col].to_dict()
        line = f"Column '{col}' ({dtype}) - Example: {df[col].dropna().iloc[0] if not df[col].dropna().empty else 'N/A'}"
        if dtype.startswith("float") or dtype.startswith("int"):
            line += f", Mean: {summary.get('mean', '')}, Std: {summary.get('std', '')}"
        lines.append(line)
    return "\n".join(lines)

# ------------------ LLM Call for Dynamic Chart Code ------------------
from openai import OpenAI
client = OpenAI()  # Make sure your API key is set in env or passed here

def ask_llm_for_charts(requirements_text, column_info, summary):
    prompt = f"""
    You are a data visualization expert. Based on the following requirements and data summary,
    generate 3 chart configurations. Each configuration should be a JSON dict with:
    - chart_type (bar, line, pie, scatter, heatmap)
    - x (column name)
    - y (optional)
    - title

    Requirements:\n{requirements_text}
    Column Info:\n{column_info}
    Summary:\n{summary}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You generate chart specifications as JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except:
        st.error("❌ Failed to parse LLM response. Check formatting.")
        return []

    import json
    return json.loads(response['choices'][0]['message']['content'])

# ------------------ Dynamic Plotly Chart Execution ------------------
def plot_chart_from_code(df, code_str):
    local_vars = {"df": df.copy()}
    try:
        exec(code_str, {}, local_vars)
        return local_vars.get("fig", None)
    except Exception as e:
        st.error(f"⚠️ Chart execution failed:\n```python\n{code_str}\n```")
        st.exception(e)
        return None

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="🧠 Smart Dashboard", layout="wide")
st.title("🧠 Smart Dashboard using LLM")
st.markdown("Upload your data + requirements to generate AI-powered visualizations.")

uploaded_data = st.file_uploader("📂 Upload CSV or Excel file", type=["csv", "xlsx"])
uploaded_req = st.file_uploader("📝 Upload Requirement File (txt or docx)", type=["txt", "docx"])

if uploaded_data and uploaded_req:
    df = read_data(uploaded_data)
    requirements_text = read_requirements(uploaded_req)

    st.success("✅ Files uploaded successfully")
    st.subheader("📑 Preview of Uploaded Data")
    st.dataframe(df.head(10), use_container_width=True)

    with st.spinner("🤖 Analyzing data and generating charts..."):
        col_info = summarize_dataframe(df)
        charts = ask_llm_for_charts(requirements_text, col_info, df.describe(include='all').to_string())

    # Group charts by theme
    from collections import defaultdict
    themes = defaultdict(list)
    for chart in charts:
        themes[chart.get("theme", "General")].append(chart)

    st.subheader("📈 Generated Visualizations")
    for theme, chart_group in themes.items():
        st.markdown(f"### 📂 Theme: {theme}")
        for chart in chart_group:
            fig = plot_chart_from_code(df, chart['code'])
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f"🔍 **Insight**: {chart['insight']}")
            else:
                st.warning(f"⚠️ Skipped: {chart['title']}")
else:
    st.info("👆 Please upload both data and requirement files to begin.")
