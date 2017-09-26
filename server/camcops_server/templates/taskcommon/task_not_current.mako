## task_not_current.mako
<%page args="task: Task"/>

<%!

from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import DateFormat

%>

<div class="warning">
    %if task._pk is None:
        WARNING! This is NOT a valid record. It has a blank primary
        key and is therefore nonsensical (and only useful for
        software testing).
    %else:
        WARNING! This is NOT a current record.<br>
        %if task._successor_pk is not None:
            It was MODIFIED at
            ${ format_datetime(task._when_removed_exact, DateFormat.LONG_DATETIME_SECONDS) }.
        %elif task._manually_erased:
            It was MANUALLY ERASED at
            ${ format_datetime(task._manually_erased_at, DateFormat.LONG_DATETIME_SECONDS) }
            by ${ task.get_manually_erasing_user_username() | h }.
        %else:
            It was DELETED at
            ${ format_datetime(task._when_removed_exact, DateFormat.LONG_DATETIME_SECONDS) }.
        %endif
    %endif
</div>
