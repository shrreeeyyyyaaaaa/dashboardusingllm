import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import docx
import os

# ------------------ Config ------------------
openai.api_key = "OPENAI_API_KEY"

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
def ask_llm_for_charts(requirements, column_info, summary):
    prompt = f"""
You are a Python data visualization expert.

Given:
- User requirements
- Data column descriptions
- Statistical summaries

Generate 4 to 6 meaningful Plotly charts in JSON list format like this:

[
  {{
    "title": "",
    "theme": "",
    "insight": "",
  }},
  ...
]

Only use 'df' as the dataframe variable. Do not import anything.

### Requirements:
{requirements}

### Column Info:
{column_info}

### Summary:
{summary}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
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
