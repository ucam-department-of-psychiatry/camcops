#!/usr/bin/env python
# cc_string.py

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
from typing import List, Optional, Tuple
import xml.etree.cElementTree as ElementTree
# ... cElementTree is a faster implementation
# ... http://docs.python.org/2/library/xml.etree.elementtree.html
# ... http://effbot.org/zone/celementtree.htm

import cardinal_pythonlib.rnc_web as ws

from .cc_convert import unescape_newlines
from .cc_logger import log
from . import cc_pls


APPSTRING_TASKNAME = "camcops"


# =============================================================================
# Localization strings
# =============================================================================

# def cache_strings() -> None:
#     """
#     Caches strings from the main XML string file.
#     The string file looks like this:
#         <?xml version="1.0" encoding="UTF-8"?>
#         <resources>
#             <string name="NAME">VALUE</string>
#             <!-- ... -->
#         </resources>
#     """
#     if cc_pls.pls.stringDict is not None:
#         return
#     if cc_pls.pls.MAIN_STRING_FILE is None:
#         raise AssertionError(
#             "pls.MAIN_STRING_FILE is None -- likely use of "
#             "LSTRING/WSTRING/wappstring/wxstring in classmethod, before "
#             "initialization via "
#             "the WSGI application entry point")
#     log.info("Loading XML file: " + cc_pls.pls.MAIN_STRING_FILE)
#     parser = ElementTree.XMLParser(encoding="UTF-8")
#     tree = ElementTree.parse(cc_pls.pls.MAIN_STRING_FILE, parser=parser)
#     cc_pls.pls.stringDict = {}
#     # find all children of the root with tag "string" and attribute "name"
#     for e in tree.findall("./string[@name]"):
#         cc_pls.pls.stringDict[e.attrib.get("name")] = unescape_newlines(e.text)  # noqa


# # noinspection PyPep8Naming
# def LSTRING(stringname: str) -> str:  # equivalent of Titanium's L()
#     """Looks up a string from the XML string file."""
#     cache_strings()
#     return cc_pls.pls.stringDict.get(stringname,
#                                      "XML_STRING_NOT_FOUND_" + stringname)


# # noinspection PyPep8Naming
# def WSTRING(stringname: str) -> str:
#     """Returns a web-safe version of a string from the XML string file."""
#     return ws.webify(LSTRING(stringname))


def cache_extra_strings() -> None:
    """
    Caches strings from the all the extra XML string files.
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
    if cc_pls.pls.extraStringDicts is not None:
        return
    if cc_pls.pls.EXTRA_STRING_FILES is None:
        raise AssertionError(
            "pls.EXTRA_STRING_FILES is None -- likely use of "
            "XSTRING/WXSTRING in classmethod, before initialization via "
            "the WSGI application entry point")
    cc_pls.pls.extraStringDicts = OrderedDict()
    # Glob support added 2016-01-04.
    # for filename in cc_pls.pls.EXTRA_STRING_FILES:
    filenames = []
    for filespec in cc_pls.pls.EXTRA_STRING_FILES:
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
            if taskname not in cc_pls.pls.extraStringDicts:
                cc_pls.pls.extraStringDicts[taskname] = OrderedDict()
            for e in taskroot.findall("./string[@name]"):
                stringname = e.attrib.get("name")
                cc_pls.pls.extraStringDicts[taskname][stringname] = (
                    unescape_newlines(e.text)
                )


# noinspection PyPep8Naming
def XSTRING(taskname: str,
            stringname: str,
            default: str = None,
            provide_default_if_none: bool = True) -> Optional[str]:
    """Looks up a string from one of the optional extra XML string files."""
    # For speed, calculate default only if needed:
    cache_extra_strings()
    if taskname in cc_pls.pls.extraStringDicts:
        if stringname in cc_pls.pls.extraStringDicts[taskname]:
            return cc_pls.pls.extraStringDicts[taskname].get(stringname)
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
    cache_extra_strings()
    rows = []
    for task, subdict in cc_pls.pls.extraStringDicts.items():
        for name, value in subdict.items():
            rows.append((task, name, value))
    return rows


def task_extrastrings_exist(taskname: str) -> bool:
    """Has the server been supplied with extra strings for a specific task?"""
    cache_extra_strings()
    return taskname in cc_pls.pls.extraStringDicts


def wappstring(stringname: str,
               default: str = None,
               provide_default_if_none: bool = True) -> Optional[str]:
    value = XSTRING(APPSTRING_TASKNAME, stringname, default,
                    provide_default_if_none=provide_default_if_none)
    if value is None and not provide_default_if_none:
        return None
    return ws.webify(value)
