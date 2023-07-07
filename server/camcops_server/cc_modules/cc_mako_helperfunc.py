#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_mako_helperfunc.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Helper functions used by Mako templates.**

"""

from typing import Any, Iterable, List, TYPE_CHECKING

from camcops_server.cc_modules.cc_pyramid import ViewParam

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


# =============================================================================
# Helper functions
# =============================================================================


def listview(
    req: "CamcopsRequest",
    objects: Iterable[Any],
    route_name: str,
    description: str,
    icon: str,
    sep: str = "<br>",
) -> str:
    """
    Provides an autolinked catalogue of objects, in HTML, via those objects'
    ``id`` fields and a standard URL format

    Args:
        req:
            A :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`.
        objects:
            Objects to catalogue.
        route_name:
            Pyramid route name.
        description:
            Object type description.
        icon:
            Icon name for each object.
        sep:
            Separator string for HTML.

    Returns:
        str: HTML
    """
    parts = []  # type: List[str]
    for obj in objects:
        obj_id = obj.id
        url = req.route_url(route_name, _query={ViewParam.ID: obj_id})
        text = f"{description} {obj_id}"
        parts.append(req.icon_text(icon=icon, url=url, text=text))
    return sep.join(parts)
