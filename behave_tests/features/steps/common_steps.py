import json
import yaml

from behave import given, step
from behave.runner import Context

from behave_tests.features.common import get_logger
from testipy.helpers.prettify import prettify


@given("we have behave installed")
def behave_is_installed(context: Context):
    pass


@step("I have the following {dtype} data")
def save_into_context_data(context: Context, dtype: str):
    get_logger(context).info(context.text)

    accepted_types = {"yaml", "json"}
    dtype = dtype.lower()

    if dtype == "yaml":
        context.data = yaml.safe_load(context.text)
    elif dtype == "json":
        context.data = json.loads(context.text)
    else:
        raise ValueError(f"Unsupported dtype: {dtype}. Only {accepted_types}")
