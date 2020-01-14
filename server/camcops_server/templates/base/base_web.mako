## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/base/base_web.mako

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

</%doc>

<%inherit file="base.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%block name="logo">
    <div class="web_logo_header">
        <a href="${request.route_url(Routes.HOME)}"><img class="logo_left" src="${request.url_camcops_logo}" alt="" /></a>
        <a href="${request.url_local_institution}"><img class="logo_right" src="${request.url_local_logo}" alt="" /></a>
    </div>
</%block>

<%block name="css">
    <%include file="css_web.mako"/>
</%block>

${next.body()}

