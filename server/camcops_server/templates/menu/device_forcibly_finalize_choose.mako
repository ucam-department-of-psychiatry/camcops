## device_forcibly_finalize_choose.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Forcibly finalize a device</h1>

<h2>Step 1: choose a device</h2>

<div class="important">
    This process marks all records from a particular device (e.g. tablet,
    or desktop client) as final, so the device can no longer alter them.
    If you do this and the client re-uploads records, they will be created as
    fresh tasks, so only force-finalize devices that are no longer in use and
    to which you no longer have access.
</div>

${ form }

<%include file="to_main_menu.mako"/>
