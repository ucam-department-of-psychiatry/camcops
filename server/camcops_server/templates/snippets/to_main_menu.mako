## to_main_menu.mako

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<div>
    <a href="${request.route_url(Routes.HOME)}">Return to main menu</a>
</div>
