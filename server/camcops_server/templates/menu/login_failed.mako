## login_failed.mako
<%inherit file="base_web.mako"/>

<div class="error">
    Invalid username/password.
</div>
<div>
    Click <a href="${request.route_url(Routes.LOGIN)}">here</a> to try again.
</div>
