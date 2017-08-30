#!/usr/bin/env python
# camcops_server/cc_modules/cc_tracker.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from cardinal_pythonlib.lists import flatten_list
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws

from .cc_audit import audit
from .cc_constants import (
    ACTION,
    CSS_PAGED_MEDIA,
    DATEFORMAT,
    FP_ID_NUM,
    FULLWIDTH_PLOT_WIDTH,
    PARAM,
    RESTRICTED_WARNING_SINGULAR,
    VALUE,
)
from .cc_dt import format_datetime
from .cc_filename import get_export_filename
from .cc_html import (
    get_generic_action_url,
    get_html_from_pyplot_figure,
    get_url_field_value_pair,
    pdf_footer_content,
    pdf_header_content,
)
from .cc_plot import matplotlib, set_matplotlib_fontsize
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_pdf import pdf_from_html
from .cc_request import CamcopsRequest
from .cc_session import CamcopsSession
from .cc_task import Task
from .cc_trackerhelpers import TrackerInfo
from .cc_unittest import unit_test_ignore
from .cc_version import CAMCOPS_SERVER_VERSION
from .cc_xml import get_xml_document, XmlDataTypes, XmlElement

import matplotlib.pyplot as plt  # ONLY AFTER IMPORTING cc_plot

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

TRACKER_DATEFORMAT = "%Y-%m-%d"
WARNING_NO_PATIENT_FOUND = """
    <div class="warning">
        No patient found, or the patient has no relevant tasks in the time
        period requested.
    </div>
"""
WARNING_DENIED_INFORMATION = """
    <div class="warning">
        Other tasks exist for this patient that you do not have access to view.
    </div>
"""

DEBUG_TRACKER_TASK_INCLUSION = False  # should be False for production system


# =============================================================================
# Helper functions
# =============================================================================
# http://stackoverflow.com/questions/11788195

def consistency(values: List[Any],
                servervalue: Any = None,
                case_sensitive: bool = True) -> Tuple[bool, str]:
    """Checks for consistency in a set of values (e.g. ID numbers, names).

    The list of values (with the servervalue appended, if not None) is checked
    to ensure that it contains only one unique value (ignoring None values or
    empty "" values).

    Returns tuple: (consistent, msg)
        consistent: Boolean
        msg: HTML message
    """
    if case_sensitive:
        vallist = [str(v) if v is not None else v for v in values]
        if servervalue is not None:
            vallist.append(str(servervalue))
    else:
        vallist = [str(v).upper() if v is not None else v for v in values]
        if servervalue is not None:
            vallist.append(str(servervalue).upper())
    # Replace "" with None, so we only have a single "not-present" value
    vallist = [None if x == "" else x for x in vallist]
    unique = list(set(vallist))
    if len(unique) == 0:
        return True, "consistent (no values)"
    if len(unique) == 1:
        return True, "consistent ({})".format(unique[0])
    if len(unique) == 2:
        if None in unique:
            return True, "consistent (all blank or {})".format(
                unique[1 - unique.index(None)]
            )
    return False, "<b>INCONSISTENT (contains values {})</b>".format(
        ", ".join(unique)
    )


def consistency_idnums(idnum_lists: List[List[PatientIdNum]]) \
        -> Tuple[bool, str]:
    known = {}  # type: Dict[int, Set[int]]  # maps which_idnum -> set of idnum_values  # noqa
    for idnum_list in idnum_lists:
        for idnum in idnum_list:
            idnum_value = idnum.idnum_value
            if idnum_value is not None:
                which_idnum = idnum.which_idnum
                if which_idnum not in known:
                    known[which_idnum] = set()  # type: Set[int]
                known[which_idnum].add(idnum_value)
    failures = []  # type: List[str]
    successes = []  # type: List[str]
    for which_idnum, encountered_values in known.items():
        value_str = ", ".join(str(v) for v in sorted(list(encountered_values)))
        if len(encountered_values) > 1:
            failures.append("idnum{} contains values {}".format(
                which_idnum, value_str))
        else:
            successes.append("idnum{} all blank or {}".format(
                which_idnum, value_str))
    if failures:
        return False, "<b>INCONSISTENT ({})</b>".format(
            "; ".join(failures + successes))
    else:
        return True, "consistent ({})".format("; ".join(successes))


def get_summary_of_tasks(list_of_task_instance_lists: List[List[Task]]) -> str:
    """Textual list of participating tasks."""
    return " — ".join(
        [
            "; ".join(
                [
                    "({},{},{})".format(
                        task.tablename,
                        task.get_pk(),
                        task.get_patient_server_pk()
                    )
                    for task in tasklist
                ]
            )
            for tasklist in list_of_task_instance_lists
        ]
    )


def format_daterange(start: Optional[datetime.datetime],
                     end: Optional[datetime.datetime]) -> str:
    """Textual representation of inclusive date range.

    Arguments are datetime values."""
    return "[{}, {}]".format(
        format_datetime(start, DATEFORMAT.ISO8601_DATE_ONLY, default="−∞"),
        format_datetime(end, DATEFORMAT.ISO8601_DATE_ONLY, default="+∞")
    )


# =============================================================================
# ConsistencyInfo class
# =============================================================================

