#!/usr/bin/env python3

import os
from yaml import safe_load
from pkgutil import walk_packages
from importlib import import_module
from logging.config import dictConfig
from ._version import get_versions

__version__ = get_versions()["version"]
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_EXIT_MSG = "Exiting with error."

def import_submodules(package, recursive=True):
    if isinstance(package, str):
        package = import_module(package)
    results = {}
    for _, name, is_pkg in walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        if name != "__main__":
            results[full_name] = import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results

import_submodules(__name__, recursive=True)

with open(
    os.path.join(ROOT_DIR, __package__, "logger_settings.yml"), mode="r", encoding="UTF-8"
) as f:
    dictConfig(safe_load(f))

del get_versions, safe_load, walk_packages, import_module, dictConfig
