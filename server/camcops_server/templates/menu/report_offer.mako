## report_offer.mako
<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes
%>

<%include file="db_user_info.mako"/>

<h1>${_("Configure report:")} ${ report.title(request) | h }</h1>

${ form }

<div>
    <a href="${request.route_url(Routes.REPORTS_MENU)}">${_("Return to reports menu")}</a>
</div>
<%include file="to_main_menu.mako"/>
