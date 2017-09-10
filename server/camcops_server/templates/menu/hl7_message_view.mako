## hl7_message_view.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>Individual HL7 message</h1>

<table>
    <tr>
        <th>Message ID</th>
        <td>${ msg.msg_id }</td>
    </tr>
    <tr>
        <th>Run ID</th>
        <td><a href="${ req.route_url(Routes.VIEW_HL7_RUN, _query={ViewParam.HL7_RUN_ID: msg.run_id}) }">${ msg.run_id }</a></td>
    </tr>
    <tr>
        <th>Base table</th>
        <td>${ msg.basetable | h }</td>
    </tr>
    <tr>
        <th>Task server PK</th>
        <td>
            %if msg.basetable and msg.serverpk:
                <a href="${ req.route_url(Routes.TASK, msg.basetable, msg.serverpk) }">${ msg.serverpk }</a>
            %else:
                ${ msg.serverpk }
            %endif
        </td>
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
        <th>Filename</th>
        <td>${ msg.filename | h }</td>
    </tr>
    <tr>
        <th>RiO metadata filename</th>
        <td>${ msg.rio_metadata_filename | h }</td>
    </tr>
    <tr>
        <th>Cancelled?</th>
        <td>${ msg.cancelled }</td>
    </tr>
    <tr>
        <th>Cancelled at (UTC)</th>
        <td>${ msg.cancelled_at_utc }</td>
    </tr>
    <tr>
        <th>Message</th>
        <td>${ msg.message | h }</td>
    </tr>
    <tr>
        <th>Reply</th>
        <td>${ msg.reply | h }</td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
