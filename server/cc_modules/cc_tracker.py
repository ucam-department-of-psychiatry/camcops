#!/usr/bin/env python3
# cc_tracker.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import datetime
from typing import Any, List, Optional, Tuple

import cardinal_pythonlib.rnc_pdf as rnc_pdf
import cardinal_pythonlib.rnc_web as ws

from .cc_audit import audit
from .cc_constants import (
    ACTION,
    CSS_PAGED_MEDIA,
    DATEFORMAT,
    FULLWIDTH_PLOT_WIDTH,
    NUMBER_OF_IDNUMS,
    PARAM,
    PDFEND,
    PDF_HEAD_NO_PAGED_MEDIA,
    PDF_HEAD_PORTRAIT,
    RESTRICTED_WARNING_SINGULAR,
    VALUE,
    WKHTMLTOPDF_OPTIONS,
)
from . import cc_dt
from . import cc_filename
from . import cc_html
from . import cc_lang
from .cc_logger import log
from .cc_namedtuples import XmlElementTuple
from . import cc_plot
from .cc_pls import pls
from .cc_session import Session
from .cc_task import Task
from .cc_unittest import unit_test_ignore
from . import cc_version
from . import cc_xml

import matplotlib.pyplot as plt  # ONLY AFTER IMPORTING cc_plot

# =============================================================================
# Constants
# =============================================================================

DEFAULT_TRACKER_ASPECT_RATIO = 2.0  # width / height
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
DEBUG_CTV_TASK_INCLUSION = False  # should be False for production system


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
    # log.debug("consistency: values = {}, unique = {}".format(repr(values),
    #                                                            repr(unique)))
    if len(unique) == 2:
        if None in unique:
            return True, "consistent (all blank or {})".format(
                unique[1 - unique.index(None)]
            )
    return False, "<b>INCONSISTENT (contains values {})</b>".format(
        ", ".join(unique)
    )


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
        cc_dt.format_datetime(start, DATEFORMAT.ISO8601_DATE_ONLY,
                              default="−∞"),
        cc_dt.format_datetime(end, DATEFORMAT.ISO8601_DATE_ONLY,
                              default="+∞")
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
            [task.get_patient_dob_first10chars() for task in flattasklist])
        self.consistent_sex, self.msg_sex = consistency(
            [task.get_patient_sex() for task in flattasklist])
        self.consistent_idnums = []
        self.msg_idnums = []
        self.consistent_iddescs = []
        self.msg_iddescs = []
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            result, msg = consistency(
                [task.get_patient_idnum(n) for task in flattasklist])
            self.consistent_idnums.append(result)
            self.msg_idnums.append(msg)
            if result and (len(flattasklist) == 0 or (
                    len(flattasklist) > 0 and
                    flattasklist[0].get_patient_idnum(n) is None)):
                # Values consistent; either no values, or all values are
                # None... we don't care about description consistency
                self.consistent_iddescs.append(True)
                self.msg_iddescs.append("")
            else:
                # Description consistent?
                result, msg = consistency(
                    [task.get_patient_iddesc(n) for task in flattasklist],
                    pls.get_id_desc(n))
                self.consistent_iddescs.append(result)
                self.msg_iddescs.append(msg)
        self.all_consistent = (
            self.consistent_forename and
            self.consistent_surname and
            self.consistent_dob and
            self.consistent_sex and
            all(self.consistent_idnums) and
            all(self.consistent_iddescs)
        )

    def are_all_consistent(self) -> bool:
        """Is all the ID information consistent?"""
        return self.all_consistent

    def get_description_list(self) -> str:
        """Textual representation of ID information, indicating consistency or
        lack of it."""
        cons = [
            "Forename: {}".format(self.msg_forename),
            "Surname: {}".format(self.msg_surname),
            "DOB: {}".format(self.msg_dob),
            "Sex: {}".format(self.msg_sex),
        ]
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            i = n - 1
            if self.msg_iddescs[i]:
                cons.append("""iddesc{}: {}""".format(n, self.msg_iddescs[i]))
            if self.msg_idnums[i]:
                cons.append("""idnum{}: {}""".format(n, self.msg_idnums[i]))
        return cons

    def get_xml_root(self) -> XmlElementTuple:
        """XML tree (as root XmlElementTuple) of consistency information."""
        branches = [
            XmlElementTuple(
                name="all_consistent",
                value=self.are_all_consistent(),
                datatype="boolean"
            )
        ]
        for c in self.get_description_list():
            branches.append(XmlElementTuple(
                name="consistency_check",
                value=c,
            ))
        return XmlElementTuple(name="_consistency", value=branches)


