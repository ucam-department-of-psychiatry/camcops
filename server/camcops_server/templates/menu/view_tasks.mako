## view_tasks.mako
## <%page args="page: Page, head_form_html: str, no_patient_selected_and_user_restricted: bool, user: User"/>
<%inherit file="base_web_form.mako"/>

<%!

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dt import format_datetime
from camcops_server.cc_modules.cc_html import get_true_false
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam

OFFER_HTML_ANON_VERSION = False
OFFER_PDF_ANON_VERSION = False

%>

<%include file="db_user_info.mako"/>

<h1>Currently applicable filters</h1>

<%include file="describe_task_filter.mako" args="task_filter=request.camcops_session.get_task_filter()"/>

<div><a href="${ request.route_url(Routes.SET_FILTERS) }">Set or clear filters</a></div>

<h1>Tasks</h1>

## https://stackoverflow.com/questions/12201835/form-inline-inside-a-form-horizontal-in-twitter-bootstrap
## https://stackoverflow.com/questions/18429121/inline-form-nested-within-horizontal-form-in-bootstrap-3
${ tpp_form }

${ refresh_form }

%if no_patient_selected_and_user_restricted:
    <div class="explanation">
        Your user isn’t configured to view all patients’ records when no
        patient filters are applied, and none is.
        Only anonymous records will be shown.
        Choose a patient to see their records.
    </div>
%endif
%if not user.superuser and not user.group_ids():
    <div class="warning">
        Your administrator has not assigned you to any groups.
        You won’t be able to see any tasks.
    </div>
%endif

%if page.item_count == 0:

    <div class="important">
        No tasks found for your search criteria!
    </div>

%else:

    <div>${page.pager()}</div>

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

        %for task in page:
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
                    ## ***
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

    <div>${page.pager()}</div>

    <div class="footnotes">
        Colour in the Patient column means that an ID policy is not yet
            satisfied.
        Colour in the Task Type column means the record is not current.
        Colour in the Created column means the task is ‘live’ on the tablet,
            not finalized (so patient and task details may change).
        Colour in the View/Print columns means the task is incomplete.
        ## NOT CURRENTLY: Colour in the Identifiers column means a conflict
        ## between the server’s and the tablet’s ID descriptions.
    </div>

%endif

<%include file="to_main_menu.mako"/>
