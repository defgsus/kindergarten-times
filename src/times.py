import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from .weather import Weather


class Times:
    def __init__(self):
        df = pd.read_csv(Path(__file__).resolve().parent.parent / "times.csv")
        df["date"] = pd.to_datetime(df["date"])
        df["weekday"] = [
            row["date"].strftime("%A")
            for i, row in df.iterrows()
        ]
        df["minutes"] = [
            self.time_to_minutes(row["arrival"])
            for _, row in df.iterrows()
        ]
        df.set_index("date", inplace=True)

        self.df_weather = Weather().table(hour=8)
        df = df.join(self.df_weather)

        self.df = df
        self.df_not_managed = df[pd.isna(df["arrival"])]

        self.df_managed = df[~pd.isna(df["arrival"])].copy()

    @classmethod
    def time_to_minutes(cls, t: str) -> Optional[int]:
        try:
            tup = t.split(":")
            return int(tup[0]) * 60 + int(tup[1])
        except AttributeError:
            pass

    @classmethod
    def minutes_to_time(cls, m: int) -> str:
        m = int(round(m))
        return f"{m//60}:{m%60:02d}"