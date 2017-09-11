## tracker_ctv_footer.mako
<%page args="tracker: TrackerCtvCommon"/>

<%!

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dt import format_datetime

%>

${ ("CTV" if tracker.as_ctv else "Tracker") }
accessed ${ format_datetime(request.now, DateFormat.LONG_DATETIME) }.
