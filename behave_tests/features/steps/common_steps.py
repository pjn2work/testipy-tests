import json
import yaml

from behave import given, step
from behave.runner import Context

from behave_tests.features.common import get_logger


@step("do nothing")
@given("we have behave installed")
def dummy_step(context: Context):
    pass


@step("I have the following {dtype} data")
def save_into_context_data(context: Context, dtype: str):
    get_logger(context).info(context.text)

    accepted_types = {"yaml", "json", "text"}
    dtype = dtype.lower()

    if dtype == "yaml":
        context.data = yaml.safe_load(context.text)
    elif dtype == "json":
        context.data = json.loads(context.text)
    elif dtype == "text":
        context.data = context.text
    else:
        raise ValueError(f"Unsupported dtype: {dtype}. Only {accepted_types}")
