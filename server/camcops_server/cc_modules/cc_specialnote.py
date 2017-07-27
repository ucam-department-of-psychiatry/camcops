#!/usr/bin/env python
# camcops_server/cc_modules/cc_specialnote.py

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

from typing import List, Optional

import cardinal_pythonlib.rnc_web as ws

from .cc_constants import (
    DATEFORMAT,
    ERA_NOW,
    ISO8601_STRING_LENGTH,
)
from . import cc_db
from .cc_dt import format_datetime
from .cc_pls import pls
from .cc_user import get_username_from_id
from .cc_xml import make_xml_branches_from_fieldspecs, XmlElement


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
            user=self.get_username() or "?",
            note=self.note or "",
        )

    def get_note_as_html(self) -> str:
        """Return an HTML-formatted version of the note."""
        return "[{dt}, {user}]<br><b>{note}</b>".format(
            dt=self.note_at or "?",
            user=self.get_username() or "?",
            note=ws.webify(self.note) or "",
        )

    def get_username(self) -> Optional[str]:
        return get_username_from_id(self.user_id)

    def get_xml_root(self, skip_fields: List[str] = None) -> XmlElement:
        """Get root of XML tree, as an XmlElementTuple."""
        skip_fields = skip_fields or []
        branches = make_xml_branches_from_fieldspecs(
            self, self.FIELDSPECS, skip_fields=skip_fields)
        return XmlElement(name=self.TABLENAME, value=branches)

    @classmethod
    def get_all_instances(cls,
                          basetable: str,
                          task_id: int,
                          device_id: int,
                          era: str) -> List[SPECIALNOTE_FWD_REF]:
        """Return all SpecialNote objects applicable to a task."""
        wheredict = dict(
            basetable=basetable,
            task_id=task_id,
            device_id=device_id,
            era=era
        )
        return pls.db.fetch_all_objects_from_db_where(
            SpecialNote, SpecialNote.TABLENAME, SpecialNote.FIELDS,
            True, wheredict)


def forcibly_preserve_special_notes(device_id: int) -> None:
    """WRITES TO DATABASE."""
    new_era = format_datetime(pls.NOW_UTC_NO_TZ, DATEFORMAT.ERA)
    query = """
        UPDATE  {table}
        SET     era = ?
        WHERE   device_id = ?
        AND     era = '{now}'
    """.format(table=SpecialNote.TABLENAME, now=ERA_NOW)
    args = [
        new_era,
        device_id
    ]
    pls.db.db_exec(query, *args)
