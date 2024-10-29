import json
import yaml
from behave import given, step
from behave.runner import Context

from behave_tests.features.common import get_logger, save_into_context, get_from_context, clear_context_data_bucket
from behave_tests.resources import read_resources_data_file
from common.utils.datetimes import now


@step("do nothing")
@given("we have behave installed")
def dummy_step(context: Context):
    pass


@step("I have the following {dtype} data, as {key}")
def save_into_context_data(context: Context, dtype: str, key: str):
    get_logger(context).info(context.text)

    accepted_types = {"yaml", "json", "text"}
    dtype = dtype.lower()

    if dtype == "yaml":
        data = yaml.safe_load(context.text)
    elif dtype == "json":
        data = json.loads(context.text)
    elif dtype == "text":
        data = context.text
    else:
        raise ValueError(f"Unsupported dtype: {dtype}. Only {accepted_types}")

    save_into_context(context, key, data)


@step("read resources/{filepath} file as {dtype} into {key}")
def read_resources_file_into_context(context: Context, filepath: str, dtype: str, key: str):
    data = read_resources_data_file(filepath, dtype)
    context.logging.info(f"File resources/{filepath} has {len(data)} rows")
    save_into_context(context, key, data)


@step("save current datetime in context as {key}")
def save_datetime_into_context(context: Context, key: str):
    save_into_context(context, key, now())


@step("context clear data bucket")
def clear_context_data(context: Context):
    clear_context_data_bucket(context)


@step("context clear data in {key}")
def clear_context_variable_data(context: Context, key: str):
    save_into_context(context, key, None)


@step("context has data in {key}")
def verify_context_has_variable_with_data(context: Context, key: str):
    value = get_from_context(context, key)
    if not value:
        raise ValueError(f"Variable '{key}' in context should have data!")


@step("context has no data in {key}")
def verify_context_has_variable_with_no_data(context: Context, key: str):
    value = get_from_context(context, key)
    if value:
        raise ValueError(f"Variable '{key}' in context should be empty!")
