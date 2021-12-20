## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/reports_menu.mako

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

from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
from camcops_server.cc_modules.cc_report import get_all_report_classes

%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.REPORTS,
        text=_("Available reports")
    ) | n }
</h1>

<ul class="menu">
    %for cls in get_all_report_classes(request):
        %if request.user.superuser or not cls.superuser_only:
            <li>
                ${ req.icon_text(
                        icon=Icons.REPORT_CONFIG,
                        url=request.route_url(
                            Routes.OFFER_REPORT,
                            _query={
                                ViewParam.REPORT_ID: cls.report_id
                            }
                        ),
                        text=cls.title(request)
                ) | n }
            </li>
        %endif
    %endfor
</ul>

<%include file="to_main_menu.mako"/>
