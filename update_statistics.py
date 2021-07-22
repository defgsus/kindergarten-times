import datetime
import pandas as pd
import numpy as np

df = pd.read_csv("./times.csv")
df["date"] = pd.to_datetime(df["date"])
df["weekday"] = [
    row["date"].strftime("%A")
    for i, row in df.iterrows()
]

df_not_managed = df[pd.isna(df["arrival"])]

df_managed = (
    df[~pd.isna(df["arrival"])].copy()
)

df_managed["minutes"] = [
    int(row["arrival"].split(":")[0]) * 60 + int(row["arrival"].split(":")[1])
    for _, row in df_managed.iterrows()
]


def minute_to_time(m: int) -> str:
    m = int(round(m))
    return f"{m//60}:{m%60:02d}"


def time_stats_table(df: pd.DataFrame, df_not_managed: pd.DataFrame) -> pd.DataFrame:
    df_overslept = df_not_managed[df_not_managed["tag"] == "overslept"].copy()
    df_overslept["one"] = 1
    df_overslept = df_overslept.groupby("weekday").sum()

    table = []
    for weekday in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "all"]:
        if weekday == "all":
            df2 = df
        else:
            df2 = df[df["weekday"] == weekday]

        stats = df2.describe()

        if weekday in df_overslept.index:
            overslept = df_overslept.loc[weekday]["one"]
        elif weekday == "all":
            overslept = df_overslept["one"].sum()
        else:
            overslept = 0

        table.append({
            "weekday": "**all**" if weekday == "all" else weekday,
            "drives": int(stats.loc["count", "minutes"]),
            "overslept": overslept,
            "mean arrival": minute_to_time(stats.loc["mean", "minutes"]),
            "earliest": minute_to_time(stats.loc["min", "minutes"]),
            "latest": minute_to_time(stats.loc["max", "minutes"]),
        })

    return pd.DataFrame(table).set_index("weekday")



stats_str = f"""# Statistics

*updated on {datetime.date.today()}*

{time_stats_table(df_managed, df_not_managed).to_markdown()}

"""


def update_readme(stats_str: str):
    with open("README.md") as fp:
        readme = fp.read()

    stats_idx = readme.index("# Statistics")
    readme = readme[:stats_idx] + stats_str

    with open("README.md", "w") as fp:
        fp.write(readme)


print(stats_str)
update_readme(stats_str)
