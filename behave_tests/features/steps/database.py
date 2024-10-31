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
