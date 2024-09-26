import logging

from behave.runner import Context


_logger = logging.getLogger("TestiPy_demo")


def set_up_logging(context: Context):
    # Configure logging
    context.config.setup_logging(
        level=logging.DEBUG, format="%(name)s - %(filename)s - %(lineno)d - %(message)s", force=True
    )
    context.logging = get_logger()

    # Turn down logging
    other_loggers = [
        logging.getLogger("testipy"),
        logging.getLogger("geventwebsocket"),
    ]
    for logger in other_loggers:
        logger.setLevel(logging.WARNING)


def get_logger():
    return _logger
