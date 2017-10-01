## view_tasks.mako
## <%page args="page: Page, head_form_html: str, no_patient_selected_and_user_restricted: bool, user: User"/>
<%inherit file="base_web_form.mako"/>

<%!

from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam

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
        Records will only be shown if they are anonymous, or for groups that
        allow you to see all patients in these circumstances.
        Choose a specific patient to see their records.
    </div>
%endif
%if not user.superuser and not user.group_ids:
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

    <%include file="view_tasks_table.mako" args="tasks=page"/>

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
