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
from typing import (Any, Dict, Generator, List, Optional, Sequence, Type,
                    TYPE_CHECKING, Union)

from cardinal_pythonlib.classes import all_subclasses, classproperty
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import TsvResponse
from deform.form import Form
import pendulum
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.renderers import render_to_response
from pyramid.response import Response
from sqlalchemy.engine.result import ResultProxy
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.expression import func, select, and_
from sqlalchemy.sql.selectable import SelectBase

# import as LITTLE AS POSSIBLE; this is used by lots of modules
from camcops_server.cc_modules.cc_convert import tsv_from_query
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
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_forms import (
        ReportParamForm,
        ReportParamSchema,
    )
    from camcops_server.cc_modules.cc_patient import Patient
    from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
    from camcops_server.cc_modules.cc_request import CamcopsRequest
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
        rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                          DEFAULT_ROWS_PER_PAGE)
        page_num = req.get_int_param(ViewParam.PAGE, 1)

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
                    "Report did not implement either of get_query()"
                    " or get_rows_colnames()")
            column_names = plain_report.column_names
            rows = plain_report.rows

        # Serve the result
        if viewtype == ViewArg.HTML:
            page = CamcopsPage(collection=rows,
                               page=page_num,
                               items_per_page=rows_per_page,
                               url_maker=PageUrl(req),
                               request=req)
            return self.render_html(req=req,
                                    column_names=column_names,
                                    page=page)
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

    def render_html(self,
                    req: "CamcopsRequest",
                    column_names: List[str],
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


class AverageScoreReport(Report):
    """
    Used by MAAS, CORE-10 and PBQ to report average scores and progress
    """
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    @classproperty
    def higher_score_is_better(cls) -> bool:
        return True

    @classproperty
    def task_class(cls) -> "Task":
        raise NotImplementedError(
            "Report did not implement task_class"
        )

    @classproperty
    def score_fieldnames(cls) -> List[str]:
        raise NotImplementedError(
            "Report did not implement score_fieldnames"
        )

    def get_rows_colnames(self,
                          req: "CamcopsRequest") -> Optional[PlainReportType]:
        row = []

        _ = req.gettext

        """
        First record for each patient (e.g. for CORE-10):
        SELECT DISTINCT(patient_id),MIN(when_created) AS when_created
        FROM core10 GROUP BY patient_id
        """

        first_record_query = (
            select([self.task_class.patient_id,
                    func.min(self.task_class.when_created)
                    .label("when_created")])
            .select_from(self.task_class.__table__)
            .distinct(self.task_class.patient_id)
            .group_by(self.task_class.patient_id)
        )

        first_records = first_record_query.alias("first_records")

        results = req.dbsession.execute(first_record_query)
        total_first_records = len(results.fetchall())

        """
        Latest record for each patient (e.g. for CORE-10):
        SELECT DISTINCT(patient_id),MAX(when_created) AS when_created
        FROM core10 GROUP BY patient_id
        """

        latest_record_query = (
            select([self.task_class.patient_id,
                    func.max(self.task_class.when_created)
                    .label("when_created")])
            .select_from(self.task_class.__table__)
            .distinct(self.task_class.patient_id)
            .group_by(self.task_class.patient_id)
        )

        results = req.dbsession.execute(latest_record_query)
        total_latest_records = len(results.fetchall())

        latest_records = latest_record_query.alias("latest_records")

        column_names = [
            _("Total first records"),
            _("Total latest records"),
        ]

        row = [total_first_records, total_latest_records]

        for score_name, fieldnames in self.score_fieldnames.items():
            """
            Average first score (e.g. for CORE-10):
            SELECT AVG(q1+q2+q3+q4+q5+q6+q7+q8+q9+q10) AS average_score
            FROM (first_record_query) AS first_records
            INNER JOIN core10 ON core10.patient_id = first_records.patient_id
            AND core10.when_created = first_records.when_created;
            """

            total_score_expr = sum([getattr(self.task_class, f)
                                    for f in fieldnames])

            average_first_score_query = (
                select([func.avg(total_score_expr)])
                .select_from(
                    first_records
                    .join(
                        self.task_class.__table__,
                        and_(
                            self.task_class.patient_id == first_records.c.patient_id,  # noqa
                            self.task_class.when_created == first_records.c.when_created  # noqa
                        )
                    )
                )
            )

            """
            Average latest score (e.g. for CORE-10):
            SELECT AVG(q1+q2+q3+q4+q5+q6+q7+q8+q9+q10) AS average_score
            FROM (latest_record_query) AS latest_records
            INNER JOIN core10 ON core10.patient_id = latest_records.patient_id
            AND core10.when_created = latest_records.when_created;
            """
            average_latest_score_query = (
                select([func.avg(total_score_expr)])
                .select_from(
                    latest_records
                    .join(
                        self.task_class.__table__, and_(
                            self.task_class.patient_id == latest_records.c.patient_id,  # noqa
                            self.task_class.when_created == latest_records.c.when_created  # noqa
                        )
                    )
                )
            )

            results = req.dbsession.execute(average_first_score_query)
            average_first_score = next(results)[0]

            results = req.dbsession.execute(average_latest_score_query)
            average_latest_score = next(results)[0]

            if average_first_score is not None and (
                    average_latest_score is not None
            ):
                average_progress = self.calculate_progress(
                    average_first_score, average_latest_score
                )
            else:
                average_progress = _("Unable to calculate")

            if average_first_score is None:
                average_first_score = _("No data")

            if average_latest_score is None:
                average_latest_score = _("No data")

            column_names += [
                "{}: {}".format(score_name, _("Average first")),
                "{}: {}".format(score_name, _("Average latest")),
                "{}: {}".format(score_name, _("Average progress")),
            ]

            row += [average_first_score, average_latest_score,
                    average_progress]

        report = PlainReportType(
            column_names=column_names,
            rows=[row]
        )

        return report

    def calculate_progress(self,
                           first_score: float,
                           latest_score: float) -> float:
        progress = latest_score - first_score

        if not self.higher_score_is_better:
            return -1 * progress

        return progress


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

class ReportTests(DemoDatabaseTestCase):
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


class AverageScoreReportTestCase(DemoDatabaseTestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.patient_id_sequence = self.get_patient_id()
        self.task_id_sequence = self.get_task_id()
        self.patient_idnum_id_sequence = self.get_patient_idnum_id()

    def setUp(self) -> None:
        super().setUp()

        self.report = self.create_report()

    def create_tasks(self):
        pass

    def create_report(self) -> Report:
        raise NotImplementedError(
            "Report TestCase needs to implement create_report"
        )

    @staticmethod
    def get_patient_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    @staticmethod
    def get_task_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    @staticmethod
    def get_patient_idnum_id() -> Generator[int, None, None]:
        i = 1

        while True:
            yield i
            i += 1

    def create_patient(self) -> "Patient":
        from camcops_server.cc_modules.cc_patient import Patient
        patient = Patient()
        patient.id = next(self.patient_id_sequence)
        self._apply_standard_db_fields(patient)

        patient.forename = f"Forename {patient.id}"
        patient.surname = f"Surname {patient.id}"
        patient.dob = pendulum.parse("1950-01-01")
        self.dbsession.add(patient)

        self.create_patient_idnum(patient)

        self.dbsession.commit()

        return patient

    def create_patient_idnum(self, patient) -> "PatientIdNum":
        from camcops_server.cc_modules.cc_patient import PatientIdNum
        patient_idnum = PatientIdNum()
        patient_idnum.id = next(self.patient_idnum_id_sequence)
        self._apply_standard_db_fields(patient_idnum)
        patient_idnum.patient_id = patient.id
        patient_idnum.which_idnum = self.nhs_iddef.which_idnum
        patient_idnum.idnum_value = 333
        self.dbsession.add(patient_idnum)

        return patient_idnum
