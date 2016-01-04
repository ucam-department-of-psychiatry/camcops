#!/usr/bin/env python3
# cc_namedtuples.py

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

import collections

# Optional arguments for named tuples that also allow isinstance() checking:
# http://stackoverflow.com/questions/11351032


# =============================================================================
# PatientIdentifierTuple
# =============================================================================

PatientIdentifierTuple = collections.namedtuple("PatientIdentifierTuple", [
    "id",
    "id_type",
    "assigning_authority"
])


# =============================================================================
# BarePatientInfo
# =============================================================================
# We avoid using Patient because otherwise we have to deal
# with mutual dependency problems and the use of the database (prior to full
# database initialization)

BarePatientInfo = collections.namedtuple("BarePatientInfo", [
    "forename",
    "surname",
    "dob",
    "sex",
    "idnum_array"
])


# =============================================================================
# XML element
# =============================================================================

class XmlElementTuple(collections.namedtuple("XmlElementTuple",
                                             ["name",
                                              "value",
                                              "datatype",
                                              "comment"])):
    """Represents XML data in a tree. See functions in cc_xml.py"""
    def __new__(cls, name, value=None, datatype=None, comment=None):
        # Special: boolean requires lower case "true"/"false" (or 0/1)
        if datatype == "boolean" and value is not None:
            value = unicode(value).lower()
        return super(XmlElementTuple, cls).__new__(cls, name, value, datatype,
                                                   comment)


# =============================================================================
# Raw XML value
# =============================================================================

class XmlSimpleValue(collections.namedtuple("XmlSimpleValue", ["value"])):
    """Represents XML lowest-level items. See functions in cc_xml.py"""
    def __new__(cls, value):
        return super(XmlSimpleValue, cls).__new__(cls, value)


# =============================================================================
# IntrospectionFileDetails
# =============================================================================

IntrospectionFileDetails = collections.namedtuple("IntrospectionFileDetails", [
    "fullpath",
    "prettypath",
    "searchterm",
    "ext"
])
