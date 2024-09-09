import pandas as pd

df = pd.read_csv("data/2024-06-10-fd-on-iccbench/2024-06-10-fd-on-iccbench.csv")


print (df[df["Detected Flows"] != df["UBC FlowDroid v2.7.1 Detected Flows"]])