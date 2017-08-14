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

from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.text import unescape_newlines

from .cc_cache import cache_region_static, fkg
from .cc_config import get_config

log = BraceStyleAdapter(logging.getLogger(__name__))


APPSTRING_TASKNAME = "camcops"


# =============================================================================
# Localization strings
# =============================================================================
# In a change to thinking... Pyramid emphasizes: NO MUTABLE GLOBAL STATE.
# https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/advanced-features.html  # noqa
# This is a good thing. But it means that:
# - because we configure our XML files in our config...
# - and in principle even two different threads coming here may have different
#   configs...
# - ... that string requests need to be attached to a Pyramid Request.

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def all_extra_strings_as_dicts(
        config_filename: str) -> Dict[str, Dict[str, str]]:
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
    cfg = get_config(config_filename)
    assert cfg.EXTRA_STRING_FILES is not None
    filenames = []  # type: List [str]
    for filespec in cfg.EXTRA_STRING_FILES:
        possibles = glob.glob(filespec)
        filenames.extend(possibles)
    filenames = sorted(set(filenames))  # just unique ones
    allstrings = {}  # type: Dict[str, Dict[str, str]]
    for filename in filenames:
        log.info("Loading XML file: " + filename)
        parser = ElementTree.XMLParser(encoding="UTF-8")
        tree = ElementTree.parse(filename, parser=parser)
        root = tree.getroot()
        for taskroot in root.findall("./task[@name]"):
            taskname = taskroot.attrib.get("name")
            if taskname not in allstrings:
                allstrings[taskname] = {}  # type: Dict[str, str]
            for e in taskroot.findall("./string[@name]"):
                stringname = e.attrib.get("name")
                allstrings[taskname][stringname] = unescape_newlines(e.text)
    return allstrings
