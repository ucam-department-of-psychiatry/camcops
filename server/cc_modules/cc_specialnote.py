#!/usr/bin/env python3
# cc_specialnote.py

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

from typing import List

import cardinal_pythonlib.rnc_web as ws

from .cc_constants import ISO8601_STRING_LENGTH
from . import cc_db
from .cc_namedtuples import XmlElementTuple
from .cc_pls import pls
from . import cc_xml


# =============================================================================
# SpecialNote class
# =============================================================================

SPECIALNOTE_FWD_REF = "SpecialNote"


class SpecialNote(object):
    """Represents a special note, attached server-side to a task.

    'Task' means all records representing versions of a single task instance,
    identified by the combination of {id, device, era}.
    """
    TABLENAME = "_special_notes"
    FIELDSPECS = [
        # PK
        dict(name="note_id", cctype="INT_UNSIGNED", pk=True,
             autoincrement=True, comment="Arbitrary primary key"),
        # Composite FK
        dict(name="basetable", cctype="TABLENAME", indexed=True,
             comment="Base table of task concerned (part of FK)"),
        dict(name="task_id", cctype="INT_UNSIGNED", indexed=True,
             comment="Client-side ID of the task concerned (part of FK)"),
        dict(name="device_id", cctype="INT_UNSIGNED", indexed=True,
             comment="Source tablet device (part of FK)"),
        dict(name="era", cctype="ISO8601", indexed=True,
             index_nchar=ISO8601_STRING_LENGTH,
             comment="Era (part of FK)"),
        # Details of note
        dict(name="note_at", cctype="ISO8601",
             comment="Date/time of note entry (ISO 8601)"),
        dict(name="user_id", cctype="INT_UNSIGNED",
             comment="User that entered this note"),
        dict(name="note", cctype="TEXT",
             comment="Special note, added manually"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Create underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, note_id: int = None) -> None:
        """Initializes, reading from database if necessary."""
        pls.db.fetch_object_from_db_by_pk(self, SpecialNote.TABLENAME,
                                          SpecialNote.FIELDS, note_id)

    def save(self) -> None:
        """Saves note to database. """
        pls.db.save_object_to_db(self, self.TABLENAME, self.FIELDS,
                                 self.note_id is None)

    def get_note_as_string(self) -> str:
        """Return a string-formatted version of the note."""
        return "[{dt}, {user}]\n{note}".format(
            dt=self.note_at or "?",
            user=self.user or "?",
            note=self.note or "",
        )

    def get_note_as_html(self) -> str:
        """Return an HTML-formatted version of the note."""
        return "[{dt}, {user}]<br><b>{note}</b>".format(
            dt=self.note_at or "?",
            user=self.user or "?",
            note=ws.webify(self.note) or "",
        )

    def get_xml_root(self, skip_fields: List[str] = None) -> XmlElementTuple:
        """Get root of XML tree, as an XmlElementTuple."""
        skip_fields = skip_fields or []
        branches = cc_xml.make_xml_branches_from_fieldspecs(
            self, self.FIELDSPECS, skip_fields=skip_fields)
        return XmlElementTuple(name=self.TABLENAME, value=branches)

    @classmethod
    def get_all_instances(cls,
                          basetable: str,
                          task_id: int,
                          device: str,
                          era: str) -> List[SPECIALNOTE_FWD_REF]:
        """Return all SpecialNote objects applicable to a task."""
        wheredict = dict(
            basetable=basetable,
            task_id=task_id,
            device=device,
            era=era
        )
        return pls.db.fetch_all_objects_from_db_where(
            SpecialNote, SpecialNote.TABLENAME, SpecialNote.FIELDS,
            True, wheredict)
