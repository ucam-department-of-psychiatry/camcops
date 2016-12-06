#!/usr/bin/env python
# cc_report.py

"""
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
"""

import cgi
import re
from typing import (Any, Dict, Iterable, List, Optional, Sequence, Tuple,
                    Type, TypeVar, Union)

import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_web import WSGI_TUPLE_TYPE

from .cc_constants import (
    ACTION,
    DATEFORMAT,
    NUMBER_OF_IDNUMS,
    PARAM,
    VALUE,
    WEBEND,
)
from . import cc_dt
from . import cc_html
from .cc_pls import pls
from .cc_unittest import (
    unit_test_ignore,
    unit_test_require_truthy_attribute,
)
# NO: CIRCULAR # from .cc_session import Session

SESSION_FWD_REF = "Session"

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

    def get_rows_descriptions(self, **kwargs) -> REPORT_RESULT_TYPE:
        """Execute the report. Must override. Parameters are passed in via
        **kwargs."""
        return [], []


# =============================================================================
# Report framework
# =============================================================================

def offer_report_menu(session: SESSION_FWD_REF) -> str:
    """HTML page offering available reports."""
    html = pls.WEBSTART + """
        {}
        <h1>Reports</h1>
        <ul>
    """.format(
        session.get_current_user_html(),
    )
    for cls in get_all_report_classes():
        html += "<li><a href={}>{}</a></li>".format(
            cc_html.get_generic_action_url(ACTION.OFFER_REPORT) +
                cc_html.get_url_field_value_pair(PARAM.REPORT_ID,
                                                 cls.report_id),
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
                for n in range(1, NUMBER_OF_IDNUMS + 1)
            ])
        )
    else:
        # Invalid type
        return ""


def get_params_from_form(paramspeclist: List[ReportParamSpec],
                         form: cgi.FieldStorage) -> Dict:
    """Returns key/value dictionary of applicable parameters from form."""
    kwargs = {}
    for paramspec in paramspeclist:
        if paramspec.type == PARAM.WHICH_IDNUM:
            idnum = ws.get_cgi_parameter_int(form, paramspec.name)
            if idnum is None or idnum < 1 or idnum > NUMBER_OF_IDNUMS:
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
    for cls in Report.__subclasses__():
        if cls.report_id == report_id:
            return cls()
    return None


def offer_individual_report(session: SESSION_FWD_REF,
                            form: cgi.FieldStorage) -> str:
    """For a specific report (specified within the CGI form), offers an HTML
    page with the parameters to be configured for that report."""
    # Which report?
    report_id = ws.get_cgi_parameter_str(form, PARAM.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        return cc_html.fail_with_error_stay_logged_in("Invalid report_id")

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
        userdetails=session.get_current_user_html(),
        reporttitle=report.report_title,
        script=pls.SCRIPT_NAME,
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


def provide_report(session: SESSION_FWD_REF,
                   form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Extracts report type, report parameters, and output type from the CGI
    form; offers up the results in the chosen format."""

    # Which report?
    report_id = ws.get_cgi_parameter_str(form, PARAM.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        return cc_html.fail_with_error_stay_logged_in("Invalid report_id")

    # What output type?
    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    if (outputtype != VALUE.OUTPUTTYPE_HTML and
            outputtype != VALUE.OUTPUTTYPE_TSV):
        return cc_html.fail_with_error_stay_logged_in("Unknown outputtype")

    # Get parameters
    params = get_params_from_form(report.param_spec_list, form)

    # Get query details
    rows, descriptions = report.get_rows_descriptions(**params)
    if rows is None or descriptions is None:
        return cc_html.fail_with_error_stay_logged_in(
            "Report failed to return a list of descriptions/results")

    if outputtype == VALUE.OUTPUTTYPE_TSV:
        filename = (
            "CamCOPS_" +
            report.report_id +
            "_" +
            cc_dt.format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.FILENAME) +
            ".tsv"
        )
        return ws.tsv_result(tsv_from_query(rows, descriptions), [], filename)
    else:
        # HTML
        html = pls.WEBSTART + """
            {}
            <h1>{}</h1>
        """.format(
            session.get_current_user_html(),
            report.report_title,
        ) + ws.html_table_from_query(rows, descriptions) + WEBEND
        return html


# =============================================================================
# Helper functions
# =============================================================================

T = TypeVar('T')


def get_all_report_classes() -> List[Type[T]]:
    classes = Report.__subclasses__()
    classes.sort(key=lambda cls: cls.report_title)
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
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        fieldnames = [
            f.replace(
                "idnum" + str(n),
                "idnum" + str(n) + " (" + pls.get_id_desc(n) + ")"
            )
            for f in fieldnames
        ]
    return fieldnames


# =============================================================================
# Unit testing
# =============================================================================

def task_unit_test_report(name: str, r: Report) -> None:
    """Unit tests for reports."""
    unit_test_require_truthy_attribute(r, 'report_id')
    unit_test_require_truthy_attribute(r, 'report_title')
    unit_test_ignore("Testing {}.get_rows_descriptions".format(name),
                     r.get_rows_descriptions)


def unit_tests() -> None:
    """Unit tests for cc_report module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS (UNIT TESTING ONLY)
    # -------------------------------------------------------------------------
    from . import cc_session

    session = cc_session.Session()
    paramspec = {
        PARAM.TYPE: PARAM.WHICH_IDNUM,
        PARAM.NAME: "xname",
        PARAM.LABEL: "label"
    }
    form = cgi.FieldStorage()
    rows = [
        ["a1", "a2", "a3"],
        ["b1", "b2", "b3"],
    ]
    descriptions = ["one", "two", "three"]

    unit_test_ignore("", offer_report_menu, session)
    unit_test_ignore("", get_param_html, paramspec)
    unit_test_ignore("", get_params_from_form, [paramspec], form)
    unit_test_ignore("", get_all_report_ids)
    unit_test_ignore("", get_report_instance, "hello")
    unit_test_ignore("", offer_individual_report, session, form)
    unit_test_ignore("", ws.html_table_from_query, rows, descriptions)
    unit_test_ignore("", escape_for_tsv, "x")
    unit_test_ignore("", tsv_from_query, rows, descriptions)
    unit_test_ignore("", provide_report, session, form)
    unit_test_ignore("", get_param_html, paramspec)
    unit_test_ignore("", get_param_html, paramspec)

    for cls in Report.__subclasses__():
        name = cls.__name__
        report = cls()
        task_unit_test_report(name, report)
