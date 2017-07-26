#!/usr/bin/env python
# cc_patientidnum.py

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

import logging
from typing import List

import cardinal_pythonlib.rnc_web as ws

from .cc_constants import (
    FP_ID_NUM,
    STANDARD_GENERIC_FIELDSPECS,
)
from . import cc_db
from .cc_pls import pls

log = logging.getLogger(__name__)


# =============================================================================
# PatientIdNum class
# =============================================================================

class PatientIdNum:
    tablename = "patient_idnum"
    fkname = "patient_id"
    # Using 'tablename' and 'fkname' allow the use of
    # get_contemporaneous_matching_ancillary_objects_by_fk() but this is
    # INELEGANT. Fix with proper DB engine. ***
    FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
        dict(name="patient_id", cctype="INT_UNSIGNED", notnull=True,
             comment="FK to patient.id (for this device/era)"),
        dict(name="which_idnum", cctype="INT_UNSIGNED", notnull=True,
             comment="Which of the server's ID numbers is this?"),
        dict(name="idnum_value", cctype="BIGINT_UNSIGNED",
             comment="The value of the ID number"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make underlying database tables."""
        cc_db.create_standard_table(
            cls.tablename, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    @classmethod
    def get_fieldnames(cls) -> List[str]:
        return cls.FIELDS

    def __init__(self, serverpk: int = None) -> None:
        """Initialize, loading from database."""
        pls.db.fetch_object_from_db_by_pk(self, PatientIdNum.tablename,
                                          PatientIdNum.FIELDS, serverpk)

    def save(self) -> None:
        """Saves patient record back to database. UNUSUAL."""
        pls.db.save_object_to_db(self,
                                 PatientIdNum.tablename,
                                 PatientIdNum.FIELDS,
                                 is_new_record=self._pk is None)

    def description(self) -> str:
        return pls.get_id_desc(self.which_idnum, default="?")

    def short_description(self) -> str:
        return pls.get_id_shortdesc(self.which_idnum, default="?")

    def get_html(self, longform: bool, label_id_numbers: bool = False) -> str:
        """
        Returns description HTML.

        Args:
            longform: verbose (for most HTML) or not (for PDF headers)
            label_id_numbers: whether to use prefix
        """
        if self.which_idnum is None:
            return ""
        nstr = str(self.which_idnum)  # which ID number?
        prefix = ("<i>(" + FP_ID_NUM + nstr + ")</i> "
                  if label_id_numbers else "")
        if longform:
            return "<br>{}{}: <b>{}</b>".format(
                prefix,
                ws.webify(self.description()),
                self.idnum_value
            )
        else:
            return "{}{}: {}.".format(
                prefix,
                ws.webify(self.short_description()),
                self.idnum_value
            )

    def get_filename_component(self) -> str:
        if self.which_idnum is None or self.idnum_value is None:
            return ""
        return "{}-{}".format(self.short_description(), self.idnum_value)

    def set_idnum(self, idnum_value: int) -> None:
        self.idnum_value = idnum_value


