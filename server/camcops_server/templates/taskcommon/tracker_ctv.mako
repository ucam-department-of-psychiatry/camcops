## tracker.mako
## <%page args="tracker: Tracker, pdf_landscape: bool"/>

<%!

from cardinal_pythonlib.datetimefunc import format_datetime
from camcops_server.cc_modules.cc_constants import CSS_PAGED_MEDIA, DateFormat
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
from camcops_server.cc_modules.cc_tracker import format_daterange
from camcops_server.cc_modules.cc_version_string import CAMCOPS_SERVER_VERSION_STRING

def inherit_file(context):
    viewtype = context['viewtype']
    if viewtype == ViewArg.HTML:
        return "base_web.mako"
    elif viewtype == ViewArg.PDF:
        if CSS_PAGED_MEDIA:
            pdf_landscape = context['pdf_landscape']
            if pdf_landscape:
                return "base_pdf_landscape.mako"
            else:
                return "base_pdf_portrait.mako"
        else:
            return "base_pdf_no_paged_media.mako"
    else:
        raise ValueError("This template is only for HTML/PDF views")

%>

<%inherit file="${ inherit_file(context) }"/>

## ============================================================================
## For CSS paged media, extra headers
## ============================================================================

%if CSS_PAGED_MEDIA and viewtype == ViewArg.PDF:
    <%block name="extra_header_content">
        <%include file="tracker_ctv_header.mako" args="tracker=tracker"/>
    </%block>
    <%block name="extra_footer_content">
        <%include file="tracker_ctv_footer.mako" args="tracker=tracker"/>
    </%block>
%endif
## For non-paged media (i.e. wkhtmltopdf), the headers/footers are made separately.

## ============================================================================
## Header for tracker/CTV, including patient ID information
## ============================================================================

<div class="trackerheader">
    Patient identified by: <b>${ ("; ".join(x.description(request) for x in tracker.taskfilter.idnum_criteria) + ".") }</b>
    Date range for search: <b>${ format_daterange(tracker.taskfilter.start_datetime, tracker.taskfilter.end_datetime) }</b>.
    The tracker information will <b>only be valid</b> (i.e. will
    only be from only one patient!) if all contributing tablet
    devices use these identifiers consistently. The consistency
    check is below. The patient information shown below is taken
    from the first task used.
</div>

## Consistency
<%
    cons = tracker.consistency_info.get_description_list()
    if tracker.consistency_info.are_all_consistent():
        cons_class = "tracker_all_consistent"
        joiner = ". "
    else:
        cons_class = "warning"
        joiner = "<br>"
    consistency = joiner.join(cons)
%>
<div class="${ cons_class }">
    ${ consistency }
</div>

## Patient
%if tracker.patient:
    <%include file="patient.mako" args="patient=tracker.patient"/>
%else:
    <div class="warning">
        No patient found, or the patient has no relevant tasks in the time
        period requested.
    </div>
%endif

## ============================================================================
## Main bit
## ============================================================================

${next.body()}

## ============================================================================
## Office stuff
## ============================================================================

<div class="office">
    <%block name="office_preamble"/>

    Requested tasks:
        ${ (", ".join(tracker.taskfilter.task_tablename_list) if tracker.taskfilter.task_classes else "None") }.
    Sources (tablename, task server PK, patient server PK):
        ${ tracker.summary }.
    Information retrieved from ${ request.application_url }
        (server version ${ CAMCOPS_SERVER_VERSION_STRING })
        at: ${ format_datetime(request.now, DateFormat.SHORT_DATETIME_SECONDS) }.
</div>

## ============================================================================
## Navigation links, if applicable
## ============================================================================

%if viewtype == ViewArg.HTML:
    <div class="navigation">
        ## Link to PDF version
        <a href="${ req.route_url(
            Routes.CTV if tracker.as_ctv else Routes.TRACKER,
            _query={
                ViewParam.WHICH_IDNUM: tracker.taskfilter.idnum_criteria[0].which_idnum,
                ViewParam.IDNUM_VALUE: tracker.taskfilter.idnum_criteria[0].idnum_value,
                ViewParam.START_DATETIME: tracker.taskfilter.start_datetime,
                ViewParam.END_DATETIME: tracker.taskfilter.end_datetime,
                ViewParam.TASKS: tracker.taskfilter.task_tablename_list,
                ViewParam.VIEWTYPE: ViewArg.PDF,
            }) }">View PDF for printing/saving</a>
    </div>
%endif
