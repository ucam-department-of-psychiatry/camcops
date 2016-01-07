#!/usr/bin/env python3
# cc_report.py

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

import cgi
import re

import pythonlib.rnc_web as ws

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
from .cc_unittest import unit_test_ignore

# =============================================================================
# Other constants
# =============================================================================

TAB_REGEX = re.compile("\t", re.MULTILINE)
NEWLINE_REGEX = re.compile("\n", re.MULTILINE)


# =============================================================================
# Report framework
# =============================================================================

def offer_report_menu(session):
    """HTML page offering available reports."""
    html = pls.WEBSTART + """
        {}
        <h1>Reports</h1>
        <ul>
    """.format(
        session.get_current_user_html(),
    )
    for cls in Report.__subclasses__():
        html += "<li><a href={}>{}</a></li>".format(
            cc_html.get_generic_action_url(ACTION.OFFER_REPORT)
                + cc_html.get_url_field_value_pair(PARAM.REPORT_ID,
                                                   cls.get_report_id()),
            cls.get_report_title()
        )
    return html + "</ul>" + WEBEND


def get_param_html(paramspec):
    """Return HTML selector from paramspec."""
    paramtype = paramspec[PARAM.TYPE]
    paramname = paramspec[PARAM.NAME]
    paramlabel = paramspec[PARAM.LABEL]
    if paramtype == PARAM.WHICH_IDNUM:
        return """
            {}
            <select name="{}">
                {}
            </select>
        """.format(
            paramlabel,
            paramname,
            " ".join([
                """<option value="{}">{}</option>""".format(
                    str(n), pls.get_id_desc(n))
                for n in range(1, NUMBER_OF_IDNUMS + 1)
            ])
        )
    else:
        # Invalid paramtype
        return ""


def get_params_from_form(paramspeclist, form):
    """Returns key/value dictionary of applicable parameters from form."""
    kwargs = {}
    for paramspec in paramspeclist:
        paramtype = paramspec[PARAM.TYPE]
        paramname = paramspec[PARAM.NAME]
        if paramtype == PARAM.WHICH_IDNUM:
            idnum = ws.get_cgi_parameter_int(form, paramname)
            if idnum is None or idnum < 1 or idnum > NUMBER_OF_IDNUMS:
                continue
            kwargs[paramname] = idnum
        else:
            # Invalid paramtype
            continue
    return kwargs


def get_all_report_ids():
    """Get all report IDs.

    Report IDs are fixed names defined in each Report subclass.
    """
    return [cls.get_report_id() for cls in Report.__subclasses__()]


def get_report_instance(report_id):
    """Creates an instance of a Report, given its ID (name), or None."""
    for cls in Report.__subclasses__():
        if cls.get_report_id() == report_id:
            return cls()
    return None


def offer_individual_report(session, form):
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
        reporttitle=report.get_report_title(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
        report_id=report_id
    )
    for p in report.get_param_spec_list():
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


def escape_for_tsv(value):
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


def tsv_from_query(rows, descriptions):
    """Converts rows from an SQL query result to TSV format."""
    tsv = "\t".join([escape_for_tsv(x) for x in descriptions]) + "\n"
    for row in rows:
        tsv += "\t".join([escape_for_tsv(x) for x in row]) + "\n"
    return tsv


def provide_report(session, form):
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
    if (outputtype != VALUE.OUTPUTTYPE_HTML
            and outputtype != VALUE.OUTPUTTYPE_TSV):
        return cc_html.fail_with_error_stay_logged_in("Unknown outputtype")

    # Get parameters
    params = get_params_from_form(report.get_param_spec_list(), form)

    # Get query details
    rows, descriptions = report.get_rows_descriptions(**params)
    if rows is None or descriptions is None:
        return cc_html.fail_with_error_stay_logged_in(
            "Report failed to return a list of descriptions/results")

    if outputtype == VALUE.OUTPUTTYPE_TSV:
        filename = (
            "CamCOPS_"
            + report.get_report_id()
            + "_"
            + cc_dt.format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.FILENAME)
            + ".tsv"
        )
        return ws.tsv_result(tsv_from_query(rows, descriptions), [], filename)
    else:
        # HTML
        html = pls.WEBSTART + """
            {}
            <h1>{}</h1>
        """.format(
            session.get_current_user_html(),
            report.get_report_title(),
        ) + ws.html_table_from_query(rows, descriptions) + WEBEND
        return html


# =============================================================================
# Report class
# =============================================================================

class Report(object):
    """Abstract base class representing a report."""

    @classmethod
    def get_report_id(cls):
        """String used in HTML selector. Must override."""
        return None

    @classmethod
    def get_report_title(cls):
        """String for display purposes. Must override."""
        return None

    @classmethod
    def get_param_spec_list(cls):
        """Returns a list of dictionaries, each of the format: {
            "type": ... internal code (e.g. which ID number? Integer? etc.)
            "name": used in URL and in **kwargs to get_rows_descriptions
            "label": cosmetic, used for offering HTML
        }
        Must override."""
        return []

    def get_rows_descriptions(self, **kwargs):
        """Execute the report. Must override. Parameters are passed in via
        **kwargs."""
        return [], []


# =============================================================================
# Unit testing
# =============================================================================

def task_unit_test_report(name, r):
    """Unit tests for reports."""
    unit_test_ignore("Testing {}.get_report_id".format(name),
                     r.get_report_id)
    unit_test_ignore("Testing {}.get_report_title".format(name),
                     r.get_report_title)
    unit_test_ignore("Testing {}.get_param_spec_list".format(name),
                     r.get_param_spec_list)
    unit_test_ignore("Testing {}.get_rows_descriptions".format(name),
                     r.get_rows_descriptions)


def unit_tests():
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
