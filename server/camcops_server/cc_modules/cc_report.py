#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_report.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**CamCOPS reports.**

"""

import logging
from typing import (Any, Dict, List, Optional, Sequence, Type, TYPE_CHECKING,
                    Union)

from cardinal_pythonlib.classes import all_subclasses, classproperty
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import (
    OdsResponse, TsvResponse, XlsxResponse,
)
from deform.form import Form
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.renderers import render_to_response
from pyramid.response import Response
from sqlalchemy.engine.result import ResultProxy
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import and_, column, func, select
from sqlalchemy.sql.selectable import SelectBase

# import as LITTLE AS POSSIBLE; this is used by lots of modules
from camcops_server.cc_modules.cc_constants import (
    DateFormat,
    DEFAULT_ROWS_PER_PAGE,
)
from camcops_server.cc_modules.cc_pyramid import (
    CamcopsPage,
    PageUrl,
    ViewArg,
    ViewParam,
)
from camcops_server.cc_modules.cc_tsv import TsvCollection, TsvPage
from camcops_server.cc_modules.cc_unittest import (
    DemoDatabaseTestCase,
    DemoRequestTestCase,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_forms import (
        ReportParamForm,
        ReportParamSchema,
    )
    from camcops_server.cc_modules.cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Other constants
# =============================================================================

class PlainReportType(object):
    """
    Simple class to hold the results of a plain report.
    """
    def __init__(self, rows: Sequence[Sequence[Any]],
                 column_names: Sequence[str]) -> None:
        self.rows = rows
        self.column_names = column_names


# =============================================================================
# Report class
# =============================================================================

class Report(object):
    """
    Abstract base class representing a report.

    If you are writing a report, you must override these attributes:

    - ``report_id``
    - ``report_title``
    - ``get_query`` OR ``get_rows_colnames``

    See the explanations of each.
    """

    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        """
        Returns a identifying string, unique to this report, used in the HTML
        report selector.
        """
        raise NotImplementedError("implement in subclass")

    @classmethod
    def title(cls, req: "CamcopsRequest") -> str:
        """
        Descriptive title for display purposes.
        """
        raise NotImplementedError("implement in subclass")

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        """
        If ``True`` (the default), only superusers may run the report.
        You must explicitly override this property to permit others.
        """
        return True

    @classmethod
    def get_http_query_keys(cls) -> List[str]:
        """
        Returns the keys used for the HTTP GET query. They include details of:

        - which report?
        - how to view it?
        - pagination options
        - report-specific configuration details from
          :func:`get_specific_http_query_keys`.
        """
        return [
            ViewParam.REPORT_ID,
            ViewParam.VIEWTYPE,
            ViewParam.ROWS_PER_PAGE,
            ViewParam.PAGE,
        ] + cls.get_specific_http_query_keys()

    @classmethod
    def get_specific_http_query_keys(cls) -> List[str]:
        """
        Additional HTTP GET query keys used by this report. Override to add
        custom ones.
        """
        return []

    def get_query(self, req: "CamcopsRequest") \
            -> Union[None, SelectBase, Query]:
        """
        Overriding this function is one way of providing a report. (The other
        is :func:`get_rows_colnames`.)

        To override this function, return the SQLAlchemy Base :class:`Select`
        statement or the SQLAlchemy ORM :class:`Query` to execute the report.

        Parameters are passed in via the request.
        """
        return None

    def get_rows_colnames(self, req: "CamcopsRequest") \
            -> Optional[PlainReportType]:
        """
        Overriding this function is one way of providing a report. (The other
        is :func:`get_query`.)

        To override this function, return a :class:`PlainReportType` with
        column names and row content.
        """
        return None

    @staticmethod
    def get_paramform_schema_class() -> Type["ReportParamSchema"]:
        """
        Returns the class used as the Colander schema for the form that
        configures the report. By default, this is a simple form that just
        offers a choice of output format, but you can provide a more
        extensive one (an example being in
        :class:`camcops_server.tasks.diagnosis.DiagnosisFinderReportBase`.
        """
        from camcops_server.cc_modules.cc_forms import ReportParamSchema  # delayed import  # noqa
        return ReportParamSchema

    def get_form(self, req: "CamcopsRequest") -> Form:
        """
        Returns a Colander form to configure the report. The default usually
        suffices, and it will use the schema specified in
        :func:`get_paramform_schema_class`.
        """
        from camcops_server.cc_modules.cc_forms import ReportParamForm  # delayed import  # noqa
        schema_class = self.get_paramform_schema_class()
        return ReportParamForm(request=req, schema_class=schema_class)

    @staticmethod
    def get_test_querydict() -> Dict[str, Any]:
        """
        What this function returns is used as the specimen Colander
        ``appstruct`` for unit tests. The default is an empty dictionary.
        """
        return {}

    def add_report_filters(self, wheres: List[ColumnElement]) -> None:
        """
        Override this to provide global filters to queries used to create
        reports. Used by :class:`DateTimeFilteredReportMixin`.
        """

    # -------------------------------------------------------------------------
    # Common functionality: classmethods
    # -------------------------------------------------------------------------

    @classmethod
    def all_subclasses(cls) -> List[Type["Report"]]:
        """
        Get all report subclasses, except those not implementing their
        ``report_id`` property. Optionally, sort by their title.
        """
        # noinspection PyTypeChecker
        classes = all_subclasses(cls)  # type: List[Type["Report"]]
        instantiated_report_classes = []  # type: List[Type["Report"]]
        for reportcls in classes:
            if reportcls.__name__ == 'TestReport':
                continue

            try:
                _ = reportcls.report_id
                instantiated_report_classes.append(reportcls)
            except NotImplementedError:
                # This is a subclass of Report, but it's still an abstract
                # class; skip it.
                pass
        return instantiated_report_classes

    # -------------------------------------------------------------------------
    # Common functionality: default Response
    # -------------------------------------------------------------------------

    def get_response(self, req: "CamcopsRequest") -> Response:
        """
        Return the report content itself, as an HTTP :class:`Response`.
        """
        # Check the basic parameters
        report_id = req.get_str_param(ViewParam.REPORT_ID)

        if report_id != self.report_id:
            raise HTTPBadRequest("Error - request directed to wrong report!")

        # viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML,
        #                              lower=True)
        # ... NO; for a Deform radio button, the request contains parameters
        # like
        #   ('__start__', 'viewtype:rename'),
        #   ('deformField2', 'tsv'),
        #   ('__end__', 'viewtype:rename')
        # ... so we need to ask the appstruct instead.
        # This is a bit different from how we manage trackers/CTVs, where we
        # recode the appstruct to a URL.
        #
        # viewtype = appstruct.get(ViewParam.VIEWTYPE)  # type: str
        #
        # Ah, no... that fails with pagination of reports. Let's redirect
        # things to the HTTP query, as for trackers/audit!

        viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML,
                                     lower=True)
        # Run the report (which may take additional parameters from the
        # request)
        # Serve the result
        if viewtype == ViewArg.HTML:
            return self.render_html(req=req)

        if viewtype == ViewArg.ODS:
            return self.render_ods(req=req)

        if viewtype == ViewArg.TSV:
            return self.render_tsv(req=req)

        if viewtype == ViewArg.XLSX:
            return self.render_xlsx(req=req)

        raise HTTPBadRequest("Bad viewtype")

    def render_html(self, req: "CamcopsRequest"):
        rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                          DEFAULT_ROWS_PER_PAGE)
        page_num = req.get_int_param(ViewParam.PAGE, 1)

        plain_report = self._get_plain_report(req)

        page = CamcopsPage(collection=plain_report.rows,
                           page=page_num,
                           items_per_page=rows_per_page,
                           url_maker=PageUrl(req),
                           request=req)

        return self.render_single_page_html(
            req=req,
            column_names=plain_report.column_names,
            page=page
        )

    def render_tsv(self, req: "CamcopsRequest") -> TsvResponse:
        filename = self.get_filename(req, ViewArg.TSV)

        # By default there is only one page. If there are more,
        # we only output the first
        page = self.get_tsv_pages(req)[0]

        return TsvResponse(body=page.get_tsv(), filename=filename)

    def render_xlsx(self, req: "CamcopsRequest") -> XlsxResponse:
        filename = self.get_filename(req, ViewArg.XLSX)
        tsvcoll = self.get_tsv_collection(req)
        content = tsvcoll.as_xlsx()

        return XlsxResponse(body=content, filename=filename)

    def render_ods(self, req: "CamcopsRequest") -> OdsResponse:
        filename = self.get_filename(req, ViewArg.ODS)
        tsvcoll = self.get_tsv_collection(req)
        content = tsvcoll.as_ods()

        return OdsResponse(body=content, filename=filename)

    def get_tsv_collection(self, req: "CamcopsRequest") -> TsvCollection:
        tsvcoll = TsvCollection()
        tsvcoll.add_pages(self.get_tsv_pages(req))

        return tsvcoll

    def get_tsv_pages(self, req: "CamcopsRequest") -> List[TsvPage]:
        plain_report = self._get_plain_report(req)

        page = self.get_tsv_page(name=self.title(req),
                                 column_names=plain_report.column_names,
                                 rows=plain_report.rows)
        return [page]

    @staticmethod
    def get_tsv_page(name: str,
                     column_names: Sequence[str],
                     rows: Sequence[Sequence[str]]) -> TsvPage:
        keyed_rows = [dict(zip(column_names, r)) for r in rows]
        page = TsvPage(name=name, rows=keyed_rows)

        return page

    def get_filename(self, req: "CamcopsRequest", viewtype: str) -> str:
        extension_dict = {
            ViewArg.ODS: 'ods',
            ViewArg.TSV: 'tsv',
            ViewArg.XLSX: 'xlsx',
        }

        if viewtype not in extension_dict:
            raise HTTPBadRequest("Unsupported viewtype")

        extension = extension_dict.get(viewtype)

        return (
            "CamCOPS_" +
            self.report_id +
            "_" +
            format_datetime(req.now, DateFormat.FILENAME) +
            "." +
            extension
        )

    def render_single_page_html(self,
                                req: "CamcopsRequest",
                                column_names: Sequence[str],
                                page: CamcopsPage) -> Response:
        """
        Converts a paginated report into an HTML response.

        If you wish, you can override this for more report customization.
        """
        return render_to_response(
            "report.mako",
            dict(title=self.title(req),
                 page=page,
                 column_names=column_names,
                 report_id=self.report_id),
            request=req
        )

    def _get_plain_report(self, req: "CamcopsRequest") -> PlainReportType:
        statement = self.get_query(req)
        if statement is not None:
            rp = req.dbsession.execute(statement)  # type: ResultProxy
            column_names = rp.keys()
            rows = rp.fetchall()

            plain_report = PlainReportType(rows=rows,
                                           column_names=column_names)
        else:
            plain_report = self.get_rows_colnames(req)
            if plain_report is None:
                raise NotImplementedError(
                    "Report did not implement either of get_query()"
                    " or get_rows_colnames()")

        return plain_report


class PercentageSummaryReportMixin(object):
    @classproperty
    def task_class(self) -> "Task":
        raise NotImplementedError("implement in subclass")

    def get_percentage_summaries(self,
                                 req: "CamcopsRequest",
                                 column_dict: Dict[str, str],
                                 num_answers: int,
                                 cell_format: str = "{}",
                                 min_answer: int = 0) -> List[List[str]]:
        """
        Provides a summary of each question, x% of people said each response.
        """
        rows = []

        for column_name, question in column_dict.items():
            """
            e.g. SELECT COUNT(col) FROM perinatal_poem WHERE col IS NOT NULL
            """
            wheres = [
                column(column_name).isnot(None)
            ]

            self.add_report_filters(wheres)

            # noinspection PyUnresolvedReferences
            total_query = (
                select([func.count(column_name)])
                .select_from(self.task_class.__table__)
                .where(and_(*wheres))
            )

            total_responses = req.dbsession.execute(total_query).fetchone()[0]

            row = [question] + [total_responses] + [""] * num_answers

            """
            e.g.
            SELECT total_responses,col, ((100 * COUNT(col)) / total_responses)
            FROM perinatal_poem WHERE col is not NULL
            GROUP BY col
            """
            # noinspection PyUnresolvedReferences
            query = (
                select([
                    column(column_name),
                    ((100 * func.count(column_name))/total_responses)
                ])
                .select_from(self.task_class.__table__)
                .where(and_(*wheres))
                .group_by(column_name)
            )

            # row output is:
            #      0              1               2              3
            # +----------+-----------------+--------------+--------------+----
            # | question | total responses | % 1st answer | % 2nd answer | ...
            # +----------+-----------------+--------------+--------------+----
            for result in req.dbsession.execute(query):
                col = 2 + (result[0] - min_answer)
                row[col] = cell_format.format(result[1])

            rows.append(row)

        return rows


class DateTimeFilteredReportMixin(object):
    @staticmethod
    def get_paramform_schema_class() -> Type["ReportParamSchema"]:
        from camcops_server.cc_modules.cc_forms import DateTimeFilteredReportParamSchema  # delayed import  # noqa
        return DateTimeFilteredReportParamSchema

    @classmethod
    def get_specific_http_query_keys(cls) -> List[str]:
        return super().get_specific_http_query_keys() + [
            ViewParam.START_DATETIME,
            ViewParam.END_DATETIME,
        ]

    def get_response(self, req: "CamcopsRequest") -> Response:
        self.start_datetime = format_datetime(
            req.get_datetime_param(ViewParam.START_DATETIME),
            DateFormat.ERA
        )
        self.end_datetime = format_datetime(
            req.get_datetime_param(ViewParam.END_DATETIME),
            DateFormat.ERA
        )

        return super().get_response(req)

    def add_report_filters(self, wheres: List[ColumnElement]) -> None:
        super().add_report_filters(wheres)

        if self.start_datetime is not None:
            wheres.append(
                column("when_created") >= self.start_datetime
            )

        if self.end_datetime is not None:
            wheres.append(
                column("when_created") < self.end_datetime
            )


# =============================================================================
# Report framework
# =============================================================================

def get_all_report_classes(req: "CamcopsRequest") -> List[Type["Report"]]:
    """
    Returns all :class:`Report` (sub)classes, i.e. all report types.
    """
    classes = Report.all_subclasses()
    classes.sort(key=lambda c: c.title(req))
    return classes


def get_report_instance(report_id: str) -> Optional[Report]:
    """
    Creates an instance of a :class:`Report`, given its ID (name), or return
    ``None`` if the ID is invalid.
    """
    if not report_id:
        return None
    for cls in Report.all_subclasses():
        if cls.report_id == report_id:
            return cls()
    return None


# =============================================================================
# Unit testing
# =============================================================================

class AllReportTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """
    def test_reports(self) -> None:
        self.announce("test_reports")
        req = self.req
        for cls in get_all_report_classes(req):
            log.info("Testing report: {}", cls)
            from camcops_server.cc_modules.cc_forms import ReportParamSchema
            report = cls()

            self.assertIsInstance(report.report_id, str)
            self.assertIsInstance(report.title(req), str)
            self.assertIsInstance(report.superuser_only, bool)

            querydict = report.get_test_querydict()
            # We can't use req.params.update(querydict); we get
            # "NestedMultiDict objects are read-only". We can't replace
            # req.params ("can't set attribute"). Making a fresh request is
            # also a pain, as they are difficult to initialize properly.
            # However, achievable with some hacking to make "params" writable;
            # see CamcopsDummyRequest.
            # Also: we must use self.req as this has the correct database
            # session.
            req = self.req
            req.clear_get_params()  # as we're re-using old requests
            req.add_get_params(querydict)

            try:
                q = report.get_query(req)
                assert (q is None or
                        isinstance(q, SelectBase) or
                        isinstance(q, Query)), (
                    f"get_query() method of class {cls} returned {q} which is "
                    f"of type {type(q)}"
                )
            except HTTPBadRequest:
                pass

            try:
                self.assertIsInstanceOrNone(
                    report.get_rows_colnames(req), PlainReportType)
            except HTTPBadRequest:
                pass

            cls = report.get_paramform_schema_class()
            assert issubclass(cls, ReportParamSchema)

            self.assertIsInstance(report.get_form(req), Form)

            try:
                self.assertIsInstance(report.get_response(req), Response)
            except HTTPBadRequest:
                pass


class TestReport(Report):
    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "test_report"

    @classmethod
    def title(cls, req: "CamcopsRequest") -> str:
        return "Test report"

    def get_rows_colnames(self, req: "CamcopsRequest") -> Optional[
            PlainReportType]:
        rows = [
            ["one", "two", "three"],
            ["eleven", "twelve", "thirteen"],
            ["twenty-one", "twenty-two", "twenty-three"],
        ]

        column_names = ["column 1", "column 2", "column 3"]

        return PlainReportType(rows=rows, column_names=column_names)


class ReportSpreadsheetTests(DemoRequestTestCase):
    def test_render_xlsx(self) -> None:
        report = TestReport()

        response = report.render_xlsx(self.req)
        self.assertIsInstance(response, XlsxResponse)

        self.assertIn(
            "filename=CamCOPS_test_report",
            response.content_disposition
        )

        self.assertIn(
            ".xlsx", response.content_disposition
        )

    def test_render_ods(self) -> None:
        report = TestReport()

        response = report.render_ods(self.req)
        self.assertIsInstance(response, OdsResponse)

        self.assertIn(
            "filename=CamCOPS_test_report",
            response.content_disposition
        )

        self.assertIn(
            ".ods", response.content_disposition
        )

    def test_render_tsv(self) -> None:
        report = TestReport()

        response = report.render_tsv(self.req)
        self.assertIsInstance(response, TsvResponse)

        self.assertIn(
            "filename=CamCOPS_test_report",
            response.content_disposition
        )

        self.assertIn(
            ".tsv", response.content_disposition
        )

        import csv
        import io
        reader = csv.reader(io.StringIO(response.body.decode()),
                            dialect="excel-tab")

        headings = next(reader)
        row_1 = next(reader)

        self.assertEqual(headings, ["column 1", "column 2", "column 3"])
        self.assertEqual(row_1, ["one", "two", "three"])
