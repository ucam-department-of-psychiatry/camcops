## success.mako
<%page args="msg"/>
<%inherit file="base_web.mako"/>

<h1>Success!</h1>

<div>${msg | h}</div>

<%include file="to_main_menu.mako"/>
