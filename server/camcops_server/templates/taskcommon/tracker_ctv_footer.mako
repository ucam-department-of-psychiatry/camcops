## tracker_ctv_footer.mako
<%page args="tracker: TrackerCtvCommon"/>

${ ("CTV" if tracker.as_ctv else "Tracker") }
accessed ${ format_datetime(request.now, DateFormat.LONG_DATETIME }.
