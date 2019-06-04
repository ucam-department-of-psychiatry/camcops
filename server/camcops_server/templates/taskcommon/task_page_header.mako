## task_page_header.mako
<%page args="task: Task, anonymise: bool"/>

<%!
from camcops_server.cc_modules.cc_text import SS
%>

%if task.is_anonymous:
    ${ request.sstring(SS.ANONYMOUS_TASK) }
%elif anonymise:
    <div class="warning">${_("Patient details hidden at user’s request!")}</div>
%else:
    %if task.patient:
        <%include file="patient_page_header.mako" args="patient=task.patient"/>
    %else:
        <div class="warning">${_("Missing patient!")}</div>
    %endif
%endif
