#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_text.py

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

**Text used by the server, and translated.**

"""

from typing import TYPE_CHECKING

from enum import auto, Enum, unique

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


@unique
class SS(Enum):
    """
    Server string enumeration.
    """
    ANSWER = auto()
    IF_APPLICABLE = auto()
    QUESTION = auto()


def server_string(req: "CamcopsRequest", w: SS) -> str:
    """
    Returns a translated server string.

    Use this mechanism when the same string is re-used in several places in
    the server (but not by the client).

    Args:
        req:
            a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        w:
            which string? A :class:`camcops_server.cc_modules.cc_text.SS`
            enumeration value

    Returns:
        the translated string

    """
    _ = req.gettext
    if w == SS.ANSWER:
        return _("Answer")
    elif w == SS.IF_APPLICABLE:
        return _("If applicable")
    elif w == SS.QUESTION:
        return _("Question")
    raise ValueError("Bad value passed to server_string")
