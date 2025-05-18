import pandas as pd

def extract_column_info(df):
    info = {
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "nulls": df.isnull().sum().to_dict(),
        "n_unique": df.nunique().to_dict()
    }
    return info
