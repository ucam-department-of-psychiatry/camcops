## view_policies.mako
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>CamCOPS: this database’s identification policies</h1>

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
        <td>${upload}</td>
    </tr>
    <tr>
        <td>Finalize</td>
        <td>${finalize}</td>
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

<%include file="to_main_menu.mako"/>
