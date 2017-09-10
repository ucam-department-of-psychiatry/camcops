## hl7_message_log_view.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>HL7 message log</h1>

%if conditions:
    <h2>Conditions</h2>
    ${conditions | h}
%endif

<h2>Results</h2>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>Message ID</th>
        <th>Run ID</th>
        <th>Base table</th>
        <th>Task server PK</th>
        <th>Sent at (UTC)</th>
        <th>Reply at (UTC)</th>
        <th>Success?</th>
        <th>Failure reason</th>
        <th>Filename</th>
        <th>RiO metadata filename</th>
        <th>Cancelled?</th>
        <th>Cancelled at (UTC)</th>
        <th>Full message</th>
    </tr>

    %for msg in page:
        <tr>
            <td>${ msg.msg_id }</td>
            <td><a href="${ req.route_url(Routes.VIEW_HL7_RUN, _query={ViewParam.HL7_RUN_ID: msg.run_id}) }">${ msg.run_id }</a></td>
            <td>${ msg.basetable | h }</td>
            <td>
                %if msg.basetable and msg.serverpk:
                    <a href="${ req.route_url(Routes.TASK, msg.basetable, msg.serverpk) }">${ msg.serverpk }</a>
                %else:
                    ${ msg.serverpk }
                %endif
            </td>

            <td>${ msg.sent_at_utc }</td>
            <td>${ msg.reply_at_utc }</td>
            <td>${ msg.success }</td>
            <td>${ msg.failure_reason | h }</td>
            <td>${ msg.filename | h }</td>
            <td>${ msg.rio_metadata_filename | h }</td>
            <td>${ msg.cancelled }</td>
            <td>${ msg.cancelled_at_utc }</td>
            <td><a href="${ req.route_url(Routes.VIEW_HL7_MESSAGE, _query={ViewParam.HL7_MSG_ID: msg.msg_id})}">full</a></td>
        </tr>
    %endfor
</table>

<div>${page.pager()}</div>

<div>
    <a href="${ req.route_url(Routes.OFFER_HL7_MESSAGE_LOG)}">Choose different options</a>
</div>

<%include file="to_main_menu.mako"/>
