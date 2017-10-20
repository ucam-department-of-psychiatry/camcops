## view_tasks_table.mako
<%page args="tasks"/>

<%!

from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_html import get_true_false
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam

OFFER_HTML_ANON_VERSION = False
OFFER_PDF_ANON_VERSION = False

%>

<table>
    <tr>
        <th>Patient</th>
        <th>Identifiers</th>
        <th>Task type</th>
        <th>Added by</th>
        <th>Created</th>
        <th>View</th>
        <th>Print/save</th>
    </tr>

    %for task in tasks:
        ## ${ repr(task) | h }
        <tr>
            ## ------------------------------------------------------------
            ## Surname, forename (sex, DOB, age)
            ## ------------------------------------------------------------
            <td
                %if (not task.is_anonymous) and task.patient:
                    %if not task.patient.satisfies_upload_id_policy():
                        class="badidpolicy_severe"
                    %elif not task.patient.satisfies_finalize_id_policy():
                        class="badidpolicy_mild"
                    %endif
                %endif
                >
                %if task.is_anonymous:
                    —
                %else:
                    %if task.patient:
                        <b>${ task.patient.get_surname_forename_upper() }</b>
                        (${ task.patient.get_sex_verbose() },
                        ${ format_datetime(task.patient.dob, DateFormat.SHORT_DATE, default="?") },
                        aged ${ task.patient.get_age(req=req, default="?") })
                    %else:
                        ?
                    %endif
                %endif
            </td>
            ## ------------------------------------------------------------
            ## ID numbers
            ## ------------------------------------------------------------
            <td>
                %if task.is_anonymous:
                    —
                %else:
                    %if task.patient:
                        %for idobj in task.patient.idnums:
                            ${ idobj.short_description(request) }: ${ idobj.idnum_value }
                        %endfor
                    %else:
                        ?
                    %endif
                %endif
            </td>
            ## ------------------------------------------------------------
            ## Task type
            ## ------------------------------------------------------------
            <td
                %if not task._current:
                    ## Shouldn't occur these days; we pre-filter for this!
                    class="warning"
                %endif
                >
                <b> ${ task.shortname | h }</b>
            </td>
            ## ------------------------------------------------------------
            ## Adding user
            ## ------------------------------------------------------------
            <td>
                ${ task._adding_user.username | h }
            </td>
            ## ------------------------------------------------------------
            ## When created
            ## ------------------------------------------------------------
            <td
                %if task.is_live_on_tablet():
                    class="live_on_tablet"
                %endif
                >
                ${ format_datetime(task.when_created, DateFormat.SHORT_DATETIME) }
            </td>
            ## ------------------------------------------------------------
            ## Hyperlink to HTML
            ## ------------------------------------------------------------
            <td
                %if not task.is_complete():
                    class="incomplete"
                %endif
                >
                <a href="${ req.route_url(
                        Routes.TASK,
                        _query={
                            ViewParam.TABLE_NAME: task.tablename,
                            ViewParam.SERVER_PK: task._pk,
                            ViewParam.VIEWTYPE: ViewArg.HTML,
                        }) }">HTML</a>
                %if OFFER_HTML_ANON_VERSION:
                    [<a href="${ req.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: task.tablename,
                                ViewParam.SERVER_PK: task._pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML,
                                ViewParam.ANONYMISE: True,
                            }) }">anon</a>]
                %endif
            </td>
            ## ------------------------------------------------------------
            ## Hyperlink to PDF
            ## ------------------------------------------------------------
            <td
                %if not task.is_complete():
                    class="incomplete"
                %endif
                >
                <a href="${ req.route_url(
                    Routes.TASK,
                    _query={
                        ViewParam.TABLE_NAME: task.tablename,
                        ViewParam.SERVER_PK: task._pk,
                        ViewParam.VIEWTYPE: ViewArg.PDF,
                    }) }">PDF</a>
                %if OFFER_PDF_ANON_VERSION:
                    [<a href="${ req.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: task.tablename,
                                ViewParam.SERVER_PK: task._pk,
                                ViewParam.VIEWTYPE: ViewArg.PDF,
                                ViewParam.ANONYMISE: True,
                            }) }">anon</a>]
                %endif
            </td>
            ## We used to use target="_blank", but probably that is not the
            ## best: https://css-tricks.com/use-target_blank/
        </tr>

    %endfor

</table>
