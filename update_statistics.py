import datetime
import pandas as pd
import numpy as np

from src.times import Times


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
            "mean arrival": Times.minutes_to_time(stats.loc["mean", "minutes"]),
            "earliest": Times.minutes_to_time(stats.loc["min", "minutes"]),
            "latest": Times.minutes_to_time(stats.loc["max", "minutes"]),
        })

    return pd.DataFrame(table).set_index("weekday")


def weather_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["temperature"] = (df["temp200"] / 3).round() * 3
    #df["selector"] = df["steam_pressure"].round()
    #df["selector"] = df["dew_point"].round()
    grouped = df.groupby("temperature")
    yes_no = grouped.sum()[["yes", "no"]]
    minutes = grouped.mean()["minutes"].map(Times.minutes_to_time)
    df = yes_no.join(minutes).T
    df.index = ["driven", "not driven", "mean arrival"]
    return df


def update_readme():
    times = Times()

    stats_str = f"""# Statistics

*updated on {datetime.date.today()}*

#### by weekday

{time_stats_table(times.df_managed, times.df_not_managed).to_markdown()}

#### by temperature

{weather_stats_table(times.df).to_markdown()}

"""
    print(stats_str)

    with open("README.md") as fp:
        readme = fp.read()

    stats_idx = readme.index("# Statistics")
    readme = readme[:stats_idx] + stats_str

    with open("README.md", "w") as fp:
        fp.write(readme)


update_readme()
