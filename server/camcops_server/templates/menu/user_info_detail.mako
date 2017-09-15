## user_info_detail.mako
<%inherit file="base_web.mako"/>
<%!
    from camcops_server.cc_modules.cc_html import get_yes_no
%>
<%namespace file="displayfunc.mako" import="one_per_line"/>

<%include file="db_user_info.mako"/>

<%
    user = request.camcops_session.user
%>

<h1>Information about user ${ user.username | h }</h1>

<table>
    <tr>
        <th>Username</th>
        <td>${ user.username | h }</td>
    </tr>
    <tr>
        <th>User ID</th>
        <td>${ user.id }</td>
    </tr>
    <tr>
        <th>Full name</th>
        <td>${ (user.fullname or "") | h }</td>
    </tr>
    <tr>
        <th>E-mail address</th>
        <td>${ (user.email or "") | h }</td>
    </tr>
    <tr>
        <th>Last password change (UTC)</th>
        <td>${ user.last_password_change_utc }</td>
    </tr>
    <tr>
        <th>Must change password at next login?</th>
        <td>${ get_yes_no(request, user.must_change_password) }</td>
    </tr>
    <tr>
        <th>Agreed to terms of use at:</th>
        <td>${ user.when_agreed_terms_of_use }</td>
    </tr>
    <tr>
        <th>Superuser?</th>
        <td>${ get_yes_no(request, user.superuser) }</td>
    </tr>
    <tr>
        <th>May log in to web viewer?</th>
        <td>${ get_yes_no(request, user.may_use_webviewer) }</td>
    </tr>
    <tr>
        <th>May upload data?</th>
        <td>${ get_yes_no(request, user.may_upload) }</td>
    </tr>
    <tr>
        <th>May register new tablet devices?</th>
        <td>${ get_yes_no(request, user.may_register_devices) }</td>
    </tr>
    <tr>
        <th>When no task filters are applied, can the user browse all tasks?
            (If not, then none are shown.)</th>
        <td>${ get_yes_no(request, user.view_all_patients_when_unfiltered) }</td>
    </tr>
    <tr>
        <th>May dump data?</th>
        <td>${ get_yes_no(request, user.may_dump_data) }</td>
    </tr>
    <tr>
        <th>May run reports?</th>
        <td>${ get_yes_no(request, user.may_run_reports) }</td>
    </tr>
    <tr>
        <th>May add notes to tasks/patients?</th>
        <td>${ get_yes_no(request, user.may_add_notes) }</td>
    </tr>
    <tr>
        <th>Groups this user is a member of:</th>
        <td>
            <%
                groups = list(user.groups)
                groups.sort(key=lambda g: g.name)
            %>
            ${ one_per_line(g.name for g in groups) }
        </td>
    </tr>
    <tr>
        <th>Groups this user can see data from:</th>
        <td>
            ${ one_per_line(g.name for g in user.groups_user_may_see()) }
        </td>
    </tr>
    <tr>
        <th>Group this user is currently set to upload into:</th>
        <td>
            %if user.upload_group:
                ${ user.upload_group.name | h }
            %else:
                <i>(None)</i>
            %endif
        </td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
