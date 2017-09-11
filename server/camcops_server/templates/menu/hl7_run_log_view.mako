## hl7_run_log_view.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>HL7 run log</h1>

%if conditions:
    <h2>Conditions</h2>
    ${conditions | h}
%endif

<h2>Results</h2>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>Run ID</th>
        <th>Started at (UTC)</th>
        <th>Finished at (UTC)</th>
        <th>Recipient definition</th>
        <th>Recipient type (e.g. hl7, file)</th>
        <th>Start date for tasks (UTC)</th>
        <th>End date for tasks (UTC)</th>
        <th>(HL7) Host</th>
        <th>(HL7) Port</th>
        <th>(HL7) Divert to file</th>


        <th>Full details</th>
    </tr>

    %for hl7run in page:
        <tr>
            <td><a href="${ request.route_url(Routes.VIEW_HL7_RUN, _query={ViewParam.HL7_RUN_ID: msg.run_id}) }">${ msg.run_id }</a></td>
            <td>${ hl7run.start_at_utc }</td>
            <td>${ hl7run.finish_at_utc }</td>
            <td>${ hl7run.recipient | h }</td>
            <td>${ hl7run.type | h }</td>
            <td>${ hl7run.start_date }</td>
            <td>${ hl7run.end_date }</td>
            <td>${ hl7run.host | h }</td>
            <td>${ hl7run.port }</td>
            <td>${ hl7run.divert_to_file }</td>

            <td><a href="${ req.route_url(Routes.VIEW_HL7_RUN, _query={ViewParam.HL7_RUN_ID: msg.run_id}) }">details</a></td>
        </tr>
    %endfor
</table>

<div>${page.pager()}</div>

<div>
    <a href="${ req.route_url(Routes.OFFER_HL7_RUN_LOG)}">Choose different options</a>
</div>

<%include file="to_main_menu.mako"/>
