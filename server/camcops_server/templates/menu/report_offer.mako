## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/report_offer.mako

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

<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Icons, Routes
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.REPORT_CONFIG,
        text=_("Configure report:") + " " + report.title(request)
    ) | n }
</h1>

${ form | n }

<div>
    ${ req.icon_text(
            icon=Icons.REPORTS,
            url=request.route_url(Routes.REPORTS_MENU),
            text=_("Return to reports menu")
    ) | n }
</div>
<%include file="to_main_menu.mako"/>
