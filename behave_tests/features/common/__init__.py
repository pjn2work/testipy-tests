from .context_utils import get_from_context, save_into_context, get_data_bucket_from_context
from .log import get_logger, set_up_logging
from .modules import load_module, import_steps_modules
from .tags import filter_tags_with_prefix, get_all_tags_with_prefix, get_tag_values_for_prefix


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
