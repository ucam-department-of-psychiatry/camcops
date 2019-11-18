## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/download_area.mako

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

</%doc>

<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h2>${_("Download area")}</h2>

<table>
    <tr>
        <th>${_("Name")}</th>
        <th>${_("Size")}</th>
        <th>${_("Created")}</th>
        <th>${_("Time left")}</th>
        <th>${_("Delete")}</th>
        <th>${_("Download")}</th>
    </tr>
    %for f in files:
        <tr>
            <td><a href="${f.download_url(req)}">${f.filename}</a></td>
            <td>${f.size_str}</td>
            <td>${f.when_last_modified_str}</td>
            <td>${f.time_left_str}</td>
            <td><a href="${f.delete_url(req)}">${_("Delete")}</a></td>
            <td><a href="${f.download_url(req)}">${_("Download")}</a></td>
        </tr>
    %endfor
</table>

<div>
    ${_("Space permitted:")} ${permitted}.
    ${_("Space used:")} ${used}.
    ${_("Space available:")} ${available}.
    ${_("File lifetime (minutes):")} ${lifetime_min}.
</div>

<%include file="to_main_menu.mako"/>
