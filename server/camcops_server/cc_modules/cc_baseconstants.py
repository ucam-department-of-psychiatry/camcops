#!/usr/bin/env python
# cc_baseconstants.py

"""
Constants required during package creation, which therefore can't rely on 
anything except the Python standard library.
"""

import os

_this_directory = os.path.dirname(os.path.abspath(__file__))
CAMCOPS_SERVER_DIRECTORY = os.path.abspath(
    os.path.join(_this_directory,  # cc_modules
                 os.pardir))  # camcops_server
TABLET_SOURCE_COPY_DIR = os.path.join(CAMCOPS_SERVER_DIRECTORY,
                                      "tablet_source_copy")

INTROSPECTABLE_EXTENSIONS = [".cpp", ".h", ".html", ".js", ".jsx",
                             ".py", ".pl", ".xml"]
