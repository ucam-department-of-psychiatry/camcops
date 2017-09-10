## task_page_header.mako
<%page args="task: Task, anonymise: bool"/>

%if task.is_anonymous:
    ${ request.wappstring("anonymous_task") }
%elif anonymise:
    <div class="warning">Patient details hidden at user’s request!</div>
%else:
    %if task.patient:
        <%include file="patient_page_header.mako" args="patient=task.patient"/>
    %else:
        <div class="warning">Missing patient!</div>
    %endif
%endif
