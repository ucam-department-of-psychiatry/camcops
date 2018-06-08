## login.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<div>
    <b>Unauthorized access prohibited.</b>
    All use is recorded and monitored.
</div>

<h1>Please log in to CamCOPS</h1>

${form}
