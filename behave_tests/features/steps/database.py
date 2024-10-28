from decimal import Decimal
from datetime import datetime, date
from typing import Any

import numpy as np
from assertpy import assert_that
from behave import step
from behave.runner import Context

from behave_tests.features.common import get_logger, save_into_context, get_from_context, has_key_in_context


@step("query {table_name} table and save in context, when column {col_name} is after {after} ")
def save_queried_table_into_context_after(
    context: Context, table_name: str, col_name: str, after: str
):
    _save_queried_table_into_context(
        context, table_name, filter_after=after, after_col_name=col_name
    )


@step("query {table_name} table and save in context")
def save_queried_table_into_context(context: Context, table_name: str) -> None:
    _save_queried_table_into_context(
        context, table_name, filter_after="", after_col_name=""
    )


@step("table {table_name} was already saved in context")
def is_table_in_context(context: Context, table_name: str) -> None:
    if not has_key_in_context(context, table_name):
        raise KeyError(f"{table_name} was not saved in context before.")


@step("data from {table_name}, must have {expected_len:d} entries")
def verify_size_for_table(context: Context, table_name: str, expected_len: int):
    table_data: list[dict] = get_from_context(context, table_name)
    observed_len = len(table_data)
    assert observed_len == expected_len, f"Expected exactly {expected_len} results inside {table_name}. And not {observed_len}."


@step("data from {table_name}, must have the following types")
def verify_table_field_types_from_context(context: Context, table_name: str):
    table_data: list[dict] = get_from_context(context, table_name)

    assert len(table_data) > 0, f"Expected some results inside {table_name}"

    _verify_field_types(context, table_data)


def _save_queried_table_into_context(
    context: Context, table_name: str, filter_after: str, after_col_name: str
) -> None:
    qm = context.query_manager
    database_name, just_table_name = table_name.split(".")

    if filter_after and after_col_name:
        after = get_from_context(context, filter_after)
        error_msg = f" when {after_col_name} is after {after}."
    else:
        error_msg = "."
        after = None

    results: list[dict] = qm.get_table_data(
        context=context, database=database_name, table=just_table_name,
        after_col_name=after_col_name, after_datetime=after
    )

    if len(results) == 0:
        get_logger(context).warning(
            f"Expected some results for {table_name}{error_msg}"
        )

    save_into_context(context, table_name, results)


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


def _verify_field_types(context: Context, results_list: list[dict]) -> None:
    expected_column_types = context.table

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
