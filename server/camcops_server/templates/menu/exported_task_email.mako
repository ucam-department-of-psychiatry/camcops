## exported_task_email.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Exported task e-mail")}</h1>

<table>
    <tr>
        <th>ExportedTaskEmail ID</th>
        <td>${ ete.id }</td>
    </tr>
    <tr>
        <th>Exported task ID</th>
        <td><a href="${ req.route_url(Routes.VIEW_EXPORTED_TASK, _query={ViewParam.ID: ete.exported_task_id}) }">ExportedTask ${ ete.exported_task_id }</a></td>
    </tr>
    <tr>
        <th>E-mail ID</th>
        <td><a href="${ req.route_url(Routes.VIEW_EMAIL, _query={ViewParam.ID: ete.email_id}) }">Email ${ ete.email_id } </a></td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
