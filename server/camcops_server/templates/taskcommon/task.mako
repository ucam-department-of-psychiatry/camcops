## task.mako
## <%page args="task: Task, viewtype: str, anonymise: bool"/>

<%!

from camcops_server.cc_modules.cc_constants import DateFormat, ERA_NOW
from camcops_server.cc_modules.cc_dt import format_datetime
from camcops_server.cc_modules.cc_html import (
    answer,
    get_yes_no,
)
from camcops_server.cc_modules.cc_version_string import CAMCOPS_SERVER_VERSION_STRING

def inherit_file(context):
    ## https://groups.google.com/forum/#!topic/mako-discuss/okPBlbGhy_U
    ViewArg = context['ViewArg']
    viewtype = context['viewtype']
    if viewtype == ViewArg.HTML:
        return "base_web.mako"
    elif viewtype in [ViewArg.PDF, ViewArg.PDFHTML]:
        return "base_pdf_no_paged_media.mako"
        # ... for wkhtmltopdf (for other engines we might have to look at
        # task.use_landscape_for_pdf and choose "base_pdf_landscape.mako" or
        # "base_pdf_portrait.mako".
    else:
        raise ValueError("This template is only for HTML/PDF/PDFHTML views")

%>

<%inherit file="${ inherit_file(context) }"/>

## ============================================================================
## Patient (or "anonymous" label)
## ============================================================================

%if task.has_patient:
    %if anonymise:
        <div class="warning">
            Patient details hidden at user’s request!
        </div>
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

## ============================================================================
## Erasure notice (if applicable)
## ============================================================================

%if task._manually_erased:
    <div class="warning">
        <b>RECORD HAS BEEN MANUALLY ERASED
            BY ${ task.get_manually_erasing_user_username() | h }
            AT ${ task._manually_erased_at }.</b>
    </div>
%endif

## ============================================================================
## "Not current" warning (if applicable)
## ============================================================================

%if not task._current:
    <div class="warning">
        %if task._pk is None:
            WARNING! This is NOT a valid record. It has a blank primary
            key and is therefore nonsensical (and only useful for
            software testing).
        %else:
            WARNING! This is NOT a current record.<br>
            %if task._successor_pk is not None:
                It was MODIFIED at ${ format_datetime(task._when_removed_exact, DateFormat.LONG_DATETIME_SECONDS) }.
            %elif task._manually_erased:
                It was MANUALLY ERASED at ${ format_datetime(task._manually_erased_at, DateFormat.LONG_DATETIME_SECONDS) }.
            %else:
                It was DELETED at ${ format_datetime(task._when_removed_exact, DateFormat.LONG_DATETIME_SECONDS) }.
            %endif
        %endif
    </div>
%endif

## ============================================================================
## "Invalid contents" warning (if applicable)
## ============================================================================

%if not task.field_contents_valid():
    <div class="warning">
        <b>WARNING. Invalid values.</b>
        %for idx, explanation in enumerate(task.field_contents_invalid_because()):
            %if idx > 0:
                <br>
            %endif
            ${ explanation | h }
        %endfor
    </div>
%endif

## ============================================================================
## Special notes (if applicable)
## ============================================================================

%if task.special_notes:
    <%include file="special_notes.mako" args="special_notes=task.special_notes, title='TASK SPECIAL NOTES'"/>
%endif

## ============================================================================
## Clinician
## ============================================================================

%if task.has_clinician:
    <%include file="clinician.mako" args="task=task"/>
%endif

## ============================================================================
## Respondent
## ============================================================================

%if task.has_respondent:
    <%include file="respondent.mako" args="task=task"/>
%endif

## ============================================================================
## Main task content
## ============================================================================

${ task.get_task_html(req) }

## ============================================================================
## "Office" stuff
## ============================================================================

