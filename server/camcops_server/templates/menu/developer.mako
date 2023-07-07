## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/developer.mako

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
%>

<h1>
    ${ req.icon_text(
        icon=Icons.DEVELOPER,
        text="Developer test pages"
    ) | n }
</h1>

<h2>Basic HTTP</h2>
<ul>
    <li><a href="${ request.route_url(Routes.TESTPAGE_PUBLIC_1) | n }">
        Public test page 1</a> (plain)</li>
    <li><a href="${ request.route_url(Routes.TESTPAGE_PRIVATE_1) | n }">
        Private test page 1</a> (plain)</li>
    <li><a href="${ request.route_url(Routes.TESTPAGE_PRIVATE_2) | n }">
        Private test page 2</a> (<b>sensitive</b> variables)</li>
    <li><a href="${ request.route_url(Routes.TESTPAGE_PRIVATE_3) | n }">
        Private test page 3</a> (template inheritance)</li>
    <li><a href="${ request.route_url(Routes.TESTPAGE_PRIVATE_4) | n }">
        Private test page 4</a> (Mako filtering)</li>
    <li><a href="${ request.route_url(Routes.CRASH) | n }">
        Deliberately crash the request</a> (shouldn’t crash the server!)</li>
</ul>

<h2>Index testing</h2>
<ul>
    <li><a href=" ${request.route_url(
                        Routes.VIEW_TASKS,
                        _query={ViewParam.VIA_INDEX: False}
                    ) | n }">View tasks without using index</a></li>
    <li>Trackers and CTVs have a no-index option available to users directly.</li>
</ul>

<h2>Less accessible options</h2>
<ul>
    <li>
        Tasks can be viewed with
        <code>${ ViewParam.VIEWTYPE}=${ ViewArg.PDFHTML}</code>
        to show the HTML that goes into PDF generation (without page headers or
        footers).
    </li>
</ul>

<h2>Test data</h2>
<ul>
    <li><a href=" ${request.route_url(Routes.TEST_NHS_NUMBERS) | n }">
        NHS numbers for testing</a></li>
</ul>
