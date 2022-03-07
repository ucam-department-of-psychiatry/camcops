## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/dump_basic_offer.mako

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
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.DUMP_BASIC,
        text=_("Basic research data dump")
    ) | n }
</h1>

<h2>${ _("Explanation") }</h2>
<div>
    <ul>
        <li>
            ${ _("Provides a spreadsheet-style download (usually one sheet "
                 "per task; for some tasks, more than one).") }
        </li>
        <li>
            ${ _("Incorporates patient and summary information into each row. "
                 "Doesn’t provide binary large objects (e.g. pictures).") }
        </li>
        <li>
            ${ _("If there are no instances of a particular task, no sheet is returned.") }
        </li>
        <li>
            ${ _("Restricted to current records (i.e. ignores historical "
                 "versions of tasks that have been edited).") }
        </li>
        <li>
            ${ _("For more advanced features, use the") }
            <a href="${ request.route_url(Routes.OFFER_SQL_DUMP) | n }">
                ${ _("SQL dump") }</a> ${ _("to get the raw data.") }
        </li>
        <li>
            ${ _("Includes a sheet describing every column. "
                 "You can add a full description of the source database. "
                 "You can also") }
            <a href="${ request.route_url(Routes.VIEW_DDL) | n }">
                ${ _("inspect the table definitions") }</a>;
            <a href="${ request.route_url(Routes.TASK_LIST) | n }">
                ${ _("explore the task list") }</a>.
        </li>
    </ul>
</div>

<h2>${ _("Choose basic dump settings") }</h2>

${ form | n }

<%include file="to_main_menu.mako"/>
