import openai

def generate_kpis(df_info):
    prompt = f"""
    You are a data analyst. Based on the following dataset metadata, generate bullet-point KPIs and insights:

    Columns: {df_info['columns']}
    DTypes: {df_info['dtypes']}
    Null Counts: {df_info['nulls']}
    Unique Values: {df_info['n_unique']}

    Output should be concise bullet points.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']
