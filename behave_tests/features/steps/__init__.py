import glob
import os
import importlib.util


def load_module(file_path: str, raise_on_error: bool = True) -> object:
    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        if module_name != '__init__':
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as exc:
        if raise_on_error:
            raise exc
    return None


def import_steps_modules(directory: str):
    # Import all Python modules found in the specified directory's subdirectories.
    for file_path in glob.glob(directory + '/**/*.py', recursive=True):
        load_module(file_path, raise_on_error=True)


import_steps_modules(os.path.dirname(__file__))
