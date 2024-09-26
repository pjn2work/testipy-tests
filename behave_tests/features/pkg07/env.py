from behave.runner import Context

from behave_tests.features.testipy_report import ReportManager, TestDetails, STATE_PASSED, STATE_FAILED


def before_all(context: Context, rm: ReportManager, td: TestDetails):
    rm.test_step(td, state=STATE_PASSED, reason_of_state="Init package")


def after_all(context: Context, rm: ReportManager, td: TestDetails):
    rm.test_step(td, state=STATE_PASSED, reason_of_state="Close package")
