#!/usr/bin/env python
# camcops_server/cc_modules/cc_specialnote.py

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

from typing import List, Optional

from cardinal_pythonlib.datetimefunc import format_datetime
import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import update
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from .cc_constants import DateFormat, ERA_NOW
from .cc_request import CamcopsRequest
from .cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    EraColType,
    TableNameColType,
)
from .cc_sqlalchemy import Base
from .cc_xml import make_xml_branches_from_columns, XmlElement


# =============================================================================
# SpecialNote class
# =============================================================================

SPECIALNOTE_FWD_REF = "SpecialNote"


class SpecialNote(Base):
    """
    Represents a special note, attached server-side to a task.

    'Task' means all records representing versions of a single task instance,
    identified by the combination of {id, device, era}.
    """
    __tablename__ = "_special_notes"

    # PK:
    note_id = Column(
        "note_id", Integer,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    # Composite FK:
    basetable = Column(
        "basetable", TableNameColType,
        index=True,
        comment="Base table of task concerned (part of FK)"
    )
    task_id = Column(
        "task_id", Integer,
        index=True,
        comment="Client-side ID of the task, or patient, concerned "
                "(part of FK)"
    )
    device_id = Column(
        "device_id", Integer,
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
        "note_at", PendulumDateTimeAsIsoTextColType,
        comment="Date/time of note entry (ISO 8601)"
    )
    user_id = Column(
        "user_id", Integer,
        ForeignKey("_security_users.id"),
        comment="User that entered this note"
    )
    user = relationship("User")
    note = Column(
        "note", UnicodeText,
        comment="Special note, added manually"
    )

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
        branches = make_xml_branches_from_columns(
            self, skip_fields=skip_fields)
        return XmlElement(name=self.__tablename__, value=branches)

    @classmethod
    def forcibly_preserve_special_notes_for_device(cls, req: CamcopsRequest,
                                                   device_id: int) -> None:
        """
        WRITES TO DATABASE.

        For update methods, see also:
        http://docs.sqlalchemy.org/en/latest/orm/persistence_techniques.html
        """
        dbsession = req.dbsession
        new_era = format_datetime(req.now_utc, DateFormat.ERA)

        # METHOD 1: use the ORM, object by object
        #
        # noinspection PyProtectedMember
        # notes = dbsession.query(cls)\
        #     .filter(cls._device_id == device_id)\
        #     .filter(cls._era == ERA_NOW)\
        #     .all()
        # for note in notes:
        #     note._era = new_era

        # METHOD 2: use the Core, in bulk
        # You can use update(table)... or table.update()...;
        # http://docs.sqlalchemy.org/en/latest/core/dml.html#sqlalchemy.sql.expression.update  # noqa

        statement = update(cls.__table__)\
            .where(cls.device_id == device_id)\
            .where(cls.era == ERA_NOW)\
            .values(era=new_era)
        dbsession.execute(statement)
