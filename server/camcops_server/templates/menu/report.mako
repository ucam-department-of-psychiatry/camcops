## report.mako
## <%page args="title: str, column_names: List[str], page: CamcopsPage"/>
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${ title | h }</h1>

<%block name="additional_report_above_results"></%block>

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

<%block name="additional_report_below_results"></%block>

<div>
    <a href="${ request.route_url(Routes.OFFER_REPORT, _query={ViewParam.REPORT_ID: report_id}) }">Re-configure report</a>
</div>
<div>
    <a href="${request.route_url(Routes.REPORTS_MENU)}">Return to reports menu</a>
</div>
<%include file="to_main_menu.mako"/>

<%block name="additional_report_below_menu"></%block>
