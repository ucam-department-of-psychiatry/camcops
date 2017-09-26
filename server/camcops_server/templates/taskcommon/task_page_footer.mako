## task_page_footer.mako
<%page args="task: Task"/>

<%!

from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import DateFormat

%>

${ task.shortname | h } created ${ format_datetime(task.when_created, DateFormat.LONG_DATETIME) }.
