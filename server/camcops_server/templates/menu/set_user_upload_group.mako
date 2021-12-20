## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/set_user_upload_group.mako

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
from camcops_server.cc_modules.cc_pyramid import Icons
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.UPLOAD,
        text=_("Set upload group for user")
    ) | n }
    ${ user.username }
</h1>

<div class="important">
    ${ _("A group must be selected for the server to permit uploads.") }
</div>

<div class="warning">
    ${ _("Don’t change groups if tasks have been uploaded by this user but "
         "not finalized; this may lead to incorrect group assignment. "
         "(Finalize first, then change groups.)") }
</div>

${ form | n }

<%include file="to_view_all_users.mako"/>
<%include file="to_main_menu.mako"/>
