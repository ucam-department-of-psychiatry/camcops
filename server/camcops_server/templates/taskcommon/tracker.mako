## tracker.mako
## <%page args="tracker: Tracker, viewtype: str, pdf_landscape: bool"/>
<%inherit file="tracker_ctv.mako"/>

<%block name="office_preamble">
    Trackers use only information from tasks that are flagged CURRENT and
    COMPLETE.
</%block>

%if not tracker.collection.all_tasks:

    <div class="warning">
        No tasks found for tracker.
    </div>

%elif not tracker.patient:

    <div class="warning">
        No patient found for tracker.
    </div>

%else:

    %for cls in tracker.taskfilter.task_classes:
        <% instances = tracker.collection.tasks_for_task_class(cls) %>
        %if instances:
            <div class="taskheader">
                <b>${ instances[0].longname | h } (${ instances[0].shortname | h })</b>
            </div>
            ${ tracker.get_all_plots_for_one_task_html(instances) }
        %endif
    %endfor

%endif
