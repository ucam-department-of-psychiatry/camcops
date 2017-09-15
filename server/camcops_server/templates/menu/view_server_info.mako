## view_server_info.mako
<%inherit file="base_web.mako"/>
<%namespace file="displayfunc.mako" import="one_per_line"/>

<%include file="db_user_info.mako"/>

<h1>CamCOPS: information about this database/server</h1>

<h2>Identification (ID) numbers</h2>

<table>
    <tr>
        <th>ID number</th>
        <th>Description</th>
        <th>Short description</th>
    </tr>
    %for i in range(len(which_idnums)):
        <tr>
            <td>${which_idnums[i]}</td>
            <td>${descriptions[i] | h}</td>
            <td>${short_descriptions[i] | h}</td>
        </tr>
    %endfor
</table>

<h2>ID policies</h2>

<table>
    <tr>
        <th>Policy</th>
        <th>Details</th>
    </tr>
    <tr>
        <td>Upload</td>
        <td>${upload | h}</td>
    </tr>
    <tr>
        <td>Finalize</td>
        <td>${finalize | h}</td>
    </tr>
    <tr>
        <td>Principal (single necessary) ID number required by Upload policy</td>
        <td>${upload_principal}</td>
    </tr>
    <tr>
        <td>Principal (single necessary) ID number required by Finalize policy</td>
        <td>${finalize_principal}</td>
    </tr>
</table>

<h2>Groups</h2>

<table>
    <tr>
        <th>Group name</th>
        <th>Group ID</th>
        <th>Description</th>
        <th>Groups this group is allowed to see, in addition to itself</th>
    </tr>
    %for group in groups:
        <tr>
            <td>${ group.name | h }</td>
            <td>${ group.id }</td>
            <td>${ (group.description or "") | h }</td>
            <td>
                ${ one_per_line(g.name for g in group.can_see_other_groups) }
            </td>
        </tr>
    %endfor
</table>

<%include file="to_main_menu.mako"/>
