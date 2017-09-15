## view_tasks.mako
## <%page args="page: Page, head_form_html: str, no_patient_selected_and_user_restricted: bool"/>
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

<i>
    <%
        ccsession = request.camcops_session
        some_filter = False
    %>
    %if ccsession.filter_surname:
        Surname = <b>${ ccsession.filter_surname | h }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_forename:
        Forename = <b>${ ccsession.filter_forename | h }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_dob:
        DOB = <b>${ format_datetime(ccsession.filter_dob, DateFormat.SHORT_DATE )}</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_sex:
        Sex = <b>${ ccsession.filter_sex }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_task:
        Task = <b>${ ccsession.filter_task }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_complete:
        <b>Complete tasks only.</b>
        <% some_filter = True %>
    %endif
    %if ccsession.filter_device:
        Device ID = <b>${ ccsession.filter_device.name }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_user:
        Adding user = <b>${ ccsession.filter_user.username }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_start_datetime:
        Created <b>&ge; ${ ccsession.filter_start_datetime }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_end_datetime:
        Created <b>&le; ${ ccsession.filter_end_datetime }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_text:
        Text contains: <b>${ repr(ccsession.filter_text) | h }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_idnums:
        ID numbers match one of:
        ${ ("; ".join("{which} = <b>{value}</b>".format(
                which=request.config.get_id_shortdesc(iddef.which_idnum),
                value=iddef.idnum_value,
            ) for iddef in ccsession.filter_idnums) + ".") }
        <% some_filter = True %>
    %endif

    %if not some_filter:
        [No filters.]
    %endif
</i>

<div><a href="${ request.route_url(Routes.SET_FILTERS) }">Set or clear filters</a></div>

<h1>Tasks</h1>

## https://stackoverflow.com/questions/12201835/form-inline-inside-a-form-horizontal-in-twitter-bootstrap
## https://stackoverflow.com/questions/18429121/inline-form-nested-within-horizontal-form-in-bootstrap-3
${ tpp_form }

${ refresh_form }

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
                    %endif
                    class="warning"
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
                                ViewParam.TABLENAME: task.tablename,
                                ViewParam.SERVER_PK: task._pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML,
                            }) }">HTML</a>
                    %if OFFER_HTML_ANON_VERSION:
                        [<a href="${ req.route_url(
                                Routes.TASK,
                                _query={
                                    ViewParam.TABLENAME: task.tablename,
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
                            ViewParam.TABLENAME: task.tablename,
                            ViewParam.SERVER_PK: task._pk,
                            ViewParam.VIEWTYPE: ViewArg.PDF,
                        }) }">PDF</a>
                    %if OFFER_PDF_ANON_VERSION:
                        [<a href="${ req.route_url(
                                Routes.TASK,
                                _query={
                                    ViewParam.TABLENAME: task.tablename,
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
