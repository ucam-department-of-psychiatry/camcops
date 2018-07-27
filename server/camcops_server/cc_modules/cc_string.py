#!/usr/bin/env python
# camcops_server/cc_modules/cc_string.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

import glob
import logging
from typing import Dict, List
import xml.etree.cElementTree as ElementTree
# ... cElementTree is a faster implementation
# ... http://docs.python.org/2/library/xml.etree.elementtree.html
# ... http://effbot.org/zone/celementtree.htm
from xml.etree.ElementTree import Element, tostring

from cardinal_pythonlib.logs import BraceStyleAdapter
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


def text_contents(e: Element, plain: bool = False, strip: bool = True) -> str:
    """
    A normal string looks like

        .. code-block:: xml

            <string name="stringname">words words words</string>

    and we extract its contents ("words words words") with

        .. code-block:: python

            e.text

    However, for this:

        .. code-block:: xml

            <string name="stringname">words <b>bold words</b> words</string>

    we want to extract "words <b>bold words</b> words" and that's a little
    trickier.
    """
    n_children = len(e)
    if n_children == 0:
        result = e.text or ""
    elif plain:
        result = "".join(e.itertext())  # e.g. "words bold words words"
    else:
        result = (
            (e.text or "") +
            "".join(tostring(child, encoding="unicode") for child in e) +
            (e.tail or "")
        )
    if strip:
        return result.strip()
    else:
        return result


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def all_extra_strings_as_dicts(
        config_filename: str) -> Dict[str, Dict[str, str]]:
    r"""
    Returns strings from the all the extra XML string files.
    Caching is now via a proper cache.

    - Returns a dictionary whose keys are tasknames,

      - and whose values are each a dictionary

        - whose keys are string names
        - and whose values are strings.

    For example, ``result['phq9']['q5'] == "5. Poor appetite or overeating"``.
    There is also a top-level dictionary with the key APPSTRING_TASKNAME.

    The extra string files look like this:

    .. code-block:: xml

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
    assert cfg.extra_string_files is not None
    filenames = []  # type: List [str]
    for filespec in cfg.extra_string_files:
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
                final_string = text_contents(e)
                final_string = unescape_newlines(final_string)
                allstrings[taskname][stringname] = final_string

    return allstrings
