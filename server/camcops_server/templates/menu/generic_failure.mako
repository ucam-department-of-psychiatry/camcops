## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/generic_failure.mako

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
from types import BuiltinFunctionType
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

%if msg:
    <h2 class="error">${ msg }</h2>
%endif

%if extra_html:
    ${ extra_html | n }
%endif

<%doc>
Without the check on "next" that follows, this template cannot be used
directly, but only inherited from, or you will get the error:
    AttributeError: 'builtin_function_or_method' object has no attribute 'body'
See https://github.com/sqlalchemy/mako/issues/252.
If inheritance is occurring, "next" is a Mako thing; otherwise, it's a Python
keyword.
</%doc>
%if not isinstance(next, BuiltinFunctionType):
    ${ next.body() | n }
%endif

%if request.exception:
<div class="error">
    ${ request.exception.message }
</div>
%endif

<div class="error">
    %if request.user_id is None:
        <%block name="go_to_login">
            <div>
                ${ _("Click") }
                <a href="${ request.route_url(Routes.LOGIN) | n }">
                    ${ _("here") }</a> ${ _("to log in") }.
            </div>
        </%block>
    %else:
        <%include file="to_main_menu.mako"/>
    %endif
</div>
