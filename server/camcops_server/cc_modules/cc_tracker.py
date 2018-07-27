#!/usr/bin/env python
# camcops_server/cc_modules/cc_tracker.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from pendulum import DateTime as Pendulum
from pyramid.renderers import render

from .cc_audit import audit
from .cc_constants import (
    CssClass,
    CSS_PAGED_MEDIA,
    DateFormat,
    FULLWIDTH_PLOT_WIDTH,
    WHOLE_PANEL,
)
from .cc_filename import get_export_filename
from .cc_plot import matplotlib
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_pdf import pdf_from_html
from .cc_pyramid import ViewArg, ViewParam
from .cc_request import CamcopsRequest
from .cc_task import Task
from .cc_taskfactory import (
    TaskCollection,
    TaskFilter,
    TaskSortMethod,
)
from .cc_trackerhelpers import TrackerInfo
from .cc_unittest import DemoDatabaseTestCase
from .cc_xml import get_xml_document, XmlDataTypes, XmlElement

import matplotlib.dates  # delayed until after the cc_plot import

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

TRACKER_DATEFORMAT = "%Y-%m-%d"
WARNING_NO_PATIENT_FOUND = """
    <div class="{CssClass.WARNING}">
    </div>
""".format(CssClass=CssClass)
WARNING_DENIED_INFORMATION = """
    <div class="{CssClass.WARNING}">
        Other tasks exist for this patient that you do not have access to view.
    </div>
""".format(CssClass=CssClass)

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


def format_daterange(start: Optional[Pendulum],
                     end: Optional[Pendulum]) -> str:
    """Textual representation of inclusive date range.

    Arguments are datetime values."""
    return "[{}, {}]".format(
        format_datetime(start, DateFormat.ISO8601_DATE_ONLY, default="−∞"),
        format_datetime(end, DateFormat.ISO8601_DATE_ONLY, default="+∞")
    )


# =============================================================================
# ConsistencyInfo class
# =============================================================================

