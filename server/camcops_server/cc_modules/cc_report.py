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
                    Type, Union)

from cardinal_pythonlib.classes import all_subclasses
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_web import WSGI_TUPLE_TYPE

from .cc_constants import (
    ACTION,
    DATEFORMAT,
    FP_ID_NUM,
    PARAM,
    VALUE,
    WEBEND,
)
from .cc_dt import format_datetime
from .cc_html import (
    fail_with_error_stay_logged_in,
    get_generic_action_url,
    get_url_field_value_pair,
)
from .cc_request import CamcopsRequest
from .cc_unittest import (
    unit_test_ignore,
    unit_test_require_truthy_attribute,
)


SESSION_FWD_REF = "CamcopsSession"


# =============================================================================
# Other constants
# =============================================================================

REPORT_RESULT_TYPE = Tuple[Sequence[Sequence[Any]], Sequence[str]]
TAB_REGEX = re.compile("\t", re.MULTILINE)
NEWLINE_REGEX = re.compile("\n", re.MULTILINE)


# =============================================================================
# ReportParamSpec
# =============================================================================

class ReportParamSpec(object):
    # noinspection PyShadowingBuiltins
    def __init__(self, type: str, name: str, label: str):
        self.type = type
        self.name = name
        self.label = label


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

    Can override attributes:

        param_spec_list
            A list of dictionaries, each of the format: {
                "type": ... internal code (e.g. which ID number? Integer? etc.)
                "name": used in URL and in **kwargs to get_rows_descriptions
                "label": cosmetic, used for offering HTML
            }
    """

    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------
    report_id = None
    report_title = None
    param_spec_list = []

    def get_rows_descriptions(self, req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        """Execute the report. Must override. Parameters are passed in via
        **kwargs."""
        return [], []

    @classmethod
    def all_subclasses(cls,
                       sort_title: bool = False) -> List[Type["Report"]]:
        classes = all_subclasses(cls)
        if sort_title:
            classes.sort(key=lambda c: c.report_title)
        return classes


# =============================================================================
# Report framework
# =============================================================================

def offer_report_menu(req: CamcopsRequest) -> str:
    """HTML page offering available reports."""
    cfg = req.config
    ccsession = req.camcops_session
    html = req.webstart_html + """
        {}
        <h1>Reports</h1>
        <ul>
    """.format(
        ccsession.get_current_user_html(),
    )
    for cls in get_all_report_classes():
        html += "<li><a href={}>{}</a></li>".format(
            get_generic_action_url(req, ACTION.OFFER_REPORT) +
            get_url_field_value_pair(PARAM.REPORT_ID, cls.report_id),
            cls.report_title
        )
    return html + "</ul>" + WEBEND


def get_param_html(paramspec: ReportParamSpec) -> str:
    """Return HTML selector from paramspec."""
    if paramspec.type == PARAM.WHICH_IDNUM:
        return """
            {}
            <select name="{}">
                {}
            </select>
        """.format(
            paramspec.label,
            paramspec.name,
            " ".join([
                """<option value="{}">{}</option>""".format(
                    str(n), pls.get_id_desc(n))
                for n in pls.get_which_idnums()
            ])
        )
    else:
        # Invalid type
        return ""


def get_params_from_form(req: CamcopsRequest,
                         paramspeclist: List[ReportParamSpec],
                         form: cgi.FieldStorage) -> Dict:
    """Returns key/value dictionary of applicable parameters from form."""
    cfg = req.config
    kwargs = {}
    for paramspec in paramspeclist:
        if paramspec.type == PARAM.WHICH_IDNUM:
            idnum = ws.get_cgi_parameter_int(form, paramspec.name)
            if idnum not in cfg.get_which_idnums():
                continue
            kwargs[paramspec.name] = idnum
        else:
            # Invalid paramtype
            continue
    return kwargs


def get_all_report_ids() -> List[str]:
    """Get all report IDs.

    Report IDs are fixed names defined in each Report subclass.
    """
    return [cls.report_id for cls in get_all_report_classes()]


def get_report_instance(report_id: str) -> Optional[Report]:
    """Creates an instance of a Report, given its ID (name), or None."""
    for cls in Report.all_subclasses():
        if cls.report_id == report_id:
            return cls()
    return None


def offer_individual_report(req: CamcopsRequest,
                            form: cgi.FieldStorage) -> str:
    """For a specific report (specified within the CGI form), offers an HTML
    page with the parameters to be configured for that report."""
    # Which report?
    ccsession = req.camcops_session
    report_id = ws.get_cgi_parameter_str(form, PARAM.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        return fail_with_error_stay_logged_in(req, "Invalid report_id")

    html = pls.WEBSTART + """
        {userdetails}
        <h1>Report: {reporttitle}</h1>
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.PROVIDE_REPORT}">
                <input type="hidden" name="{PARAM.REPORT_ID}"
                    value="{report_id}">
    """.format(
        userdetails=ccsession.get_current_user_html(),
        reporttitle=report.report_title,
        script=req.script_name,
        ACTION=ACTION,
        PARAM=PARAM,
        report_id=report_id
    )
    for p in report.param_spec_list:
        html += get_param_html(p)
    html += """
                <br>
                Report output format:<br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_HTML}" checked>
                    HTML
                </label><br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_TSV}">
                    Tab-separated values (TSV)
                </label><br>
                <br>
                <input type="submit" value="Report">
            </form>
        </div>
    """.format(
        PARAM=PARAM,
        VALUE=VALUE,
    )
    return html + WEBEND


def escape_for_tsv(value: Optional[Any]) -> str:
    """Escapes value for tab-separated value (TSV) format.

    Converts to unicode/str and escapes tabs/newlines.
    """
    if value is None:
        return ""
    s = str(value)
    # escape tabs and newlines:
    s = TAB_REGEX.sub("\\t", s)
    s = NEWLINE_REGEX.sub("\\n", s)
    return s


def tsv_from_query(rows: Iterable[Iterable[Any]],
                   descriptions: Iterable[str]) -> str:
    """Converts rows from an SQL query result to TSV format."""
    tsv = "\t".join([escape_for_tsv(x) for x in descriptions]) + "\n"
    for row in rows:
        tsv += "\t".join([escape_for_tsv(x) for x in row]) + "\n"
    return tsv


def serve_report(req: CamcopsRequest,
                 form: cgi.FieldStorage) -> Union[str, WSGI_TUPLE_TYPE]:
    """Extracts report type, report parameters, and output type from the CGI
    form; offers up the results in the chosen format."""
    ccsession = req.camcops_session

    # Which report?
    report_id = ws.get_cgi_parameter_str(form, PARAM.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        return fail_with_error_stay_logged_in(req, "Invalid report_id")

    # What output type?
    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    if (outputtype != VALUE.OUTPUTTYPE_HTML and
            outputtype != VALUE.OUTPUTTYPE_TSV):
        return fail_with_error_stay_logged_in(req, "Unknown outputtype")

    # Get parameters
    params = get_params_from_form(req=req,
                                  paramspeclist=report.param_spec_list,
                                  form=form)

    # Get query details
    rows, descriptions = report.get_rows_descriptions(**params)
    if rows is None or descriptions is None:
        return fail_with_error_stay_logged_in(
            req,
            "Report failed to return a list of descriptions/results")

    if outputtype == VALUE.OUTPUTTYPE_TSV:
        filename = (
            "CamCOPS_" +
            report.report_id +
            "_" +
            format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.FILENAME) +
            ".tsv"
        )
        return ws.tsv_result(tsv_from_query(rows, descriptions), [], filename)
    else:
        # HTML
        html = pls.WEBSTART + """
            {}
            <h1>{}</h1>
        """.format(
            ccsession.get_current_user_html(),
            report.report_title,
        ) + ws.html_table_from_query(rows, descriptions) + WEBEND
        return html


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
        if fieldname.startswith(FP_ID_NUM):
            nstr = fieldname[len(FP_ID_NUM):]
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


def ccreport_unit_tests(req: CamcopsRequest) -> None:
    """Unit tests for cc_report module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS (UNIT TESTING ONLY)
    # -------------------------------------------------------------------------
    from . import cc_session

    session = cc_session.CamcopsSession(
        ip_addr="127.0.0.1",
        last_activity_utc=datetime.datetime.now())
    paramspec = ReportParamSpec(type=PARAM.WHICH_IDNUM,
                                name="xname",
                                label="label")
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
