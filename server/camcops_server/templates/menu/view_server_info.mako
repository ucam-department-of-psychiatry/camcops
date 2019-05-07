## view_server_info.mako
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>${_("CamCOPS: information about this database/server")}</h1>

<h2>${_("Identification (ID) numbers")}</h2>
<table>
    <tr>
        <th>${_("ID number")}</th>
        <th>${_("Description")}</th>
        <th>${_("Short description")}</th>
    </tr>
    %for iddef in idnum_definitions:
        <tr>
            <td>${iddef.which_idnum}</td>
            <td>${iddef.description | h}</td>
            <td>${iddef.short_description | h}</td>
        </tr>
    %endfor
</table>

<h2>${_("Recent activity")}</h2>
<table>
    <tr>
        <th>${_("Time-scale")}</th>
        <th>${_("Number of active sessions")}</th>
    </tr>
    %for k, v in recent_activity.items():
        <tr>
            <td>${k}</td>
            <td>${v}</td>
        </tr>
    %endfor
</table>
<p>
    ${_("Sessions time out after ${session_timeout_minutes} minutes; sessions older than this are periodically deleted.")}
</p>

<h2>${_("Extra string families present")}</h2>
<pre>
    %for sf in string_families:
${ sf | h }
    %endfor
</pre>

<h2>${_("All known tasks")}</h2>
<p>${_("Format is: long name (short name; base table name).")}</p>
<pre>
    %for tc in all_task_classes:
${ tc.longname | h } (${ tc.shortname | h }; ${ tc.tablename | h })
    %endfor
</pre>

<%include file="to_main_menu.mako"/>
