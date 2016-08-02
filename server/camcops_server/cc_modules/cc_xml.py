#!/usr/bin/env python3
# cc_xml.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

import base64
from typing import Dict, List, Optional
import xml.sax.saxutils

from cardinal_pythonlib.rnc_db import FIELDSPEC_TYPE, FIELDSPECLIST_TYPE

from . import cc_db
from . import cc_namedtuples
from .cc_namedtuples import XmlElementTuple

# =============================================================================
# Constants
# =============================================================================

XML_COMMENT_ANONYMOUS = "<!-- Anonymous task; no patient info -->"
XML_COMMENT_BLOBS = "<!-- Associated BLOBs -->"
XML_COMMENT_CALCULATED = "<!-- Calculated fields -->"
XML_COMMENT_PATIENT = "<!-- Associated patient details -->"
XML_COMMENT_SPECIAL_NOTES = "<!-- Any special notes added -->"
XML_COMMENT_STORED = "<!-- Stored fields -->"

XML_NAMESPACES = [
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    # ' xmlns:dt="http://www.w3.org/2001/XMLSchema-datatypes"'
]
XML_IGNORE_NAMESPACES = [
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"',
    'xmlns:ignore="http://www.camcops.org/ignore"',
    # ... actual URL unimportant
    'mc:Ignorable="ignore"'
]
# http://www.w3.org/TR/xmlschema-1/
# http://www.w3.org/TR/2004/REC-xmlschema-2-20041028/datatypes.html


# =============================================================================
# XML processing
# =============================================================================
# The xml.etree.ElementTree and lxml libraries can both do this sort of thing.
# However, they do look quite fiddly and we only want to create something
# simple. Therefore, let's roll our own:

def make_xml_branches_from_fieldspecs(
        obj,
        fieldspecs: FIELDSPECLIST_TYPE,
        skip_fields: List[str] = None) -> List[XmlElementTuple]:
    """Returns a list of XML branches, each an XmlElementTuple, from an
    objects and the list of fieldspecs that define/describe its fields."""
    skip_fields = skip_fields or []
    branches = []
    for fs in fieldspecs:
        name = fs["name"]
        if name in skip_fields:
            continue
        branches.append(XmlElementTuple(
            name=name,
            value=getattr(obj, name),
            datatype=get_xml_datatype_from_fieldspec(fs),
            comment=fs.get("comment", None)
        ))
    return branches


def make_xml_branches_from_summaries(
        summaries: List[Dict],
        skip_fields: List[str] = None) -> List[XmlElementTuple]:
    """Returns a list of XML branches, each an XmlElementTuple, from a
    list of summary data provided by a task."""
    skip_fields = skip_fields or []
    branches = []
    for d in summaries:
        name = d["name"]
        if name in skip_fields:
            continue
        branches.append(cc_namedtuples.XmlElementTuple(
            name=name,
            value=d["value"],
            datatype=get_xml_datatype_from_fieldspec(d),
            comment=d.get("comment", None)
        ))
    return branches