<div class="office">
    Created on device at: ${ format_datetime(task.when_created, DateFormat.SHORT_DATETIME_SECONDS) }.
    Last modified at: ${ format_datetime(task.when_last_modified, DateFormat.SHORT_DATETIME_SECONDS) }.
    Table: ${ task.tablename }.
    Task PK on client device: ${ task.id }.
    Uploading device ID: ${ task.device.get_friendly_name_and_id() if task.device else "?" | h }.
    Tablet CamCOPS version at upload: ${ task._camcops_version }.
    Uploaded at: ${ format_datetime(task._when_added_exact, DateFormat.SHORT_DATETIME_SECONDS) }.
    Adding user: ${ task.get_adding_user_username() }.
    Server PK: ${ task._pk }
        (predecessor ${ task._predecessor_pk },
        successor ${ task._successor_pk }).
    Current?
        %if task._current:
            ## some repetition as harder to have no space before "." otherwise!
            ${ get_yes_no(req, True) }.
        %else:
            ${ get_yes_no(req, False) }
            %if task._successor_pk is None:
                (deleted
            %else:
                (modified
            %endif
            by ${ task.get_removing_user_username() | h }
            at ${ format_datetime(task._when_removed_exact, DateFormat.SHORT_DATETIME_SECONDS) }.
        %endif
    Preserved/erased from tablet?
        %if task.is_preserved():
            ${ get_yes_no(req, True) }
            %if task.was_forcibly_preserved():
                (forcibly preserved
            %else:
                (preserved
            %endif
            by ${ task.get_preserving_user_username() | h }
            at ${ task._era }.
            ## ... already an UTC ISO8601 string (BUT Python transformation now).
        %else:
            ${ get_yes_no(req, False) }.
        %endif
    Patient server PK used: ${ task.get_patient_server_pk() if not task.is_anonymous else "N/A" }.
    Information retrieved from ${ req.url | h }
        (server version ${ CAMCOPS_SERVER_VERSION_STRING })
        at: ${ format_datetime(req.now_arrow, DateFormat.SHORT_DATETIME_SECONDS) }.
</div>

## ============================================================================
## Extra hyperlinks for web version
## ============================================================================

%if viewtype == ViewArg.HTML:

    ## Link to XML version

    <div class="office">
        <a href="${ req.route_url(
                        Routes.TASK,
                        _query={
                            ViewParam.TABLENAME: task.tablename,
                            ViewParam.SERVER_PK: task._pk,
                            ViewParam.VIEWTYPE: ViewArg.XML,
                        }) }">View raw data as XML</a>
    </div>

    ## Superuser options
    <div class="superuser">
        ## check this collapses to zero height with no content!
        %if req.camcops_session.authorized_to_add_special_note():
            <p><a href="${ req.route_url(
                        Routes.ADD_SPECIAL_NOTE,
                        _query={
                            ViewParam.TABLENAME: task.tablename,
                            ViewParam.SERVER_PK: task._pk,
                        }) }">Apply special note</a></p>
        %endif
        %if req.camcops_session.authorized_as_superuser():
            %if not task.is_erased() and task._era != ERA_NOW:
                ## Note: prohibit manual erasure for non-finalized tasks.
                <p><a href="${ req.route_url(
                            Routes.ADD_SPECIAL_NOTE,
                            _query={
                                ViewParam.TABLENAME: task.tablename,
                                ViewParam.SERVER_PK: task._pk,
                            }) }">Erase task instance</a></p>
            %endif
        %endif
    </div>

    ## Links to predecessor / successor / PDF

    <div class="navigation">
        ## Links to predecessor/successor
        %if task._predecessor_pk is not None:
            <p><i>
                An older version of this record exists:
                <a href="${ req.route_url(
                        Routes.TASK,
                        _query={
                            ViewParam.TABLENAME: task.tablename,
                            ViewParam.SERVER_PK: task._predecessor_pk,
                            ViewParam.VIEWTYPE: ViewArg.HTML,
                        }) }">view previous version</a>.
            </i></p>
        %endif
        %if task._successor_pk is not None:
            <p><b>
                An newer version of this record exists:
                <a href="${ req.route_url(
                        Routes.TASK,
                        _query={
                            ViewParam.TABLENAME: task.tablename,
                            ViewParam.SERVER_PK: task._successor_pk,
                            ViewParam.VIEWTYPE: ViewArg.HTML,
                        }) }">view next version</a>.
            </b></p>
        %endif

        ## Link to PDF version
        <p>
            <a href="${ req.route_url(
                Routes.TASK,
                _query={
                    ViewParam.TABLENAME: task.tablename,
                    ViewParam.SERVER_PK: task._pk,
                    ViewParam.VIEWTYPE: ViewArg.PDF,
                }) }">View PDF for printing/saving</a>
        </p>
    </div>

%endif
