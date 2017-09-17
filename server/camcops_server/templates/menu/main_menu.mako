## main_menu.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>CamCOPS web view: Main menu</h1>

<ul>
    <li><a href="${ request.route_url(Routes.SET_FILTERS, _query={
                    ViewParam.REDIRECT_URL: request.route_url(Routes.HOME)
                }) }">Set task filters</a></li>
    <li><a href="${request.route_url(Routes.VIEW_TASKS)}">View tasks</a></li>
    <li><a href="${request.route_url(Routes.CHOOSE_TRACKER)}">Trackers for numerical information</a></li>
    <li><a href="${request.route_url(Routes.CHOOSE_CTV)}">Clinical text view</a></li>
</ul>

%if authorized_for_reports or authorized_to_dump:
    <ul>

    %if authorized_for_reports:
        <li><a href="${request.route_url(Routes.REPORTS_MENU)}">Run reports</a></li>
    %endif

    %if authorized_to_dump:
        <li><a href="${request.route_url(Routes.OFFER_BASIC_DUMP)}">Basic research dump (fields and summaries)</a></li>
        ## DISABLED FOR NOW:
        ## <li><a href="FILL_ME_IN">Regenerate summary tables</a></li>
        <li><a href="${request.route_url(Routes.OFFER_TABLE_DUMP)}">Dump table/view data</a></li>
        <li><a href="${request.route_url(Routes.VIEW_DDL)}">Inspect table definitions</a>
    %endif

    </ul>
%endif

%if authorized_as_superuser:
    <ul>
        <li><a href="${request.route_url(Routes.VIEW_ALL_USERS)}">View/manage users</a></li>
        <li><a href="${request.route_url(Routes.VIEW_GROUPS)}">View/manage groups</a></li>
        <li><a href="${request.route_url(Routes.DELETE_PATIENT)}">Delete patient entirely</a></li>
        <li><a href="${request.route_url(Routes.FORCIBLY_FINALIZE)}">Forcibly preserve/finalize records for a device</a></li>
        <li><a href="${request.route_url(Routes.OFFER_AUDIT_TRAIL)}">View audit trail</a></li>
        <li><a href="${request.route_url(Routes.OFFER_HL7_MESSAGE_LOG)}">View HL7 message log</a></li>
        <li><a href="${request.route_url(Routes.OFFER_HL7_RUN_LOG)}">View HL7 run log</a></li>
    </ul>
%endif

<ul>
    <li><a href="${request.route_url(Routes.VIEW_SERVER_INFO)}">Show database settings (identification policies)</a></li>
    %if introspection:
        <li><a href="${request.route_url(Routes.OFFER_INTROSPECTION)}">Introspect source code</a></li>
    %endif
    %if request.camcops_session.username:
        <li><a href="${request.route_url(Routes.CHANGE_OWN_PASSWORD, username=request.camcops_session.username)}">Change password</a></li>
    %else:
        <li class="warning">No username!</li>
    %endif
    <li><a href="${request.route_url(Routes.SET_OWN_USER_UPLOAD_GROUP)}">Choose group into which to upload data</a></li>
    <li><a href="${request.route_url(Routes.VIEW_OWN_USER_INFO)}">Show your user settings</a></li>
    <li><a href="${request.route_url(Routes.LOGOUT)}">Log out</a></li>
</ul>

<div class="office">
    It’s ${now}.
    Server version ${server_version}.
    See <a href="${camcops_url}">${camcops_url}</a> for more information on CamCOPS.
    Clicking on the CamCOPS logo will return you to the main menu.
</div>

%if not id_policies_valid:
    <div class="badidpolicy_severe">
        Server’s ID policies are missing or invalid.
        This needs fixing urgently by the system administrator.
    </div>
%endif
