#!/usr/bin/env python
# camcops_server/cc_modules/cc_string.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

from collections import OrderedDict
import glob
import logging
from typing import Dict, List, Optional, Tuple
import xml.etree.cElementTree as ElementTree
# ... cElementTree is a faster implementation
# ... http://docs.python.org/2/library/xml.etree.elementtree.html
# ... http://effbot.org/zone/celementtree.htm

import cardinal_pythonlib.rnc_web as ws

from .cc_cache import cache_region_static, fkg
from .cc_convert import unescape_newlines
from .cc_logger import BraceStyleAdapter
from .cc_config import pls

log = BraceStyleAdapter(logging.getLogger(__name__))


APPSTRING_TASKNAME = "camcops"


# =============================================================================
# Localization strings
# =============================================================================

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def all_extra_strings_as_dicts() -> Dict[str, Dict[str, str]]:
    """
    Returns strings from the all the extra XML string files.
    Caching is now via a proper cache.

    Returns a dictionary whose keys are tasknames,
        and whose values are each a dictionary
            whose keys are string names
            and whose values are strings.
    For example, result['phq9']['q5'] == "5. Poor appetite or overeating".
    There is also a top-level dictionary with the key APPSTRING_TASKNAME.

    The extra string files look like this:
        <?xml version="1.0" encoding="UTF-8"?>
        <resources>
            <task name="TASK_1">
                <string name="NAME_1">VALUE</string>
                <string name="NAME_2">VALUE WITH\nNEWLINE</string>
                <!-- ... -->
            </task>
            <!-- ... -->
        </resources>
    """
    if pls.EXTRA_STRING_FILES is None:
        raise AssertionError(
            "pls.EXTRA_STRING_FILES is None -- likely use of "
            "XSTRING/WXSTRING in classmethod, before initialization via "
            "the WSGI application entry point")
    allstrings = OrderedDict()
    # Glob support added 2016-01-04.
    # for filename in pls.EXTRA_STRING_FILES:
    filenames = []
    for filespec in pls.EXTRA_STRING_FILES:
        possibles = glob.glob(filespec)
        filenames.extend(possibles)
    filenames = sorted(set(filenames))  # just unique ones
    for filename in filenames:
        log.info("Loading XML file: " + filename)
        parser = ElementTree.XMLParser(encoding="UTF-8")
        tree = ElementTree.parse(filename, parser=parser)
        root = tree.getroot()
        for taskroot in root.findall("./task[@name]"):
            taskname = taskroot.attrib.get("name")
            if taskname not in allstrings:
                allstrings[taskname] = OrderedDict()
            for e in taskroot.findall("./string[@name]"):
                stringname = e.attrib.get("name")
                allstrings[taskname][stringname] = unescape_newlines(e.text)
    return allstrings


# noinspection PyPep8Naming
def XSTRING(taskname: str,
            stringname: str,
            default: str = None,
            provide_default_if_none: bool = True) -> Optional[str]:
    """Looks up a string from one of the optional extra XML string files."""
    # For speed, calculate default only if needed:
    allstrings = all_extra_strings_as_dicts()
    if taskname in allstrings:
        if stringname in allstrings[taskname]:
            return allstrings[taskname].get(stringname)
    if default is None and provide_default_if_none:
        default = "EXTRA_STRING_NOT_FOUND({}.{})".format(taskname, stringname)
    return default


# noinspection PyPep8Naming
def WXSTRING(taskname: str,
             stringname: str,
             default: str = None,
             provide_default_if_none: bool = True) -> Optional[str]:
    """Returns a web-safe version of an XSTRING (see above)."""
    value = XSTRING(taskname, stringname, default,
                    provide_default_if_none=provide_default_if_none)
    if value is None and not provide_default_if_none:
        return None
    return ws.webify(value)


def get_all_extra_strings() -> List[Tuple[str, str, str]]:
    """Returns all extra strings, as a list of (task, name, value) tuples."""
    allstrings = all_extra_strings_as_dicts()
    rows = []
    for task, subdict in allstrings.items():
        for name, value in subdict.items():
            rows.append((task, name, value))
    return rows


def task_extrastrings_exist(taskname: str) -> bool:
    """Has the server been supplied with extra strings for a specific task?"""
    allstrings = all_extra_strings_as_dicts()
    return taskname in allstrings


def wappstring(stringname: str,
               default: str = None,
               provide_default_if_none: bool = True) -> Optional[str]:
    value = XSTRING(APPSTRING_TASKNAME, stringname, default,
                    provide_default_if_none=provide_default_if_none)
    if value is None and not provide_default_if_none:
        return None
    return ws.webify(value)
