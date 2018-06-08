## main_menu.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>CamCOPS web view: Main menu</h1>

<h3>Tasks, trackers, and clinical text views</h3>
<ul>
    <li><a href="${ request.route_url(Routes.SET_FILTERS, _query={
                    ViewParam.REDIRECT_URL: request.route_url(Routes.HOME)
                }) }">Set task filters</a></li>
    <li><a href="${request.route_url(Routes.VIEW_TASKS)}">View tasks</a></li>
    <li><a href="${request.route_url(Routes.CHOOSE_TRACKER)}">Trackers for numerical information</a></li>
    <li><a href="${request.route_url(Routes.CHOOSE_CTV)}">Clinical text views</a></li>
</ul>

%if authorized_to_dump:
    <h3>Research views</h3>
    <ul>
        <li><a href="${request.route_url(Routes.OFFER_TSV_DUMP)}">Basic research dump (fields and summaries)</a></li>
        <li><a href="${request.route_url(Routes.OFFER_SQL_DUMP)}">Dump table data as SQL</a></li>
        <li><a href="${request.route_url(Routes.VIEW_DDL)}">Inspect table definitions</a>
    </ul>
%endif

%if authorized_for_reports:
    <h3>Reports</h3>
    <ul>
        <li><a href="${request.route_url(Routes.REPORTS_MENU)}">Run reports</a></li>
    </ul>
%endif

%if authorized_as_groupadmin:
    <h3>Group administrator options</h3>
    <ul>
        <li><a href="${request.route_url(Routes.VIEW_ALL_USERS)}">View/manage users</a></li>
        <li><a href="${request.route_url(Routes.DELETE_PATIENT)}">Delete patient entirely</a></li>
        <li><a href="${request.route_url(Routes.FORCIBLY_FINALIZE)}">Forcibly preserve/finalize records for a device</a></li>
    </ul>
%endif

%if authorized_as_superuser:
    <h3>Superuser options</h3>
    <ul>
        <li><a href="${request.route_url(Routes.VIEW_GROUPS)}">View/manage groups</a></li>
        <li><a href="${request.route_url(Routes.OFFER_AUDIT_TRAIL)}">View audit trail</a></li>
        <li><a href="${request.route_url(Routes.OFFER_HL7_MESSAGE_LOG)}">View HL7 message log</a></li>
        <li><a href="${request.route_url(Routes.OFFER_HL7_RUN_LOG)}">View HL7 run log</a></li>
        <li><a href="${request.route_url(Routes.VIEW_ID_DEFINITIONS)}">View/edit ID number definitions</a></li>
        <li><a href="${request.route_url(Routes.EDIT_SERVER_SETTINGS)}">Edit server settings</a></li>
        <li><a href="${request.route_url(Routes.DEVELOPER)}">Developer test page</a></li>
    </ul>
%endif

<h3>Settings</h3>
<ul>
    <li><a href="${request.route_url(Routes.VIEW_SERVER_INFO)}">Show database/server settings</a></li>
    %if request.camcops_session.username:
        <li><a href="${request.route_url(Routes.CHANGE_OWN_PASSWORD, username=request.camcops_session.username)}">Change password</a></li>
    %else:
        <li class="warning">No username!</li>
    %endif
    <li><a href="${request.route_url(Routes.SET_OWN_USER_UPLOAD_GROUP)}">Choose group into which to upload data</a></li>
    <li><a href="${request.route_url(Routes.VIEW_OWN_USER_INFO)}">Show your user settings</a></li>
</ul>

%if introspection:
    <h3>Introspection</h3>
    <ul>
        <li><a href="${request.route_url(Routes.OFFER_INTROSPECTION)}">Introspect source code</a></li>
    </ul>
%endif

<h3>Help</h3>
<ul>
    <li><a href="${request.url_camcops_manual_pdf}">CamCOPS documentation</a></li>
</ul>

<h3>Log out</h3>
<ul>
    <li><a href="${request.route_url(Routes.LOGOUT)}">Log out</a></li>
</ul>

<div class="office">
    It’s ${now}.
    Server version ${server_version}.
    See <a href="${camcops_url}">${camcops_url}</a> for more information on CamCOPS.
    Clicking on the CamCOPS logo will return you to the main menu.
</div>

%if warn_bad_id_policies:
    <div class="badidpolicy_severe">
        Server’s group ID policies are missing or invalid.
        This needs fixing urgently by the system administrator. See “Groups”.
    </div>
%endif
