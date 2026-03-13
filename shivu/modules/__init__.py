import logging
import sys
import time
import random
from shivu import *
from functools import wraps
from telegram import Update
from shivu.utils import * 
from .watchers import *
from .lock import *


StartTime = time.time()
dev_users = {8535832693}

sudb = db.sudo
devb = db.dev 

# enable logging

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

LOAD = []
NO_LOAD = []

def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    # This generates a list of modules in this folder for the * in __main__ to work.
    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    # Keep Holi event modules out of default module loading.
    all_modules = [m for m in all_modules if m.lower() != "holievent"]

    if LOAD or NO_LOAD:
        to_load = LOAD
        if to_load:
            if not all(
                any(mod == module_name for module_name in all_modules)
                for mod in to_load
            ):
                print("Invalid loadorder names, Quitting...")
                quit(1)

            all_modules = sorted(set(all_modules) - set(to_load))
            to_load = list(all_modules) + to_load

        else:
            to_load = all_modules

        if NO_LOAD:
            print("Not loading: {}".format(NO_LOAD))
            return [item for item in to_load if item not in NO_LOAD]

        return to_load

    return all_modules


ALL_MODULES = __list_all_modules()
print("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]
