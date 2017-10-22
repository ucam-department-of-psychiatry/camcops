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

import logging
from typing import Any, List, Optional, Type, TYPE_CHECKING, Union

from cardinal_pythonlib.classes import all_subclasses, classproperty
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import TsvResponse
from deform.form import Form
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.renderers import render_to_response
from pyramid.response import Response
from sqlalchemy.engine.result import ResultProxy
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.selectable import SelectBase

# import as LITTLE AS POSSIBLE; this is used by lots of modules
from .cc_convert import tsv_from_query
from .cc_constants import DateFormat, DEFAULT_ROWS_PER_PAGE
from .cc_pyramid import CamcopsPage, PageUrl, ViewArg, ViewParam
from .cc_unittest import DemoDatabaseTestCase

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest
    from .cc_forms import ReportParamForm, ReportParamSchema

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Other constants
# =============================================================================

class PlainReportType(object):
    def __init__(self, rows: List[List[Any]], columns: List[str]) -> None:
        self.rows = rows
        self.columns = columns


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

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        raise NotImplementedError()

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        raise NotImplementedError()

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return True  # must explicitly override to permit others!

    def get_query(self, req: "CamcopsRequest") -> Union[None, SelectBase,
                                                        Query]:
        """
        Return the Select statement to execute the report. Must override.
        Parameters are passed in via the Request.
        """
        return None

    def get_rows_colnames(self, req: "CamcopsRequest") \
            -> Optional[PlainReportType]:
        return None

    @staticmethod
    def get_paramform_schema_class() -> Type["ReportParamSchema"]:
        from .cc_forms import ReportParamSchema  # delayed import
        return ReportParamSchema

    def get_form(self, req: "CamcopsRequest") -> Form:
        from .cc_forms import ReportParamForm  # delayed import
        schema_class = self.get_paramform_schema_class()
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
        rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                          DEFAULT_ROWS_PER_PAGE)
        page_num = req.get_int_param(ViewParam.PAGE, 1)

        if report_id != self.report_id:
            raise HTTPBadRequest("Error - request directed to wrong report!")
        viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML,
                                     lower=True)
        if viewtype not in [ViewArg.HTML, ViewArg.TSV]:
            raise HTTPBadRequest("Bad viewtype")

        # Run the report (which may take additional parameters from the
        # request)
        statement = self.get_query(req)
        if statement is not None:
            rp = req.dbsession.execute(statement)  # type: ResultProxy
            column_names = rp.keys()
            rows = rp.fetchall()
        else:
            plain_report = self.get_rows_colnames(req)
            if plain_report is None:
                raise NotImplementedError(
                    "Report did not implement either of get_select_statement()"
                    " or get_rows_colnames()")
            rows = plain_report.rows
            column_names = plain_report.columns

        # Serve the result
        if viewtype == ViewArg.HTML:
            page = CamcopsPage(collection=rows,
                               page=page_num,
                               items_per_page=rows_per_page,
                               url_maker=PageUrl(req))
            return render_to_response(
                "report.mako",
                dict(title=self.title,
                     page=page,
                     column_names=column_names),
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
            content = tsv_from_query(rows, column_names)
            return TsvResponse(body=content, filename=filename)


# =============================================================================
# Report framework
# =============================================================================

def get_all_report_classes() -> List[Type["Report"]]:
    classes = Report.all_subclasses(sort_title=True)
    return classes


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
# Unit testing
# =============================================================================

class ReportTests(DemoDatabaseTestCase):
    def test_reports(self) -> None:
        self.announce("test_reports")
        req = self.req
        for cls in get_all_report_classes():
            log.info("Testing report: {}", cls)
            from camcops_server.cc_modules.cc_forms import ReportParamSchema
            r = cls()

            self.assertIsInstance(r.report_id, str)
            self.assertIsInstance(r.title, str)
            self.assertIsInstance(r.superuser_only, bool)

            try:
                q = r.get_query(req)
                assert (q is None or
                        isinstance(q, SelectBase) or
                        isinstance(q, Query)), (
                    "get_query() method of class {cls} returned {q} which is "
                    "of type {t}".format(cls=cls, q=q, t=type(q))
                )
            except HTTPBadRequest:
                pass

            try:
                self.assertIsInstanceOrNone(r.get_rows_colnames(req),
                                            PlainReportType)
            except HTTPBadRequest:
                pass

            cls = r.get_paramform_schema_class()
            assert issubclass(cls, ReportParamSchema)

            self.assertIsInstance(r.get_form(req), Form)

            try:
                self.assertIsInstance(r.get_response(req), Response)
            except HTTPBadRequest:
                pass
