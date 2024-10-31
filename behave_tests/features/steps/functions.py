from decimal import Decimal
from datetime import datetime, date
from typing import Any

import numpy as np
from assertpy import assert_that
from behave.runner import Context


def _get_equivalent_python_type(vartype: str) -> Any:
    types = {
        "boolean": bool,
        "string": str,
        "datetime": datetime,
        "date": date,
        "time": datetime.time,
        "struct": dict,
        "list": list,
        "array": np.ndarray,
        "none": type(None),
        "null": type(None),
        "byte": int,
        "short": int,
        "integer": int,
        "long": int,
        "float": float,
        "decimal": Decimal,
    }

    try:
        return types[vartype]
    except KeyError as err:
        raise RuntimeError(
            f"Unable to get equivalent python type for '{vartype}'"
        ) from err


def verify_field_types(context: Context, results_list: list[dict]) -> None:
    expected_column_types = context.table

    if not isinstance(results_list, list):
        results_list = [results_list]

    for row in results_list:
        assert_that(
            row.keys(), "Saved query_results don't have same amount of columns"
        ).is_length(len(expected_column_types.rows))

        for expected_column in expected_column_types:
            column_name = expected_column["column_name"]
            expected_types = expected_column["column_type"].split(",")

            assert (
                column_name in row
            ), f"Missing column {column_name} in saved query_results"

            observed_type = type(row[column_name])
            for expected_type in expected_types:
                expected_type = _get_equivalent_python_type(expected_type.strip().lower())
                if expected_type == observed_type:
                    break
            else:
                raise ValueError(
                    f"Unexpected type {observed_type} for {column_name}. {expected_types=}"
                )
