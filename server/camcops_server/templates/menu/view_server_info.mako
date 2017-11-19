## view_server_info.mako
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>CamCOPS: information about this database/server</h1>

<h2>Identification (ID) numbers</h2>

<table>
    <tr>
        <th>ID number</th>
        <th>Description</th>
        <th>Short description</th>
    </tr>
    %for iddef in idnum_definitions:
        <tr>
            <td>${iddef.which_idnum}</td>
            <td>${iddef.description | h}</td>
            <td>${iddef.short_description | h}</td>
        </tr>
    %endfor
</table>

<h2>Extra string families present</h2>
<pre>
    %for sf in string_families:
${ sf | h }
    %endfor
</pre>

<h2>All known tasks</h2>
<pre>
    %for tc in all_task_classes:
${ tc.longname | h } (${ tc.shortname | h }; ${ tc.tablename | h })
    %endfor
</pre>

<%include file="to_main_menu.mako"/>
