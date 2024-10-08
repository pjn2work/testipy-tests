import os
import logging
from typing import TYPE_CHECKING

from behave.runner import Context

if TYPE_CHECKING:
    from behave_tests.features.testipy_report import TestipyReporting


_logger = logging.getLogger("TestiPy_demo")


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Convert the absolute path to a relative path (relative to current working directory)
        record.relativepathname = os.path.relpath(record.pathname)

        context = record.behave_context
        if hasattr(context, "step"):
            record.behavestep = f"{context.step.keyword} {context.step.name}\n"
        else:
            record.behavestep = ""

        return super().format(record)


class TestiPyLogHandler(logging.Handler):
    def __init__(self, context: Context):
        super().__init__()
        self.context: Context = context

    def emit(self, record):
        testipy_reporting: TestipyReporting = self.context.testipy_reporting
        current_test = testipy_reporting.get_current_test(self.context)

        record.behave_context = self.context
        level, info = record.levelname, self.format(record)
        testipy_reporting.rm.test_info(current_test, info=info, level=level)


def set_up_logging(context: Context):
    # Configure logging
    context.logging = _logger
    context.config.setup_logging(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
        force=True
    )

    # Create a custom TestiPy log handler
    testipy_log_handler = TestiPyLogHandler(context)
    testipy_log_handler.setLevel(logging.DEBUG)
    formatter = CustomFormatter("%(behavestep)s%(relativepathname)s:%(lineno)d - %(funcName)s\n%(message)s")
    testipy_log_handler.setFormatter(formatter)
    context.logging.addHandler(testipy_log_handler)

    # Turn down logging
    other_loggers = [
        logging.getLogger("testipy"),
        logging.getLogger("geventwebsocket"),
        logging.getLogger("parse"),
    ]
    for logger in other_loggers:
        logger.setLevel(logging.WARNING)


def get_logger(context: Context):
    # return _logger
    return context.logging
