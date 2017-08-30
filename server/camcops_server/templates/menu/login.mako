## login.mako
<%inherit file="base_web_form.mako"/>

<div>${request.config.get_database_title_html()}</div>

<div>
    <b>Unauthorized access prohibited.</b>
    All use is recorded and monitored.
</div>

<h1>Please log in to the CamCOPS web portal</h1>

${form}
