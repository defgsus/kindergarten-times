import requests
import csv
import zipfile
import datetime
import os
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd


class Weather:

    CACHE = Path(__file__).resolve().parent.parent / "cache"
    STATION_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/" \
                  "climate/daily/kl/recent/tageswerte_KL_02444_akt.zip"
    STATION_FILE = CACHE / "2224-recent.zip"

    def __init__(self):
        self._data = dict()

    def table(self):
        if not self._data:
            self._update_cache()
            with zipfile.ZipFile(self.STATION_FILE) as zipf:
                for fn in zipf.filelist:
                    if fn.filename.startswith("produkt_klima_tag"):
                        with zipf.open(fn) as fp:
                            self._load_table(fp)
        df = pd.DataFrame(self._data).T
        df.index = pd.to_datetime(df.index).rename("date")
        return df

    def _update_cache(self):
        if self.STATION_FILE.exists():
            file_date = datetime.date.fromtimestamp(self.STATION_FILE.stat().st_mtime)
            if file_date == datetime.date.today():
                return

        response = requests.get(self.STATION_URL)
        os.makedirs(self.CACHE, exist_ok=True)
        self.STATION_FILE.write_bytes(response.content)

    def _load_table(self, fp: BytesIO):
        lines = fp.read().decode("utf-8").splitlines()
        reader = csv.DictReader(lines, delimiter=";", skipinitialspace=True)
        for row in list(reader):
            date = datetime.datetime.strptime(row["MESS_DATUM"], "%Y%m%d").date()
            self._data[date] = {
                "rain": self._to_float(row["RSK"]),
                # not available for Jena since 1991
                # "sun": self._to_float(row["SDK"]),
                "temp": self._to_float(row["TMK"]),
                "moist": self._to_float(row["UPM"]),
            }

    @classmethod
    def _to_float(cls, v) -> Optional[float]:
        if v == "-999":
            return None
        return float(v)


if __name__ == "__main__":
    import pandas as pd
    df = Weather().table()
    print(df)
