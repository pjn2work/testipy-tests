import yaml

from behave import given, step
from behave.runner import Context

from behave_tests.features.common import get_logger
from testipy.helpers.prettify import prettify


@given("we have behave installed")
def behave_is_installed(context: Context):
    pass


@step("I have the following YAML data")
def save_into_context_yaml(context: Context):
    context.data = yaml.safe_load(context.text)
    get_logger(context).info(prettify(context.data, as_yaml=True))
