#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_string.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**Manage the "extra strings" that the server reads from XML files. The server
uses these for displaying tasks, and provides them to client devices.**

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

from camcops_server.cc_modules.cc_cache import cache_region_static, fkg
from camcops_server.cc_modules.cc_config import get_config
from camcops_server.cc_modules.cc_exception import raise_runtime_error

log = BraceStyleAdapter(logging.getLogger(__name__))


APPSTRING_TASKNAME = "camcops"
MISSING_LOCALE = ""


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
    Extract the exact text contents of an XML element, including any XML/HTML
    tags within it.

    A normal string looks like

    .. code-block:: xml

        <string name="stringname">words words words</string>

    and we extract its contents ("words words words") with

    .. code-block:: python

        e.text

    However, for this:

    .. code-block:: xml

        <string name="stringname">words <b>bold words</b> words</string>

    we want to extract ``words <b>bold words</b> words`` and that's a little
    trickier. This function does that.

    Args:
        e: the :class:`Element` to read
        plain: remove all HTML/XML tags?
        strip: strip leading/trailing whitespace?

    Returns:
        the text contents of the element
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
        config_filename: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    r"""
    Returns strings from the all the extra XML string files.

    The result is cached (via a proper cache).

    Args:
        config_filename: a CamCOPS config filename

    Returns: a dictionary like

        .. code-block:: none

            {
                'task1': {
                    'stringname1': {
                        "en-GB": "a string in British English",
                        "da-DK": "a string in Danish",
                    },
                    'stringname1': {
                    },
                },
                'task2: {
                    ...
                },
                ...
            }

    ... in other words a ``Dict[taskname: str, Dict[stringname: str,
    Dict[locale: str, stringvalue: str]]]``.

    For example, ``result['phq9']['q5'][locale] == "5. Poor appetite or
    overeating"``. There is also a top-level dictionary with the key
    ``APPSTRING_TASKNAME``.

    **XML format**

    The extra string files should look like this:

    .. code-block:: xml

        <?xml version="1.0" encoding="UTF-8"?>
        <resources>
            <task name="TASK_1" locale="en_GB">
                <string name="NAME_1">VALUE</string>
                <string name="NAME_2">VALUE WITH\nNEWLINE</string>
                <!-- ... -->
            </task>
            <!-- ... -->
        </resources>

    If the ``language`` attribute is not specified, a language tag of ``""`` is
    used internally and will be the fallback position if nothing else is found.

    """
    _ = """
    The extra string files looked like this prior to 2019-05-05:

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

    Designing XML:

    - an "element" looks like ``<thing>blah</thing>``, or ``<thing />``;
      the "element name" is "thing" in this example, and "blah" is called the
      "content".
    - the delimiters of an element are tags: start tags such as ``<thing>``,
      end tags such as ``</thing>``, or empty-element tags such as
      ``<thing />``.
    - an "attribute" is a name-value pair, e.g. ``<tagname attrname=value
      ...>``; "attrname" in this example is called the "attribute name".
    - So you can add information via the element structure or the attribute
      system.

    So, as we add language support (2019-05-05), we start with:

    - element names for types of information (task, string)
    - attribute values for labelling the content
    - content for the string data

    There are many ways we could add language information. Adding an attribute
    to every string seems verbose, though. We could use one of these systems:

    .. code-block:: xml

        <?xml version="1.0" encoding="UTF-8"?>
        <resources>
            <task name="TASK_1">
                <locale name="en_GB">
                    <string name="NAME_1">VALUE</string>
                    <string name="NAME_2">VALUE WITH\nNEWLINE</string>
                    <!-- ... -->
                </locale>
            </task>
            <!-- ... -->
        </resources>

    .. code-block:: xml

        <?xml version="1.0" encoding="UTF-8"?>
        <resources>
            <task name="TASK_1" locale="en_GB">
                <string name="NAME_1">VALUE</string>
                <string name="NAME_2">VALUE WITH\nNEWLINE</string>
                <!-- ... -->
            </task>
            <!-- ... -->
        </resources>

    The second seems a bit clearer (fewer levels). Let's do that. It also makes
    all existing XML files automatically compatible (with minor code
    adaptations).
    """

    cfg = get_config(config_filename)
    assert cfg.extra_string_files is not None
    filenames = []  # type: List [str]
    for filespec in cfg.extra_string_files:
        possibles = glob.glob(filespec)
        filenames.extend(possibles)
    filenames = sorted(set(filenames))  # just unique ones
    if not filenames:
        raise_runtime_error("No CamCOPS extra string files specified; "
                            "config is misconfigured; aborting")
    allstrings = {}  # type: Dict[str, Dict[str, Dict[str, str]]]
    for filename in filenames:
        log.info("Loading string XML file: {}", filename)
        parser = ElementTree.XMLParser(encoding="UTF-8")
        tree = ElementTree.parse(filename, parser=parser)
        root = tree.getroot()
        # We'll search via an XPath. See
        # https://docs.python.org/3.7/library/xml.etree.elementtree.html#xpath-support  # noqa
        for taskroot in root.findall("./task[@name]"):
            # ... "all elements with the tag 'task' that have an attribute
            # named 'name'"
            taskname = taskroot.attrib.get("name")
            locale = taskroot.attrib.get("locale", MISSING_LOCALE)
            taskstrings = allstrings.setdefault(taskname, {})  # type: Dict[str, Dict[str, str]]  # noqa
            for e in taskroot.findall("./string[@name]"):
                # ... "all elements with the tag 'string' that have an attribute
                # named 'name'"
                stringname = e.attrib.get("name")
                final_string = text_contents(e)
                final_string = unescape_newlines(final_string)
                langversions = taskstrings.setdefault(stringname, {})  # type: Dict[str, str]  # noqa
                langversions[locale] = final_string

    if APPSTRING_TASKNAME not in allstrings:
        raise_runtime_error(
            "Extra string files do not contain core CamCOPS strings; "
            "config is misconfigured; aborting")

    return allstrings
