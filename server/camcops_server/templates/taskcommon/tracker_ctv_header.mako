## tracker_ctv_header.mako
<%page args="tracker: TrackerCtvCommon"/>

%if tracker.patient:
    <%include file="patient_page_header.mako" args="patient=tracker.patient"/>
%else:
    <div class="warning">Missing patient!</div>
%endif
