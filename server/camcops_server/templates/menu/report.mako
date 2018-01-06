## report.mako
## <%page args="title: str, column_names: List[str], page: CamcopsPage"/>
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${ title | h }</h1>

<div>${page.pager()}</div>

<table>
    <tr>
        %for c in column_names:
            <th>${c | h}</th>
        %endfor
    </tr>
    %for row in page:
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

<div>${page.pager()}</div>

<div>
    <a href="${ request.route_url(Routes.REPORT, _query={ViewParam.REPORT_ID: report_id}) }">Re-run report</a>
</div>
<div>
    <a href="${request.route_url(Routes.REPORTS_MENU)}">Return to reports menu</a>
</div>
<%include file="to_main_menu.mako"/>
