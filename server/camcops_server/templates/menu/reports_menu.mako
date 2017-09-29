## reports_menu.mako
<%inherit file="base_web.mako"/>

<%!

from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
from camcops_server.cc_modules.cc_report import get_all_report_classes

%>

<%include file="db_user_info.mako"/>

<h1>Available reports</h1>

<ul>
    %for cls in get_all_report_classes():
        %if request.user.superuser or not cls.superuser_only:
            <li><a href="${ request.route_url(Routes.OFFER_REPORT, _query={ViewParam.REPORT_ID: cls.report_id}) }">${ cls.title | h }</a></li>
        %endif
    %endfor
</ul>

<%include file="to_main_menu.mako"/>
