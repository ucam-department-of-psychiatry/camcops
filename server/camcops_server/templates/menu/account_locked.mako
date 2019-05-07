## account_locked.mako
## <%page args="locked_until"/>
<%inherit file="generic_failure.mako"/>

<div class="error">
    ${_("Account locked until ${locked_until} due to multiple login failures. Try again later or contact your administrator.")}
</div>
