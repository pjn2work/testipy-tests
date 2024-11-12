import os
from typing import Literal

from common.utils.files import read_data_file


RESOURCES_FOLDER = os.path.dirname(os.path.abspath(__file__))


def get_resources_abspath(relative_path: str) -> str:
    return os.path.join(RESOURCES_FOLDER, relative_path)


def read_resources_data_file(
        relative_path: str,
        dtype: Literal["yaml", "json", "text", "csv"],
        **csv_kwargs
) -> dict | list[dict] | list[str]:
    absolute_path = get_resources_abspath(relative_path)
    return read_data_file(absolute_path, dtype, **csv_kwargs)