class ConsistencyInfo(object):
    """Stores ID consistency information about a set of tasks."""

    def __init__(self, flattasklist: List[Task]) -> None:
        """Initialize values, from a list of task instances."""
        self.consistent_forename, self.msg_forename = consistency(
            [task.get_patient_forename() for task in flattasklist],
            servervalue=None, case_sensitive=False)
        self.consistent_surname, self.msg_surname = consistency(
            [task.get_patient_surname() for task in flattasklist],
            servervalue=None, case_sensitive=False)
        self.consistent_dob, self.msg_dob = consistency(
            [task.get_patient_dob_first11chars() for task in flattasklist])
        self.consistent_sex, self.msg_sex = consistency(
            [task.get_patient_sex() for task in flattasklist])
        self.consistent_idnums, self.msg_idnums = consistency_idnums(
            [task.get_patient_idnum_objects() for task in flattasklist])
        self.all_consistent = (
            self.consistent_forename and
            self.consistent_surname and
            self.consistent_dob and
            self.consistent_sex and
            self.consistent_idnums
        )

    def are_all_consistent(self) -> bool:
        """Is all the ID information consistent?"""
        return self.all_consistent

    def get_description_list(self) -> List[str]:
        """Textual representation of ID information, indicating consistency or
        lack of it."""
        cons = [
            "Forename: {}".format(self.msg_forename),
            "Surname: {}".format(self.msg_surname),
            "DOB: {}".format(self.msg_dob),
            "Sex: {}".format(self.msg_sex),
            "ID numbers: {}".format(self.msg_idnums),
        ]
        return cons

    def get_xml_root(self) -> XmlElement:
        """XML tree (as root XmlElementTuple) of consistency information."""
        branches = [
            XmlElement(
                name="all_consistent",
                value=self.are_all_consistent(),
                datatype="boolean"
            )
        ]
        for c in self.get_description_list():
            branches.append(XmlElement(
                name="consistency_check",
                value=c,
            ))
        return XmlElement(name="_consistency", value=branches)


# =============================================================================
# TrackerCtvCommon class:
# =============================================================================

