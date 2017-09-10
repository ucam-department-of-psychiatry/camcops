## css_web.mako

## Genuinely static, so we can cache it:
<%page cached="True" cache_region="local" cache_key="css_web.mako"/>

<%inherit file="css_base.mako"/>

<%namespace file="def_css_constants.mako" import="_get_css_varargs"/>
<%def name="get_css_varargs()"><%
    return _get_css_varargs("web")
%></%def>
