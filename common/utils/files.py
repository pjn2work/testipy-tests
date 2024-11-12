import json
from typing import Literal

import pandas as pd
import yaml


def read_data_file(
        filepath: str,
        dtype: Literal["yaml", "json", "text", "csv"],
        **csv_kwargs,
) -> dict | list[dict] | list[str]:
    dtype = dtype.lower()
    with open(filepath, "r") as f:
        if dtype == "yaml":
            data = yaml.full_load(f)
        elif dtype == "json":
            data = json.load(f)
        elif dtype == "text":
            data = str(f.read()).split("\n")
        elif dtype == "csv":
            data = pd.read_csv(f, **csv_kwargs).to_dict("records")
        else:
            raise ValueError(f"Unsupported data file type: {dtype}.")

        return data