class ConsistencyInfo(object):
    """Stores ID consistency information about a set of tasks."""

    def __init__(self, tasklist: List[Task]) -> None:
        """Initialize values, from a list of task instances."""
        self.consistent_forename, self.msg_forename = consistency(
            [task.get_patient_forename() for task in tasklist],
            servervalue=None, case_sensitive=False)
        self.consistent_surname, self.msg_surname = consistency(
            [task.get_patient_surname() for task in tasklist],
            servervalue=None, case_sensitive=False)
        self.consistent_dob, self.msg_dob = consistency(
            [task.get_patient_dob_first11chars() for task in tasklist])
        self.consistent_sex, self.msg_sex = consistency(
            [task.get_patient_sex() for task in tasklist])
        self.consistent_idnums, self.msg_idnums = consistency_idnums(
            [task.get_patient_idnum_objects() for task in tasklist])
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
                 req: CamcopsRequest,
                 taskfilter: TaskFilter,
                 as_ctv: bool) -> None:
        """Initialize, fetching applicable tasks."""

        # Record input variables at this point (for URL regeneration)
        self.req = req
        self.taskfilter = taskfilter
        self.as_ctv = as_ctv
        assert taskfilter.tasks_with_patient_only

        self.collection = TaskCollection(
            req=req,
            taskfilter=taskfilter,
            sort_method_by_class=TaskSortMethod.CREATION_DATE_ASC,
            sort_method_global=TaskSortMethod.CREATION_DATE_ASC
        )
        all_tasks = self.collection.all_tasks
        if all_tasks:
            self.earliest = all_tasks[0].when_created
            self.latest = all_tasks[-1].when_created
            self.patient = all_tasks[0].patient
        else:
            self.earliest = None  # type: Pendulum
            self.latest = None  # type: Pendulum
            self.patient = None  # type: Patient

        # Summary information
        self.summary = ""
        first = True
        if DEBUG_TRACKER_TASK_INCLUSION:
            for cls in self.taskfilter.task_classes:
                if not first:
                    self.summary += " // "
                self.summary += cls.tablename
                first = False
                task_instances = self.collection.tasks_for_task_class(cls)
                if not task_instances:
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        self.summary += " (no instances)"
                    continue
                for task in task_instances:
                    if DEBUG_TRACKER_TASK_INCLUSION:
                        # noinspection PyProtectedMember
                        self.summary += " / PK {}".format(task._pk)
            self.summary += " ~~~ "
        self.summary += " — ".join([
            "; ".join([
                "({},{},{})".format(task.tablename,
                                    task.get_pk(),
                                    task.get_patient_server_pk())
                for task in self.collection.tasks_for_task_class(cls)
            ])
            for cls in self.taskfilter.task_classes
        ])

        # Consistency information
        self.consistency_info = ConsistencyInfo(all_tasks)

    # -------------------------------------------------------------------------
    # Required for implementation
    # -------------------------------------------------------------------------

    def get_xml(self,
                indent_spaces: int = 4,
                eol: str = '\n',
                include_comments: bool = False) -> str:
        raise NotImplementedError()

    def _get_html(self) -> str:
        raise NotImplementedError()

    def _get_pdf_html(self) -> str:
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
        iddef = self.taskfilter.get_only_iddef()
        if not iddef:
            raise ValueError("Tracker/CTV doesn't have a single ID number "
                             "criterion")
        branches = [
            self.consistency_info.get_xml_root(),
            XmlElement(
                name="_search_criteria",
                value=[
                    XmlElement(
                        name="task_tablename_list",
                        value=",".join(self.taskfilter.task_tablename_list)
                    ),
                    XmlElement(
                        name=ViewParam.WHICH_IDNUM,
                        value=iddef.which_idnum,
                        datatype=XmlDataTypes.INTEGER
                    ),
                    XmlElement(
                        name=ViewParam.IDNUM_VALUE,
                        value=iddef.idnum_value,
                        datatype=XmlDataTypes.INTEGER
                    ),
                    XmlElement(
                        name=ViewParam.START_DATETIME,
                        value=format_datetime(self.taskfilter.start_datetime,
                                              DateFormat.ISO8601),
                        datatype=XmlDataTypes.DATETIME
                    ),
                    XmlElement(
                        name=ViewParam.END_DATETIME,
                        value=format_datetime(self.taskfilter.end_datetime,
                                              DateFormat.ISO8601),
                        datatype=XmlDataTypes.DATETIME
                    ),
                ]
            )
        ]
        for t in self.collection.all_tasks:
            branches.append(t.get_xml_root(self.req,
                                           include_calculated=True,
                                           include_blobs=False))
            audit(
                self.req,
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

    def get_html(self) -> str:
        """Get HTML representing tracker."""
        self.req.prepare_for_html_figures()
        return self._get_html()

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf_html(self) -> str:
        self.req.prepare_for_pdf_figures()
        return self._get_pdf_html()

    def get_pdf(self) -> bytes:
        """Get PDF representing tracker/CTV."""
        req = self.req
        html = self.get_pdf_html()  # main content
        if CSS_PAGED_MEDIA:
            return pdf_from_html(req, html)
        else:
            return pdf_from_html(
                req,
                html=html,
                header_html=render(
                    "wkhtmltopdf_header.mako",
                    dict(inner_text=render("tracker_ctv_header.mako",
                                           dict(tracker=self),
                                           request=req)),
                    request=req
                ),
                footer_html=render(
                    "wkhtmltopdf_footer.mako",
                    dict(inner_text=render("tracker_ctv_footer.mako",
                                           dict(tracker=self),
                                           request=req)),
                    request=req
                ),
                extra_wkhtmltopdf_options={
                    "orientation": "Portrait"
                }
            )

    def suggested_pdf_filename(self) -> str:
        """Get suggested filename for tracker/CTV PDF."""
        cfg = self.req.config
        return get_export_filename(
            req=self.req,
            patient_spec_if_anonymous=cfg.patient_spec_if_anonymous,
            patient_spec=cfg.patient_spec,
            filename_spec=cfg.ctv_filename_spec if self.as_ctv else cfg.tracker_filename_spec,  # noqa
            task_format=ViewArg.PDF,
            is_anonymous=self.patient is None,
            surname=self.patient.get_surname() if self.patient else "",
            forename=self.patient.get_forename() if self.patient else "",
            dob=self.patient.get_dob() if self.patient else None,
            sex=self.patient.get_sex() if self.patient else None,
            idnum_objects=self.patient.get_idnum_objects() if self.patient else None,  # noqa
            creation_datetime=None,
            basetable=None,
            serverpk=None
        )


# =============================================================================
# Tracker class
# =============================================================================

class Tracker(TrackerCtvCommon):
    """Class representing numerical tracker."""

    def __init__(self,
                 req: CamcopsRequest,
                 taskfilter: TaskFilter) -> None:
        super().__init__(
            req=req,
            taskfilter=taskfilter,
            as_ctv=False
        )

    def get_xml(self,
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

    def _get_html(self) -> str:
        """Get HTML representing tracker."""
        return render("tracker.mako",
                      dict(tracker=self,
                           viewtype=ViewArg.HTML),
                      request=self.req)

    def _get_pdf_html(self) -> str:
        """Get HTML used to generate PDF representing tracker."""
        return render("tracker.mako",
                      dict(tracker=self,
                           pdf_landscape=False,
                           viewtype=ViewArg.PDF),
                      request=self.req)

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def get_all_plots_for_one_task_html(self, tasks: List[Task]) -> str:
        """HTML for all plots for a given task type."""
        html = ""
        ntasks = len(tasks)
        if ntasks == 0:
            return html
        if not tasks[0].provides_trackers:
            # ask the first of the task instances
            return html
        alltrackers = [task.get_trackers(self.req) for task in tasks]
        datetimes = [task.get_creation_datetime() for task in tasks]
        ntrackers = len(alltrackers[0])
        # ... number of trackers supplied by the first task (and all tasks)
        for tracker in range(ntrackers):
            values = [
                alltrackers[tasknum][tracker].value
                for tasknum in range(ntasks)
            ]
            html += self.get_single_plot_html(
                datetimes, values,
                specimen_tracker=alltrackers[0][tracker]
            )
        for task in tasks:
            # noinspection PyProtectedMember
            audit(self.req,
                  "Tracker data accessed",
                  table=task.tablename,
                  server_pk=task._pk,
                  patient_server_pk=task.get_patient_server_pk())
        return html

    def get_single_plot_html(self,
                             datetimes: List[Pendulum],
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
        fig = self.req.create_figure(figsize=figsize)
        ax = fig.add_subplot(WHOLE_PANEL)
        x = [matplotlib.dates.date2num(t) for t in datetimes]
        datelabels = [dt.strftime(TRACKER_DATEFORMAT) for dt in datetimes]

        # First plot
        ax.plot(x, values, color="b", linestyle="-", marker="+",
                markeredgecolor="r", markerfacecolor="r", label=None)
        # ... NB command performed twice, see below

        # x axis
        ax.set_xlabel("Date/time", fontdict=self.req.fontdict)
        ax.set_xticks(x)
        ax.set_xticklabels(datelabels, fontdict=self.req.fontdict)
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
            ax.set_yticklabels(tick_labels, fontdict=self.req.fontdict)

        # y axis
        ax.set_ylabel(axis_label, fontdict=self.req.fontdict)
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
        ax.set_title(plot_label, fontdict=self.req.fontdict)

        # Horizontal lines
        stupid_jitter = 0.001
        if horizontal_lines is not None:
            for y in horizontal_lines:
                ax.plot(xlim, [y, y + stupid_jitter], color="0.5",
                        linestyle=":")
                # PROBLEM: horizontal lines becoming invisible
                # (whether from ax.axhline or plot)

        # Horizontal labels
        if horizontal_labels is not None:
            label_left = xlim[0] + 0.01 * (xlim[1] - xlim[0])
            for lab in horizontal_labels:
                y = lab.y
                l_ = lab.label
                va = lab.vertical_alignment.value
                ax.text(label_left, y, l_, verticalalignment=va, alpha=0.5,
                        fontdict=self.req.fontdict)
                # was "0.5" rather than 0.5, which led to a tricky-to-find
                # "TypeError: a float is required" exception after switching
                # to Python 3.

        # replot so the data are on top of the rest:
        ax.plot(x, values, color="b", linestyle="-", marker="+",
                markeredgecolor="r", markerfacecolor="r", label=None)
        # ... NB command performed twice, see above

        self.req.set_figure_font_sizes(ax)

        fig.tight_layout()
        # ... stop the labels dropping off
        # (only works properly for LEFT labels...)

        # http://matplotlib.org/faq/howto_faq.html
        # ... tried it - didn't work (internal numbers change fine,
        # check the logger, but visually doesn't help)
        # - http://stackoverflow.com/questions/9126838
        # - http://matplotlib.org/examples/pylab_examples/finance_work2.html
        return self.req.get_html_from_pyplot_figure(fig) + "<br>"
        # ... extra line break for the PDF rendering


# =============================================================================
# ClinicalTextView class
# =============================================================================

class ClinicalTextView(TrackerCtvCommon):
    """Class representing a clinical text view."""

    def __init__(self,
                 req: CamcopsRequest,
                 taskfilter: TaskFilter) -> None:
        super().__init__(
            req=req,
            taskfilter=taskfilter,
            as_ctv=True
        )

    def get_xml(self,
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

    def _get_html(self) -> str:
        """Get HTML representing CTV."""
        return render("ctv.mako",
                      dict(tracker=self,
                           viewtype=ViewArg.HTML),
                      request=self.req)

    def _get_pdf_html(self) -> str:
        """Get HTML used to generate PDF representing CTV."""
        return render("ctv.mako",
                      dict(tracker=self,
                           pdf_landscape=False,
                           viewtype=ViewArg.PDF),
                      request=self.req)


# =============================================================================
# Unit tests
# =============================================================================

class TrackerCtvTests(DemoDatabaseTestCase):
    def test_tracker(self) -> None:
        self.announce("test_tracker")
        req = self.req
        taskfilter = TaskFilter()
        t = Tracker(req, taskfilter)

        self.assertIsInstance(t.get_html(), str)
        self.assertIsInstance(t.get_pdf(), str)
        self.assertIsInstance(t.get_pdf_html(), str)
        self.assertIsInstance(t.get_xml(), str)
        self.assertIsInstance(t.suggested_pdf_filename(), str)

    def test_ctv(self) -> None:
        self.announce("test_ctv")
        req = self.req
        taskfilter = TaskFilter()
        c = ClinicalTextView(req, taskfilter)

        self.assertIsInstance(c.get_html(), str)
        self.assertIsInstance(c.get_pdf(), str)
        self.assertIsInstance(c.get_pdf_html(), str)
        self.assertIsInstance(c.get_xml(), str)
        self.assertIsInstance(c.suggested_pdf_filename(), str)
