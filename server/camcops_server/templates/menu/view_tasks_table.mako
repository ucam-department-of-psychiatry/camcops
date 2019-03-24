## view_tasks_table.mako
<%page args="tasks"/>

<%!

from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_html import get_true_false
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
from camcops_server.cc_modules.cc_taskindex import TaskIndexEntry

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
        <%
            # Whether it's a Task or a TaskIndexEntry:
            task_tablename = task.tablename
            task_shortname = task.shortname
            # noinspection PyProtectedMember
            task_pk = task._pk
            when_created = task.when_created
            # noinspection PyProtectedMember
            adding_user = task._adding_user
            # noinspection PyProtectedMember
            current = task._current
            is_live_on_tablet = task.is_live_on_tablet()
            patient = task.patient
            is_anonymous = task.is_anonymous
            is_complete = task.is_complete()
            any_patient_idnums_invalid = task.any_patient_idnums_invalid(req)
        %>
        ## ${ repr(task) | h }
        <tr>
            ## ------------------------------------------------------------
            ## Surname, forename (sex, DOB, age)
            ## ------------------------------------------------------------
            <td
                %if patient:
                    %if not patient.satisfies_upload_id_policy():
                        class="badidpolicy_severe"
                    %elif not patient.satisfies_finalize_id_policy():
                        class="badidpolicy_mild"
                    %endif
                %endif
                >
                %if is_anonymous:
                    —
                %else:
                    %if patient:
                        <b>${ patient.get_surname_forename_upper() }</b>
                        (${ patient.get_sex_verbose() },
                        ${ format_datetime(patient.dob, DateFormat.SHORT_DATE, default="?") })
                    %else:
                        ?
                    %endif
                %endif
            </td>
            ## ------------------------------------------------------------
            ## ID numbers
            ## ------------------------------------------------------------
            <td
                %if any_patient_idnums_invalid:
                    class="invalid_id_number_background"
                %endif
                >
                %if is_anonymous:
                    —
                %else:
                    %if patient:
                        %for idobj in patient.idnums:
                            ${ idobj.short_description(request) }: ${ idobj.idnum_value }.
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
                %if not current:
                    ## Shouldn't occur these days; we pre-filter for this!
                    class="warning"
                %endif
                >
                <b> ${ task_shortname | h }</b>
            </td>
            ## ------------------------------------------------------------
            ## Adding user
            ## ------------------------------------------------------------
            <td>
                ${ adding_user.username | h }
            </td>
            ## ------------------------------------------------------------
            ## When created
            ## ------------------------------------------------------------
            <td
                %if is_live_on_tablet:
                    class="live_on_tablet"
                %endif
                >
                ${ format_datetime(when_created, DateFormat.SHORT_DATETIME_NO_TZ) }
            </td>
            ## ------------------------------------------------------------
            ## Hyperlink to HTML
            ## ------------------------------------------------------------
            <td
                %if not is_complete:
                    class="incomplete"
                %endif
                >
                <a href="${ req.route_url(
                        Routes.TASK,
                        _query={
                            ViewParam.TABLE_NAME: task_tablename,
                            ViewParam.SERVER_PK: task_pk,
                            ViewParam.VIEWTYPE: ViewArg.HTML,
                        }) }">HTML</a>
                %if OFFER_HTML_ANON_VERSION:
                    [<a href="${ req.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: task_tablename,
                                ViewParam.SERVER_PK: task_pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML,
                                ViewParam.ANONYMISE: True,
                            }) }">anon</a>]
                %endif
            </td>
            ## ------------------------------------------------------------
            ## Hyperlink to PDF
            ## ------------------------------------------------------------
            <td
                %if not is_complete:
                    class="incomplete"
                %endif
                >
                <a href="${ req.route_url(
                    Routes.TASK,
                    _query={
                        ViewParam.TABLE_NAME: task_tablename,
                        ViewParam.SERVER_PK: task_pk,
                        ViewParam.VIEWTYPE: ViewArg.PDF,
                    }) }">PDF</a>
                %if OFFER_PDF_ANON_VERSION:
                    [<a href="${ req.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: task_tablename,
                                ViewParam.SERVER_PK: task_pk,
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
