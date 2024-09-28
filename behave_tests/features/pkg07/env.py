from behave.runner import Context

from behave_tests.features.testipy_report import TestipyStep


def before_all(context: Context):
    with TestipyStep(context, "before_all"):
        context.var07_0 = "TUTORIAL_07"


def after_all(context: Context):
    with TestipyStep(context, "after_all", reason_of_state="Close package"):
        assert context.var07_0 == "TUTORIAL_07"
