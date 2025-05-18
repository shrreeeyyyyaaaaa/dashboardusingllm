import openai
import plotly.express as px
import pandas as pd


def dynamic_viz_gen_agent(df, info, kpis, req_text):
    prompt = f"""
    You're a data analyst. Given:
    1. Dataset columns and info: {info}
    2. KPIs: {kpis}
    3. Requirements: {req_text}

    Suggest 3-5 charts (Plotly format). Output Python code for each chart wrapped in markdown triple backticks. Each chart should include a meaningful title and be useful.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", response['choices'][0]['message']['content'], re.DOTALL)

    results = []
    for block in code_blocks:
        try:
            local_env = {"df": df, "px": px, "pd": pd}
            exec(block, local_env)
            figs = [v for v in local_env.values() if hasattr(v, 'to_plotly_json')]
            if figs:
                results.append({
                    "theme": "Auto",  # Add logic later to detect theme
                    "chart_type": "Auto",
                    "title": block.split("title=")[1].split(")")[0].strip('"\''),
                    "code": figs[0],
                    "bullets": [f"Generated from: {block[:50]}..."]
                })
        except Exception as e:
            continue
    return results
