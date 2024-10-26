from .context_utils import *
from .log import get_logger, set_up_logging
from .modules import load_module, import_steps_modules


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
