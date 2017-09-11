## base_web.mako
<%inherit file="base.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%block name="logo">
    <div class="web_logo_header">
        <a href="${request.route_url(Routes.HOME)}"><img class="logo_left" src="${request.url_camcops_logo}" alt="" /></a>
        <a href="${request.url_local_institution}"><img class="logo_right" src="${request.url_local_logo}" alt="" /></a>
    </div>
</%block>

<%block name="css">
    <%include file="css_web.mako"/>
</%block>

${next.body()}

