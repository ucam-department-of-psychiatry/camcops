## logged_out.mako
<%inherit file="base_web.mako"/>

<div>
    You have logged out.
</div>
<div>
    Click <a href="${request.route_url(Routes.LOGIN)}">here</a> to log in again.
</div>
