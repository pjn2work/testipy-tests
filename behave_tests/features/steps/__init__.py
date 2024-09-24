import glob
import os
import importlib.util


def import_steps_modules(directory: str):
    # Import all Python modules found in the specified directory's subdirectories.
    for file_path in glob.glob(directory + '/**/*.py', recursive=True):
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        if module_name != '__init__':
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)


import_steps_modules(os.path.dirname(__file__))