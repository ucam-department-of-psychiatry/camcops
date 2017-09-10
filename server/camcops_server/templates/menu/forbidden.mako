## forbidden.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<div class="error">
    %if request.user_id is None:
        <!--
            Not logged in.

            (OR ANOTHER POSSIBILITY: CamCOPS being offered over HTTP, which
            will cause cookies not to be saved, because they're marked to the
            client as being HTTPS-only cookies by default.)
       -->
        You are not logged in (or your session has timed out).
        <div>
            Click <a href="${request.route_url(Routes.LOGIN, _query=querydict)}">here</a> to log in.
        </div>
    %else:
        <!-- Logged in, but permission denied: probably a non-administrator trying an administrative function. -->
        You do not have permission to view this page.
        It may be restricted to administrators.
        <%include file="to_main_menu.mako"/>
    %endif
</div>
