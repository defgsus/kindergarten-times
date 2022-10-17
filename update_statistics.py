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
            "median arrival": Times.minutes_to_time(df2["minutes"].median()),
            "earliest": Times.minutes_to_time(stats.loc["min", "minutes"]),
            "latest": Times.minutes_to_time(stats.loc["max", "minutes"]),
        })

    return pd.DataFrame(table).set_index("weekday")


def weather_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["tag"] != "short-friday"]

    df["temperature"] = (df["temp200"] / 3).round() * 3
    #df["selector"] = df["steam_pressure"].round()
    #df["selector"] = df["dew_point"].round()
    grouped = df.groupby("temperature")
    yes_no = grouped.sum()[["yes", "no"]]
    minutes = grouped.mean()["minutes"].map(Times.minutes_to_time)
    df = yes_no.join(minutes).T
    df.index = ["driven", "not driven", "mean arrival"]
    return df


def consecutive_days(df: pd.DataFrame) -> pd.DataFrame:
    count_dict = {
        i: 0
        for i in range(1, 6)
    }
    counter = 0
    df = df.resample("1d").sum()
    # print(df.to_markdown())
    all = 0
    for i, row in df.iterrows():
        if row["yes"]:
            counter += 1
            all += 1
        elif counter:
            count_dict[counter] += 1
            counter = 0
    df = pd.DataFrame(
        count_dict.values(),
        index=count_dict.keys(),
        columns=["number of times"],
    )
    df.index.rename("days in row", inplace=True)
    df.sort_index(inplace=True)
    return df.replace({0: "-"})


def update_readme():
    times = Times()

    stats_str = f"""# Statistics

*updated on {datetime.date.today()}*

#### by weekday

{time_stats_table(times.df_managed, times.df_not_managed).to_markdown()}

#### by temperature

{weather_stats_table(times.df).to_markdown()}

#### consecutive kindergarten days

{consecutive_days(times.df_managed).to_markdown()}

"""
    print(stats_str)

    with open("README.md") as fp:
        readme = fp.read()

    stats_idx = readme.index("# Statistics")
    readme = readme[:stats_idx] + stats_str

    with open("README.md", "w") as fp:
        fp.write(readme)


update_readme()