def xml_header(eol: str = '\n') -> str:
    """XML declaration header."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>{eol}'.format(
            eol=eol,
        )
    )


def get_xml_datatype_from_fieldspec(fs: FIELDSPEC_TYPE) -> Optional[str]:
    """Returns the XML schema datatype from a fieldspec."""
    # http://www.xml.dvint.com/docs/SchemaDataTypesQR-2.pdf
    # http://www.w3.org/TR/2004/REC-xmlschema-2-20041028/datatypes.html
    t = fs["cctype"]
    if t in ["ISO8601", "DATETIME"]:
        return "dateTime"
    if t in ["INT", "INT_UNSIGNED", "BIGINT", "BIGINT_UNSIGNED"]:
        return "integer"
    if t in ["FLOAT"]:
        return "double"
    if t in ["BOOL"]:
        return "boolean"
    if cc_db.cctype_is_string(t):
        return "string"
    # BLOBs are handled separately.
    return None


def get_xml_blob_tuple(name: str,
                       blobdata: Optional[bytes],
                       comment: str = None) -> XmlElementTuple:
    """Returns an XmlElementTuple representing a base-64-encoded BLOB."""
    return XmlElementTuple(
        name=name,
        value=base64.b64encode(blobdata) if blobdata else None,
        datatype="base64Binary",
        comment=comment
    )
    # http://www.w3.org/TR/2001/REC-xmlschema-2-20010502/#base64Binary


def xml_escape_value(value: str) -> str:
    """Escape a value for XML."""
    # http://stackoverflow.com/questions/1091945/
    # https://wiki.python.org/moin/EscapingXml
    return xml.sax.saxutils.escape(value)


def xml_quote_attribute(attr: str) -> str:
    """Escapes and quotes an attribute for XML.

    More stringent than value escaping.
    """
    return xml.sax.saxutils.quoteattr(attr)


def get_xml_tree(element: XmlElementTuple,
                 level: int = 0,
                 indent_spaces: int = 4,
                 eol: str = '\n',
                 include_comments: bool = False) -> str:
    """Returns an entire XML tree as text, given the root XmlElementTuple."""
    # We will represent NULL values with xsi:nil, but this requires a
    # namespace: http://stackoverflow.com/questions/774192
    # http://books.xmlschemata.org/relaxng/relax-CHP-11-SECT-1.html
    # Comments:
    # - http://blog.galasoft.ch/posts/2010/02/quick-tip-commenting-out-properties-in-xaml/  # noqa
    # - http://stackoverflow.com/questions/2073140/
    xmltext = ""
    prefix = ' ' * level * indent_spaces

    if isinstance(element, cc_namedtuples.XmlElementTuple):

        # Attributes
        namespaces = []
        if level == 0:  # root
            # Apply namespace to root element (will inherit):
            namespaces.extend(XML_NAMESPACES)
            if include_comments:
                namespaces.extend(XML_IGNORE_NAMESPACES)
        namespace = " ".join(namespaces)
        dt = ""
        if element.datatype:
            dt = ' xsi:type="{}"'.format(element.datatype)
        cmt = ""
        if include_comments and element.comment:
            cmt = ' ignore:comment={}'.format(
                xml_quote_attribute(element.comment))
        attributes = "{ns}{dt}{cmt}".format(ns=namespace, dt=dt, cmt=cmt)

        # Assemble
        if element.value is None:
            # NULL handling
            xmltext += '{pr}<{name}{attributes} xsi:nil="true"/>{eol}'.format(
                name=element.name,
                pr=prefix,
                eol=eol,
                attributes=attributes,
            )
        else:
            complex_value = isinstance(element.value,
                                       cc_namedtuples.XmlElementTuple) \
                or isinstance(element.value, list)
            value_to_recurse = element.value if complex_value else \
                cc_namedtuples.XmlSimpleValue(element.value)
            # ... XmlSimpleValue is a marker that subsequently distinguishes
            # things that were part of an XmlElementTuple from user-inserted
            # raw XML.
            nl = eol if complex_value else ""
            pr2 = prefix if complex_value else ""
            xmltext += (
                '{pr}<{name}{attributes}>{nl}'
                '{value}{pr2}</{name}>{eol}'.format(
                    name=element.name,
                    pr=prefix,
                    eol=eol,
                    pr2=pr2,
                    nl=nl,
                    value=get_xml_tree(
                        value_to_recurse,
                        level=level + 1,
                        indent_spaces=indent_spaces,
                        eol=eol,
                        include_comments=include_comments
                    ),
                    attributes=attributes,
                )
            )

    elif isinstance(element, list):
        for subelement in element:
            xmltext += get_xml_tree(subelement, level,
                                    indent_spaces=indent_spaces,
                                    eol=eol,
                                    include_comments=include_comments)
        # recursive

    elif isinstance(element, cc_namedtuples.XmlSimpleValue):
        # The lowest-level thing a value. No extra indent.
        xmltext += xml_escape_value(str(element.value))
        # Regarding newlines: no need to do anything special (although some
        # browsers may fail to display them correctly):
        # http://stackoverflow.com/questions/2004386

    else:
        # A user-inserted piece of XML. Insert, but indent.
        xmltext += prefix + str(element) + eol

    return xmltext


def get_xml_document(root: XmlElementTuple,
                     indent_spaces: int = 4,
                     eol: str = '\n',
                     include_comments: bool = False) -> str:
    """Returns an entire XML document as text, given the root
    XmlElementTuple."""
    if not isinstance(root, cc_namedtuples.XmlElementTuple):
        raise AssertionError("get_xml_document: root not an XmlElementTuple; "
                             "XML requires a single root")
    return xml_header(eol) + get_xml_tree(
        root,
        indent_spaces=indent_spaces,
        eol=eol,
        include_comments=include_comments
    )
