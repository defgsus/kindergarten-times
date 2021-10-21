import requests
import csv
import zipfile
import datetime
import os
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd


class Weather:

    CACHE = Path(__file__).resolve().parent.parent / "cache"
    STATION_ID = "02444"

    DATA_POINTS = (
        ("TU", "air_temperature", {"TT_TU": "temp200"}),
        # ("C", "cloudiness"),  # unfortunately not available for Jena
        ("TD", "dew_point", {"TD": "dew_point"}),
        # ("FX", "extreme_wind"),
        ("TF", "moisture", {"P_STD": "air_pressure", "TD_STD": "dew_temp200", "VP_STD": "steam_pressure"}),
        ("RR", "precipitation", {"R1": "rain"}),
        # ("P0", "pressure"),
        ("EB", "soil_temperature", {"V_TE005": "temp005", "V_TE100": "temp100"}),
        # ("SD", "sun"),  # not available since 1991
        # ("VV", "visibility"),
        # ("WW", "weather_phenomena"),
        # ("FF", "wind"),
        # ("F", "wind_synop"),
    )

    BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly"

    def __init__(self):
        self._data = dict()

    def table(self, hour: Optional[int] = None):
        if not self._data:
            self._update_cache()
            self._load_tables()

        df = pd.DataFrame(self._data).T
        df.index = pd.to_datetime(df.index)
        df.sort_index(axis=0, inplace=True)
        df.sort_index(axis=1, inplace=True)
        if hour:
            df = df[df.index.hour == hour]
            df.index = df.index.date
        df.index = pd.to_datetime(df.index).rename("date")
        return df

    def _update_cache(self):
        for code, path, mapping in self.DATA_POINTS:
            filename = self.CACHE / f"{path}-recent.zip"
            if filename.exists():
                file_date = datetime.date.fromtimestamp(filename.stat().st_mtime)
                if file_date == datetime.date.today():
                    continue

            url = f"{self.BASE_URL}/{path}/recent/stundenwerte_{code}_{self.STATION_ID}_akt.zip"
            print(f"downloading {url}", file=sys.stderr)
            response = requests.get(url)
            assert response.status_code == 200, f"Status {response.status_code}: {url}"
            os.makedirs(self.CACHE, exist_ok=True)
            filename.write_bytes(response.content)

    def _load_table(self, fp: BytesIO, code: str, path: str, mapping: dict):
        lines = fp.read().decode("utf-8").splitlines()
        reader = csv.DictReader(lines, delimiter=";", skipinitialspace=True)
        for row in list(reader):
            date = datetime.datetime.strptime(row["MESS_DATUM"], "%Y%m%d%H")
            for key, name in mapping.items():
                try:
                    self._data.setdefault(date, {}).update({name: self._to_float(row[key])})
                except KeyError:
                    raise KeyError(f"{key} not in {row.keys()} in {path}")

    def _load_tables(self):
        for code, path, mapping in self.DATA_POINTS:
            with zipfile.ZipFile(self.CACHE / f"{path}-recent.zip") as zipf:
                for fn in zipf.filelist:
                    if fn.filename.startswith(f"produkt_{code.lower()}_stunde"):
                        with zipf.open(fn) as fp:
                            self._load_table(fp, code, path, mapping)

    @classmethod
    def _to_float(cls, v) -> Optional[float]:
        if v == "-999":
            return None
        return float(v)


if __name__ == "__main__":
    import pandas as pd
    df = Weather().table(hour=8)
    print(df)
