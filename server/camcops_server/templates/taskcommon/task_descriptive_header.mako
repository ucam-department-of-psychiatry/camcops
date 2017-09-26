## task_descriptive_header.mako
<%page args="task: Task, anonymise: bool"/>

<%!
from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_html import answer
%>

## ============================================================================
## Patient (or "anonymous" label)
## ============================================================================

%if task.has_patient:
    %if anonymise:
        <div class="warning">Patient details hidden at user’s request!</div>
    %else:
        %if task.patient:
            <%include file="patient.mako" args="patient=task.patient, anonymise=anonymise"/>
        %else:
            <div class="warning">Missing patient information!</div>
        %endif
    %endif
%else:
    <div class="patient">
        ${ req.wappstring("anonymous_task") }
    </div>
%endif

## ============================================================================
## Which task, and when created (+/- how old was the patient then)?
## ============================================================================

<div class="taskheader">
    <b>${ task.longname | h } (${ task.shortname | h })</b><br>
    Created: ${ answer(format_datetime(task.when_created,
                                       DateFormat.LONG_DATETIME_WITH_DAY,
                                       default=None)) }
    %if not task.is_anonymous and task.patient:
        (patient aged ${ answer(task.patient.get_age_at(task.when_created),
                                default_for_blank_strings=True) })
    %endif
</div>
