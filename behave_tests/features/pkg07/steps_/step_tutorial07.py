import sys

from behave import step, when, then
from behave.runner import Context

from behave_tests.features.common import get_logger
from behave_tests.features import start_independent_test, end_independent_test, test_step, TestipyStep


@step('send message to stdout')
def send_to_stdout(context: Context):
    print(">>>>> sent to stdOUT", file=sys.stdout)


@step('send message to stderr')
def send_to_stderr(context: Context):
    print(">>>>> sent to stdERR", file=sys.stderr)


@step('log message to logger')
def log_message(context: Context):
    get_logger(context).info(">>>>> sent to log")


@when('this test is running')
def test_is_running(context: Context):
    pass

  
@then('a new test {test_name} is created')
def create_new_test(context: Context, test_name: str):
    td = start_independent_test(context, test_name, usecase="manually closed")
    with TestipyStep(context, "isolated test step 1", reason_of_state="Save screenshot", take_screenshot=True):
        pass
    end_independent_test(td)


@then('a new test {test_name} is created but not ended')
def create_new_test_not_end(context: Context, test_name: str):
    td = start_independent_test(context, test_name, usecase="automatically closed")
    test_step(context, "isolated test step 2", reason_of_state="Save screenshot", take_screenshot=True, td=td)


@step('save text {text} into context as {var_name}')
def save_text_into_context(context: Context, text: str, var_name: str):
    setattr(context, var_name, text)


@step('variable {var_name} from context has value {value}')
def get_text_from_context(context: Context, var_name: str, value: str):
    text = getattr(context, var_name)
    assert text == value
