## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/edit_user_authentication.mako

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

</%doc>

<%inherit file="base_web_form.mako"/>
<%include file="db_user_info.mako"/>

<h1>${ _("Change authentication for user: {username}").format(username=username) }</h1>

${form | n}

<script type="text/javascript">
    <%text>
        document.addEventListener("DOMContentLoaded", function(event) {
            $('input[name="change_password"]').change(function() {
                var show = $('input[name="change_password"]:checked').val() !== undefined;
                $(".item-new_password, .item-must_change_password").toggle(show);
            });
            $('input[name="change_password"]').change();
        });
    </%text>
</script>


<%include file="to_view_all_users.mako"/>
<%include file="to_main_menu.mako"/>