import pandas as pd
df=pd.read_parquet("domains.parquet")
print(df.head())
print(len(df))
print(df.columns)