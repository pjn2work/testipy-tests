import contextlib
import io
import logging

from behave import fixture, use_fixture
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
    use_fixture(capture_logs, context)
    start_scenario(context, scenario)

def after_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    end_scenario(context, scenario)


def before_step(context: Context, step: Step):
    pass

def after_step(context: Context, step: Step):
    end_step(context, step)


def before_tag(context: Context, tag: Tag):
    pass

def after_tag(context: Context, tag: Tag):
    pass


@fixture
def capture_logs(context):
    stdout, stderr, log_stream, stdout_redirect, stderr_redirect, log_handler, logger = _capture_output()

    context.stdout = stdout
    context.stderr = stderr
    context.log_stream = log_stream
    context.stdout_redirect = stdout_redirect
    context.stderr_redirect = stderr_redirect
    context.log_handler = log_handler
    context.logger = logger

    with stdout_redirect, stderr_redirect:
        yield

    logger.removeHandler(log_handler)


def _capture_output():
    stdout = io.StringIO()
    stderr = io.StringIO()
    log_stream = io.StringIO()

    # Redirect stdout and stderr
    stdout_redirect = contextlib.redirect_stdout(stdout)
    stderr_redirect = contextlib.redirect_stderr(stderr)

    # Set up logging to capture to a stream
    log_handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger("TestiPy_demo")
    logger.addHandler(log_handler)

    return stdout, stderr, log_stream, stdout_redirect, stderr_redirect, log_handler, logger