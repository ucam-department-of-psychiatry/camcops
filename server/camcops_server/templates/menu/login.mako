## login.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<div>
    <b>${_("Unauthorized access prohibited.")}</b>
    ${_("All use is recorded and monitored.")}
</div>

<h1>${_("Please log in to CamCOPS")}</h1>

${form}
