## tracker_ctv_footer.mako
<%page args="tracker: TrackerCtvCommon"/>

<%!

from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import DateFormat

%>

${ ("CTV" if tracker.as_ctv else "Tracker") }
accessed ${ format_datetime(request.now, DateFormat.LONG_DATETIME) }.
