from behave.runner import Context
from behave.model import Feature, Scenario

from behave_tests.features.testipy_report import TestipyStep
from behave_tests.features.common import get_all_features_tags_with_prefix, get_logger

def before_all(context: Context):
    with TestipyStep(context, "before_all"):
        context.var07_0 = "TUTORIAL_07"
    with TestipyStep(context, "get features tags @setup."):
        tags = get_all_features_tags_with_prefix(context, prefix="setup.", trim_prefix=False)
        tag_values = get_all_features_tags_with_prefix(context, prefix="setup.", trim_prefix=True)
        get_logger(context).info(f"Tags: {tags}\nValues: {tag_values}")


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
