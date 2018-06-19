## groups_table.mako
<%page args="groups_page, with_edit: bool"/>
<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
from markupsafe import escape
%>
<%namespace file="displayfunc.mako" import="one_per_line"/>

<div>${groups_page.pager(show_if_single_page=False)}</div>

<table>
    <tr>
        <th>Group name</th>
        <th>Group ID</th>
        <th>Description</th>
        <th>Groups this group is allowed to see, in addition to itself</th>
        <th>Upload ID policy</th>
        <th>Principal (single necessary) ID number required by Upload policy</th>
        <th>Finalize ID policy</th>
        <th>Principal (single necessary) ID number required by Finalize policy</th>
        <th>Members</th>
        %if with_edit:
            <th>Edit</th>
            <th>Delete</th>
        %endif
    </tr>
    %for group in groups_page:
        <%
            upload_tk = group.tokenized_upload_policy()  # type: TokenizedPolicy
            finalize_tk = group.tokenized_finalize_policy()  # type: TokenizedPolicy
            upload_valid = upload_tk.is_valid_from_req(request)
            finalize_valid = upload_tk.is_valid_from_req(request)
        %>
        <tr>
            <td>${ group.name | h }</td>
            <td>${ group.id }</td>
            <td>${ (group.description or "") | h }</td>
            <td>
                ${ one_per_line(g.name for g in group.can_see_other_groups) }
            </td>

            <td
                %if not upload_valid:
                    class="warning"
                %endif
                >
                ${ (escape(group.upload_policy) if group.upload_policy else "<i>None</i>") }
            </td>

            <td>${ upload_tk.find_critical_single_numerical_id_from_req(request) }</td>

            <td
                %if not finalize_valid:
                    class="warning"
                %endif
                >
                ${ (escape(group.finalize_policy) if group.finalize_policy else "<i>None</i>") }
            </td>

            <td>${ finalize_tk.find_critical_single_numerical_id_from_req(request) }</td>

            <td>
                ${ (", ".join(sorted(u.username if u is not None else "<DATA_ERROR_NULL_USER>"
                                     for u in group.users))) | h }
            </td>

            %if with_edit:
                <td><a href="${ req.route_url(Routes.EDIT_GROUP, _query={ViewParam.GROUP_ID: group.id}) }">Edit</a></td>
                <td><a href="${ req.route_url(Routes.DELETE_GROUP, _query={ViewParam.GROUP_ID: group.id}) }">Delete</a></td>
            %endif
        </tr>
    %endfor
</table>

<div>${groups_page.pager(show_if_single_page=False)}</div>

<div class="footnotes">
    Colour in a policy column means that an ID policy is not valid (either
    syntactically, or because it refers to ID numbers that do not exist).
</div>
