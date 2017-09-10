## task_page_footer.mako
<%page args="task: Task"/>

<%!

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dt import format_datetime

%>

${ task.shortname | h } created ${ format_datetime(task.when_created, DateFormat.LONG_DATETIME) }.
