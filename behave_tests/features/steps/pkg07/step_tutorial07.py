import sys

from behave import step, when, then
from behave.runner import Context

from behave_tests.features.common import get_logger
from behave_tests.features.testipy_report import start_independent_test, end_independent_test, get_rm, STATE_PASSED


@step('send message to stdout')
def send_to_stdout(context: Context):
    print(">>>>> sent to stdOUT", file=sys.stdout)


@step('send message to stderr')
def send_to_stderr(context: Context):
    print(">>>>> sent to stdERR", file=sys.stderr)


@step('log message to logger')
def log_message(context: Context):
    get_logger().info(">>>>> sent to log")


@when('this test is running')
def test_is_running(context: Context):
    pass


@then('a new test is created')
def create_new_test(context: Context):
    td = start_independent_test(context, "manually created")
    get_rm().test_step(td, state=STATE_PASSED, reason_of_state="Save screenshot", take_screenshot=True)
    end_independent_test(context)
