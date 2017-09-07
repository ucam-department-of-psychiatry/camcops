## view_tasks.mako
## <%page args="page: Page, head_form_html: str, no_patient_selected_and_user_restricted: bool"/>
<%inherit file="base_web_form.mako"/>

<%!

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dt import format_datetime

%>

<%include file="db_user_info.mako"/>

<h1>View tasks</h1>

<h2>Filters (criteria)</h2>

XXX_form

<h2>Number of tasks to view per page</h2>

XXX_form

<h2>Tasks</h2>

XXX_filter

%if no_patient_selected_and_user_restricted:
    <div class="explanation">
        Your user isn’t configured to view all patients’ records when no
        patient filters are applied. Only anonymous records will be
        shown. Choose a patient to see their records.
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
            <th>Surname, forename (sex, DOB, age)</th>
            <th>Identifiers</th>
            <th>Task type</th>
            <th>Adding user</th>
            <th>Created</th>
            <th>View detail</th>
            <th>Print/save detail</th>
        </tr>

        %for task in page:
            ## ${ repr(task) | h }
            <tr>
                ## Surname, forename (sex, DOB, age)
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
                            ${ task.patient.get_html_for_webview_patient_column(req) }
                        %else:
                            ?
                        %endif
                    %endif
                </td>
                ## ID numbers
                <td>
                    %if task.is_anonymous:
                        —
                    %else:
                        %if task.patient:
                            ${ task.patient.get_html_for_id_col(req) }
                        %else:
                            ?
                        %endif
                    %endif
                </td>
                ## Task type
                <td
                    %if not task._current:
                        ## Shouldn't occur these days; we pre-filter for this!
                    %endif
                    class="warning"
                    >
                    <b> ${ task.shortname | h }</b>
                </td>
                ## Adding user
                <td>
                    ${ task._adding_user.username | h }
                </td>
                ## When created
                <td
                    %if task.is_live_on_tablet():
                        class="live_on_tablet"
                    %endif
                    >
                    ${ format_datetime(task.when_created, DateFormat.SHORT_DATETIME) }
                    ## ***
                </td>
                ## Hyperlink to HTML
                <td
                    %if not task.is_complete():
                        class="incomplete"
                    %endif
                    >
                    <a href="${ req.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLENAME: task.tablename,
                                ViewParam.SERVER_PK: task._pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML,
                            }) }">HTML</a>
                    [<a href="${ req.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLENAME: task.tablename,
                                ViewParam.SERVER_PK: task._pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML,
                                ViewParam.ANONYMISE: True,
                            }) }">anon</a>]
                </td>
                ## Hyperlink to PDF
                <td
                    %if not task.is_complete():
                        class="incomplete"
                    %endif
                    >
                    <a href="${ req.route_url(
                        Routes.TASK,
                        _query={
                            ViewParam.TABLENAME: task.tablename,
                            ViewParam.SERVER_PK: task._pk,
                            ViewParam.VIEWTYPE: ViewArg.PDF,
                        }) }">PDF</a>
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
