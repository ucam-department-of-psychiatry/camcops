## exported_task_hl7_message.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>Individual HL7 message</h1>

<table>
    <tr>
        <th>HL7 message ID</th>
        <td>${ msg.id }</td>
    </tr>
    <tr>
        <th>Exported task ID</th>
        <td><a href="${ req.route_url(Routes.VIEW_EXPORTED_TASK, _query={ViewParam.ID: msg.exported_task_id}) }">ExportedTask ${ msg.exported_task_id }</a></td>
    </tr>
    <tr>
        <th>Sent at (UTC)</th>
        <td>${ msg.sent_at_utc }</td>
    </tr>
    <tr>
        <th>Reply at (UTC)</th>
        <td>${ msg.reply_at_utc }</td>
    </tr>
    <tr>
        <th>Success?</th>
        <td>${ msg.success }</td>
    </tr>
    <tr>
        <th>Failure reason</th>
        <td>${ msg.failure_reason | h }</td>
    </tr>
    <tr>
        <th>Message</th>
        <td><pre>${ msg.message or "" | h }</pre></td>
    </tr>
    <tr>
        <th>Reply</th>
        <td><pre>${ msg.reply or "" | h }</pre></td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
