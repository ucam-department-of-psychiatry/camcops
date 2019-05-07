## exported_task.mako
<%inherit file="base_web.mako"/>

<%!
from markupsafe import escape
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam

def listview(req, objects, route_name, description):
    parts = []
    for obj in objects:
        url = req.route_url(route_name, _query={ViewParam.ID: obj.id})
        parts.append('<a href="{url}">{description} {id}</a>'.format(
            url=url, description=description, id=obj.id))
    return "<br>".join(parts)

%>

<%include file="db_user_info.mako"/>

<h1>${_("Individual task export attempt")}</h1>

<table>
    <tr>
        <th>Export ID</th>
        <td>${ et.id }</td>
    </tr>
    <tr>
        <th>Export recipient ID</th>
        <td><a href="${ req.route_url(Routes.VIEW_EXPORT_RECIPIENT, _query={ViewParam.ID: et.recipient_id}) }">ExportRecipient ${ et.recipient_id }</a></td>
    </tr>
    <tr>
        <th>Base table</th>
        <td>${ et.basetable | h }</td>
    </tr>
    <tr>
        <th>Task server PK</th>
        <td>${ et.task_server_pk } (<a href="${ req.route_url(Routes.TASK, _query={ViewParam.TABLE_NAME: et.basetable, ViewParam.SERVER_PK: et.task_server_pk, ViewParam.VIEWTYPE: ViewArg.HTML}) }">View task</a>)</td>
    </tr>
    <tr>
        <th>Start at (UTC)</th>
        <td>${ et.start_at_utc }</td>
    </tr>
    <tr>
        <th>Finish at (UTC)</th>
        <td>${ et.finish_at_utc }</td>
    </tr>
    <tr>
        <th>Success?</th>
        <td>${ et.success }</td>
    </tr>
    <tr>
        <th>Failure reasons</th>
        <td>${ "<br>".join(escape(reason) for reason in et.failure_reasons) | n }</td>
    </tr>
    <tr>
        <th>Cancelled?</th>
        <td>${ et.cancelled }</td>
    </tr>
    <tr>
        <th>Cancelled at (UTC)</th>
        <td>${ et.cancelled_at_utc or "" }</td>
    </tr>
    <tr>
        <th>E-mails</th>
        <td>${ listview(req, et.emails, Routes.VIEW_EXPORTED_TASK_EMAIL, "ExportedTaskEmail") }</td>
    </tr>
    <tr>
        <th>Files</th>
        <td>${ listview(req, et.filegroups, Routes.VIEW_EXPORTED_TASK_FILE_GROUP, "ExportedTaskFileGroup") }</td>
    </tr>
    <tr>
        <th>HL7 messages</th>
        <td>${ listview(req, et.hl7_messages, Routes.VIEW_EXPORTED_TASK_HL7_MESSAGE, "ExportedTaskHL7Message") }</td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
