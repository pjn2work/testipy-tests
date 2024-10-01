from behave.runner import Context
from behave.model import Feature, Scenario

from behave_tests.features.testipy_report import TestipyStep


def before_all(context: Context):
    with TestipyStep(context, "before_all"):
        context.var07_0 = "TUTORIAL_07"


def after_all(context: Context):
    with TestipyStep(context, "after_all", reason_of_state="Close package"):
        assert context.var07_0 == "TUTORIAL_07"


def before_feature(context: Context, feature: Feature):
    pass

def after_feature(context: Context, feature: Feature):
    pass

def before_scenario(context: Context, scenario: Scenario):
    pass

def after_scenario(context: Context, scenario: Scenario):
    pass
