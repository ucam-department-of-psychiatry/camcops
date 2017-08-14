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
from cardinal_pythonlib.sqlalchemy.orm_inspect import get_orm_column_names
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, Text

from .cc_constants import (
    DATEFORMAT,
    ERA_NOW,
    ISO8601_STRING_LENGTH,
)
from .cc_config import pls
from . import cc_db
from .cc_dt import format_datetime
from .cc_request import CamcopsRequest
from .cc_sqla_coltypes import (
    BigIntUnsigned,
    DateTimeAsIsoTextColType,
    EraColType,
    HostnameColType,
    IntUnsigned,
    LongText,
    SendingFormatColType,
    TableNameColType,
)
from .cc_sqlalchemy import Base
from .cc_user import get_username_from_id
from .cc_xml import make_xml_branches_from_fieldspecs, XmlElement


# =============================================================================
# SpecialNote class
# =============================================================================

SPECIALNOTE_FWD_REF = "SpecialNote"


class SpecialNote(Base):
    """Represents a special note, attached server-side to a task.

    'Task' means all records representing versions of a single task instance,
    identified by the combination of {id, device, era}.
    """
    __tablename__ = "_special_notes"

    # PK:
    note_id = Column(
        "note_id", IntUnsigned,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    # Composite FK:
    basetable = Column(
        "basetable", TableNameColType,
        index=True,
        comment="Base table of task concerned (part of FK)"
    )
    task_or_patient_id = Column(
        "task_id", IntUnsigned,
        index=True,
        comment="Client-side ID of the task, or patient, concerned "
                "(part of FK)"
    )
    device_id = Column(
        "device_id", IntUnsigned,
        index=True,
        comment="Source tablet device (part of FK)"
    )
    era = Column(
        "era", EraColType,
        index=True,
        comment="Era (part of FK)"
    )
    # Details of note
    note_at = Column(
        "note_at", DateTimeAsIsoTextColType,
        comment="Date/time of note entry (ISO 8601)"
    )
    user_id = Column(
        "user_id", IntUnsigned, ForeignKey("_security_users.id"),
        comment="User that entered this note"
    )
    user = relationship("User")
    note = Column(
        "note", Text,
        comment="Special note, added manually"
    )

    @classmethod
    def get_all_instances(cls,
                          dbsession: SqlASession,
                          basetable: str,
                          task_or_patient_id: int,
                          device_id: int,
                          era: str) -> List[SPECIALNOTE_FWD_REF]:
        """Return all SpecialNote objects applicable to a task (or patient)."""
        q = dbsession.query(SpecialNote)
        q = q.filter(SpecialNote.basetable == basetable)
        q = q.filter(SpecialNote.task_or_patient_id == task_or_patient_id)
        q = q.filter(SpecialNote._device_id == device_id)
        q = q.filter(SpecialNote._era == era)
        special_notes = q.fetchall()  # type: List[SpecialNote]
        return special_notes

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
        if self.user is None:
            return None
        return self.user.username

    def get_xml_root(self, skip_fields: List[str] = None) -> XmlElement:
        """Get root of XML tree, as an XmlElementTuple."""
        skip_fields = skip_fields or []
        branches = make_xml_branches_from_fieldspecs(
            self, skip_fields=skip_fields)
        return XmlElement(name=self.TABLENAME, value=branches)

    @classmethod
    def forcibly_preserve_special_notes(cls, req: CamcopsRequest,
                                        device_id: int) -> None:
        """
        WRITES TO DATABASE.

        We could do an UPDATE, or something involving the ORM more. See also
        http://docs.sqlalchemy.org/en/latest/orm/persistence_techniques.html
        """
        dbsession = req.dbsession
        new_era = format_datetime(pls.NOW_UTC_NO_TZ, DATEFORMAT.ERA)
        notes = dbsession.query(cls)\
            .filter(cls._device_id == device_id)\
            .filter(cls._era == ERA_NOW)\
            .all()
        for note in notes:
            note._era = new_era
