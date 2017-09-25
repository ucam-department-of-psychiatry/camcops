## generic_success.mako
## <%page args="msg"/>
<%inherit file="base_web.mako"/>

<h1>Success!</h1>

%if msg:
<div>${msg | h}</div>
%endif

%if extra_html:
    ${extra_html}
%endif

<%include file="to_main_menu.mako"/>
