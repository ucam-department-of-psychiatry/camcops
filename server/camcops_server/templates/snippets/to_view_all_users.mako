## to_view_all_users.mako

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<div>
    <a href="${ req.route_url(Routes.VIEW_ALL_USERS)}">${_("View all users")}</a>
</div>
