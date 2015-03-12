#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import xml.etree.cElementTree as ElementTree
# ... cElementTree is a faster implementation
# ... http://docs.python.org/2/library/xml.etree.elementtree.html
# ... http://effbot.org/zone/celementtree.htm

import rnc_web as ws

from cc_logger import logger
import cc_pls


# =============================================================================
# Localization strings
# =============================================================================

def LSTRING(stringname):  # equivalent of Titanium's L()
    """Looks up a string from the XML string file."""
    if cc_pls.pls.stringDict is None:
        if cc_pls.pls.CAMCOPS_STRINGS_FILE_ABSOLUTE is None:
            raise AssertionError(
                "pls.CAMCOPS_STRINGS_FILE_ABSOLUTE is None -- likely use of "
                "LSTRING/WSTRING in classmethod, before initialization via "
                "the WSGI application entry point")
        logger.debug("Loading XML file: " +
                     cc_pls.pls.CAMCOPS_STRINGS_FILE_ABSOLUTE)
        parser = ElementTree.XMLParser(encoding="UTF-8")
        tree = ElementTree.parse(cc_pls.pls.CAMCOPS_STRINGS_FILE_ABSOLUTE,
                                 parser=parser)
        cc_pls.pls.stringDict = {}
        # find all children of the root with tag "string" and attribute "name"
        for e in tree.findall("./string[@name]"):
            cc_pls.pls.stringDict[e.attrib.get("name")] = e.text

    return cc_pls.pls.stringDict.get(stringname,
                                     "XML_STRING_NOT_FOUND_" + stringname)


def WSTRING(stringname):
    """Returns a web-safe version of a string from the XML string file."""
    return ws.webify(LSTRING(stringname))
