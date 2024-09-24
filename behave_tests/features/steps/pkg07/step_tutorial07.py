from behave import given, when, then
from behave.runner import Context

from behave_tests.features.testipy_report import start_independent_test, end_independent_test, get_rm, STATE_PASSED


@given('we2 have behave installed')
def step_impl7(context: Context):
    print(">>>>> given 7", context)

    td = start_independent_test(context, "test_07")
    rm = get_rm()
    rm.test_step(td, state=STATE_PASSED, reason_of_state="Save screenshot", take_screenshot=True)
    end_independent_test(context)
