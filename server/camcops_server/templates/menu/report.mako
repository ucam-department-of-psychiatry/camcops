## report.mako
## <%page args="title: str, descriptions: List[str], rows: List[List[Any]]"/>
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${ title | h }</h1>

<table>
    <tr>
        %for d in descriptions:
            <th>${d | h}</th>
        %endfor
    </tr>
    %for row in rows:
        <tr>
            %for val in row:
                <td>
                    %if val is None:
                        <!-- NULL -->
                        ## <i>NULL</i>
                    %else:
                        ${val | h}
                    %endif
                </td>
            %endfor
        </tr>
    %endfor
</table>

<div>
    <a href="${request.route_url(Routes.REPORTS_MENU)}">Return to reports menu</a>
</div>
<%include file="to_main_menu.mako"/>
