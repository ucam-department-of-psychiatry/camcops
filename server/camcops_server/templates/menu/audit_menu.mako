## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/audit_menu.mako

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

</%doc>

<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Icons, Routes
%>

<h1>
    ${ req.icon_text(
        icon=Icons.AUDIT_MENU,
        text=_("Audit options")
    ) | n }
</h1>

<h2>${ _("Access logs") }</h2>
<ul class="menu">
    <li>
        ${ req.icon_text(
                icon=Icons.AUDIT_OPTIONS,
                url=request.route_url(Routes.OFFER_AUDIT_TRAIL),
                text=_("Audit trail")
        ) | n }
    </li>
</ul>

<h2>${ _("Export logs") }</h2>
<ul class="menu">
    <li>
        ${ req.icon_text(
                icon=Icons.AUDIT_OPTIONS,
                url=request.route_url(Routes.OFFER_EXPORTED_TASK_LIST),
                text=_("Exported task log")
        ) | n }
    </li>
</ul>

<%include file="to_main_menu.mako"/>
