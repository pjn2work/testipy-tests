from behave.model import Feature, Scenario, ScenarioOutline, Tag, Step
from behave.runner import Context

from behave_tests.features.testipy_report import (
    tear_up,
    tear_down,
    start_feature,
    end_feature,
    start_scenario,
    end_scenario,
    end_step
)


def before_all(context: Context):
    tear_up(context)

def after_all(context: Context):
    tear_down(context)


def before_feature(context: Context, feature: Feature):
    start_feature(context, feature)

def after_feature(context: Context, feature: Feature):
    end_feature(context, feature)


def before_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    start_scenario(context, scenario)

def after_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    end_scenario(context, scenario)


def before_step(context: Context, step: Step):
    pass

def after_step(context: Context, step: Step):
    end_step(context, step)


def before_tag(context: Context, tag: Tag):
    print(" -> before_tag", tag)

def after_tag(context: Context, tag: Tag):
    print(" -- after_tag", tag)
