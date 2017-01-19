#!/usr/bin/env python
# cc_namedtuples.py

"""
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

class XmlElementTuple(collections.namedtuple(
        "XmlElementTuple", ["name", "value", "datatype", "comment"])):
    """Represents XML data in a tree. See functions in cc_xml.py"""
    def __new__(cls, name, value=None, datatype=None, comment=None):
        # Special: boolean requires lower case "true"/"false" (or 0/1)
        if datatype == "boolean" and value is not None:
            value = str(value).lower()
        # noinspection PyTypeChecker
        return super().__new__(cls, name, value, datatype, comment)


# =============================================================================
# Raw XML value
# =============================================================================

XmlSimpleValue = collections.namedtuple("XmlSimpleValue", [
    "value"
])
# Represents XML lowest-level items. See functions in cc_xml.py


# =============================================================================
# IntrospectionFileDetails
# =============================================================================

IntrospectionFileDetails = collections.namedtuple("IntrospectionFileDetails", [
    "fullpath",
    "prettypath",
    "searchterm",
    "ext"
])
