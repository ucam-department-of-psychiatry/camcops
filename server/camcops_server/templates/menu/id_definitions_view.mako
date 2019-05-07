## id_definitions_view.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Identification (ID) numbers")}</h1>

<table>
    <tr>
        <th>${_("ID number")}</th>
        <th>${_("Description")}</th>
        <th>${_("Short description")}</th>
        <th>${_("Validation method")}</th>
        <th>${_("HL7 ID Type")}</th>
        <th>${_("HL7 Assigning Authority")}</th>
        <th>${_("Edit")}</th>
        <th>${_("Delete")}</th>
    </tr>
    %for iddef in idnum_definitions:
        <tr>
            <td>${iddef.which_idnum}</td>
            <td>${iddef.description | h}</td>
            <td>${iddef.short_description | h}</td>
            <td>${iddef.validation_method or "" | h}</td>
            <td>${iddef.hl7_id_type or "" | h}</td>
            <td>${iddef.hl7_assigning_authority or "" | h}</td>
            <td><a href="${request.route_url(Routes.EDIT_ID_DEFINITION, _query={ViewParam.WHICH_IDNUM: iddef.which_idnum})}">${_("Edit")}</a></td>
            <td><a href="${request.route_url(Routes.DELETE_ID_DEFINITION, _query={ViewParam.WHICH_IDNUM: iddef.which_idnum})}">${_("Delete")}</a></td>
        </tr>
    %endfor
</table>

<a href="${request.route_url(Routes.ADD_ID_DEFINITION)}">${_("Add new ID number definition")}</a>

<%include file="to_main_menu.mako"/>
