#!/usr/bin/env python
# camcops_server/cc_modules/cc_report.py

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

import cgi
import datetime
import re
from typing import (Any, Dict, Iterable, List, Optional, Sequence, Tuple,
                    Type, TYPE_CHECKING, Union)

from cardinal_pythonlib.classes import all_subclasses, classproperty
import cardinal_pythonlib.rnc_web as ws
from deform.form import Form
import pyramid.httpexceptions as exc
from pyramid.renderers import render_to_response
from pyramid.response import Response

# import as LITTLE AS POSSIBLE; this is used by lots of modules
from .cc_convert import tsv_from_query
from .cc_constants import DateFormat, FP_ID_NUM_DEFUNCT
from .cc_dt import format_datetime
from .cc_forms import ReportParamForm, ReportParamSchema
from .cc_pyramid import TsvResponse, ViewArg, ViewParam
from .cc_unittest import (
    unit_test_ignore,
    unit_test_require_truthy_attribute,
)

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

SESSION_FWD_REF = "CamcopsSession"


# =============================================================================
# Other constants
# =============================================================================

REPORT_RESULT_TYPE = Tuple[Sequence[Sequence[Any]], Sequence[str]]


# =============================================================================
# Report class
# =============================================================================

class Report(object):
    """
    Abstract base class representing a report.

    Must override attributes:

        report_id
            String used in HTML selector
        report_title
            String for display purposes
        get_rows_descriptions
            returns the actual data; the request data will have been pre-
            validated against the report's form

        get_schema_class
            Schema used to create a form for seeking parameters; override this
            for simple parameter collection (if you just override this, you'll
            get a ReportParamForm with this schema).
        get_form
            Schema used to create a form for seeking parameters; override this
            for full control over parameter collection.
    """

    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------

    @classproperty
    def report_id(cls) -> str:
        raise NotImplementedError()

    @classproperty
    def title(cls) -> str:
        raise NotImplementedError()

    def get_rows_descriptions(self, req: "CamcopsRequest") -> REPORT_RESULT_TYPE:
        """Execute the report. Must override. Parameters are passed in via
        **kwargs."""
        raise NotImplementedError()
        # return [], []

    @staticmethod
    def get_schema_class() -> Type[ReportParamSchema]:
        return ReportParamSchema

    def get_form(self, req: "CamcopsRequest") -> Form:
        schema_class = self.get_schema_class()
        return ReportParamForm(request=req, schema_class=schema_class)

    # -------------------------------------------------------------------------
    # Common functionality: classmethods
    # -------------------------------------------------------------------------

    @classmethod
    def all_subclasses(cls,
                       sort_title: bool = False) -> List[Type["Report"]]:
        classes = all_subclasses(cls)  # type: List[Type["Report"]]
        if sort_title:
            classes.sort(key=lambda c: c.title)
        return classes

    # -------------------------------------------------------------------------
    # Common functionality: default Response
    # -------------------------------------------------------------------------

    def get_response(self, req: "CamcopsRequest") -> Response:
        # Check the basic parameters
        report_id = req.get_str_param(ViewParam.REPORT_ID)
        if report_id != self.report_id:
            raise exc.HTTPBadRequest(
                "Error - request directed to wrong report!")
        viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML,
                                     lower=True)
        if viewtype not in [ViewArg.HTML, ViewArg.TSV]:
            raise exc.HTTPBadRequest("Bad viewtype")

        # Run the report (which may take additional parameters from the
        # request)
        rows, descriptions = self.get_rows_descriptions(req)
        if rows is None or descriptions is None:
            raise exc.HTTPBadRequest("Report failed to return a list of "
                                     "descriptions/results")

        # Serve the result
        if viewtype == ViewArg.HTML:
            return render_to_response(
                "report.mako",
                dict(title=self.title,
                     rows=rows,
                     descriptions=descriptions),
                request=req
            )
        else:  # TSV
            filename = (
                "CamCOPS_" +
                self.report_id +
                "_" +
                format_datetime(req.now, DateFormat.FILENAME) +
                ".tsv"
            )
            content = tsv_from_query(rows, descriptions)
            return TsvResponse(body=content, filename=filename)


# =============================================================================
# Report framework
# =============================================================================

def get_all_report_ids() -> List[str]:
    """Get all report IDs.

    Report IDs are fixed names defined in each Report subclass.
    """
    return [cls.report_id for cls in get_all_report_classes()]


def get_report_instance(report_id: str) -> Optional[Report]:
    """Creates an instance of a Report, given its ID (name), or None."""
    if not report_id:
        return None
    for cls in Report.all_subclasses():
        if cls.report_id == report_id:
            return cls()
    return None


# =============================================================================
# Helper functions
# =============================================================================

def get_all_report_classes() -> List[Type["Report"]]:
    classes = Report.all_subclasses(sort_title=True)
    return classes


def expand_id_descriptions(fieldnames: Iterable[str]) -> List[str]:
    """
    Not easy to get UTF-8 fields out of a query in the column headings!
    So don't do SELECT idnum8 AS 'idnum8 (Addenbrooke's number)';
    change it post hoc like this:

        SELECT idnum1 FROM ...
    ...
        fieldnames = expand_id_descriptions(fieldnames)
    """
    def replacer(fieldname: str) -> str:
        if fieldname.startswith(FP_ID_NUM_DEFUNCT):
            nstr = fieldname[len(FP_ID_NUM_DEFUNCT):]
            try:
                n = int(nstr)
                if n in pls.get_which_idnums():
                    return "{} ({})".format(fieldname, pls.get_id_desc(n))
            except (TypeError, ValueError):
                pass
        return fieldname  # unmodified

    return [replacer(f) for f in fieldnames]


# =============================================================================
# Unit testing
# =============================================================================

def task_unit_test_report(name: str, r: Report) -> None:
    """Unit tests for reports."""
    unit_test_require_truthy_attribute(r, 'report_id')
    unit_test_require_truthy_attribute(r, 'report_title')
    unit_test_ignore("Testing {}.get_rows_descriptions".format(name),
                     r.get_rows_descriptions)


def ccreport_unit_tests(req: "CamcopsRequest") -> None:
    """Unit tests for cc_report module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS (UNIT TESTING ONLY)
    # -------------------------------------------------------------------------
    from . import cc_session

    session = cc_session.CamcopsSession(
        ip_addr="127.0.0.1",
        last_activity_utc=datetime.datetime.now())
    form = cgi.FieldStorage()
    rows = [
        ["a1", "a2", "a3"],
        ["b1", "b2", "b3"],
    ]
    descriptions = ["one", "two", "three"]

    unit_test_ignore("", offer_report_menu, req)
    unit_test_ignore("", get_param_html, paramspec)
    unit_test_ignore("", get_params_from_form, req, [paramspec], form)
    unit_test_ignore("", get_all_report_ids)
    unit_test_ignore("", get_report_instance, "hello")
    unit_test_ignore("", offer_individual_report, req, form)
    unit_test_ignore("", ws.html_table_from_query, rows, descriptions)
    unit_test_ignore("", escape_for_tsv, "x")
    unit_test_ignore("", tsv_from_query, rows, descriptions)
    unit_test_ignore("", serve_report, req, form)
    unit_test_ignore("", get_param_html, paramspec)
    unit_test_ignore("", get_param_html, paramspec)

    for cls in Report.all_subclasses(sort_title=True):
        name = cls.__name__
        report = cls()
        task_unit_test_report(name, report)
