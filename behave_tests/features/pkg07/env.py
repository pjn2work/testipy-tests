from behave.runner import Context

from behave_tests.features.testipy_report import start_independent_test, get_rm, end_independent_test, STATE_PASSED


def before_all(context: Context):
    td = start_independent_test(context, test_name="Before All")
    get_rm().test_step(td, state=STATE_PASSED, reason_of_state="Init package")
    end_independent_test(context)


def after_all(context: Context):
    td = start_independent_test(context, test_name="After All")
    get_rm().test_step(td, state=STATE_PASSED, reason_of_state="Close package")
    end_independent_test(context)
