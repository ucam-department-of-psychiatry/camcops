## audit_trail_view.mako
<%inherit file="base_web.mako"/>

<%!

from mako.filters import html_escape
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam

def trunc(value, truncate, truncate_at):
    if not value:
        return ""
    text = value[:truncate_at] if truncate else value
    return html_escape(text)


def filter_generic_value(value):
    if value is None:
        return ""
    return html_escape(str(value))


def get_username(audit_entry):
    if audit_entry.user is None or not audit_entry.user.username:
        return ""
    return html_escape(audit_entry.user.username)

%>

<%include file="db_user_info.mako"/>

<h1>Audit trail</h1>

%if conditions:
    <h2>Conditions</h2>
    ${conditions | h}
%endif

<h2>Results</h2>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>ID</th>
        <th>When (UTC)</th>
        <th>Source</th>
        <th>Remote IP</th>
        <th>Username</th>
        <th>Device ID</th>
        <th>Table name</th>
        <th>Server PK</th>
        <th>Patient server PK</th>
        %if truncate:
            <th>Details (truncated)</th>
        %else:
            <th>Details</th>
        %endif
    </tr>
    %for audit in page:
        <tr>
            <td>${ audit.id }</td>
            <td>${ audit.when_access_utc }</td>
            <td>${ filter_generic_value(audit.source) }</td>
            <td>${ filter_generic_value(audit.remote_addr) }</td>
            <td>${ get_username(audit) }</td>
            <td>${ filter_generic_value(audit.device_id) }</td>
            <td>${ filter_generic_value(audit.table_name) }</td>
            <td>${ filter_generic_value(audit.server_pk) }</td>
            <td>${ filter_generic_value(audit.patient_server_pk) }</td>
            <td>${ trunc(audit.details, truncate, truncate_at) }</td>
        </tr>
    %endfor
</table>

<div>${page.pager()}</div>

<div>
    <a href="${ req.route_url(Routes.OFFER_AUDIT_TRAIL)}">Choose different options</a>
</div>

<%include file="to_main_menu.mako"/>


## TODO: Consider: cross-link tasks from this audit trail view to their task view
