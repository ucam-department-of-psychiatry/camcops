"""
camcops_server/cc_modules/tests/cc_report_tests.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

import csv
import io
import logging
from typing import Optional, TYPE_CHECKING

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import (
    OdsResponse,
    TsvResponse,
    XlsxResponse,
)
from deform.form import Form
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.selectable import SelectBase

from camcops_server.cc_modules.cc_report import (
    get_all_report_classes,
    PlainReportType,
    Report,
)
from camcops_server.cc_modules.cc_unittest import (
    DemoDatabaseTestCase,
    DemoRequestTestCase,
)
from camcops_server.cc_modules.cc_validators import (
    validate_alphanum_underscore,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_forms import (  # noqa: F401
        ReportParamForm,
        ReportParamSchema,
    )
    from camcops_server.cc_modules.cc_request import (
        CamcopsRequest,
    )

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Unit testing
# =============================================================================


class AllReportTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """

    def test_reports(self) -> None:
        self.announce("test_reports")
        from camcops_server.cc_modules.cc_forms import (  # noqa: F811
            ReportParamSchema,
        )

        req = self.req
        for cls in get_all_report_classes(req):
            log.info("Testing report: {}", cls)

            report = cls()

            self.assertIsInstance(report.report_id, str)
            validate_alphanum_underscore(report.report_id)
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
                assert (
                    q is None
                    or isinstance(q, SelectBase)
                    or isinstance(q, Query)
                ), (
                    f"get_query() method of class {cls} returned {q} which is "
                    f"of type {type(q)}"
                )
            except HTTPBadRequest:
                pass

            try:
                self.assertIsInstanceOrNone(
                    report.get_rows_colnames(req), PlainReportType
                )
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

    def get_rows_colnames(
        self, req: "CamcopsRequest"
    ) -> Optional[PlainReportType]:
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
            "filename=CamCOPS_test_report", response.content_disposition
        )

        self.assertIn(".xlsx", response.content_disposition)

    def test_render_ods(self) -> None:
        report = TestReport()

        response = report.render_ods(self.req)
        self.assertIsInstance(response, OdsResponse)

        self.assertIn(
            "filename=CamCOPS_test_report", response.content_disposition
        )

        self.assertIn(".ods", response.content_disposition)

    def test_render_tsv(self) -> None:
        report = TestReport()

        response = report.render_tsv(self.req)
        self.assertIsInstance(response, TsvResponse)

        self.assertIn(
            "filename=CamCOPS_test_report", response.content_disposition
        )

        self.assertIn(".tsv", response.content_disposition)

        reader = csv.reader(
            io.StringIO(response.body.decode()), dialect="excel-tab"
        )

        headings = next(reader)
        row_1 = next(reader)

        self.assertEqual(headings, ["column 1", "column 2", "column 3"])
        self.assertEqual(row_1, ["one", "two", "three"])