# =============================================================================
# Tracker class
# =============================================================================

class Tracker(object):
    """Class representing numerical tracker."""

    def __init__(self,
                 session: Session,
                 task_tablename_list: List[str],
                 which_idnum: int,
                 idnum_value: int,
                 start_datetime: Optional[datetime.datetime],
                 end_datetime: Optional[datetime.date]) -> None:
        """Initialize, fetching applicable tasks."""

        # Preprocess
        for i in range(len(task_tablename_list)):
            if task_tablename_list[i] is not None:
                task_tablename_list[i] = task_tablename_list[i].lower()
        # Record input variables at this point (for URL regeneration)
        self.task_tablename_list = task_tablename_list
        self.which_idnum = which_idnum
        self.idnum_value = idnum_value
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

        # Which tasks?
        task_class_list = []
        classes = Task.__subclasses__()
        classes.sort(key=lambda cls_: cls_.shortname)
        for cls in classes:
            if (hasattr(cls, 'get_trackers') and
                    cls.tablename in task_tablename_list):
                task_class_list.append(cls)

        # What filters?
        self.idnumarray = []
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            self.idnumarray.append(idnum_value if n == which_idnum else None)

        # Date range? NB date adjustment to include the whole of the final day.
        self.end_datetime_extended = None
        if self.end_datetime is not None:
            self.end_datetime_extended = (
                self.end_datetime + datetime.timedelta(days=1)
            )
        log.debug("start_datetime: " + str(self.start_datetime))
        log.debug("end_datetime: " + str(self.end_datetime))
        log.debug("end_datetime_extended: " + str(
            self.end_datetime_extended))

        self.restricted_warning = (
            RESTRICTED_WARNING_SINGULAR
            if session.restricted_to_viewing_user() else ""
        )
        self._patient = None  # default value if we fail
        self.list_of_task_instance_lists = []
        # ... list (by task class) of lists of task instances
        self.earliest = None
        self.latest = None
        self.summary = ""

        # Build task lists
        for cls in task_class_list:
            if DEBUG_TRACKER_TASK_INCLUSION:
                self.summary += " // " + cls.tablename
            if cls.is_anonymous:
                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " (anonymous)"
                continue
            task_instances = []
            serverpks = cls.get_task_pks_for_tracker(
                self.idnumarray, self.start_datetime,
                self.end_datetime_extended)
            if len(serverpks) == 0:
                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " (no instances)"
                continue
            for s in serverpks:
                if DEBUG_TRACKER_TASK_INCLUSION:
                    self.summary += " / PK {}".format(s)
                task = cls(s)
                if task is None:
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (task is None)"
                    continue
                if not task.allowed_to_user(session):
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (denied to user)"
                    continue
                dt = task.get_creation_datetime()
                # Second check on datetimes
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
                if not task.is_complete():
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

        # Fetch patient information
        if (len(self.list_of_task_instance_lists) > 0 and
                len(self.list_of_task_instance_lists[0]) > 0):
            self._patient = (
                self.list_of_task_instance_lists[0][0].get_patient())
            # patient details from the first of our tasks

        # Summary information
        self.summary += get_summary_of_tasks(self.list_of_task_instance_lists)

        # Consistency information
        self.flattasklist = cc_lang.flatten_list(
            self.list_of_task_instance_lists)
        self.consistency_info = ConsistencyInfo(self.flattasklist)

    # -------------------------------------------------------------------------
    # XML view
    # -------------------------------------------------------------------------

    def get_xml(self,
                indent_spaces: int = 4,
                eol: str = '\n',
                include_comments: bool = False) -> str:
        """Get XML document representing tracker."""
        branches = [
            self.consistency_info.get_xml_root(),
            XmlElementTuple(
                name="_search_criteria",
                value=[
                    XmlElementTuple(
                        name="task_tablename_list",
                        value=",".join(self.task_tablename_list)
                    ),
                    XmlElementTuple(
                        name="which_idnum",
                        value=self.which_idnum,
                        datatype="integer"
                    ),
                    XmlElementTuple(
                        name="idnum_value",
                        value=self.idnum_value,
                        datatype="integer"
                    ),
                    XmlElementTuple(
                        name="start_datetime",
                        value=cc_dt.format_datetime(self.start_datetime,
                                                    DATEFORMAT.ISO8601),
                        datatype="dateTime"
                    ),
                    XmlElementTuple(
                        name="end_datetime",
                        value=cc_dt.format_datetime(self.end_datetime,
                                                    DATEFORMAT.ISO8601),
                        datatype="dateTime"
                    ),
                ]
            )
        ]
        for t in self.flattasklist:
            branches.append(t.get_xml_root(include_calculated=True,
                                           include_blobs=False))
            audit(
                "Tracker XML accessed",
                table=t.tablename,
                server_pk=t.get_pk(),
                patient_server_pk=t.get_patient_server_pk()
            )
        tree = XmlElementTuple(name="tracker", value=branches)
        return cc_xml.get_xml_document(
            tree,
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    # -------------------------------------------------------------------------
    # HTML view
    # -------------------------------------------------------------------------

    def get_html(self) -> str:
        """Get HTML representing tracker."""
        cc_plot.set_matplotlib_fontsize(pls.PLOT_FONTSIZE)
        pls.switch_output_to_svg()
        return (
            self.get_html_start() +
            self.get_all_plots_for_all_tasks_html() +
            self.get_office_html() +
            """<div class="navigation">""" +
            self.get_hyperlink_pdf("View PDF for printing/saving") +
            "</div>" +
            PDFEND
        )

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf(self) -> bytes:
        """Get PDF representing tracker."""
        cc_plot.set_matplotlib_fontsize(pls.PLOT_FONTSIZE)
        if CSS_PAGED_MEDIA:
            pls.switch_output_to_png()
            return rnc_pdf.pdf_from_html(self.get_pdf_html())
        else:
            pls.switch_output_to_svg()  # wkhtmltopdf can cope
            html = self.get_pdf_html()
            header = self.get_pdf_header_content()
            footer = self.get_pdf_footer_content()
            options = WKHTMLTOPDF_OPTIONS
            options.update({
                "orientation": "Portrait",
            })
            return rnc_pdf.pdf_from_html(html,
                                         header_html=header,
                                         footer_html=footer,
                                         wkhtmltopdf_options=options)

    def get_pdf_html(self) -> str:
        """Get HTML used to generate PDF representing tracker."""
        return (
            self.get_pdf_start() +
            self.get_all_plots_for_all_tasks_html() +
            self.get_office_html() +
            PDFEND
        )

    def suggested_pdf_filename(self) -> str:
        """Get suggested filename for tracker PDF."""
        return cc_filename.get_export_filename(
            pls.PATIENT_SPEC_IF_ANONYMOUS,
            pls.PATIENT_SPEC,
            pls.TRACKER_FILENAME_SPEC,
            VALUE.OUTPUTTYPE_PDF,
            is_anonymous=self._patient is None,
            surname=self._patient.get_surname() if self._patient else "",
            forename=self._patient.get_forename() if self._patient else "",
            dob=self._patient.get_dob() if self._patient else None,
            sex=self._patient.get_sex() if self._patient else None,
            idnums=self._patient.get_idnum_array() if self._patient else None,
            idshortdescs=(
                self._patient.get_idshortdesc_array()
                if self._patient else None
            ),
            creation_datetime=None,
            basetable=None,
            serverpk=None)

    # -------------------------------------------------------------------------
    # Headers and footers
    # -------------------------------------------------------------------------

    def get_tracker_header_html(self) -> str:
        """HTML for tracker header, including patient ID information."""
        conditions = []
        for i in range(len(self.idnumarray)):
            n = i + 1
            nstr = str(n)
            if self.idnumarray[i] is not None:
                conditions.append(
                    "idnum" + nstr + " = {}".format(self.idnumarray[i]))
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

    def get_html_start(self) -> str:
        """HTML with CSS and header."""
        return pls.WEBSTART + self.get_tracker_header_html()

    def get_pdf_header_content(self) -> str:
        if self._patient is not None:
            ptinfo = self._patient.get_html_for_page_header()
        else:
            ptinfo = ""
        return cc_html.pdf_header_content(ptinfo)

    @staticmethod
    def get_pdf_footer_content() -> str:
        accessed = cc_dt.format_datetime(pls.NOW_LOCAL_TZ,
                                         DATEFORMAT.LONG_DATETIME)
        content = "Tracker accessed {}.".format(accessed)
        return cc_html.pdf_footer_content(content)

    def get_pdf_start(self) -> str:
        """Opening HTML for PDF, including CSS."""
        if CSS_PAGED_MEDIA:
            head = PDF_HEAD_PORTRAIT
            pdf_header_footer = (
                self.get_pdf_header_content() + self.get_pdf_footer_content()
            )
        else:
            head = PDF_HEAD_NO_PAGED_MEDIA
            pdf_header_footer = ""
        return (
            head +
            pdf_header_footer +
            pls.PDF_LOGO_LINE +
            self.get_tracker_header_html()
        )

    def get_office_html(self) -> str:
        """Tedious HTML listing sources."""
        if len(self.task_tablename_list) == 0:
            request = "None"
        else:
            request = ", ".join(self.task_tablename_list)
        return """
            <div class="office">
                Trackers use only information from tasks that are flagged
                CURRENT and COMPLETE.
                Requested tasks: {request}.
                Sources (tablename, task server PK, patient server PK):
                    {summary}.
                Information retrieved from {url} (server version
                    {server_version}) at: {when}.
            </div>
        """.format(
            request=request,
            summary=self.summary,
            url=pls.SCRIPT_PUBLIC_URL_ESCAPED,
            server_version=cc_version.CAMCOPS_SERVER_VERSION,
            when=cc_dt.format_datetime(pls.NOW_LOCAL_TZ,
                                       DATEFORMAT.SHORT_DATETIME_SECONDS),
        )

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def get_all_plots_for_all_tasks_html(self) -> str:
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
            html += self.get_all_plots_for_one_task_html(task_instance_list)
        return html

    def get_all_plots_for_one_task_html(self,
                                        task_instance_list: List[Task]) -> str:
        """HTML for all plots for a given task type."""
        html = ""
        if len(task_instance_list) == 0:
            return html
        if not hasattr(task_instance_list[0], 'get_trackers'):
            # ask the first of the task instances
            return html
        ntasks = len(task_instance_list)
        task_instance_list.sort(key=lambda task: task.get_creation_datetime())
        alltrackers = [task.get_trackers() for task in task_instance_list]
        datetimes = [
            task.get_creation_datetime() for task in task_instance_list
        ]
        ntrackers = len(alltrackers[0])
        # ... number of trackers supplied by the first task (and all tasks)
        for tracker in range(ntrackers):
            values = [
                alltrackers[tasknum][tracker]["value"]
                for tasknum in range(ntasks)
            ]
            specimen_tracker = alltrackers[0][tracker]
            plot_label = specimen_tracker.get("plot_label", None)
            axis_label = specimen_tracker.get("axis_label", None)
            axis_min = specimen_tracker.get("axis_min", None)
            axis_max = specimen_tracker.get("axis_max", None)
            axis_ticks = specimen_tracker.get("axis_ticks", None)
            horizontal_lines = specimen_tracker.get("horizontal_lines", None)
            horizontal_labels = specimen_tracker.get("horizontal_labels", None)
            aspect_ratio = specimen_tracker.get("aspect_ratio",
                                                DEFAULT_TRACKER_ASPECT_RATIO)
            html += self.get_single_plot_html(
                datetimes,
                values,
                plot_label,
                axis_label,
                axis_min,
                axis_max,
                axis_ticks,
                horizontal_lines,
                horizontal_labels,
                aspect_ratio
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
            datetimes: List[datetime.datetime],
            values: List[float],
            plot_label: str = None,
            axis_label: str = None,
            axis_min: float = None,
            axis_max: float = None,
            axis_ticks: List[float] = None,
            horizontal_lines: List[float] = None,
            horizontal_labels: List[str] = None,
            aspect_ratio: float = DEFAULT_TRACKER_ASPECT_RATIO) -> str:
        """HTML for a single figure."""
        axis_ticks = axis_ticks or []
        horizontal_lines = horizontal_lines or []
        horizontal_labels = horizontal_labels or []
        if not aspect_ratio:  # duff input
            aspect_ratio = DEFAULT_TRACKER_ASPECT_RATIO
        figsize = (FULLWIDTH_PLOT_WIDTH,
                   (1.0/float(aspect_ratio)) * FULLWIDTH_PLOT_WIDTH)
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(1, 1, 1)
        x = [cc_plot.matplotlib.dates.date2num(t) for t in datetimes]
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
            xlim = cc_plot.matplotlib.dates.date2num((self.earliest,
                                                      self.latest))
            margin = (2.5 / 95.0) * (xlim[1] - xlim[0])
            xlim[0] -= margin
            xlim[1] += margin
            ax.set_xlim(xlim)
        xlim = ax.get_xlim()
        fig.autofmt_xdate(rotation=90)
        # ... autofmt_xdate must be BEFORE twinx:
        # http://stackoverflow.com/questions/8332395
        if axis_ticks is not None and len(axis_ticks) > 0:
            tick_positions = [m[0] for m in axis_ticks]
            tick_labels = [m[1] for m in axis_ticks]
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
                plt.plot(xlim, [y, y+stupid_jitter], color="0.5",
                         linestyle=":")
                # PROBLEM: horizontal lines becoming invisible
                # (whether from ax.axhline or plot)

        # Horizontal labels
        if horizontal_labels is not None:
            label_left = xlim[0] + 0.01 * (xlim[1] - xlim[0])
            for t in horizontal_labels:
                y = t[0]
                l = t[1]
                if len(t) > 2:
                    va = t[2]
                else:
                    va = "center"
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
        return cc_html.get_html_from_pyplot_figure(fig) + "<br>"
        # ... extra line break for the PDF rendering

    # -------------------------------------------------------------------------
    # URLs
    # -------------------------------------------------------------------------

    def get_hyperlink_pdf(self, text: str) -> str:
        """URL to a PDF version of the tracker."""
        url = cc_html.get_generic_action_url(ACTION.TRACKER)
        for tt in self.task_tablename_list:
            url += cc_html.get_url_field_value_pair(PARAM.TASKTYPES, tt)
        url += cc_html.get_url_field_value_pair(
            PARAM.WHICH_IDNUM,
            "" if self.which_idnum is None else self.which_idnum)
        url += cc_html.get_url_field_value_pair(
            PARAM.IDNUM_VALUE,
            "" if self.idnum_value is None else self.idnum_value)
        url += cc_html.get_url_field_value_pair(
            PARAM.START_DATETIME,
            cc_dt.format_datetime(self.start_datetime,
                                  DATEFORMAT.ISO8601_DATE_ONLY, default="")
        )
        url += cc_html.get_url_field_value_pair(
            PARAM.END_DATETIME,
            cc_dt.format_datetime(self.end_datetime,
                                  DATEFORMAT.ISO8601_DATE_ONLY, default="")
        )
        url += cc_html.get_url_field_value_pair(
            PARAM.OUTPUTTYPE,
            VALUE.OUTPUTTYPE_PDF)
        return """<a href="{}" target="_blank">{}</a>""".format(url, text)


# =============================================================================
# ClinicalTextView class
# =============================================================================

class ClinicalTextView(object):
    """Class representing a clinical text view."""

    def __init__(self,
                 session: Session,
                 which_idnum: int,
                 idnum_value: int,
                 start_datetime: Optional[datetime.datetime],
                 end_datetime: Optional[datetime.datetime]) -> None:
        """Initialize, fetching applicable tasks."""

        # Record input variables at this point (for URL regeneration)
        self.which_idnum = which_idnum
        self.idnum_value = idnum_value
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

        # Which tasks? We want to note all within date range, so we use all
        # classes.
        task_class_list = Task.__subclasses__()

        # What filters?
        self.idnumarray = []
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            self.idnumarray.append(idnum_value if n == which_idnum else None)

        # Date range? NB date adjustment to include the whole of the final day.
        self.end_datetime_extended = None
        if self.end_datetime is not None:
            self.end_datetime_extended = (
                self.end_datetime + datetime.timedelta(days=1)
            )
        log.debug("start_datetime: " + str(self.start_datetime))
        log.debug("end_datetime: " + str(self.end_datetime))
        log.debug("end_datetime_extended: " + str(self.end_datetime_extended))

        if session.restricted_to_viewing_user():
            self.restricted_warning = RESTRICTED_WARNING_SINGULAR
        else:
            self.restricted_warning = ""
        self._patient = None  # default value if we fail
        self.summary = ""

        # Build task lists
        list_of_task_instance_lists = []
        # ... list (by task class) of lists of task instances
        for cls in task_class_list:
            if DEBUG_CTV_TASK_INCLUSION:
                self.summary += " // " + cls.tablename
            if cls.is_anonymous:
                if DEBUG_CTV_TASK_INCLUSION:
                    self.summary += " (anonymous)"
                continue
            task_instances = []
            serverpks = cls.get_task_pks_for_clinical_text_view(
                self.idnumarray, self.start_datetime,
                self.end_datetime_extended)
            if len(serverpks) == 0:
                if DEBUG_CTV_TASK_INCLUSION:
                    self.summary += " (no instances)"
                continue
            for s in serverpks:
                if DEBUG_CTV_TASK_INCLUSION:
                    self.summary += "/ PK {} ".format(s)
                task = cls(s)
                if task is None:
                    if DEBUG_CTV_TASK_INCLUSION:
                        self.summary += " (task is None)"
                    continue
                if not task.allowed_to_user(session):
                    if DEBUG_CTV_TASK_INCLUSION:
                        self.summary += " (denied to user)"
                    continue
                dt = task.get_creation_datetime()
                # Second check on datetimes
                if (self.start_datetime is not None and
                        dt < self.start_datetime):
                    if DEBUG_CTV_TASK_INCLUSION:
                        self.summary += " (start date wrong)"
                    continue
                if (self.end_datetime_extended is not None and
                        dt > self.end_datetime_extended):
                    if DEBUG_CTV_TASK_INCLUSION:
                        self.summary += " (end date wrong)"
                    continue
                # We include incomplete tasks
                if DEBUG_CTV_TASK_INCLUSION:
                    self.summary += " (FOUND ONE)"
                task_instances.append(task)
            if len(task_instances) > 0:
                list_of_task_instance_lists.append(task_instances)

        # Move to a flat list and sort by creation date/time:
        self.flattasklist = cc_lang.flatten_list(list_of_task_instance_lists)
        self.flattasklist.sort(key=lambda task_: task_.get_creation_datetime())

        # Fetch patient information
        if len(self.flattasklist) > 0:
            # noinspection PyProtectedMember
            self._patient = self.flattasklist[0]._patient
            # patient details from the first of our tasks

        # Summary information
        self.summary += get_summary_of_tasks(list_of_task_instance_lists)

        # Consistency information
        self.consistency_info = ConsistencyInfo(self.flattasklist)

    # -------------------------------------------------------------------------
    # XML view
    # -------------------------------------------------------------------------

    def get_xml(self,
                indent_spaces: int = 4,
                eol: str = '\n',
                include_comments: bool = False) -> str:
        """Get XML document representing CTV."""
        branches = [
            self.consistency_info.get_xml_root(),
            XmlElementTuple(
                name="_search_criteria",
                value=[
                    XmlElementTuple(
                        name="which_idnum",
                        value=self.which_idnum,
                        datatype="integer"
                    ),
                    XmlElementTuple(
                        name="idnum_value",
                        value=self.idnum_value,
                        datatype="integer"
                    ),
                    XmlElementTuple(
                        name="start_datetime",
                        value=cc_dt.format_datetime(self.start_datetime,
                                                    DATEFORMAT.ISO8601),
                        datatype="dateTime"
                    ),
                    XmlElementTuple(
                        name="end_datetime",
                        value=cc_dt.format_datetime(self.end_datetime,
                                                    DATEFORMAT.ISO8601),
                        datatype="dateTime"
                    ),
                ]
            )
        ]
        for t in self.flattasklist:
            branches.append(t.get_xml_root(include_calculated=True,
                                           include_blobs=False))
            audit(
                "Clinical text view XML accessed",
                table=t.tablename,
                server_pk=t.get_pk(),
                patient_server_pk=t.get_patient_server_pk()
            )
        tree = XmlElementTuple(name="tracker", value=branches)
        return cc_xml.get_xml_document(
            tree,
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    # -------------------------------------------------------------------------
    # HTML view
    # -------------------------------------------------------------------------

    def get_html(self) -> str:
        """Get HTML representing CTV."""
        return (
            self.get_html_start() +
            self.get_clinicaltextview_main_html(as_pdf=False) +
            self.get_office_html() +
            """<div class="navigation">""" +
            self.get_hyperlink_pdf("View PDF for printing/saving") +
            "</div>" +
            PDFEND
        )

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf(self) -> bytes:
        """Get PDF representing CTV."""
        return rnc_pdf.pdf_from_html(self.get_pdf_html())

    def get_pdf_html(self) -> str:
        """Get HTML used to generate PDF representing CTV."""
        return (
            self.get_pdf_start() +
            self.get_clinicaltextview_main_html(as_pdf=True) +
            self.get_office_html() +
            PDFEND
        )

    def suggested_pdf_filename(self) -> str:
        """Get suggested filename for CTV PDF."""
        return cc_filename.get_export_filename(
            pls.PATIENT_SPEC_IF_ANONYMOUS,
            pls.PATIENT_SPEC,
            pls.CTV_FILENAME_SPEC,
            VALUE.OUTPUTTYPE_PDF,
            is_anonymous=self._patient is None,
            surname=self._patient.get_surname() if self._patient else "",
            forename=self._patient.get_forename() if self._patient else "",
            dob=self._patient.get_dob() if self._patient else None,
            sex=self._patient.get_sex() if self._patient else None,
            idnums=self._patient.get_idnum_array() if self._patient else None,
            idshortdescs=(
                self._patient.get_idshortdesc_array()
                if self._patient else None
            ),
            creation_datetime=None,
            basetable=None,
            serverpk=None)

    # -------------------------------------------------------------------------
    # Headers and footers
    # -------------------------------------------------------------------------

    def get_clinicaltextview_header_html(self) -> str:
        """HTML for CTV header, including patient ID information."""
        conditions = []
        for i in range(len(self.idnumarray)):
            n = i + 1
            nstr = str(n)
            if self.idnumarray[i] is not None:
                conditions.append(
                    "idnum" + nstr + " = {}".format(self.idnumarray[i])
                )

        cons = self.consistency_info.get_description_list()
        if self.consistency_info.are_all_consistent():
            cons_class = "tracker_all_consistent"
            joiner = ". "
        else:
            cons_class = "warning"
            joiner = "<br>"
        h = """
            <div class="trackerheader">
                Patient identified by: <b>{}</b>.
                Date range for search: <b>{}</b>.
                The information will <b>only be valid</b> (i.e. will only be
                from only one patient!) if all contributing tablet devices use
                these identifiers consistently. The consistency check is below.
                The patient information shown below is taken from the first
                task used.
            </div>
            <div class="{}">
                {}
        """.format(
            ";".join(conditions),
            format_daterange(self.start_datetime, self.end_datetime),
            cons_class,
            joiner.join(cons)
        )
        if self._patient is not None:
            ptinfo = self._patient.get_html_for_task_header(
                label_id_numbers=True)
        else:
            ptinfo = WARNING_NO_PATIENT_FOUND
        h += """
            </div>
            {}
            {}
        """.format(
            ptinfo,
            self.restricted_warning,
        )
        return h

    def get_html_start(self) -> str:
        """HTML with CSS and header."""
        return pls.WEBSTART + self.get_clinicaltextview_header_html()

    def get_pdf_start(self) -> str:
        """HTML for PDF, with CSS and header."""
        if self._patient is not None:
            ptinfo = self._patient.get_html_for_page_header()
        else:
            ptinfo = ""
        return PDF_HEAD_PORTRAIT + """
            <div id="headerContent">
                {}
            </div>
            <div id="footerContent">
                Page <pdf:pagenumber> of <pdf:pagecount>.
                Clinical text view accessed {}.
            </div>
            {}
        """.format(
            ptinfo,
            cc_dt.format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.LONG_DATETIME),
            pls.PDF_LOGO_LINE,
        ) + self.get_clinicaltextview_header_html()

    def get_office_html(self) -> str:
        """Tedious HTML listing sources."""
        return """
            <div class="office">
                The clinical text view uses only information from tasks that
                are flagged CURRENT.
                Sources (tablename, task server PK, patient server PK):
                    {summary}.
                Information retrieved from {url} (server version
                    {server_version}) at: {when}.
            </div>
        """.format(
            summary=self.summary,
            url=pls.SCRIPT_PUBLIC_URL_ESCAPED,
            server_version=cc_version.CAMCOPS_SERVER_VERSION,
            when=cc_dt.format_datetime(pls.NOW_LOCAL_TZ,
                                       DATEFORMAT.SHORT_DATETIME_SECONDS),
        )

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def get_clinicaltextview_main_html(self, as_pdf: bool = False) -> str:
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
            cc_dt.format_datetime(self.start_datetime,
                                  DATEFORMAT.ISO8601_DATE_ONLY, default="−∞")
        )
        for t in range(len(self.flattasklist)):
            html += self.get_textview_for_one_task_instance_html(
                self.flattasklist[t], as_pdf=as_pdf)
        html += """
            <div class="ctv_datelimit_end">
                End date for search: {}
            </div>
        """.format(
            cc_dt.format_datetime(self.end_datetime,
                                  DATEFORMAT.ISO8601_DATE_ONLY, default="+∞")
        )
        return html

    @staticmethod
    def get_textview_for_one_task_instance_html(task: Task,
                                                as_pdf: bool = False) -> str:
        """HTML for the CTV contribution of a single task."""
        datetext = cc_dt.format_datetime(task.get_creation_datetime(),
                                         DATEFORMAT.LONG_DATETIME_WITH_DAY)
        # HTML versions get hyperlinks.
        if as_pdf:
            links = ""
        else:
            links = "({}, {})".format(
                task.get_hyperlink_html("HTML"),
                task.get_hyperlink_pdf("PDF"),
            )
        # Get information from the task.
        ctv_dict_list = task.get_clinical_text()
        # If it provides none, we offer a line indicating just the existence of
        # the task, with no further details.
        if ctv_dict_list is None:
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
            task.get_special_notes() +  # if applicable
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
        nfields = len(ctv_dict_list)
        for i in range(nfields):
            fielddict = ctv_dict_list[i]
            heading = fielddict.get("heading", None)
            subheading = fielddict.get("subheading", None)
            description = fielddict.get("description", None)
            content = fielddict.get("content", None)
            skip_if_no_content = fielddict.get("skip_if_no_content", True)
            if content or (not skip_if_no_content):
                if heading:
                    html += """
                        <div class="ctv_fieldheading">
                            {}
                        </div>
                    """.format(heading)
                if subheading:
                    html += """
                        <div class="ctv_fieldsubheading">
                            {}
                        </div>
                    """.format(subheading)
                if description:
                    html += """
                        <div class="ctv_fielddescription">
                            {}
                        </div>
                    """.format(description)
            if content:
                html += """
                    <div class="ctv_fieldcontent">
                        {}
                    </div>
                """.format(content)
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

    def get_hyperlink_pdf(self, text: str) -> str:
        """URL to a PDF version of the CTV."""
        url = cc_html.get_generic_action_url(ACTION.CLINICALTEXTVIEW)
        url += cc_html.get_url_field_value_pair(
            PARAM.WHICH_IDNUM,
            "" if self.which_idnum is None else self.which_idnum)
        url += cc_html.get_url_field_value_pair(
            PARAM.IDNUM_VALUE,
            "" if self.idnum_value is None else self.idnum_value)
        url += cc_html.get_url_field_value_pair(
            PARAM.START_DATETIME,
            cc_dt.format_datetime(self.start_datetime,
                                  DATEFORMAT.ISO8601_DATE_ONLY, default=""))
        url += cc_html.get_url_field_value_pair(
            PARAM.END_DATETIME,
            cc_dt.format_datetime(self.end_datetime,
                                  DATEFORMAT.ISO8601_DATE_ONLY, default=""))
        url += cc_html.get_url_field_value_pair(
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
    unit_test_ignore("", t.get_tracker_header_html)
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
    unit_test_ignore("", c.get_clinicaltextview_header_html)
    unit_test_ignore("", c.get_html_start)
    unit_test_ignore("", c.get_pdf_start)
    unit_test_ignore("", c.get_office_html)
    unit_test_ignore("", c.get_clinicaltextview_main_html)
    # get_textview_for_one_task_instance_html: tested implicitly
    unit_test_ignore("", c.get_hyperlink_pdf, "hello")


def unit_tests() -> None:
    """Unit tests for cc_tracker module."""
    session = Session()
    tasktables = []
    for cls in Task.__subclasses__():
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
