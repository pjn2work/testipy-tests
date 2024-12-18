import contextlib
import io

from behave import fixture, use_fixture
from behave.model import Feature, Scenario, ScenarioOutline, Step, Tag
from behave.runner import Context

from behave_tests.features.common import set_up_logging
from behave_tests.features.testipy_report import (
    tear_up,
    tear_down,
    start_tag,
    end_tag,
    start_feature,
    end_feature,
    start_scenario,
    end_scenario,
    start_step,
    end_step
)

# behave -D testipy="-rid 5 -r web -r-web-port 9204 -r log" behave_tests/features/pkg07 --no-capture --no-capture-stderr

def before_all(context: Context):
    tear_up(context)
    set_up_logging(context)

def after_all(context: Context):
    use_fixture(capture_logs, context)
    tear_down(context)


def before_tag(context: Context, tag: Tag):
    start_tag(context, tag)

def after_tag(context: Context, tag: Tag):
    end_tag(context, tag)


def before_feature(context: Context, feature: Feature):
    use_fixture(capture_logs, context)
    start_feature(context, feature)

def after_feature(context: Context, feature: Feature):
    end_feature(context, feature)


def before_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    use_fixture(capture_logs, context)
    start_scenario(context, scenario)

def after_scenario(context: Context, scenario: Scenario | ScenarioOutline):
    end_scenario(context, scenario)


def before_step(context: Context, step: Step):
    context.step = step
    start_step(context, step)

def after_step(context: Context, step: Step):
    end_step(context, step)
    context.step = None


@fixture
def capture_logs(context: Context):
    stdout, stderr, stdout_redirect, stderr_redirect = _capture_output(context)

    context.stdout = stdout
    context.stderr = stderr
    # context.log_stream = log_stream
    context.stdout_redirect = stdout_redirect
    context.stderr_redirect = stderr_redirect
    # context.log_handler = log_handler
    # context.logger = logger

    with stdout_redirect, stderr_redirect:
        yield

    # logger.removeHandler(log_handler)


def _capture_output(context: Context):
    stdout = io.StringIO()
    stderr = io.StringIO()
    # log_stream = io.StringIO()

    # Redirect stdout and stderr
    stdout_redirect = contextlib.redirect_stdout(stdout)
    stderr_redirect = contextlib.redirect_stderr(stderr)

    # Set up logging to capture to a stream
    # log_handler = logging.StreamHandler(log_stream)
    # logger = get_logger(context)
    # logger.addHandler(log_handler)

    return stdout, stderr, stdout_redirect, stderr_redirect
