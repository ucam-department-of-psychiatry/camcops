## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/download_area.mako

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
from camcops_server.cc_modules.cc_pyramid import Icons
%>

<%include file="db_user_info.mako"/>

<style nonce="${ request.nonce | n }">
    <%include file="style_deform_inside_tables.css"/>
</style>

<h1>
    ${ req.icon_text(
        icon=Icons.DOWNLOAD,
        text=_("Download area")
    ) | n }
</h1>

<table>
    <tr>
        <th>${ _("Name") }</th>
        <th>${ _("Size") }</th>
        <th>${ _("Created") }</th>
        <th>${ _("Time left") }</th>
        <th>${ _("Delete") }</th>
    </tr>
    %for f in files:
        <tr>
            <td>
                ${ req.icon_text(
                        icon=Icons.DOWNLOAD,
                        url=f.download_url,
                        text=f.filename
                ) | n }
            </td>
            <td>${ f.size_str }</td>
            <td>${ f.when_last_modified_str }</td>
            <td>${ f.time_left_str }</td>
            <td>${ f.delete_form | n }</td>
        </tr>
    %endfor
</table>

<div>
    ${ _("Space permitted:") } ${ permitted }.
    ${ _("Space used:") } ${ used }.
    ${ _("Space available:") } ${ available }.
    ${ _("File lifetime (minutes):") } ${ lifetime_min }.
</div>

<%include file="to_main_menu.mako"/>