class TrackerCtvCommon(object):
    """Base class for Tracker and ClinicalTextView."""

    def __init__(self,
                 session: CamcopsSession,
                 task_class_list: List,
                 which_idnum: int,
                 idnum_value: int,
                 start_datetime: Optional[datetime.datetime],
                 end_datetime: Optional[datetime.date],
                 as_ctv: bool) -> None:
        """Initialize, fetching applicable tasks."""

        # Record input variables at this point (for URL regeneration)
        self.task_class_list = task_class_list
        self.task_tablename_list = [cls.tablename for cls in task_class_list]
        self.which_idnum = which_idnum
        self.idnum_value = idnum_value
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.as_ctv = as_ctv

        # What filters?
        self.idnum_criteria = [(which_idnum, idnum_value)]

        # Date range? NB date adjustment to include the whole of the final day.
        self.end_datetime_extended = None
        if self.end_datetime is not None:
            self.end_datetime_extended = (
                self.end_datetime + datetime.timedelta(days=1)
            )
        log.debug("start_datetime: ", self.start_datetime)
        log.debug("end_datetime: ", self.end_datetime)
        log.debug("end_datetime_extended: ", self.end_datetime_extended)

        self.restricted_warning = (
            RESTRICTED_WARNING_SINGULAR
            if session.restricted_to_viewing_user() else ""
        )
        self._patient = None  # type: Patient  # default value if we fail
        self.list_of_task_instance_lists = []  # type: List[List[Task]]
        # ... list (by task class) of lists of task instances
        self.earliest = None  # type: datetime.datetime
        self.latest = None  # type: datetime.datetime
        self.summary = ""
        first = True

        # Build task lists. For each class:
        for cls in task_class_list:

            # Debugging information
            if DEBUG_TRACKER_TASK_INCLUSION:
                if not first:
                    self.summary += " // "
                self.summary += cls.tablename
            first = False
            if cls.is_anonymous:
                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " (anonymous)"
                continue

            # Get server PKs
            if self.as_ctv:
                serverpks = cls.get_task_pks_for_clinical_text_view(
                    self.idnum_criteria, self.start_datetime,
                    self.end_datetime_extended)
            else:
                serverpks = cls.get_task_pks_for_tracker(
                    self.idnum_criteria, self.start_datetime,
                    self.end_datetime_extended)

            if len(serverpks) == 0:
                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " (no instances)"
                continue

            # Iterate through task instances
            task_instances = []
            for s in serverpks:
                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " / PK {}".format(s)
                # Make task instance
                task = cls(s)
                if task is None:
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (task is None)"
                    continue
                if not task.allowed_to_user(session):
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (denied to user)"
                    continue

                # Second check on datetimes
                dt = task.get_creation_datetime()
                if (self.start_datetime is not None and
                        dt < self.start_datetime):
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (start date wrong)"
                    continue
                if (self.end_datetime_extended is not None and
                        dt > self.end_datetime_extended):
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (end date wrong)"
                    continue
                # We need to know earliest/latest for consistent axis scaling
                if self.earliest is None or dt < self.earliest:
                    self.earliest = dt
                if self.latest is None or dt > self.latest:
                    self.latest = dt

                # We include incomplete tasks in CTVs, but not trackers
                if not as_ctv and not task.is_complete():
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (not complete)"
                    continue

                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " (FOUND ONE)"
                task_instances.append(task)

            if len(task_instances) > 0:
                self.list_of_task_instance_lists.append(task_instances)

        # Within each task class, sort by creation date/time:
        for taskclass in range(len(self.list_of_task_instance_lists)):
            self.list_of_task_instance_lists[taskclass].sort(
                key=lambda task_: task_.get_creation_datetime())

        # Flat task list, sorted by creation date/time
        self.flattasklist = flatten_list(self.list_of_task_instance_lists)
        self.flattasklist.sort(key=lambda task_: task_.get_creation_datetime())

        # Fetch patient information
        if len(self.flattasklist) > 0:
            # noinspection PyProtectedMember
            self._patient = self.flattasklist[0]._patient
            # patient details from the first of our tasks

        # Summary information
        self.summary += get_summary_of_tasks(self.list_of_task_instance_lists)

        # Consistency information
        self.consistency_info = ConsistencyInfo(self.flattasklist)

    # -------------------------------------------------------------------------
    # Required for implementation
    # -------------------------------------------------------------------------

    def get_xml(self,
                req: CamcopsRequest,
                indent_spaces: int = 4,
                eol: str = '\n',
                include_comments: bool = False) -> str:
        raise NotImplementedError()

    def get_html(self, req: CamcopsRequest) -> str:
        raise NotImplementedError()

    def get_pdf_html(self, req: CamcopsRequest) -> str:
        raise NotImplementedError()

    def get_office_html(self, req: CamcopsRequest) -> str:
        raise NotImplementedError()

    # -------------------------------------------------------------------------
    # XML view
    # -------------------------------------------------------------------------

    def _get_xml(self,
                 audit_string: str,
                 xml_name: str,
                 indent_spaces: int = 4,
                 eol: str = '\n',
                 include_comments: bool = False) -> str:
        """Get XML document representing tracker."""
        branches = [
            self.consistency_info.get_xml_root(),
            XmlElement(
                name="_search_criteria",
                value=[
                    XmlElement(
                        name="task_tablename_list",
                        value=",".join(self.task_tablename_list)
                    ),
                    XmlElement(
                        name="which_idnum",
                        value=self.which_idnum,
                        datatype=XmlDataTypes.INTEGER
                    ),
                    XmlElement(
                        name="idnum_value",
                        value=self.idnum_value,
                        datatype=XmlDataTypes.INTEGER
                    ),
                    XmlElement(
                        name="start_datetime",
                        value=format_datetime(self.start_datetime,
                                              DATEFORMAT.ISO8601),
                        datatype=XmlDataTypes.DATETIME
                    ),
                    XmlElement(
                        name="end_datetime",
                        value=format_datetime(self.end_datetime,
                                              DATEFORMAT.ISO8601),
                        datatype=XmlDataTypes.DATETIME
                    ),
                ]
            )
        ]
        for t in self.flattasklist:
            branches.append(t.get_xml_root(include_calculated=True,
                                           include_blobs=False))
            audit(
                audit_string,
                table=t.tablename,
                server_pk=t.get_pk(),
                patient_server_pk=t.get_patient_server_pk()
            )
        tree = XmlElement(name=xml_name, value=branches)
        return get_xml_document(
            tree,
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    # -------------------------------------------------------------------------
    # HTML view
    # -------------------------------------------------------------------------

    def _get_html(self, req: CamcopsRequest, main_html: str) -> str:
        """Get HTML representing tracker."""
        cfg = req.config
        set_matplotlib_fontsize(cfg.PLOT_FONTSIZE)
        req.switch_output_to_svg()
        return (
            self.get_html_start(req) +
            main_html +
            self.get_office_html(req) +
            """<div class="navigation">""" +
            self.get_hyperlink_pdf(req, "View PDF for printing/saving") +
            "</div>" +
            PDFEND
        )

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf(self, req: CamcopsRequest) -> bytes:
        """Get PDF representing tracker."""
        cfg = req.config
        set_matplotlib_fontsize(cfg.PLOT_FONTSIZE)
        if CSS_PAGED_MEDIA:
            req.switch_output_to_png()
            return pdf_from_html(req, self.get_pdf_html(req))
        else:
            req.switch_output_to_svg()  # wkhtmltopdf can cope
            return pdf_from_html(
                req,
                html=self.get_pdf_html(req),  # main content comes here
                header_html=self.get_pdf_header_content(),
                footer_html=self.get_pdf_footer_content(req),
                extra_wkhtmltopdf_options={"orientation": "Portrait"})

    def _get_pdf_html(self, req: CamcopsRequest, main_html: str) -> str:
        """Get HTML used to generate PDF representing tracker/CTV."""
        return (
            self.get_pdf_start(req) +
            main_html +
            self.get_office_html(req) +
            PDFEND
        )

    def suggested_pdf_filename(self, req: CamcopsRequest) -> str:
        """Get suggested filename for tracker/CTV PDF."""
        cfg = req.config
        return get_export_filename(
            cfg.PATIENT_SPEC_IF_ANONYMOUS,
            cfg.PATIENT_SPEC,
            cfg.CTV_FILENAME_SPEC if self.as_ctv else cfg.TRACKER_FILENAME_SPEC,  # noqa
            VALUE.OUTPUTTYPE_PDF,
            is_anonymous=self._patient is None,
            surname=self._patient.get_surname() if self._patient else "",
            forename=self._patient.get_forename() if self._patient else "",
            dob=self._patient.get_dob() if self._patient else None,
            sex=self._patient.get_sex() if self._patient else None,
            idnum_objects=self._patient.get_idnum_objects() if self._patient else None,  # noqa
            creation_datetime=None,
            basetable=None,
            serverpk=None)

    # -------------------------------------------------------------------------
    # Headers and footers
    # -------------------------------------------------------------------------

    def get_header_html(self) -> str:
        """HTML for tracker/CTV header, including patient ID information."""
        conditions = []
        for which_idnum, idnum_value in self.idnum_criteria:
            conditions.append("{}{} = {}".format(
                FP_ID_NUM, which_idnum, idnum_value))
        cons = self.consistency_info.get_description_list()
        if self.consistency_info.are_all_consistent():
            cons_class = "tracker_all_consistent"
            joiner = ". "
        else:
            cons_class = "warning"
            joiner = "<br>"
        if self._patient is not None:
            ptinfo = self._patient.get_html_for_task_header(
                label_id_numbers=True)
        else:
            ptinfo = WARNING_NO_PATIENT_FOUND
        return """
            <div class="trackerheader">
                Patient identified by: <b>{pt_search}</b>.
                Date range for search: <b>{dt_search}</b>.
                The tracker information will <b>only be valid</b> (i.e. will
                only be from only one patient!) if all contributing tablet
                devices use these identifiers consistently. The consistency
                check is below. The patient information shown below is taken
                from the first task used.
            </div>
            <div class="{cons_class}">
                {consistency}
            </div>
            {ptinfo}
            {restricted_warning}
        """.format(
            pt_search=";".join(conditions),
            dt_search=format_daterange(self.start_datetime, self.end_datetime),
            cons_class=cons_class,
            consistency=joiner.join(cons),
            ptinfo=ptinfo,
            restricted_warning=self.restricted_warning,
        )

    def get_html_start(self, req: CamcopsRequest) -> str:
        """HTML with CSS and header."""
        return req.webstart_html + self.get_header_html()

    def get_pdf_footer_content(self, req: CamcopsRequest) -> str:
        accessed = format_datetime(req.now_arrow, DATEFORMAT.LONG_DATETIME)
        content = "{thing} accessed {accessed}.".format(
            thing="CTV" if self.as_ctv else "Tracker",
            accessed=accessed
        )
        return pdf_footer_content(content)

    def get_pdf_start(self, req: CamcopsRequest) -> str:
        """Opening HTML for PDF, including CSS."""
        cfg = req.config
        if CSS_PAGED_MEDIA:
            head = PDF_HEAD_PORTRAIT
            pdf_header_footer = (
                self.get_pdf_header_content() +
                self.get_pdf_footer_content(req)
            )
        else:
            head = PDF_HEAD_NO_PAGED_MEDIA
            pdf_header_footer = ""
        return (
            head +
            pdf_header_footer +
            cfg.PDF_LOGO_LINE +
            self.get_header_html()
        )

    def get_pdf_header_content(self) -> str:
        if self._patient is not None:
            ptinfo = self._patient.get_html_for_page_header()
        else:
            ptinfo = ""
        return pdf_header_content(ptinfo)

    def _get_office_html(self, req: CamcopsRequest, preamble: str) -> str:
        """Tedious HTML listing sources."""
        if len(self.task_tablename_list) == 0:
            request = "None"
        else:
            request = ", ".join(self.task_tablename_list)
        return """
            <div class="office">
                {preamble}
                Requested tasks: {request}.
                Sources (tablename, task server PK, patient server PK):
                    {summary}.
                Information retrieved from {url} (server version
                    {server_version}) at: {when}.
            </div>
        """.format(
            preamble=preamble,
            request=request,
            summary=self.summary,
            url=pls.SCRIPT_PUBLIC_URL_ESCAPED,
            server_version=CAMCOPS_SERVER_VERSION,
            when=format_datetime(req.now_arrow,
                                 DATEFORMAT.SHORT_DATETIME_SECONDS),
        )

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def get_all_plots_for_all_tasks_html(self, req: CamcopsRequest) -> str:
        """HTML for all plots."""
        if (self.task_tablename_list is None or
                len(self.task_tablename_list) == 0):
            return """
                <div class="warning">
                    Unable to generate tracker: no task types specified
                </div>"""
        if self._patient is None:
            return """
                <div class="warning">
                    Unable to generate tracker: no patient details
                </div>"""

        html = ""
        for c in range(len(self.list_of_task_instance_lists)):
            task_instance_list = self.list_of_task_instance_lists[c]
            if len(task_instance_list) == 0:
                continue
            html += """
                <div class="taskheader">
                    <b>{} ({})</b>
                </div>
            """.format(
                ws.webify(task_instance_list[0].longname),
                ws.webify(task_instance_list[0].shortname)
            )
            html += self.get_all_plots_for_one_task_html(req,
                                                         task_instance_list)
        return html

    def get_all_plots_for_one_task_html(self,
                                        req: CamcopsRequest,
                                        task_instance_list: List[Task]) -> str:
        """HTML for all plots for a given task type."""
        html = ""
        if len(task_instance_list) == 0:
            return html
        if not task_instance_list[0].provides_trackers:
            # ask the first of the task instances
            return html
        ntasks = len(task_instance_list)
        task_instance_list.sort(key=lambda task: task.get_creation_datetime())
        alltrackers = [task.get_trackers(req) for task in task_instance_list]
        datetimes = [
            task.get_creation_datetime() for task in task_instance_list
        ]
        ntrackers = len(alltrackers[0])
        # ... number of trackers supplied by the first task (and all tasks)
        for tracker in range(ntrackers):
            values = [
                alltrackers[tasknum][tracker].value
                for tasknum in range(ntasks)
            ]
            html += self.get_single_plot_html(
                req, datetimes, values,
                specimen_tracker=alltrackers[0][tracker]
            )
        for task in task_instance_list:
            # noinspection PyProtectedMember
            audit(
                "Tracker data accessed",
                table=task.tablename,
                server_pk=task._pk,
                patient_server_pk=task.get_patient_server_pk()
            )
        return html

    def get_single_plot_html(
            self,
            req: CamcopsRequest,
            datetimes: List[datetime.datetime],
            values: List[float],
            specimen_tracker: TrackerInfo) -> str:
        """HTML for a single figure."""
        plot_label = specimen_tracker.plot_label
        axis_label = specimen_tracker.axis_label
        axis_min = specimen_tracker.axis_min
        axis_max = specimen_tracker.axis_max
        axis_ticks = specimen_tracker.axis_ticks
        horizontal_lines = specimen_tracker.horizontal_lines
        horizontal_labels = specimen_tracker.horizontal_labels
        aspect_ratio = specimen_tracker.aspect_ratio

        figsize = (FULLWIDTH_PLOT_WIDTH,
                   (1.0/float(aspect_ratio)) * FULLWIDTH_PLOT_WIDTH)
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(1, 1, 1)
        x = [matplotlib.dates.date2num(t) for t in datetimes]
        datelabels = [dt.strftime(TRACKER_DATEFORMAT) for dt in datetimes]

        # First plot
        ax.plot(x, values, color="b", linestyle="-", marker="+",
                markeredgecolor="r", markerfacecolor="r", label=None)
        # ... NB command performed twice, see below

        # x axis
        ax.set_xlabel("Date/time")
        ax.set_xticks(x)
        ax.set_xticklabels(datelabels)
        if (self.earliest is not None and
                self.latest is not None and
                self.earliest != self.latest):
            xlim = matplotlib.dates.date2num((self.earliest, self.latest))
            margin = (2.5 / 95.0) * (xlim[1] - xlim[0])
            xlim[0] -= margin
            xlim[1] += margin
            ax.set_xlim(xlim)
        xlim = ax.get_xlim()
        fig.autofmt_xdate(rotation=90)
        # ... autofmt_xdate must be BEFORE twinx:
        # http://stackoverflow.com/questions/8332395
        if axis_ticks is not None and len(axis_ticks) > 0:
            tick_positions = [m.y for m in axis_ticks]
            tick_labels = [m.label for m in axis_ticks]
            ax.set_yticks(tick_positions)
            ax.set_yticklabels(tick_labels)

        # y axis
        ax.set_ylabel(axis_label)
        axis_min = min(axis_min, min(values)) if axis_min else min(values)
        axis_max = max(axis_max, max(values)) if axis_max else max(values)
        # ... the supplied values are stretched if the data are outside them
        # ... but min(something, None) is None, so beware
        # If we get something with no sense of scale whatsoever, then what
        # we do is arbitrary. Matplotlib does its own thing, but we could do:
        if axis_min == axis_max:
            if axis_min == 0:
                axis_min, axis_min = -1.0, 1.0
            else:
                singlevalue = axis_min
                axis_min = 0.9 * singlevalue
                axis_max = 1.1 * singlevalue
                if axis_min > axis_max:
                    axis_min, axis_max = axis_max, axis_min
        ax.set_ylim(axis_min, axis_max)

        # title
        ax.set_title(plot_label)

        # Horizontal lines
        stupid_jitter = 0.001
        if horizontal_lines is not None:
            for y in horizontal_lines:
                plt.plot(xlim, [y, y + stupid_jitter], color="0.5",
                         linestyle=":")
                # PROBLEM: horizontal lines becoming invisible
                # (whether from ax.axhline or plot)

        # Horizontal labels
        if horizontal_labels is not None:
            label_left = xlim[0] + 0.01 * (xlim[1] - xlim[0])
            for lab in horizontal_labels:
                y = lab.y
                l = lab.label
                va = lab.vertical_alignment.value
                ax.text(label_left, y, l, verticalalignment=va, alpha=0.5)
                # was "0.5" rather than 0.5, which led to a tricky-to-find
                # "TypeError: a float is required" exception after switching
                # to Python 3.

        # replot so the data are on top of the rest:
        ax.plot(x, values, color="b", linestyle="-", marker="+",
                markeredgecolor="r", markerfacecolor="r", label=None)
        # ... NB command performed twice, see above

        plt.tight_layout()
        # ... stop the labels dropping off
        # (only works properly for LEFT labels...)

        # http://matplotlib.org/faq/howto_faq.html
        # ... tried it - didn't work (internal numbers change fine,
        # check the logger, but visually doesn't help)
        # - http://stackoverflow.com/questions/9126838
        # - http://matplotlib.org/examples/pylab_examples/finance_work2.html
        return get_html_from_pyplot_figure(req, fig) + "<br>"
        # ... extra line break for the PDF rendering

    # -------------------------------------------------------------------------
    # URLs
    # -------------------------------------------------------------------------

    def get_hyperlink_pdf(self, req: CamcopsRequest, text: str) -> str:
        """URL to a PDF version of the tracker/CTV."""
        raise NotImplementedError()


# =============================================================================
# Tracker class
# =============================================================================

class Tracker(TrackerCtvCommon):
    """Class representing numerical tracker."""

    def __init__(self,
                 session: CamcopsSession,
                 task_tablename_list: List[str],
                 which_idnum: int,
                 idnum_value: int,
                 start_datetime: Optional[datetime.datetime],
                 end_datetime: Optional[datetime.date]) -> None:
        self.task_tablename_list = [t.lower() for t in task_tablename_list
                                    if t]
        task_class_list = [
            cls for cls in Task.all_subclasses_by_shortname()
            if cls.provides_trackers and cls.tablename in task_tablename_list
        ]
        super().__init__(
            session=session,
            task_class_list=task_class_list,
            which_idnum=which_idnum,
            idnum_value=idnum_value,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            as_ctv=False
        )

    def get_xml(self,
                req: CamcopsRequest,
                indent_spaces: int = 4,
                eol: str = '\n',
                include_comments: bool = False) -> str:
        """Get XML document representing tracker."""
        return self._get_xml(
            audit_string="Tracker XML accessed",
            xml_name="tracker",
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    def get_html(self, req: CamcopsRequest) -> str:
        """Get HTML representing tracker."""
        return self._get_html(req, self.get_all_plots_for_all_tasks_html(req))

    def get_pdf_html(self, req: CamcopsRequest) -> str:
        """Get HTML used to generate PDF representing tracker."""
        return self._get_pdf_html(req,
                                  self.get_all_plots_for_all_tasks_html(req))

    def get_office_html(self, req: CamcopsRequest) -> str:
        """Tedious HTML listing sources."""
        return self._get_office_html(
            req,
            "Trackers use only information from tasks that are flagged "
            "CURRENT and COMPLETE.")

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def get_all_plots_for_all_tasks_html(self, req: CamcopsRequest) -> str:
        """HTML for all plots."""
        if (self.task_tablename_list is None or
                len(self.task_tablename_list) == 0):
            return """
                <div class="warning">
                    Unable to generate tracker: no task types specified
                </div>"""
        if self._patient is None:
            return """
                <div class="warning">
                    Unable to generate tracker: no patient details
                </div>"""

        html = ""
        for c in range(len(self.list_of_task_instance_lists)):
            task_instance_list = self.list_of_task_instance_lists[c]
            if len(task_instance_list) == 0:
                continue
            html += """
                <div class="taskheader">
                    <b>{} ({})</b>
                </div>
            """.format(
                ws.webify(task_instance_list[0].longname),
                ws.webify(task_instance_list[0].shortname)
            )
            html += self.get_all_plots_for_one_task_html(req,
                                                         task_instance_list)
        return html

    def get_all_plots_for_one_task_html(self,
                                        req: CamcopsRequest,
                                        task_instance_list: List[Task]) -> str:
        """HTML for all plots for a given task type."""
        html = ""
        if len(task_instance_list) == 0:
            return html
        if not task_instance_list[0].provides_trackers:
            # ask the first of the task instances
            return html
        ntasks = len(task_instance_list)
        task_instance_list.sort(key=lambda task: task.get_creation_datetime())
        alltrackers = [task.get_trackers(req) for task in task_instance_list]
        datetimes = [
            task.get_creation_datetime() for task in task_instance_list
        ]
        ntrackers = len(alltrackers[0])
        # ... number of trackers supplied by the first task (and all tasks)
        for tracker in range(ntrackers):
            values = [
                alltrackers[tasknum][tracker].value
                for tasknum in range(ntasks)
            ]
            html += self.get_single_plot_html(
                req, datetimes, values,
                specimen_tracker=alltrackers[0][tracker]
            )
        for task in task_instance_list:
            # noinspection PyProtectedMember
            audit(
                "Tracker data accessed",
                table=task.tablename,
                server_pk=task._pk,
                patient_server_pk=task.get_patient_server_pk()
            )
        return html

    def get_single_plot_html(
            self,
            req: CamcopsRequest,
            datetimes: List[datetime.datetime],
            values: List[float],
            specimen_tracker: TrackerInfo) -> str:
        """HTML for a single figure."""
        plot_label = specimen_tracker.plot_label
        axis_label = specimen_tracker.axis_label
        axis_min = specimen_tracker.axis_min
        axis_max = specimen_tracker.axis_max
        axis_ticks = specimen_tracker.axis_ticks
        horizontal_lines = specimen_tracker.horizontal_lines
        horizontal_labels = specimen_tracker.horizontal_labels
        aspect_ratio = specimen_tracker.aspect_ratio

        figsize = (FULLWIDTH_PLOT_WIDTH,
                   (1.0/float(aspect_ratio)) * FULLWIDTH_PLOT_WIDTH)
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(1, 1, 1)
        x = [matplotlib.dates.date2num(t) for t in datetimes]
        datelabels = [dt.strftime(TRACKER_DATEFORMAT) for dt in datetimes]

        # First plot
        ax.plot(x, values, color="b", linestyle="-", marker="+",
                markeredgecolor="r", markerfacecolor="r", label=None)
        # ... NB command performed twice, see below

        # x axis
        ax.set_xlabel("Date/time")
        ax.set_xticks(x)
        ax.set_xticklabels(datelabels)
        if (self.earliest is not None and
                self.latest is not None and
                self.earliest != self.latest):
            xlim = matplotlib.dates.date2num((self.earliest, self.latest))
            margin = (2.5 / 95.0) * (xlim[1] - xlim[0])
            xlim[0] -= margin
            xlim[1] += margin
            ax.set_xlim(xlim)
        xlim = ax.get_xlim()
        fig.autofmt_xdate(rotation=90)
        # ... autofmt_xdate must be BEFORE twinx:
        # http://stackoverflow.com/questions/8332395
        if axis_ticks is not None and len(axis_ticks) > 0:
            tick_positions = [m.y for m in axis_ticks]
            tick_labels = [m.label for m in axis_ticks]
            ax.set_yticks(tick_positions)
            ax.set_yticklabels(tick_labels)

        # y axis
        ax.set_ylabel(axis_label)
        axis_min = min(axis_min, min(values)) if axis_min else min(values)
        axis_max = max(axis_max, max(values)) if axis_max else max(values)
        # ... the supplied values are stretched if the data are outside them
        # ... but min(something, None) is None, so beware
        # If we get something with no sense of scale whatsoever, then what
        # we do is arbitrary. Matplotlib does its own thing, but we could do:
        if axis_min == axis_max:
            if axis_min == 0:
                axis_min, axis_min = -1.0, 1.0
            else:
                singlevalue = axis_min
                axis_min = 0.9 * singlevalue
                axis_max = 1.1 * singlevalue
                if axis_min > axis_max:
                    axis_min, axis_max = axis_max, axis_min
        ax.set_ylim(axis_min, axis_max)

        # title
        ax.set_title(plot_label)

        # Horizontal lines
        stupid_jitter = 0.001
        if horizontal_lines is not None:
            for y in horizontal_lines:
                plt.plot(xlim, [y, y + stupid_jitter], color="0.5",
                         linestyle=":")
                # PROBLEM: horizontal lines becoming invisible
                # (whether from ax.axhline or plot)

        # Horizontal labels
        if horizontal_labels is not None:
            label_left = xlim[0] + 0.01 * (xlim[1] - xlim[0])
            for lab in horizontal_labels:
                y = lab.y
                l = lab.label
                va = lab.vertical_alignment.value
                ax.text(label_left, y, l, verticalalignment=va, alpha=0.5)
                # was "0.5" rather than 0.5, which led to a tricky-to-find
                # "TypeError: a float is required" exception after switching
                # to Python 3.

        # replot so the data are on top of the rest:
        ax.plot(x, values, color="b", linestyle="-", marker="+",
                markeredgecolor="r", markerfacecolor="r", label=None)
        # ... NB command performed twice, see above

        plt.tight_layout()
        # ... stop the labels dropping off
        # (only works properly for LEFT labels...)

        # http://matplotlib.org/faq/howto_faq.html
        # ... tried it - didn't work (internal numbers change fine,
        # check the logger, but visually doesn't help)
        # - http://stackoverflow.com/questions/9126838
        # - http://matplotlib.org/examples/pylab_examples/finance_work2.html
        return get_html_from_pyplot_figure(req, fig) + "<br>"
        # ... extra line break for the PDF rendering

    # -------------------------------------------------------------------------
    # URLs
    # -------------------------------------------------------------------------

    def get_hyperlink_pdf(self, req: CamcopsRequest, text: str) -> str:
        """URL to a PDF version of the tracker."""
        url = get_generic_action_url(req, ACTION.TRACKER)
        for tt in self.task_tablename_list:
            url += get_url_field_value_pair(PARAM.TASKTYPES, tt)
        url += get_url_field_value_pair(
            PARAM.WHICH_IDNUM,
            "" if self.which_idnum is None else self.which_idnum)
        url += get_url_field_value_pair(
            PARAM.IDNUM_VALUE,
            "" if self.idnum_value is None else self.idnum_value)
        url += get_url_field_value_pair(
            PARAM.START_DATETIME,
            format_datetime(self.start_datetime,
                            DATEFORMAT.ISO8601_DATE_ONLY, default="")
        )
        url += get_url_field_value_pair(
            PARAM.END_DATETIME,
            format_datetime(self.end_datetime,
                            DATEFORMAT.ISO8601_DATE_ONLY, default="")
        )
        url += get_url_field_value_pair(
            PARAM.OUTPUTTYPE,
            VALUE.OUTPUTTYPE_PDF)
        return """<a href="{}" target="_blank">{}</a>""".format(url, text)


# =============================================================================
# ClinicalTextView class
# =============================================================================

class ClinicalTextView(TrackerCtvCommon):
    """Class representing a clinical text view."""

    def __init__(self,
                 session: CamcopsSession,
                 which_idnum: int,
                 idnum_value: int,
                 start_datetime: Optional[datetime.datetime],
                 end_datetime: Optional[datetime.datetime]) -> None:
        task_class_list = Task.all_subclasses()
        # We want to note all within date range, so we use all classes.
        super().__init__(
            session=session,
            task_class_list=task_class_list,
            which_idnum=which_idnum,
            idnum_value=idnum_value,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            as_ctv=True
        )

    def get_xml(self,
                req: CamcopsRequest,
                indent_spaces: int = 4,
                eol: str = '\n',
                include_comments: bool = False) -> str:
        """Get XML document representing CTV."""
        return self._get_xml(
            audit_string="Clinical text view XML accessed",
            xml_name="ctv",
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    def get_html(self, req: CamcopsRequest) -> str:
        """Get HTML representing CTV."""
        return self._get_html(
            req,
            self.get_clinicaltextview_main_html(req, as_pdf=False)
        )

    def get_pdf_html(self, req: CamcopsRequest) -> str:
        """Get HTML used to generate PDF representing CTV."""
        return self._get_pdf_html(
            req,
            self.get_clinicaltextview_main_html(req, as_pdf=True)
        )

    def get_office_html(self, req: CamcopsRequest) -> str:
        """Tedious HTML listing sources."""
        return self._get_office_html(
            req,
            "The clinical text view uses only information from tasks that are "
            "flagged CURRENT.")

    # -------------------------------------------------------------------------
    # Proper content
    # -------------------------------------------------------------------------

    def get_clinicaltextview_main_html(self, req: CamcopsRequest,
                                       as_pdf: bool = False) -> str:
        """HTML for main CTV, with start date, content, end date."""
        if self._patient is None:
            return """
                <div class="warning">
                    Unable to generate tracker: no patient details
                </div>
            """
        html = """
            <div class="ctv_datelimit_start">
                Start date for search: {}
            </div>
        """.format(
            format_datetime(self.start_datetime,
                            DATEFORMAT.ISO8601_DATE_ONLY, default="−∞")
        )
        for t in range(len(self.flattasklist)):
            html += self.get_textview_for_one_task_instance_html(
                req, self.flattasklist[t], as_pdf=as_pdf)
        html += """
            <div class="ctv_datelimit_end">
                End date for search: {}
            </div>
        """.format(
            format_datetime(self.end_datetime,
                            DATEFORMAT.ISO8601_DATE_ONLY, default="+∞")
        )
        return html

    @staticmethod
    def get_textview_for_one_task_instance_html(req: CamcopsRequest,
                                                task: Task,
                                                as_pdf: bool = False) -> str:
        """HTML for the CTV contribution of a single task."""
        datetext = format_datetime(task.get_creation_datetime(),
                                   DATEFORMAT.LONG_DATETIME_WITH_DAY)
        # HTML versions get hyperlinks.
        if as_pdf:
            links = ""
        else:
            links = "({}, {})".format(
                task.get_hyperlink_html(req, "HTML"),
                task.get_hyperlink_pdf(req, "PDF"),
            )
        # Get information from the task.
        ctvinfo_list = task.get_clinical_text(req)
        # If it provides none, we offer a line indicating just the existence of
        # the task, with no further details.
        if ctvinfo_list is None:
            return """
                <div class="ctv_taskheading">{}: {} exists {}</div>
            """.format(
                datetext,
                task.longname,
                links,
            )
        # Otherwise, we give relevant details.
        # Clinician
        clinician_html = ""
        if task.has_clinician:
            clinician_html = "<i>(Clinician: {})</i>".format(
                task.get_clinician_name()
            )
        # Header
        html = """
            <div class="ctv_taskheading">{dt}: {t} {l} {c}</div>
        """.format(
            dt=datetext,
            t=task.longname,
            l=links,
            c=clinician_html,
        )
        # Warnings
        warnings = (
            task.get_erasure_notice() +  # if applicable
            task.get_special_notes_html() +  # if applicable
            task.get_invalid_warning()  # if applicable
            # task.get_not_current_warning() not required (CTV: all current)
        )
        if warnings:
            html += """
                <div class="ctv_warnings">
                    {}
                </div>
            """.format(warnings)
        # Contents
        for ctvinfo in ctvinfo_list:
            html += ctvinfo.get_html()
        # Done.
        audit(
            "Clinical text view accessed",
            table=task.tablename,
            server_pk=task.get_pk(),
            patient_server_pk=task.get_patient_server_pk()
        )
        return html

    # -------------------------------------------------------------------------
    # URLs
    # -------------------------------------------------------------------------

    def get_hyperlink_pdf(self, req: CamcopsRequest, text: str) -> str:
        """URL to a PDF version of the CTV."""
        url = get_generic_action_url(req, ACTION.CLINICALTEXTVIEW)
        url += get_url_field_value_pair(
            PARAM.WHICH_IDNUM,
            "" if self.which_idnum is None else self.which_idnum)
        url += get_url_field_value_pair(
            PARAM.IDNUM_VALUE,
            "" if self.idnum_value is None else self.idnum_value)
        url += get_url_field_value_pair(
            PARAM.START_DATETIME,
            format_datetime(self.start_datetime,
                            DATEFORMAT.ISO8601_DATE_ONLY, default=""))
        url += get_url_field_value_pair(
            PARAM.END_DATETIME,
            format_datetime(self.end_datetime,
                            DATEFORMAT.ISO8601_DATE_ONLY, default=""))
        url += get_url_field_value_pair(
            PARAM.OUTPUTTYPE, VALUE.OUTPUTTYPE_PDF)
        return """<a href="{}" target="_blank">{}</a>""".format(url, text)


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_tracker(t: Tracker) -> None:
    """Unit tests for Tracker objects."""
    unit_test_ignore("", t.get_xml)
    unit_test_ignore("", t.get_html)
    unit_test_ignore("", t.get_pdf)
    unit_test_ignore("", t.get_pdf_html)
    unit_test_ignore("", t.suggested_pdf_filename)
    unit_test_ignore("", t.get_header_html)
    unit_test_ignore("", t.get_html_start)
    unit_test_ignore("", t.get_pdf_start)
    unit_test_ignore("", t.get_office_html)
    unit_test_ignore("", t.get_all_plots_for_all_tasks_html)
    # get_all_plots_for_one_task_html: tested implicitly
    # get_single_plot_html: tested implicitly
    unit_test_ignore("", t.get_hyperlink_pdf, "hello")


def unit_tests_ctv(c: ClinicalTextView) -> None:
    """Unit tests for ClinicalTextView objects."""
    unit_test_ignore("", c.get_xml)
    unit_test_ignore("", c.get_html)
    unit_test_ignore("", c.get_pdf)
    unit_test_ignore("", c.get_pdf_html)
    unit_test_ignore("", c.suggested_pdf_filename)
    unit_test_ignore("", c.get_header_html)
    unit_test_ignore("", c.get_html_start)
    unit_test_ignore("", c.get_pdf_start)
    unit_test_ignore("", c.get_office_html)
    unit_test_ignore("", c.get_clinicaltextview_main_html)
    # get_textview_for_one_task_instance_html: tested implicitly
    unit_test_ignore("", c.get_hyperlink_pdf, "hello")


def cctracker_unit_tests(req: CamcopsRequest) -> None:
    """Unit tests for cc_tracker module."""
    session = req.camcops_session
    tasktables = []
    for cls in Task.all_subclasses_by_tablename():
        tasktables.append(cls.tablename)
    which_idnum = 1
    idnum_value = 3

    unit_test_ignore("", consistency, [1, 1, 1, 1])
    unit_test_ignore("", consistency, [1, 1, 2, 1])
    unit_test_ignore("", consistency, [None, None, 1])
    # get_summary_of_tasks tested implicitly
    unit_test_ignore("", format_daterange, None, None)
    # ConsistencyInfo tested implicitly
    tracker = Tracker(
        session,
        tasktables,
        which_idnum,
        idnum_value,
        None,
        None
    )
    unit_tests_tracker(tracker)
    ctv = ClinicalTextView(
        session,
        which_idnum,
        idnum_value,
        None,
        None
    )
    unit_tests_ctv(ctv)
