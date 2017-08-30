## account_locked.mako
<%page args="locked_until"/>
<%inherit file="base_web.mako"/>

<div class="error">
    Account locked until ${locked_until} due to multiple login failures.
    Try again later or contact your administrator.
</div>
