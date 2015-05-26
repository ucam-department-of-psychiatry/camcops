#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

from __future__ import print_function

# =============================================================================
# Debugging options
# =============================================================================

# Not possible to put the next two flags in environment variables, because we
# need them at load-time and the WSGI system only gives us environments at
# run-time.

# For debugging, set the next variable to True, and it will provide much
# better HTML debugging output.
# Use caution enabling this on a production system.
# However, system passwords should be concealed regardless (see cc_shared.py).
DEBUG_TO_HTTP_CLIENT = True

# Report profiling information to the HTTPD log? (Adds overhead; do not enable
# for production systems.)
PROFILE = False

# The other debugging control is in cc_shared: see the logger.setLevel() calls,
# controlled primarily by the configuration file's DEBUG_OUTPUT option.

# =============================================================================
# Check Python version (the shebang is not a guarantee)
# =============================================================================

import sys

if sys.version_info[0] != 2 or sys.version_info[1] != 7:
    # ... sys.version_info.major (etc.) require Python 2.7 in any case!
    raise RuntimeError(
        "CamCOPS needs Python 2.7, and this Python version is: "
        + sys.version)

# =============================================================================
# Command-line "respond quickly" point
# =============================================================================

if __name__ == '__main__':
    print("CamCOPS loading...", file=sys.stderr)

# =============================================================================
# Imports
# =============================================================================

import codecs
import collections
import ConfigParser
import getpass
import glob
import io
import lockfile
import os
import pygments
import pygments.lexers
import pygments.lexers.web
import pygments.formatters
import StringIO
import sys
import zipfile

# local:
import rnc_db
import rnc_web as ws

# CamCOPS support modules
from cc_audit import audit, SECURITY_AUDIT_TABLENAME, SECURITY_AUDIT_FIELDSPECS
from cc_constants import (
    ACTION,
    CAMCOPS_URL,
    DATEFORMAT,
    NUMBER_OF_IDNUMS,
    PARAM,
    VALUE
)
import cc_blob
import cc_db
import cc_device
import cc_dt
import cc_dump
import cc_hl7
import cc_html
from cc_logger import logger
import cc_patient
import cc_plot
cc_plot.do_nothing()
from cc_pls import pls
import cc_policy
import cc_report
import cc_session
import cc_specialnote
import cc_storedvar
from cc_string import WSTRING
import cc_task
import cc_tracker
import cc_user
import cc_version

# Conditional imports
if PROFILE:
    import werkzeug.contrib.profiler
if DEBUG_TO_HTTP_CLIENT:
    import wsgi_errorreporter

# Imports so as to set parameters in the imported modules
import rnc_pdf
rnc_pdf.set_processor("weasyprint" if cc_version.USE_WEASYPRINT
                      else "xhtml2pdf")

# Task imports: everything in "tasks" directory
task_modules = glob.glob(os.path.dirname(__file__) + "/tasks/*.py")
task_modules = [os.path.basename(f)[:-3] for f in task_modules]
for tm in task_modules:
    __import__(tm, locals(), globals())


# =============================================================================
# Constants
# =============================================================================

DEFAULT_CONFIG_FILENAME = "/etc/camcops/camcops.conf"
DEFAULT_N_AUDIT_ROWS = 100

AFFECTED_TASKS_HTML = u"<h1>Affected tasks:</h1>"
CANNOT_DUMP = "User not authorized to dump data/regenerate summary tables."
CANNOT_REPORT = "User not authorized to run reports."
CAN_ONLY_CHANGE_OWN_PASSWORD = "You can only change your own password!"
TASK_FAIL_MSG = "Task not found or user not authorized."
NOT_AUTHORIZED_MSG = "User not authorized."
NO_INTROSPECTION_MSG = "Introspection not permitted"
INTROSPECTION_INVALID_FILE_MSG = "Invalid file for introspection"
INTROSPECTION_FAILED_MSG = "Failed to read file for introspection"
MISSING_PARAMETERS_MSG = "Missing parameters"
ERROR_TASK_LIVE = (
    "Task is live on tablet; finalize (or force-finalize) first.")
NOT_ALL_PATIENTS_UNFILTERED_WARNING = u"""
    <div class="explanation">
        Your user isn’t configured to view all patients’ records when no
        patient filters are applied. Only anonymous records will be
        shown. Choose a patient to see their records.
    </div>"""
ID_POLICY_INVALID_DIV = u"""
    <div class="badidpolicy_severe">
        Server’s ID policies are missing or invalid.
        This needs fixing urgently by the system administrator.
    </div>
"""
SEPARATOR_HYPHENS = "-" * 79
SEPARATOR_EQUALS = "=" * 79

# System tables without a class representation:

DIRTY_TABLES_TABLENAME = "_dirty_tables"
DIRTY_TABLES_FIELDSPECS = [
    dict(name="device", cctype="DEVICE",
         comment="Source tablet device ID"),
    dict(name="tablename", cctype="TABLENAME",
         comment="Table in the process of being preserved"),
]


# =============================================================================
# User command-line interaction
# =============================================================================

def ask_user(prompt, default=None, to_unicode=False):
    """Prompts the user, with a default. Returns a string."""
    if default is None:
        prompt = prompt + ": "
    else:
        prompt = prompt + " [" + default + "]: "
    result = raw_input(prompt.encode(sys.stdout.encoding))
    if to_unicode:
        result = result.decode(sys.stdin.encoding)
    return result if len(result) > 0 else default


def ask_user_password(prompt):
    """Read a password from the console."""
    return getpass.getpass(prompt + ": ")


# =============================================================================
# Page components
# =============================================================================

def login_failed(redirect=None):
    """HTML given after login failure."""
    return cc_html.fail_with_error_not_logged_in(
        "Invalid username/password. Try again.",
        redirect)


def account_locked(locked_until, redirect=None):
    """HTML given when account locked out."""
    return cc_html.fail_with_error_not_logged_in(
        "Account locked until {} due to multiple login failures. "
        "Try again later or contact your administrator.".format(
            cc_dt.format_datetime(
                locked_until,
                DATEFORMAT.LONG_DATETIME_WITH_DAY,
                "(never)"
            )
        ),
        redirect)


def fail_not_user(action, redirect=None):
    """HTML given when action failed because not logged in properly."""
    return cc_html.fail_with_error_not_logged_in(
        u"Can't process action {} — not logged in as a valid user, "
        "or session has timed out.".format(action),
        redirect)


def fail_not_authorized_for_task():
    """HTML given when user isn't allowed to see a specific task."""
    return cc_html.fail_with_error_stay_logged_in(
        "Not authorized to view that task.")


def fail_task_not_found():
    """HTML given when task not found."""
    return cc_html.fail_with_error_stay_logged_in("Task not found.")


def fail_not_manager(action):
    """HTML given when user doesn't have management rights."""
    return cc_html.fail_with_error_stay_logged_in(
        "Can't process action {} - not logged in as a manager.".format(action)
    )


def fail_unknown_action(action):
    """HTML given when action unknown."""
    return cc_html.fail_with_error_stay_logged_in(
        "Can't process action {} - action not recognized.".format(action)
    )


# =============================================================================
# Pages/actions
# =============================================================================

def login(session, form):
    """Processes a login request."""

    logger.debug("Validating user login.")
    username = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    password = ws.get_cgi_parameter_str(form, PARAM.PASSWORD)
    redirect = ws.get_cgi_parameter_str(form, PARAM.REDIRECT)
    # 1. If we don't have a username, let's stop quickly.
    if not username:
        session.logout()
        return login_failed(redirect)
    # 2. Is the user locked?
    if cc_user.is_user_locked_out(username):
        return account_locked(
            cc_user.user_locked_out_until(username),
            redirect
        )
    # 3. Is the username/password combination correct?
    userobject = cc_user.get_user(username, password)  # checks password
    if userobject is not None and userobject.may_use_webviewer:
        # Successful login.
        userobject.login()  # will clear login failure record
        session.login(userobject)
        audit("Login")
    elif userobject is not None:
        # This means a user who can upload from tablet but who cannot log
        # in via the web front end.
        return login_failed(redirect)
    else:
        # Unsuccessful. Note that the username may/may not be genuine.
        cc_user.act_on_login_failure(username)  # may lock the account
        # ... call audit() before session.logout(), as the latter
        # will wipe the session IP address
        session.logout()
        return login_failed(redirect)

    # OK, logged in.

    # Need to change password?
    if session.user_must_change_password():
        return cc_user.enter_new_password(
            session, session.user,
            as_manager=False, because_password_expired=True
        )

    # Need to agree terms/conditions of use?
    if session.user_must_agree_terms():
        return offer_terms(session, form)

    # Redirect (to where user was trying to get to before timeout),
    # or main menu
    if redirect:
        return redirect_to(redirect)
    return main_menu(session, form)


def logout(session, form):
    """Logs a session out."""

    audit("Logout")
    session.logout()
    return cc_html.login_page()


def agree_terms(session, form):
    """The user has agreed the terms. Log this, then offer the main menu."""

    session.agree_terms()
    return main_menu(session, form)


def main_menu(session, form):
    """Main HTML menu."""

    # Main clinical/task section
    html = pls.WEBSTART + u"""
        {user}
        <h1>CamCOPS web view: Main menu</h1>
        <ul>
            <li><a href="{url_tasks}">View tasks</a></li>
            <li><a href="{url_tr}">Trackers for numerical information</a></li>
            <li><a href="{url_ctv}">Clinical text view</a></li>
        </ul>
    """.format(
        user=session.get_current_user_html(offer_main_menu=False),
        url_tasks=cc_html.get_generic_action_url(ACTION.VIEW_TASKS),
        url_tr=cc_html.get_generic_action_url(ACTION.CHOOSE_TRACKER),
        url_ctv=cc_html.get_generic_action_url(ACTION.CHOOSE_CLINICALTEXTVIEW),
    )

    # Reports, dump
    if session.authorized_for_reports() or session.authorized_to_dump():
        html += u"""<ul>"""
    if session.authorized_for_reports():
        html += u"""
            <li><a href="{reports}">Run reports</a></li>
        """.format(
            reports=cc_html.get_generic_action_url(ACTION.REPORTS_MENU),
        )
    if session.authorized_to_dump():
        html += u"""
            <li><a href="{basic_dump}">
                Basic research dump (fields and summaries)
            </a></li>
            <li><a href="{regen}">Regenerate summary tables</a></li>
            <li><a href="{table_dump}">Dump table/view data</a></li>
            <li>
                <a href="{table_defs}">Inspect table definitions</a>
                (... <a href="{tv_defs}">including views</a>)
            </li>
        """.format(
            basic_dump=cc_html.get_generic_action_url(ACTION.OFFER_BASIC_DUMP),
            regen=cc_html.get_generic_action_url(
                ACTION.OFFER_REGENERATE_SUMMARIES),
            table_dump=cc_html.get_generic_action_url(ACTION.OFFER_TABLE_DUMP),
            table_defs=cc_html.get_generic_action_url(
                ACTION.INSPECT_TABLE_DEFS),
            tv_defs=cc_html.get_generic_action_url(
                ACTION.INSPECT_TABLE_VIEW_DEFS),
        )
    if session.authorized_for_reports() or session.authorized_to_dump():
        html += u"""</ul>"""

    # Administrative
    if session.authorized_as_superuser():
        html += u"""
        <ul>
            <li><a href="{}">Manage users</a></li>
            <li><a href="{}">Delete patient entirely</a></li>
            <li><a href="{}">Forcibly preserve/finalize records for a
                device</a></li>
            <li><a href="{}">View audit trail</a></li>
            <li><a href="{}">View HL7 message log</a></li>
            <li><a href="{}">View HL7 run log</a></li>
        </ul>
        """.format(
            cc_html.get_generic_action_url(ACTION.MANAGE_USERS),
            cc_html.get_generic_action_url(ACTION.DELETE_PATIENT),
            cc_html.get_generic_action_url(ACTION.FORCIBLY_FINALIZE),
            cc_html.get_generic_action_url(ACTION.OFFER_AUDIT_TRAIL_OPTIONS),
            cc_html.get_generic_action_url(ACTION.OFFER_HL7_LOG_OPTIONS),
            cc_html.get_generic_action_url(ACTION.OFFER_HL7_RUN_OPTIONS),
        )

    # Everybody
    if pls.INTROSPECTION:
        introspection = u"""
            <li><a href="{}">Introspect source code</a></li>
        """.format(
            cc_html.get_generic_action_url(ACTION.OFFER_INTROSPECTION),
        )
    else:
        introspection = u""
    html += u"""
        <ul>
            <li><a href="{pol}">Show server identification policies</a></li>
            {introspection}
            <li><a href="{chpw}">Change password</a></li>
            <li><a href="{logout}">Log out</a></li>
        </ul>
        <div class="office">
            It’s {now}.
            Server version {sv}.
            See <a href="{camcops_url}">www.camcops.org</a> for more
            information on CamCOPS.
            Clicking on the CamCOPS logo will return you to the main menu.
        </div>
        {invalid_policy_warning}
    """.format(
        pol=cc_html.get_generic_action_url(ACTION.VIEW_POLICIES),
        introspection=introspection,
        chpw=cc_html.get_url_enter_new_password(session.user),
        logout=cc_html.get_generic_action_url(ACTION.LOGOUT),
        now=cc_dt.format_datetime(pls.NOW_LOCAL_TZ,
                                  DATEFORMAT.SHORT_DATETIME_SECONDS),
        sv=cc_version.CAMCOPS_SERVER_VERSION,
        camcops_url=CAMCOPS_URL,
        invalid_policy_warning=(
            "" if cc_policy.id_policies_valid() else ID_POLICY_INVALID_DIV
        ),
    ) + cc_html.WEBEND
    return html


def offer_terms(session, form):
    """HTML offering terms/conditions and requesting acknowledgement."""

    html = pls.WEBSTART + u"""
        {user}
        <h1>{title}</h1>
        <h2>{subtitle}</h2>
        <p>{content}</p>
        <form name="myform" action="{script}" method="POST">
            <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.AGREE_TERMS}">
            <input type="submit" value="{agree}">
        </form>
    """.format(
        user=session.get_current_user_html(),
        title=WSTRING("disclaimer_title"),
        subtitle=WSTRING("disclaimer_subtitle"),
        content=WSTRING("disclaimer_content"),
        script=pls.SCRIPT_NAME,
        PARAM=PARAM,
        ACTION=ACTION,
        agree=WSTRING("disclaimer_agree"),
    ) + cc_html.WEBEND
    return html


def view_policies(session, form):
    """HTML showing server's ID policies."""

    html = pls.WEBSTART + u"""
        {user}
        <h1>CamCOPS: current server identification policies</h1>
        <h2>Identification (ID) numbers</h2>
        <table>
            <tr>
                <th>ID number</th>
                <th>Description</th>
                <th>Short description</th>
            </tr>
    """.format(
        user=session.get_current_user_html(),
    )
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        html += u"""<tr> <td>{}</td> <td>{}</td> <td>{}</td> </tr>""".format(
            n,
            pls.get_id_desc(n),
            pls.get_id_shortdesc(n),
        )
    html += u"""
        </table>
        <h2>ID policies</h2>
        <table>
            <tr> <th>Policy</th> <th>Details</th> </tr>
            <tr> <td>Upload</td> <td>{}</td> </tr>
            <tr> <td>Finalize</td> <td>{}</td> </tr>
            <tr> <td>Principal (single necessary) ID number
                     required by Upload policy</td> <td>{}</td> </tr>
            <tr> <td>Principal (single necessary) ID number
                     required by Finalize policy</td> <td>{}</td> </tr>
        </table>
    """.format(
        pls.ID_POLICY_UPLOAD_STRING,
        pls.ID_POLICY_FINALIZE_STRING,
        cc_policy.get_upload_id_policy_principal_numeric_id(),
        cc_policy.get_finalize_id_policy_principal_numeric_id(),
    )
    return html + cc_html.WEBEND


def view_tasks(session, form):
    """HTML displaying tasks and applicable filters."""

    # Which tasks to view?
    first = session.get_first_task_to_view()
    n_to_view = session.number_to_view  # may be None
    if n_to_view is None:
        last = None
    else:
        last = first + n_to_view - 1

    # Get the tasks (which, in the process, tells us how many there are; we
    # use a generator rather than a giant list to save memory).
    task_rows = u""
    ntasks = 0
    for task in cc_task.gen_tasks_matching_session_filter(session):
        ntasks += 1
        tasknum = ntasks - 1
        if tasknum >= first and (last is None or tasknum <= last):
            task_rows += "<!-- task {} -->\n".format(tasknum)
            task_rows += task.get_task_list_row()

    # Output parts
    npages = session.get_npages(ntasks)
    currentpage = session.get_current_page()
    if currentpage == 1:
        nav_first = "First"
        nav_previous = "Previous"
    else:
        nav_first = """<a href="{}">First</a>""".format(
            cc_html.get_generic_action_url(ACTION.FIRST_PAGE)
        )
        nav_previous = """<a href="{}">Previous</a>""".format(
            cc_html.get_generic_action_url(ACTION.PREVIOUS_PAGE)
        )
    if currentpage >= npages:
        nav_next = "Next"
        nav_last = "Last"
    else:
        nav_next = """<a href="{}">Next</a>""".format(
            get_url_next_page(ntasks)
        )
        nav_last = """<a href="{}">Last</a>""".format(
            get_url_last_page(ntasks)
        )
    page_navigation = u"""
        <div><b>Page {}</b> of {} ({} tasks found) [ {} | {} | {} | {} ]</div>
    """.format(
        currentpage,
        npages,
        ntasks,
        nav_first,
        nav_previous,
        nav_next,
        nav_last,
    )

    if session.restricted_to_viewing_user():
        warn_restricted = cc_html.RESTRICTED_WARNING
    else:
        warn_restricted = ""
    if (not session.user_may_view_all_patients_when_unfiltered()
            and not session.any_specific_patient_filtering()):
        warn_other_pts = NOT_ALL_PATIENTS_UNFILTERED_WARNING
    else:
        warn_other_pts = ""

    if ntasks == 0:
        info_no_tasks = ("""
            <div class="important">
                No tasks found for your search criteria!
            </div>
        """)
    else:
        info_no_tasks = ""

    return pls.WEBSTART + u"""
        {user}
        <h1>View tasks</h1>
        {warn_restricted}
        {warn_other_pts}

        <h2>Filters (criteria)</h2>
        <div class="filter">
            {current_filters}
        </div>

        <h2>Number of tasks to view per page</h2>
        <div class="filter">
            {number_to_view_selector}
        </div>

        <h2>Tasks</h2>
        {page_nav}
        {task_list_header_table_start}
        {task_rows}
        {task_list_footer}
        {info_no_tasks}
        {page_nav}
    """.format(
        user=session.get_current_user_html(),
        warn_restricted=warn_restricted,
        warn_other_pts=warn_other_pts,
        current_filters=session.get_current_filter_html(),
        number_to_view_selector=session.get_number_to_view_selector(),
        page_nav=page_navigation,
        task_list_header_table_start=cc_task.TASK_LIST_HEADER,
        task_rows=task_rows,
        task_list_footer=cc_task.TASK_LIST_FOOTER,
        info_no_tasks=info_no_tasks,
    ) + cc_html.WEBEND


def change_number_to_view(session, form):
    """Change the number of tasks visible on a single screen."""

    session.change_number_to_view(form)
    return view_tasks(session, form)


def first_page(session, form):
    """Navigate to the first page of tasks."""

    session.first_page()
    return view_tasks(session, form)


def previous_page(session, form):
    """Navigate to the previous page of tasks."""

    session.previous_page()
    return view_tasks(session, form)


def next_page(session, form):
    """Navigate to the next page of tasks."""

    ntasks = ws.get_cgi_parameter_int(form, PARAM.NTASKS)
    session.next_page(ntasks)
    return view_tasks(session, form)


def last_page(session, form):
    """Navigate to the last page of tasks."""
    ntasks = ws.get_cgi_parameter_int(form, PARAM.NTASKS)
    session.last_page(ntasks)
    return view_tasks(session, form)


def serve_task(session, form):
    """Serves an individual task."""

    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    anonymise = ws.get_cgi_parameter_bool_or_default(form, PARAM.ANONYMISE,
                                                     False)
    allowed_types = [VALUE.OUTPUTTYPE_PDF,
                     VALUE.OUTPUTTYPE_HTML,
                     VALUE.OUTPUTTYPE_PDFHTML,
                     VALUE.OUTPUTTYPE_XML]
    if outputtype not in allowed_types:
        return cc_html.fail_with_error_stay_logged_in(
            "Task: outputtype must be one of {}".format(
                str(allowed_types)
            )
        )
    task = cc_task.TaskFactory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    # Is the user restricted so they can't see this particular one?
    if (session.restricted_to_viewing_user() is not None and
            session.restricted_to_viewing_user() != task._adding_user):
        return fail_not_authorized_for_task()
    task.audit("Viewed " + outputtype.upper())
    if anonymise:
        # This is for testing.
        task.anonymise()
    if outputtype == VALUE.OUTPUTTYPE_PDF:
        filename = task.suggested_pdf_filename()
        return ws.pdf_result(task.get_pdf(), [], filename)
    elif outputtype == VALUE.OUTPUTTYPE_HTML:
        return task.get_html(
            offer_add_note=session.authorized_to_add_special_note(),
            offer_erase=session.authorized_as_superuser(),
            offer_edit_patient=session.authorized_as_superuser()
        )
    elif outputtype == VALUE.OUTPUTTYPE_PDFHTML:  # debugging option
        return task.get_pdf_html()
    elif outputtype == VALUE.OUTPUTTYPE_XML:
        include_blobs = ws.get_cgi_parameter_bool_or_default(
            form, PARAM.INCLUDE_BLOBS, default=True)
        include_calculated = ws.get_cgi_parameter_bool_or_default(
            form, PARAM.INCLUDE_CALCULATED, default=True)
        include_patient = ws.get_cgi_parameter_bool_or_default(
            form, PARAM.INCLUDE_PATIENT, default=True)
        include_comments = ws.get_cgi_parameter_bool_or_default(
            form, PARAM.INCLUDE_COMMENTS, default=True)
        return ws.xml_result(
            task.get_xml(include_blobs=include_blobs,
                         include_calculated=include_calculated,
                         include_patient=include_patient,
                         include_comments=include_comments))
    else:
        raise AssertionError("ACTION.TASK: Invalid outputtype")


def choose_tracker(session, form):
    """HTML form for tracker selection."""

    if session.restricted_to_viewing_user():
        warning_restricted = cc_html.RESTRICTED_WARNING
    else:
        warning_restricted = ""
    html = pls.WEBSTART + u"""
        {userdetails}
        <h1>Choose tracker</h1>
        {warning}
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.TRACKER}">
                ID number: {which_idnum_picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}"><br>

                Start date (UTC):
                <input type="date" name="{PARAM.START_DATETIME}">
                <br>

                End date (UTC):
                <input type="date" name="{PARAM.END_DATETIME}"><br>

                <br>
                Task types:<br>
    """.format(
        userdetails=session.get_current_user_html(),
        warning=warning_restricted,
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        which_idnum_picker=cc_html.get_html_which_idnum_picker(
            PARAM.WHICH_IDNUM),
        PARAM=PARAM,
    )
    classes = cc_task.Task.__subclasses__()
    classes.sort(key=lambda cls: cls.get_taskshortname())
    for cls in classes:
        if cls.provides_trackers():
            html += u"""
                <label>
                    <input type="checkbox" name="{PARAM.TASKTYPES}"
                            value="{tablename}" checked>
                    {shortname}
                </label><br>
            """.format(
                PARAM=PARAM,
                tablename=cls.get_tablename(),
                shortname=cls.get_taskshortname(),
            )
    html += u"""
                <!-- buttons must have type "button" in order not to submit -->
                <button type="button" onclick="select_all(true);">
                    Select all
                </button>
                <button type="button" onclick="select_all(false);">
                    Deselect all
                </button>
                <br>
                <br>
                View tracker as:<br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_HTML}" checked>
                    HTML (for viewing online)
                </label><br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_PDF}">
                    PDF (for printing/saving)
                </label><br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_XML}">
                    XML (to inspect underlying raw data)
                </label><br>
                <br>

                <input type="hidden" name="{PARAM.INCLUDE_COMMENTS}" value="0">

                <input type="submit" value="View tracker">
                <script>
            function select_all(state) {{
                checkboxes = document.getElementsByName("{PARAM.TASKTYPES}");
                for (var i = 0, n = checkboxes.length; i < n; i++) {{
                    checkboxes[i].checked = state;
                }}
            }}
                </script>
            </form>
        </div>
    """.format(
        PARAM=PARAM,
        VALUE=VALUE,
    )
    # NB double the braces to escape them for Javascript
    return html + cc_html.WEBEND


def serve_tracker(session, form):
    """Serve up a tracker."""

    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    allowed_types = [VALUE.OUTPUTTYPE_PDF,
                     VALUE.OUTPUTTYPE_HTML,
                     VALUE.OUTPUTTYPE_XML]
    if outputtype not in allowed_types:
        return cc_html.fail_with_error_stay_logged_in(
            "Tracker: outputtype must be one of {}".format(
                str(allowed_types)
            )
        )
    tracker = get_tracker(session, form)
    if outputtype == VALUE.OUTPUTTYPE_PDF:
        # ... NB: may restrict its source information based on
        # restricted_to_viewing_user
        filename = tracker.suggested_pdf_filename()
        return ws.pdf_result(tracker.get_pdf(), [], filename)
    elif outputtype == VALUE.OUTPUTTYPE_HTML:
        return tracker.get_html()
    elif outputtype == VALUE.OUTPUTTYPE_XML:
        include_comments = ws.get_cgi_parameter_bool_or_default(
            form, PARAM.INCLUDE_COMMENTS, default=False)
        return ws.xml_result(tracker.get_xml(
            include_comments=include_comments))
    else:
        raise AssertionError("ACTION.TRACKER: Invalid outputtype")


def choose_clinicaltextview(session, form):
    """HTML form for CTV selection."""

    if session.restricted_to_viewing_user():
        warning_restricted = cc_html.RESTRICTED_WARNING
    else:
        warning_restricted = ""
    html = pls.WEBSTART + u"""
        {userdetails}
        <h1>Choose clinical text view</h1>
        {warning}
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.CLINICALTEXTVIEW}">

                ID number: {which_idnum_picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}"><br>

                Start date (UTC):
                <input type="date" name="{PARAM.START_DATETIME}"><br>

                End date (UTC):
                <input type="date" name="{PARAM.END_DATETIME}"><br>

                <br>
                View as:<br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_HTML}" checked>
                    HTML (for viewing online)
                </label>
                <br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_PDF}">
                    PDF (for printing/saving)
                </label>
                <br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_XML}">
                    XML (to inspect underlying raw data)
                </label><br>
                <br>

                <input type="hidden" name="{PARAM.INCLUDE_COMMENTS}" value="0">

                <input type="submit" value="View clinical text">
            </form>
        </div>
    """.format(
        userdetails=session.get_current_user_html(),
        warning=warning_restricted,
        script=pls.SCRIPT_NAME,
        which_idnum_picker=cc_html.get_html_which_idnum_picker(
            PARAM.WHICH_IDNUM),
        PARAM=PARAM,
        VALUE=VALUE,
        ACTION=ACTION,
    )
    return html + cc_html.WEBEND


def serve_clinicaltextview(session, form):
    """Returns a CTV."""

    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    allowed_types = [VALUE.OUTPUTTYPE_PDF,
                     VALUE.OUTPUTTYPE_HTML,
                     VALUE.OUTPUTTYPE_XML]
    if outputtype not in allowed_types:
        return cc_html.fail_with_error_stay_logged_in(
            "Clinical text view: outputtype must be one of {}".format(
                str(allowed_types)
            )
        )
    clinicaltextview = get_clinicaltextview(session, form)
    # ... NB: may restrict its source information based on
    # restricted_to_viewing_user
    if outputtype == VALUE.OUTPUTTYPE_PDF:
        filename = clinicaltextview.suggested_pdf_filename()
        return ws.pdf_result(clinicaltextview.get_pdf(), [], filename)
    elif outputtype == VALUE.OUTPUTTYPE_HTML:
        return clinicaltextview.get_html()
    elif outputtype == VALUE.OUTPUTTYPE_XML:
        include_comments = ws.get_cgi_parameter_bool_or_default(
            form, PARAM.INCLUDE_COMMENTS, default=False)
        return ws.xml_result(clinicaltextview.get_xml(
            include_comments=include_comments))
    else:
        raise AssertionError("ACTION.CLINICALTEXTVIEW: Invalid outputtype")


def change_task_filters(session, form):
    """Apply/clear filter parameters, then redisplay task list."""

    if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTERS):
        session.apply_filters(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTERS):
        session.clear_filters()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_SURNAME):
    #    session.apply_filter_surname(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_SURNAME):
        session.clear_filter_surname()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_FORENAME):
    #    session.apply_filter_forename(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_FORENAME):
        session.clear_filter_forename()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_DOB):
    #    session.apply_filter_dob(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_DOB):
        session.clear_filter_dob()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_SEX):
    #    session.apply_filter_sex(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_SEX):
        session.clear_filter_sex()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_IDNUMS):
    #    session.apply_filter_idnums(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_IDNUMS):
        session.clear_filter_idnums()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_TASK):
    #    session.apply_filter_task(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_TASK):
        session.clear_filter_task()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_COMPLETE):
    #    session.apply_filter_complete(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_COMPLETE):
        session.clear_filter_complete()

    # if ws.cgi_parameter_exists(form,
    #                            ACTION.APPLY_FILTER_INCLUDE_OLD_VERSIONS):
    #    session.apply_filter_include_old_versions(form)
    if ws.cgi_parameter_exists(form,
                               ACTION.CLEAR_FILTER_INCLUDE_OLD_VERSIONS):
        session.clear_filter_include_old_versions()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_DEVICE):
    #    session.apply_filter_device(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_DEVICE):
        session.clear_filter_device()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_USER):
    #    session.apply_filter_user(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_USER):
        session.clear_filter_user()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_START_DATETIME):
    #    session.apply_filter_start_datetime(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_START_DATETIME):
        session.clear_filter_start_datetime()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_END_DATETIME):
    #    session.apply_filter_end_datetime(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_END_DATETIME):
        session.clear_filter_end_datetime()

    # if ws.cgi_parameter_exists(form, ACTION.APPLY_FILTER_TEXT):
    #    session.apply_filter_text(form)
    if ws.cgi_parameter_exists(form, ACTION.CLEAR_FILTER_TEXT):
        session.clear_filter_text()

    return view_tasks(session, form)


def reports_menu(session, form):
    """Offer a menu of reports."""

    if not session.authorized_for_reports():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_REPORT)
    return cc_report.offer_report_menu(session)


def offer_report(session, form):
    """Offer configuration options for a single report."""

    if not session.authorized_for_reports():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_REPORT)
    return cc_report.offer_individual_report(session, form)


def provide_report(session, form):
    """Serve up a configured report."""

    if not session.authorized_for_reports():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_REPORT)
    return cc_report.provide_report(session, form)
    # ... unusual: manages the content type itself


def offer_regenerate_summary_tables(session, form):
    """Ask for confirmation to regenerate summary tables."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    return pls.WEBSTART + u"""
        {}
        <h1>Regenerate summary tables?</h1>
        <div class="warning">This may be slow.</div>
        <div><a href="{}">
            Proceed to regenerate summary tables (click once then <b>WAIT</b>)
        </a></div>
        <div><a href="{}">Cancel and return to main menu</a></div>
    """.format(
        session.get_current_user_html(),
        cc_html.get_generic_action_url(ACTION.REGENERATE_SUMMARIES),
        cc_html.get_url_main_menu(),
    ) + cc_html.WEBEND


def regenerate_summary_tables(session, form):
    """Drop and regenerated cached/temporary summary data tables."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    success, errormsg = make_summary_tables()
    if success:
        return cc_html.simple_success_message("Summary tables regenerated.")
    else:
        return cc_html.fail_with_error_stay_logged_in(
            u"Couldn’t regenerate summary tables. Error was: " + errormsg)


def inspect_table_defs(session, form):
    """Inspect table definitions with field comments."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    return get_descriptions_comments_html(include_views=False)


def inspect_table_view_defs(session, form):
    """Inspect table and view definitions with field comments."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    return get_descriptions_comments_html(include_views=True)


def offer_basic_dump(session, form):
    """Offer options for a basic research data dump."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    classes = cc_task.Task.__subclasses__()
    classes.sort(key=lambda cls: cls.get_taskshortname())
    possible_tasks = "".join([
        u"""
            <label>
                <input type="checkbox" name="{PARAM.TASKTYPES}"
                    value="{tablename}" checked>
                {shortname}
            </label><br>
        """.format(PARAM=PARAM,
                   tablename=cls.get_tablename(),
                   shortname=cls.get_taskshortname())
        for cls in classes])

    return pls.WEBSTART + u"""
        {userdetails}
        <h1>Basic research data dump</h1>
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.BASIC_DUMP}">

                <label onclick="show_tasks(false);">
                    <input type="radio" name="{PARAM.BASIC_DUMP_TYPE}"
                            value="{VALUE.DUMPTYPE_EVERYTHING}" checked>
                    Everything
                </label><br>

                <label onclick="show_tasks(false);">
                    <input type="radio" name="{PARAM.BASIC_DUMP_TYPE}"
                            value="{VALUE.DUMPTYPE_AS_TASK_FILTER}">
                    Those tasks selected by the current filters
                </label><br>

                <label onclick="show_tasks(true);">
                    <input type="radio" name="{PARAM.BASIC_DUMP_TYPE}"
                            value="{VALUE.DUMPTYPE_SPECIFIC_TASKS}">
                    Just specific tasks
                </label><br>

                <div id="tasklist" class="indented" style="display: none">
                    {possible_tasks}
                    <!-- buttons must have type "button" in order not to
                            submit -->
                    <button type="button" onclick="select_all(true);">
                        Select all
                    </button>
                    <button type="button" onclick="select_all(false);">
                        Deselect all
                    </button>
                </div>

                <br>

                <input type="submit" value="Dump data">

                <script>
            function select_all(state) {{
                checkboxes = document.getElementsByName("{PARAM.TASKTYPES}");
                for (var i = 0, n = checkboxes.length; i < n; i++) {{
                    checkboxes[i].checked = state;
                }}
            }}
            function show_tasks(state) {{
                s = state ? "block" : "none";
                document.getElementById("tasklist").style.display = s;
            }}
                </script>
            </form>
        </div>
        <h2>Explanation</h2>
        <div>
          <ul>
            <li>
              Provides a ZIP file containing tab-separated value (TSV)
              files (usually one per task; for some tasks, more than
              one).
            </li>
            <li>
              Restricted to current records (i.e. ignores historical
              versions of tasks that have been edited), unless you use
              the settings from the
              <a href="{view_tasks}">current filters</a> and those
              settings include non-current versions.
            </li>
            <li>
              If there are no instances of a particular task, no TSV is
              returned.
            </li>
            <li>
              Incorporates patient and summary information into each row.
              Doesn’t provide BLOBs (e.g. pictures).
              NULL values are represented by blank fields and are therefore
              indistinguishable from blank strings.
              Tabs are escaped to a literal <code>\\t</code>.
              Newlines are escaped to a literal <code>\\n</code>.
            </li>
            <li>
              Once you’ve unzipped the resulting file, you can import TSV files
              into many other software packages. Here are some examples:
              <ul>
                <li>
                  <b>OpenOffice:</b>
                  Character set =  UTF-8; Separated by / Tab.
                  <i>(Make sure no other delimiters are selected!)</i>
                </li>
                <li>
                  <b>Excel:</b> Delimited / Tab.
                  <i>(Make sure no other delimiters are selected!)</i>
                </li>
                <li>
                  <b>R:</b>
                  <code>mydf = read.table("something.tsv", sep="\\t",
                  header=TRUE, na.strings="", comment.char="")</code>
                  <i>(note that R will prepend ‘X’ to variable names starting
                  with an underscore; see <code>?make.names</code>)</i>.
                  Inspect the results with e.g. <code>colnames(mydf)</code>, or
                  in RStudio, <code>View(mydf)</code>.
                </li>
              </ul>
            </li>
            <li>
              For more advanced features, use the <a href="{table_dump}">
              table/view dump</a> to get the raw data.
            </li>
            <li>
              <b>For explanations of each field (field comments), see each
              task’s XML view or inspect the table definitions.</b>
            </li>
          </ul>
        </div>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
        VALUE=VALUE,
        view_tasks=cc_html.get_generic_action_url(ACTION.VIEW_TASKS),
        table_dump=cc_html.get_generic_action_url(ACTION.OFFER_TABLE_DUMP),
        possible_tasks=possible_tasks,
    ) + cc_html.WEBEND


def basic_dump(session, form):
    """Provides a basic research dump (ZIP of TSV files)."""

    # Permissions
    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)

    # Parameters
    dump_type = ws.get_cgi_parameter_str(form, PARAM.BASIC_DUMP_TYPE)
    permitted_dump_types = [VALUE.DUMPTYPE_EVERYTHING,
                            VALUE.DUMPTYPE_AS_TASK_FILTER,
                            VALUE.DUMPTYPE_SPECIFIC_TASKS]
    if dump_type not in permitted_dump_types:
        return cc_html.fail_with_error_stay_logged_in(
            "Basic dump: {PARAM.BASIC_DUMP_TYPE} must be one of "
            "{permitted}.".format(
                PARAM=PARAM,
                permitted=str(permitted_dump_types),
            )
        )
    task_tablename_list = ws.get_cgi_parameter_list(form, PARAM.TASKTYPES)

    # Create memory file
    memfile = io.BytesIO()
    z = zipfile.ZipFile(memfile, "w")

    # Generate everything
    classes = cc_task.Task.__subclasses__()
    classes.sort(key=lambda cls: cls.get_taskshortname())
    processed_tables = []
    for cls in classes:
        if dump_type == VALUE.DUMPTYPE_AS_TASK_FILTER:
            if not cls.filter_allows_task_type(session):
                continue
        table = cls.get_tablename()
        if dump_type == VALUE.DUMPTYPE_SPECIFIC_TASKS:
            if table not in task_tablename_list:
                continue
        processed_tables.append(table)
        if dump_type == VALUE.DUMPTYPE_AS_TASK_FILTER:
            genfunc = cls.gen_all_tasks_matching_session_filter
            args = [session]
        else:
            genfunc = cls.gen_all_current_tasks
            args = []
        kwargs = dict(sort=True, reverse=False)
        allfiles = collections.OrderedDict()
        # Some tasks may not return any rows for some of their potential
        # files. So we can't rely on the first task as being an exemplar.
        # Instead, we have a filename/contents mapping.
        for task in genfunc(*args, **kwargs):
            dictlist = task.get_dictlist_for_tsv()
            for i in range(len(dictlist)):
                filename = dictlist[i]["filenamestem"] + ".tsv"
                rows = dictlist[i]["rows"]
                if not rows:
                    continue
                if filename not in allfiles:
                    # First time we've encountered this filename; add header
                    allfiles[filename] = (
                        get_tsv_header_from_dict(rows[0]) + "\n"
                    )
                for r in rows:
                    allfiles[filename] += get_tsv_line_from_dict(r) + "\n"
        # If there are no valid task instances, there'll be no TSV; that's OK.
        for filename, contents in allfiles.items():
            z.writestr(filename, contents.encode("utf-8"))
    z.close()

    # Audit
    audit("basic dump: " + " ".join(processed_tables))

    # Return the result
    zip_contents = memfile.getvalue()
    filename = "CamCOPS_dump_" + cc_dt.format_datetime(
        pls.NOW_LOCAL_TZ,
        DATEFORMAT.FILENAME
    ) + ".zip"
    # atypical content type
    return ws.zip_result(zip_contents, [], filename)


def offer_table_dump(session, form):
    """HTML form to request dump of table data."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    # POST, not GET, or the URL exceeds the Apache limit
    html = pls.WEBSTART + u"""
        {userdetails}
        <h1>Dump table/view data</h1>
        <div class="warning">
            Beware including the blobs table; it is usually
            giant (BLOB = binary large object = pictures and the like).
        </div>
        <div class="filter">
            <form method="POST" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.TABLE_DUMP}">
                <br>

                Possible tables/views:<br>
                <br>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
    )

    for x in cc_dump.get_permitted_tables_views_sorted_labelled():
        if x["name"] == cc_blob.Blob.TABLENAME:
            name = PARAM.TABLES_BLOB
            checked = ""
        else:
            if x["view"]:
                name = PARAM.VIEWS
                checked = ""
            else:
                name = PARAM.TABLES
                checked = "checked"
        html += u"""
            <label>
                <input type="checkbox" name="{}" value="{}" {}>{}
            </label><br>
        """.format(name, x["name"], checked, x["name"])

    html += u"""
                <button type="button"
                        onclick="select_all_tables(true); deselect_blobs();">
                    Select all tables except blobs
                </button>
                <button type="button"
                        onclick="select_all_tables(false); deselect_blobs();">
                    Deselect all tables
                </button><br>
                <button type="button" onclick="select_all_views(true);">
                    Select all views
                </button>
                <button type="button" onclick="select_all_views(false);">
                    Deselect all views
                </button><br>
                <br>

                Dump as:<br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_SQL}">
                    SQL in UTF-8 encoding, views as their definitions
                </label><br>
                <label>
                    <input type="radio" name="{PARAM.OUTPUTTYPE}"
                            value="{VALUE.OUTPUTTYPE_TSV}" checked>
                    ZIP file containing tab-separated values (TSV) files in
                    UTF-8 encoding, NULL values as the string literal
                    <code>NULL</code>, views as their contents
                </label><br>
                <br>

                <input type="submit" value="Dump">

                <script>
        function select_all_tables(state) {{
            checkboxes = document.getElementsByName("{PARAM.TABLES}");
            for (var i = 0, n = checkboxes.length; i < n; i++) {{
                checkboxes[i].checked = state;
            }}
        }}
        function select_all_views(state) {{
            checkboxes = document.getElementsByName("{PARAM.VIEWS}");
            for (var i = 0, n = checkboxes.length; i < n; i++) {{
                checkboxes[i].checked = state;
            }}
        }}
        function deselect_blobs() {{
            checkboxes = document.getElementsByName("{PARAM.TABLES_BLOB}");
            for (var i = 0, n = checkboxes.length; i < n; i++) {{
                checkboxes[i].checked = false;
            }}
        }}
                </script>
            </form>
        </div>
    """.format(
        PARAM=PARAM,
        VALUE=VALUE,
    )
    return html + cc_html.WEBEND


def serve_table_dump(session, form):
    """Serve a dump of table +/- view data."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    tables = (
        ws.get_cgi_parameter_list(form, PARAM.TABLES)
        + ws.get_cgi_parameter_list(form, PARAM.VIEWS)
        + ws.get_cgi_parameter_list(form, PARAM.TABLES_BLOB)
    )
    if outputtype == VALUE.OUTPUTTYPE_SQL:
        filename = "CamCOPS_dump_" + cc_dt.format_datetime(
            pls.NOW_LOCAL_TZ,
            DATEFORMAT.FILENAME
        ) + ".sql"
        # atypical content type
        return ws.text_result(
            cc_dump.get_database_dump_as_sql(tables), [], filename
        )
    elif outputtype == VALUE.OUTPUTTYPE_TSV:
        zip_contents = cc_dump.get_multiple_views_data_as_tsv_zip(tables)
        if zip_contents is None:
            return cc_html.fail_with_error_stay_logged_in(
                cc_dump.NOTHING_VALID_SPECIFIED
            )
        filename = "CamCOPS_dump_" + cc_dt.format_datetime(
            pls.NOW_LOCAL_TZ,
            DATEFORMAT.FILENAME
        ) + ".zip"
        # atypical content type
        return ws.zip_result(zip_contents, [], filename)
    else:
        return cc_html.fail_with_error_stay_logged_in(
            "Dump: outputtype must be '{}' or '{}'".format(
                VALUE.OUTPUTTYPE_SQL,
                VALUE.OUTPUTTYPE_TSV
            )
        )


def offer_audit_trail_options(session, form):
    """HTML form to request audit trail."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return pls.WEBSTART + u"""
        {userdetails}
        <h1>View audit trail (starting with most recent)</h1>
        <p>Values below are optional.</p>
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.VIEW_AUDIT_TRAIL}">

                Number of rows:
                <input type="number" value="{DEFAULT_N_AUDIT_ROWS}"
                        name="{PARAM.NROWS}"><br>

                Start date (UTC):
                <input type="date" name="{PARAM.START_DATETIME}"><br>

                End date (UTC):
                <input type="date" name="{PARAM.END_DATETIME}"><br>

                Source (e.g. webviewer, tablet, console):
                <input type="text" name="{PARAM.SOURCE}"><br>

                Remote IP address:
                <input type="text" name="{PARAM.IPADDR}"><br>

                User name:
                <input type="text" name="{PARAM.USERNAME}"><br>

                Table name:
                <input type="text" name="{PARAM.TABLENAME}"><br>

                Server PK:
                <input type="number" name="{PARAM.SERVERPK}"><br>

                <label>
                    <input type="checkbox" name="{PARAM.TRUNCATE}"
                            value="1" checked>
                    Truncate details for easy viewing
                </label><br>

                <input type="submit" value="Submit">
            </form>
        </div>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
        DEFAULT_N_AUDIT_ROWS=DEFAULT_N_AUDIT_ROWS,
    )


def view_audit_trail(session, form):
    """Show audit trail."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    nrows = ws.get_cgi_parameter_int(form, PARAM.NROWS)
    if nrows is None or nrows < 0:
        # ... let's apply some limits!
        nrows = DEFAULT_N_AUDIT_ROWS
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    source = ws.get_cgi_parameter_str(form, PARAM.SOURCE)
    ipaddr = ws.get_cgi_parameter_str(form, PARAM.IPADDR)
    username = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    truncate = ws.get_cgi_parameter_bool(form, PARAM.TRUNCATE)

    wheres = []
    args = []
    if truncate:
        details = "LEFT(details, 100) AS details_truncated"
    else:
        details = "details"
    sql = """
        SELECT
            when_access_utc
            , source
            , remote_addr
            , user
            , table_name
            , server_pk
            , {details}
        FROM {table}
    """.format(
        table=SECURITY_AUDIT_TABLENAME,
        details=details,
    )
    if start_datetime:
        wheres.append("when_access_utc >= ?")
        args.append(start_datetime)
    if end_datetime:
        wheres.append("when_access_utc <= ?")
        args.append(end_datetime)
    if source:
        wheres.append("source = ?")
        args.append(source)
    if ipaddr:
        wheres.append("remote_addr = ?")
        args.append(ipaddr)
    if username:
        wheres.append("user = ?")
        args.append(username)
    if tablename:
        wheres.append("table_name = ?")
        args.append(tablename)
    if serverpk:
        wheres.append("server_pk = ?")
        args.append(serverpk)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY id DESC LIMIT {}".format(nrows)
    (rows, descriptions) = pls.db.fetchall_with_fieldnames(sql, *args)
    html = pls.WEBSTART + u"""
        {user}
        <h1>Audit trail</h1>
        <h2>
            Conditions: nrows={nrows}, start_datetime={start_datetime},
            end_datetime={end_datetime}
        </h2>
    """.format(
        user=session.get_current_user_html(),
        nrows=nrows,
        start_datetime=cc_dt.format_datetime(start_datetime,
                                             DATEFORMAT.ISO8601_DATE_ONLY),
        end_datetime=cc_dt.format_datetime(end_datetime,
                                           DATEFORMAT.ISO8601_DATE_ONLY),
    ) + ws.html_table_from_query(rows, descriptions) + cc_html.WEBEND
    return html


def offer_hl7_log_options(session, form):
    """HTML form to request HL7 message log view."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return pls.WEBSTART + u"""
        {userdetails}
        <h1>View HL7 outbound message log (starting with most recent)</h1>
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.VIEW_HL7_LOG}">

                Number of rows:
                <input type="number" value="{DEFAULT_N_AUDIT_ROWS}"
                        name="{PARAM.NROWS}">
                <br>

                Task base table (blank for all tasks):
                <input type="text" value="" name="{PARAM.TABLENAME}">
                <br>

                Task server PK (blank for all tasks):
                <input type="number" value="" name="{PARAM.SERVERPK}">
                <br>

                Run ID:
                <input type="number" name="{PARAM.HL7RUNID}">
                <br>

                Start date (UTC):
                <input type="date" name="{PARAM.START_DATETIME}">
                <br>

                End date (UTC):
                <input type="date" name="{PARAM.END_DATETIME}">
                <br>

                <label>
                    <input type="checkbox" value="1"
                            name="{PARAM.SHOWMESSAGE}">
                    Show message (if stored)
                </label>
                <br>

                <label>
                    <input type="checkbox" value="1"
                            name="{PARAM.SHOWREPLY}">
                    Show reply (if stored)
                </label>
                <br>

                <input type="submit" value="Submit">
            </form>
        </div>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
        DEFAULT_N_AUDIT_ROWS=DEFAULT_N_AUDIT_ROWS,
    )


def view_hl7_log(session, form):
    """Show HL7 message log."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    nrows = ws.get_cgi_parameter_int(form, PARAM.NROWS)
    basetable = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    run_id = ws.get_cgi_parameter_int(form, PARAM.HL7RUNID)
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    showmessage = ws.get_cgi_parameter_bool_or_default(form, PARAM.SHOWMESSAGE,
                                                       default=False)
    showreply = ws.get_cgi_parameter_bool_or_default(form, PARAM.SHOWREPLY,
                                                     default=False)
    if nrows is None or nrows < 0:
        # ... let's apply some limits!
        nrows = DEFAULT_N_AUDIT_ROWS
    wheres = []
    args = []
    sql = """
        SELECT msg_id
        FROM {hl7table}
    """.format(
        hl7table=cc_hl7.HL7Message.TABLENAME,
    )
    if basetable:
        wheres.append("basetable = ?")
        args.append(basetable)
    if serverpk:
        wheres.append("serverpk = ?")
        args.append(serverpk)
    if run_id:
        wheres.append("run_id = ?")
        args.append(run_id)
    if start_datetime:
        wheres.append("sent_at_utc >= ?")
        args.append(start_datetime)
    if end_datetime:
        wheres.append("sent_at_utc <= ?")
        args.append(end_datetime)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += """
        ORDER BY msg_id DESC
        LIMIT {nrows}
    """.format(
        nrows=nrows,
    )
    pks = pls.db.fetchallfirstvalues(sql, *args)
    html = pls.WEBSTART + u"""
        {user}
        <h1>HL7 log</h1>
        <h2>
            Conditions: basetable={basetable}, serverpk={serverpk},
            run_id={run_id}, nrows={nrows}, start_datetime={start_datetime},
            end_datetime={end_datetime}
        </h2>
        <table>
    """.format(
        user=session.get_current_user_html(),
        basetable=basetable,
        serverpk=serverpk,
        run_id=run_id,
        nrows=nrows,
        start_datetime=cc_dt.format_datetime(start_datetime,
                                             DATEFORMAT.ISO8601_DATE_ONLY),
        end_datetime=cc_dt.format_datetime(end_datetime,
                                           DATEFORMAT.ISO8601_DATE_ONLY),
    )
    html += cc_hl7.HL7Message.get_html_header_row(showmessage=showmessage,
                                                  showreply=showreply)
    for pk in pks:
        hl7msg = cc_hl7.HL7Message(pk)
        html += hl7msg.get_html_data_row(showmessage=showmessage,
                                         showreply=showreply)
    return html + u"""
        </table>
    """ + cc_html.WEBEND


def offer_hl7_run_options(session, form):
    """HTML form to request HL7 run log view."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return pls.WEBSTART + u"""
        {userdetails}
        <h1>View HL7 run log (starting with most recent)</h1>
        <div class="filter">
            <form method="GET" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.VIEW_HL7_RUN}">

                Run ID:
                <input type="number" name="{PARAM.HL7RUNID}">
                <br>

                Number of rows:
                <input type="number" value="{DEFAULT_N_AUDIT_ROWS}"
                        name="{PARAM.NROWS}">
                <br>

                Start date (UTC):
                <input type="date" name="{PARAM.START_DATETIME}">
                <br>

                End date (UTC):
                <input type="date" name="{PARAM.END_DATETIME}">
                <br>

                <input type="submit" value="Submit">
            </form>
        </div>
    """.format(
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
        DEFAULT_N_AUDIT_ROWS=DEFAULT_N_AUDIT_ROWS,
    )


def view_hl7_run(session, form):
    """Show HL7 run log."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    run_id = ws.get_cgi_parameter_int(form, PARAM.HL7RUNID)
    nrows = ws.get_cgi_parameter_int(form, PARAM.NROWS)
    if nrows is None or nrows < 0:
        # ... let's apply some limits!
        nrows = DEFAULT_N_AUDIT_ROWS
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    sql = """
        SELECT run_id
        FROM {hl7runtable}
    """.format(
        hl7runtable=cc_hl7.HL7Run.TABLENAME
    )
    wheres = []
    args = []
    if run_id is not None:
        wheres.append("run_id = ?")
        args.append(run_id)
    if start_datetime:
        wheres.append("start_at_utc >= ?")
        args.append(start_datetime)
    if end_datetime:
        wheres.append("start_at_utc <= ?")
        args.append(end_datetime)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += """
        ORDER BY run_id DESC
        LIMIT {}
    """.format(nrows)
    pks = pls.db.fetchallfirstvalues(sql, *args)

    html = pls.WEBSTART + u"""
        {user}
        <h1>HL7 run</h1>
        <h2>
            Conditions: nrows={nrows}, run_id={run_id},
            start_datetime={start_datetime}, end_datetime={end_datetime}
        </h2>
        <table>
    """.format(
        user=session.get_current_user_html(),
        nrows=nrows,
        run_id=run_id,
        start_datetime=cc_dt.format_datetime(start_datetime,
                                             DATEFORMAT.ISO8601_DATE_ONLY),
        end_datetime=cc_dt.format_datetime(end_datetime,
                                           DATEFORMAT.ISO8601_DATE_ONLY),
    )
    html += cc_hl7.HL7Run.get_html_header_row()
    for pk in pks:
        hl7run = cc_hl7.HL7Run(pk)
        html += hl7run.get_html_data_row()
    return html + u"""
        </table>
    """ + cc_html.WEBEND


def offer_introspection(session, form):
    """HTML form to offer CamCOPS server source code."""

    if not pls.INTROSPECTION:
        return cc_html.fail_with_error_stay_logged_in(NO_INTROSPECTION_MSG)
    html = pls.WEBSTART + u"""
        {user}
        <h1>Introspection into CamCOPS source code</h1>
    """.format(
        user=session.get_current_user_html(),
    )
    for ft in pls.INTROSPECTION_FILES:
        html += u"""
            <div>
                <a href="{url}">{prettypath}</a>
            </div>
        """.format(
            url=get_url_introspect(ft.searchterm),
            prettypath=ft.prettypath,
        )
    return html + cc_html.WEBEND


def introspect(session, form):
    """Provide formatted source code."""

    if not pls.INTROSPECTION:
        return cc_html.fail_with_error_stay_logged_in(NO_INTROSPECTION_MSG)
    filename = ws.get_cgi_parameter_str(form, PARAM.FILENAME)
    possible_filenames = [ft.searchterm for ft in pls.INTROSPECTION_FILES]
    if not filename or filename not in possible_filenames:
        return cc_html.fail_with_error_not_logged_in(
            INTROSPECTION_INVALID_FILE_MSG)
    index = possible_filenames.index(filename)
    ft = pls.INTROSPECTION_FILES[index]
    # logger.debug("INTROSPECTION: " + str(ft))
    fullpath = ft.fullpath
    if fullpath.endswith(".jsx"):
        lexer = pygments.lexers.web.JavascriptLexer()
    else:
        lexer = pygments.lexers.get_lexer_for_filename(fullpath)
    formatter = pygments.formatters.HtmlFormatter()
    try:
        with codecs.open(fullpath, "r", "utf8") as f:
            code = f.read()
    except Exception as e:
        logger.debug("INTROSPECTION ERROR: " + str(e))
        return cc_html.fail_with_error_not_logged_in(INTROSPECTION_FAILED_MSG)
    body = pygments.highlight(code, lexer, formatter)
    css = formatter.get_style_defs('.highlight')
    return u"""
        <!DOCTYPE html> <!-- HTML 5 -->
        <html>
            <head>
                <title>CamCOPS</title>
                <meta charset="utf-8">
                <style type="text/css">
                {css}
                </style>
            </head>
            <body>
            {body}
            </body>
            </html>
    """.format(css=css, body=body)


def add_special_note(session, form):
    """Add a special note to a task (after confirmation)."""

    if not session.authorized_to_add_special_note():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    N_CONFIRMATIONS = 2
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    note = ws.get_cgi_parameter_str(form, PARAM.NOTE)
    task = cc_task.TaskFactory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if (confirmation_sequence is None
            or confirmation_sequence < 0
            or confirmation_sequence > N_CONFIRMATIONS):
        confirmation_sequence = 0
    textarea = ""
    if confirmation_sequence == N_CONFIRMATIONS - 1:
        textarea = u"""
                <textarea name="{PARAM.NOTE}" rows="20" cols="80"></textarea>
                <br>
        """.format(
            PARAM=PARAM,
        )
    if confirmation_sequence < N_CONFIRMATIONS:
        return pls.WEBSTART + u"""
            {user}
            <h1>Add special note to task instance irrevocably</h1>
            {taskinfo}
            <div class="warning">
                <b>Are you {really} sure you want to apply a note?</b>
            </div>
            <p><i>Your note will be appended to any existing note.</i></p>
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.ADD_SPECIAL_NOTE}">
                <input type="hidden" name="{PARAM.TABLENAME}"
                        value="{tablename}">
                <input type="hidden" name="{PARAM.SERVERPK}"
                        value="{serverpk}">
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                {textarea}
                <input type="submit" class="important" value="Apply note">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
        """.format(
            user=session.get_current_user_html(),
            taskinfo=task.get_task_header_html(),
            really=" really" * confirmation_sequence,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            PARAM=PARAM,
            tablename=tablename,
            serverpk=serverpk,
            confirmation_sequence=confirmation_sequence + 1,
            textarea=textarea,
            cancelurl=cc_task.get_url_task_html(tablename, serverpk),
        ) + cc_html.WEBEND
    # If we get here, we'll apply the note.
    task.apply_special_note(note, session.user)
    return cc_html.simple_success_message(
        "Note applied ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(cc_task.get_url_task_html(tablename, serverpk))
    )


def erase_task(session, form):
    """Wipe all data from a task (after confirmation).

    Leaves the task record as a placeholder.
    """

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    N_CONFIRMATIONS = 3
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    task = cc_task.TaskFactory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if task.is_erased():
        return cc_html.fail_with_error_stay_logged_in("Task already erased.")
    if task.is_live_on_tablet():
        return cc_html.fail_with_error_stay_logged_in(ERROR_TASK_LIVE)
    if (confirmation_sequence is None
            or confirmation_sequence < 0
            or confirmation_sequence > N_CONFIRMATIONS):
        confirmation_sequence = 0
    if confirmation_sequence < N_CONFIRMATIONS:
        return pls.WEBSTART + u"""
            {user}
            <h1>Erase task instance irrevocably</h1>
            {taskinfo}
            <div class="warning">
                <b>ARE YOU {really} SURE YOU WANT TO ERASE THIS TASK?</b>
            </div>
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.ERASE_TASK}">
                <input type="hidden" name="{PARAM.TABLENAME}"
                        value="{tablename}">
                <input type="hidden" name="{PARAM.SERVERPK}"
                        value="{serverpk}">
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important" value="Erase task">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
        """.format(
            user=session.get_current_user_html(),
            taskinfo=task.get_task_header_html(),
            really=" REALLY" * confirmation_sequence,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            PARAM=PARAM,
            tablename=tablename,
            serverpk=serverpk,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=cc_task.get_url_task_html(tablename, serverpk),
        ) + cc_html.WEBEND
    # If we get here, we'll do the erasure.
    task.manually_erase(session.user)
    return cc_html.simple_success_message(
        "Task erased ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(cc_task.get_url_task_html(tablename, serverpk))
    )


def delete_patient(session, form):
    """Completely delete all data from a patient (after confirmation)."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    N_CONFIRMATIONS = 3
    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None
            or confirmation_sequence < 0
            or confirmation_sequence > N_CONFIRMATIONS):
        confirmation_sequence = 0
    patient_server_pks = cc_patient.get_patient_server_pks_by_idnum(
        which_idnum, idnum_value, current_only=False)
    if which_idnum is not None or idnum_value is not None:
        # A patient was asked for...
        if not patient_server_pks:
            # ... but not found
            return cc_html.fail_with_error_stay_logged_in(
                "No such patient found.")
    if confirmation_sequence < N_CONFIRMATIONS:
        # First call. Offer method.
        tasks = ""
        if which_idnum is not None and idnum_value is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                cc_task.gen_tasks_for_patient_deletion(which_idnum,
                                                       idnum_value))
        if confirmation_sequence > 0:
            warning = u"""
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO ERASE THIS PATIENT AND
                    ALL ASSOCIATED TASKS?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            patient_picker_or_label = u"""
                <input type="hidden" name="{PARAM.WHICH_IDNUM}"
                        value="{which_idnum}">
                <input type="hidden" name="{PARAM.IDNUM_VALUE}"
                        value="{idnum_value}">
                {id_desc}:
                <b>{idnum_value}</b>
            """.format(
                PARAM=PARAM,
                which_idnum=which_idnum,
                idnum_value=idnum_value,
                id_desc=pls.get_id_desc(which_idnum),
            )
        else:
            warning = ""
            patient_picker_or_label = u"""
                ID number: {which_idnum_picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}"
                        value="{idnum_value}">
            """.format(
                PARAM=PARAM,
                which_idnum_picker=cc_html.get_html_which_idnum_picker(
                    PARAM.WHICH_IDNUM, selected=which_idnum),
                idnum_value="" if idnum_value is None else idnum_value,
            )
        return pls.WEBSTART + u"""
            {user}
            <h1>Completely erase patient and associated tasks</h1>
            {warning}
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.DELETE_PATIENT}">
                {patient_picker_or_label}
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important"
                        value="Erase patient and tasks">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
            {tasks}
        """.format(
            user=session.get_current_user_html(),
            warning=warning,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            patient_picker_or_label=patient_picker_or_label,
            PARAM=PARAM,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=cc_html.get_url_main_menu(),
            tasks=tasks,
        ) + cc_html.WEBEND
    if not patient_server_pks:
        return cc_html.fail_with_error_stay_logged_in("No such patient found.")
    # If we get here, we'll do the erasure.
    # Delete tasks (with subtables)
    for cls in cc_task.Task.__subclasses__():
        tablename = cls.get_tablename()
        serverpks = cls.get_task_pks_for_patient_deletion(which_idnum,
                                                          idnum_value)
        for serverpk in serverpks:
            task = cc_task.TaskFactory(tablename, serverpk)
            task.delete_entirely()
    # Delete patients
    for ppk in patient_server_pks:
        pls.db.db_exec("DELETE FROM patient WHERE _pk = ?", ppk)
        audit("Patient deleted", patient_server_pk=ppk)
    msg = "Patient with idnum{} = {} and associated tasks DELETED".format(
        which_idnum, idnum_value)
    audit(msg)
    return cc_html.simple_success_message(msg)


def info_html_for_patient_edit(title, display, param, value, oldvalue):
    different = value != oldvalue
    newblank = (value is None or value == "")
    oldblank = (oldvalue is None or oldvalue == "")
    changetonull = different and (newblank and not oldblank)
    titleclass = ' class="important"' if changetonull else ''
    spanclass = ' class="important"' if different else ''
    return u"""
        <span{titleclass}>{title}:</span> <span{spanclass}>{display}</span><br>
        <input type="hidden" name="{param}" value="{value}">
    """.format(
        titleclass=titleclass,
        title=title,
        spanclass=spanclass,
        display=display,
        param=param,
        value=value,
    )


def edit_patient(session, form):
    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    # Inputs. We operate with text, for HTML reasons.
    patient_server_pk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    changes = {
        "forename": ws.get_cgi_parameter_str(form, PARAM.FORENAME, default=""),
        "surname": ws.get_cgi_parameter_str(form, PARAM.SURNAME, default=""),
        "dob": ws.get_cgi_parameter_datetime(form, PARAM.DOB),
        "sex": ws.get_cgi_parameter_str(form, PARAM.SEX, default=""),
        "address": ws.get_cgi_parameter_str(form, PARAM.ADDRESS, default=""),
        "gp": ws.get_cgi_parameter_str(form, PARAM.GP, default=""),
        "other": ws.get_cgi_parameter_str(form, PARAM.OTHER, default=""),
    }
    if changes["forename"]:
        changes["forename"] = changes["forename"].upper()
    if changes["surname"]:
        changes["surname"] = changes["surname"].upper()
    changes["dob"] = cc_dt.format_datetime(
        changes["dob"], DATEFORMAT.ISO8601_DATE_ONLY, default="")
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        val = ws.get_cgi_parameter_int(form, PARAM.IDNUM_PREFIX + str(n))
        if val is None:
            val = ""
        nstr = str(n)
        changes["idnum" + nstr] = val
        # We will also write the server's ID descriptions, if the ID number is
        # changing.
        if val != "":
            changes["iddesc" + nstr] = pls.get_id_desc(n)
            changes["idshortdesc" + nstr] = pls.get_id_shortdesc(n)
    # Calculations
    N_CONFIRMATIONS = 2
    if (confirmation_sequence is None
            or confirmation_sequence < 0
            or confirmation_sequence > N_CONFIRMATIONS):
        confirmation_sequence = 0
    patient = cc_patient.Patient(patient_server_pk)
    if patient._pk is None:
        return cc_html.fail_with_error_stay_logged_in(
            "No such patient found.")
    if not patient.is_preserved():
        return cc_html.fail_with_error_stay_logged_in(
            "Patient record is still live on tablet; cannot edit.")
    if confirmation_sequence < N_CONFIRMATIONS:
        # First call. Offer method.
        tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
            cc_task.gen_tasks_using_patient(
                patient.id, patient._device, patient._era))
        if confirmation_sequence > 0:
            warning = u"""
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO ALTER THIS PATIENT
                    RECORD (AFFECTING ASSOCIATED TASKS)?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            details = (
                info_html_for_patient_edit("Forename", changes["forename"],
                                           PARAM.FORENAME, changes["forename"],
                                           patient.forename)
                + info_html_for_patient_edit("Surname", changes["surname"],
                                             PARAM.SURNAME, changes["surname"],
                                             patient.surname)
                + info_html_for_patient_edit("DOB", changes["dob"],
                                             PARAM.DOB, changes["dob"],
                                             patient.dob)
                + info_html_for_patient_edit("Sex", changes["sex"],
                                             PARAM.SEX, changes["sex"],
                                             patient.sex)
                + info_html_for_patient_edit("Address", changes["address"],
                                             PARAM.ADDRESS, changes["address"],
                                             patient.address)
                + info_html_for_patient_edit("GP", changes["gp"],
                                             PARAM.GP, changes["gp"],
                                             patient.gp)
                + info_html_for_patient_edit("Other", changes["other"],
                                             PARAM.OTHER, changes["other"],
                                             patient.other)
            )
            for n in range(1, NUMBER_OF_IDNUMS + 1):
                desc = pls.get_id_desc(n)
                details += info_html_for_patient_edit(
                    u"ID number {} ({})".format(n, desc),
                    changes["idnum" + str(n)],
                    PARAM.IDNUM_PREFIX + str(n),
                    changes["idnum" + str(n)],
                    patient.get_idnum(n))
        else:
            warning = ""
            dob_for_html = cc_dt.format_datetime_string(
                patient.dob, DATEFORMAT.ISO8601_DATE_ONLY, default="")
            details = u"""
                Forename: <input type="text" name="{PARAM.FORENAME}"
                                value="{forename}"><br>
                Surname: <input type="text" name="{PARAM.SURNAME}"
                                value="{surname}"><br>
                DOB: <input type="date" name="{PARAM.DOB}"
                                value="{dob}"><br>
                Sex: {sex_picker}<br>
                Address: <input type="text" name="{PARAM.ADDRESS}"
                                value="{address}"><br>
                GP: <input type="text" name="{PARAM.GP}"
                                value="{gp}"><br>
                Other: <input type="text" name="{PARAM.OTHER}"
                                value="{other}"><br>
            """.format(
                PARAM=PARAM,
                forename=patient.forename or "",
                surname=patient.surname or "",
                dob=dob_for_html,
                sex_picker=cc_html.get_html_sex_picker(param=PARAM.SEX,
                                                       selected=patient.sex,
                                                       offer_all=False),
                address=patient.address or "",
                gp=patient.gp or "",
                other=patient.other or "",
            )
            for n in range(1, NUMBER_OF_IDNUMS + 1):
                desc = pls.get_id_desc(n)
                details += u"""
                    ID number {n} ({desc}):
                    <input type="number" name="{paramprefix}{n}"
                            value="{value}"><br>
                """.format(
                    n=n,
                    desc=pls.get_id_desc(n),
                    paramprefix=PARAM.IDNUM_PREFIX,
                    value=patient.get_idnum(n),
                )
        return pls.WEBSTART + u"""
            {user}
            <h1>Edit finalized patient details</h1>
            {warning}
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.EDIT_PATIENT}">
                <input type="hidden" name="{PARAM.SERVERPK}"
                        value="{patient_server_pk}">
                {details}
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important"
                        value="Change patient details">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
            {tasks}
        """.format(
            user=session.get_current_user_html(),
            warning=warning,
            script=pls.SCRIPT_NAME,
            PARAM=PARAM,
            ACTION=ACTION,
            patient_server_pk=patient_server_pk,
            details=details,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=cc_html.get_url_main_menu(),
            tasks=tasks,
        ) + cc_html.WEBEND
    # Line up the changes and validate, but DO NOT SAVE THE PATIENT as yet.
    changemessages = []
    for k, v in changes.iteritems():
        if v == "":
            v = None
        oldval = getattr(patient, k)
        if v is None and oldval == "":
            # Nothing really changing!
            continue
        if v != oldval:
            changemessages.append(u" {key}, {oldval} → {newval}".format(
                key=k,
                oldval=oldval,
                newval=v
            ))
            setattr(patient, k, v)
    # Valid?
    if (not patient.satisfies_upload_id_policy()
            or not patient.satisfies_finalize_id_policy()):
        return cc_html.fail_with_error_stay_logged_in(
            "New version does not satisfy uploading or finalizing policy; "
            "no changes made.")
    # Anything to do?
    if not changemessages:
        return cc_html.simple_success_message("No changes made.")
    # If we get here, we'll make the change.
    patient.save()
    msg = u"Patient details edited. Changes: "
    msg += u"; ".join(changemessages) + "."
    patient.apply_special_note(msg, session.user,
                               audit_msg="Patient details edited")
    for task in cc_task.gen_tasks_using_patient(patient.id, patient._device,
                                                patient._era):
        # Patient details changed, so resend any tasks via HL7
        task.delete_from_hl7_message_log()
    return cc_html.simple_success_message(msg)


def task_list_from_generator(generator):
    tasklist_html = u""
    for task in generator:
        tasklist_html += task.get_task_list_row()
    return u"""
        {TASK_LIST_HEADER}
        {tasklist_html}
        {TASK_LIST_FOOTER}
    """.format(
        TASK_LIST_HEADER=cc_task.TASK_LIST_HEADER,
        tasklist_html=tasklist_html,
        TASK_LIST_FOOTER=cc_task.TASK_LIST_FOOTER,
    )


def forcibly_finalize(session, form):
    """Force-finalize all live (_era == ERA_NOW) records from a device."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    N_CONFIRMATIONS = 3
    device_id = ws.get_cgi_parameter_str(form, PARAM.DEVICE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None
            or confirmation_sequence < 0
            or confirmation_sequence > N_CONFIRMATIONS):
        confirmation_sequence = 0
    if confirmation_sequence > 0 and device_id is None:
        return cc_html.fail_with_error_stay_logged_in("Device not specified.")
    if device_id is not None:
        # A device was asked for...
        d = cc_device.Device(device_id)
        if not d.is_valid():
            # ... but not found
            return cc_html.fail_with_error_stay_logged_in(
                "No such device found.")
    if confirmation_sequence < N_CONFIRMATIONS:
        # First call. Offer method.
        tasks = ""
        if device_id is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                cc_task.gen_tasks_live_on_tablet(device_id))
        if confirmation_sequence > 0:
            warning = u"""
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO FORCIBLY
                    PRESERVE/FINALIZE RECORDS FROM THIS DEVICE?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            device_picker_or_label = u"""
                <input type="hidden" name="{PARAM.DEVICE}"
                        value="{device_id}">
                <b>{device_nicename}</b>
            """.format(
                PARAM=PARAM,
                device_id=device_id,
                device_nicename=ws.webify(d.get_friendly_name_and_id())
            )
        else:
            warning = ""
            device_picker_or_label = cc_device.get_device_filter_dropdown(
                device_id)
        return pls.WEBSTART + u"""
            {user}
            <h1>
                Forcibly preserve/finalize records from a given tablet device
            </h1>
            {warning}
            <form name="myform" action="{script}" method="POST">
                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.FORCIBLY_FINALIZE}">
                Device: {device_picker_or_label}
                <input type="hidden" name="{PARAM.CONFIRMATION_SEQUENCE}"
                        value="{confirmation_sequence}">
                <input type="submit" class="important"
                        value="Forcibly finalize records from this device">
            </form>
            <div>
                <b><a href="{cancelurl}">CANCEL</a></b>
            </div>
            {tasks}
        """.format(
            user=session.get_current_user_html(),
            warning=warning,
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            device_picker_or_label=device_picker_or_label,
            PARAM=PARAM,
            confirmation_sequence=confirmation_sequence + 1,
            cancelurl=cc_html.get_url_main_menu(),
            tasks=tasks
        ) + cc_html.WEBEND

    # If we get here, we'll do the forced finalization.
    # Force-finalize tasks (with subtables)
    tables = [
        # non-task but tablet-based tables
        cc_patient.Patient.TABLENAME,
        cc_blob.Blob.TABLENAME,
        cc_storedvar.DeviceStoredVar.TABLENAME,
    ]
    for cls in cc_task.Task.__subclasses__():
        tables.append(cls.get_tablename())
        tables.extend(cls.get_extra_table_names())
    for t in tables:
        cc_db.forcibly_preserve_client_table(t, device_id, pls.session.user)
    # Field names are different in server-side tables, so they need special
    # handling:
    cc_db.forcibly_preserve_special_notes(device_id)
    # OK, done.
    msg = "Live records for device {} forcibly finalized".format(device_id)
    audit(msg)
    return cc_html.simple_success_message(msg)


def enter_new_password(session, form):
    """Ask for a new password."""

    user_to_change = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    if (user_to_change != session.user
            and not session.authorized_as_superuser()):
        return cc_html.fail_with_error_stay_logged_in(
            CAN_ONLY_CHANGE_OWN_PASSWORD)
    return cc_user.enter_new_password(
        session,
        user_to_change,
        user_to_change != session.user
    )


def change_password(session, form):
    """Implement a password change."""

    user_to_change = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    if user_to_change is None or session.user is None:
        return cc_html.fail_with_error_stay_logged_in(MISSING_PARAMETERS_MSG)
    if (user_to_change != session.user
            and not session.authorized_as_superuser()):
        return cc_html.fail_with_error_stay_logged_in(
            CAN_ONLY_CHANGE_OWN_PASSWORD)
    return cc_user.change_password(
        user_to_change,
        form,
        user_to_change != session.user
    )


def manage_users(session, form):
    """Offer user management menu."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.manage_users(session)


def ask_to_add_user(session, form):
    """Ask for details to add a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.ask_to_add_user(session)


def add_user(session, form):
    """Adds a user using the details supplied."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.add_user(form)


def edit_user(session, form):
    """Offers a user editing page."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_edit = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.edit_user(session, user_to_edit)


def change_user(session, form):
    """Applies edits to a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.change_user(form)


def ask_delete_user(session, form):
    """Asks for confirmation to delete a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_delete = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.ask_delete_user(session, user_to_delete)


def delete_user(session, form):
    """Deletes a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_delete = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.delete_user(user_to_delete)


def enable_user(session, form):
    """Enables a user (unlocks, clears login failures)."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_enable = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.enable_user_webview(user_to_enable)


def crash(session, form):
    """Deliberately raises an exception."""

    raise RuntimeError("Deliberately crashed. Should not affect other "
                       "processes.")


# =============================================================================
# Ancillary to the main pages/actions
# =============================================================================

def get_tracker(session, form):
    """Returns a Tracker() object specified by the CGI form."""

    task_tablename_list = ws.get_cgi_parameter_list(form, PARAM.TASKTYPES)
    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    return cc_tracker.Tracker(
        session,
        task_tablename_list,
        which_idnum,
        idnum_value,
        start_datetime,
        end_datetime
    )


def get_clinicaltextview(session, form):
    """Returns a ClinicalTextView() object defined by the CGI form."""

    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    return cc_tracker.ClinicalTextView(
        session,
        which_idnum,
        idnum_value,
        start_datetime,
        end_datetime
    )


def tsv_escape(x):
    if x is None:
        return u""
    if not isinstance(x, unicode):
        x = unicode(x)
    return x.replace("\t", "\\t").replace("\n", "\\n")


def get_tsv_header_from_dict(d):
    """Returns a TSV header line from a dictionary."""
    return u"\t".join([tsv_escape(x) for x in d.keys()])


def get_tsv_line_from_dict(d):
    """Returns a TSV data line from a dictionary."""
    return u"\t".join([tsv_escape(x) for x in d.values()])


# =============================================================================
# URLs
# =============================================================================

def get_url_next_page(ntasks):
    """URL to move to next page in task list."""
    return (
        cc_html.get_generic_action_url(ACTION.NEXT_PAGE)
        + cc_html.get_url_field_value_pair(PARAM.NTASKS, ntasks)
    )


def get_url_last_page(ntasks):
    """URL to move to last page in task list."""
    return (
        cc_html.get_generic_action_url(ACTION.LAST_PAGE)
        + cc_html.get_url_field_value_pair(PARAM.NTASKS, ntasks)
    )


def get_url_introspect(filename):
    """URL to view specific source code file."""
    return (
        cc_html.get_generic_action_url(ACTION.INTROSPECT)
        + cc_html.get_url_field_value_pair(PARAM.FILENAME, filename)
    )


# =============================================================================
# Redirection
# =============================================================================

def redirect_to(location):
    """Return an HTTP response redirecting to another location.

    Typically, this is used to allow a user to log in again after a timeout,
    but then to redirect where the user was wanting to go.
    """
    status = "303 See Other"
    extraheaders = [("Location", location)]
    contenttype = "text/plain"
    output = "Redirecting to {}".format(location)
    return (contenttype, extraheaders, output, status)


# =============================================================================
# Main HTTP processor
# =============================================================================

# -------------------------------------------------------------------------
# Main set of action mappings.
# All functions take parameters (session, form)
# -------------------------------------------------------------------------
ACTIONDICT = {
    None: main_menu,

    ACTION.LOGOUT: logout,
    ACTION.MAIN_MENU: main_menu,

    # Tasks, trackers, CTVs
    ACTION.TASK: serve_task,
    ACTION.TRACKER: serve_tracker,
    ACTION.CLINICALTEXTVIEW: serve_clinicaltextview,

    # Task list view: filters, pagination
    ACTION.VIEW_TASKS: view_tasks,
    ACTION.FILTER: change_task_filters,
    ACTION.CHANGE_NUMBER_TO_VIEW: change_number_to_view,
    ACTION.FIRST_PAGE: first_page,
    ACTION.PREVIOUS_PAGE: previous_page,
    ACTION.NEXT_PAGE: next_page,
    ACTION.LAST_PAGE: last_page,

    # Choosing trackers, CTVs
    ACTION.CHOOSE_TRACKER: choose_tracker,
    ACTION.CHOOSE_CLINICALTEXTVIEW: choose_clinicaltextview,

    # Reports
    ACTION.REPORTS_MENU: reports_menu,
    ACTION.OFFER_REPORT: offer_report,
    ACTION.PROVIDE_REPORT: provide_report,

    # Data dumps
    ACTION.OFFER_BASIC_DUMP: offer_basic_dump,
    ACTION.BASIC_DUMP: basic_dump,
    ACTION.OFFER_TABLE_DUMP: offer_table_dump,
    ACTION.TABLE_DUMP: serve_table_dump,
    ACTION.OFFER_REGENERATE_SUMMARIES: offer_regenerate_summary_tables,
    ACTION.REGENERATE_SUMMARIES: regenerate_summary_tables,
    ACTION.INSPECT_TABLE_DEFS: inspect_table_defs,
    ACTION.INSPECT_TABLE_VIEW_DEFS: inspect_table_view_defs,

    # User management
    ACTION.ENTER_NEW_PASSWORD: enter_new_password,
    ACTION.CHANGE_PASSWORD: change_password,
    ACTION.MANAGE_USERS: manage_users,
    ACTION.ASK_TO_ADD_USER: ask_to_add_user,
    ACTION.ADD_USER: add_user,
    ACTION.EDIT_USER: edit_user,
    ACTION.CHANGE_USER: change_user,
    ACTION.ASK_DELETE_USER: ask_delete_user,
    ACTION.DELETE_USER: delete_user,
    ACTION.ENABLE_USER: enable_user,

    # Supervisory reports
    ACTION.OFFER_AUDIT_TRAIL_OPTIONS: offer_audit_trail_options,
    ACTION.VIEW_AUDIT_TRAIL: view_audit_trail,
    ACTION.OFFER_HL7_LOG_OPTIONS: offer_hl7_log_options,
    ACTION.VIEW_HL7_LOG: view_hl7_log,
    ACTION.OFFER_HL7_RUN_OPTIONS: offer_hl7_run_options,
    ACTION.VIEW_HL7_RUN: view_hl7_run,

    # Introspection
    ACTION.OFFER_INTROSPECTION: offer_introspection,
    ACTION.INTROSPECT: introspect,

    # Amending and deleting data
    ACTION.ADD_SPECIAL_NOTE: add_special_note,
    ACTION.ERASE_TASK: erase_task,
    ACTION.DELETE_PATIENT: delete_patient,
    ACTION.EDIT_PATIENT: edit_patient,
    ACTION.FORCIBLY_FINALIZE: forcibly_finalize,

    # Miscellaneous
    ACTION.VIEW_POLICIES: view_policies,
    ACTION.AGREE_TERMS: agree_terms,
    ACTION.CRASH: crash,
}


def main_http_processor(env):
    """Main processor of HTTP requests."""

    # Sessions details are already in pls.session

    # -------------------------------------------------------------------------
    # Process requested action
    # -------------------------------------------------------------------------
    form = ws.get_cgi_fieldstorage_from_wsgi_env(env)
    action = ws.get_cgi_parameter_str(form, PARAM.ACTION)
    logger.debug("action = {}".format(action))

    # -------------------------------------------------------------------------
    # Login
    # -------------------------------------------------------------------------
    if action == ACTION.LOGIN:
        return login(pls.session, form)

    # -------------------------------------------------------------------------
    # If we're not authorized, we won't get any further:
    # -------------------------------------------------------------------------
    if not pls.session.authorized_as_viewer():
        if not action:
            return cc_html.login_page()
        else:
            return fail_not_user(action, redirect=env.get("REQUEST_URI"))

    # -------------------------------------------------------------------------
    # Can't bypass an enforced password change, or acknowledging terms:
    # -------------------------------------------------------------------------
    if pls.session.user_must_change_password():
        if action != ACTION.CHANGE_PASSWORD:
            return cc_user.enter_new_password(
                pls.session, pls.session.user,
                as_manager=False, because_password_expired=True
            )
    elif pls.session.user_must_agree_terms() and action != ACTION.AGREE_TERMS:
        return offer_terms(pls.session, form)
    # Caution with the case where the user must do both; don't want deadlock!
    # The statements let a user through if they're changing their password,
    # even if they also need to acknowledge terms (which comes next).

    # -------------------------------------------------------------------------
    # Process requested action
    # -------------------------------------------------------------------------
    fn = ACTIONDICT.get(action)
    if not fn:
        return fail_unknown_action(action)
    return fn(pls.session, form)


# =============================================================================
# Command-line debugging
# =============================================================================

# a = cc_task.TaskFactory("ace3", 6)
# a = cc_task.TaskFactory("ace3", 10)
# a.dump()
# a.write_pdf_to_disk("ace3test.pdf")

# p = cc_task.TaskFactory("phq9", 86)
# p = cc_task.TaskFactory("phq9", 1)
# p = cc_task.TaskFactory("phq9", 15)
# p.dump()
# p.write_pdf_to_disk("phq9test.pdf")

# b = cc_blob.Blob(3)

# create_demo_user()


# =============================================================================
# Version-specific database changes
# =============================================================================

def report_database_upgrade_step(version):
    print("PERFORMING UPGRADE TASKS FOR VERSION {}".format(version))


def modify_column(table, field, newdef):
    pls.db.modify_column_if_table_exists(table, field, newdef)


def change_column(tablename, oldfieldname, newfieldname, newdef):
    pls.db.change_column_if_table_exists(tablename, oldfieldname, newfieldname,
                                         newdef)


def rename_table(from_table, to_table):
    pls.db.rename_table(from_table, to_table)


def upgrade_database(old_version):
    print("Old database version: {}. New version: {}.".format(
        old_version,
        cc_version.CAMCOPS_SERVER_VERSION
    ))
    if old_version is None:
        logger.warning("Don't know old database version; can't upgrade "
                       "structure")
        return

    # Proceed IN SEQUENCE from older to newer versions.
    # Don't assume that tables exist already.
    # The changes are performed PRIOR to making tables afresh (which will
    # make any new columns required, and thereby block column renaming).
    # DO NOT DO THINGS THAT WOULD DESTROY USERS' DATA.

    if (old_version < 1.06):
        report_database_upgrade_step("1.06")
        pls.db.drop_table("_dirty_tables")

    if (old_version < 1.07):
        report_database_upgrade_step("1.07")
        pls.db.drop_table("_security_webviewer_sessions")

    if (old_version < 1.08):
        report_database_upgrade_step("1.08")
        change_column("_security_users",
                      "may_alter_users", "superuser", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_commentary", "hv_commentary", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_discussing", "hv_discussing", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_from_body", "hv_from_body", "BOOLEAN")

    if (old_version < 1.10):
        report_database_upgrade_step("1.10")
        modify_column("patient", "forename", "VARCHAR(255) NULL")
        modify_column("patient", "surname", "VARCHAR(255) NULL")
        modify_column("patient", "dob", "VARCHAR(32) NULL")
        modify_column("patient", "sex", "VARCHAR(1) NULL")

    if (old_version < 1.11):
        report_database_upgrade_step("1.11")
        # session
        modify_column("session", "ip_address", "VARCHAR(45) NULL")  # was 40
        # ExpDetThreshold
        pls.db.rename_table("expdetthreshold",
                            "cardinal_expdetthreshold")
        pls.db.rename_table("expdetthreshold_trials",
                            "cardinal_expdetthreshold_trials")
        change_column("cardinal_expdetthreshold_trials",
                      "expdetthreshold_id", "cardinal_expdetthreshold_id",
                      "INT")
        pls.db.drop_view("expdetthreshold_current")
        pls.db.drop_view("expdetthreshold_current_withpt")
        pls.db.drop_view("expdetthreshold_trials_current")
        # ExpDet
        pls.db.rename_table("expectationdetection",
                            "cardinal_expdet")
        pls.db.rename_table("expectationdetection_trialgroupspec",
                            "cardinal_expdet_trialgroupspec")
        pls.db.rename_table("expectationdetection_trials",
                            "cardinal_expdet_trials")
        pls.db.drop_table("expectationdetection_SUMMARY_TEMP")
        pls.db.drop_table("expectationdetection_BLOCKPROBS_TEMP")
        pls.db.drop_table("expectationdetection_HALFPROBS_TEMP")
        pls.db.drop_view("expectationdetection_current")
        pls.db.drop_view("expectationdetection_current_withpt")
        pls.db.drop_view("expectationdetection_trialgroupspec_current")
        pls.db.drop_view("expectationdetection_trials_current")
        pls.db.drop_view("expectationdetection_SUMMARY_TEMP_current")
        pls.db.drop_view("expectationdetection_SUMMARY_TEMP_current_withpt")
        pls.db.drop_view("expectationdetection_BLOCKPROBS_TEMP_current")
        pls.db.drop_view("expectationdetection_BLOCKPROBS_TEMP_current_withpt")
        pls.db.drop_view("expectationdetection_HALFPROBS_TEMP_current")
        pls.db.drop_view("expectationdetection_HALFPROBS_TEMP_current_withpt")
        change_column("cardinal_expdet_trials",
                      "expectationdetection_id", "cardinal_expdet_id", "INT")
        change_column("cardinal_expdet_trialgroupspec",
                      "expectationdetection_id", "cardinal_expdet_id", "INT")

    if (old_version < 1.15):
        report_database_upgrade_step("1.15")
        # these were INT UNSIGNED:
        modify_column("patient", "idnum1", "BIGINT UNSIGNED")
        modify_column("patient", "idnum2", "BIGINT UNSIGNED")
        modify_column("patient", "idnum3", "BIGINT UNSIGNED")
        modify_column("patient", "idnum4", "BIGINT UNSIGNED")
        modify_column("patient", "idnum5", "BIGINT UNSIGNED")
        modify_column("patient", "idnum6", "BIGINT UNSIGNED")
        modify_column("patient", "idnum7", "BIGINT UNSIGNED")
        modify_column("patient", "idnum8", "BIGINT UNSIGNED")

    # (etc.)


# =============================================================================
# Functions suitable for calling from the command line
# =============================================================================

def make_tables(drop_superfluous_columns=False):
    """Make database tables."""

    print(SEPARATOR_EQUALS)
    print("Checking +/- modifying database structure.")
    print("If this pauses, run 'sudo apachectl restart' in another terminal.")
    if drop_superfluous_columns:
        print("DROPPING SUPERFLUOUS COLUMNS")
    print(SEPARATOR_EQUALS)

    # MySQL engine settings
    INSERTMSG = " into my.cnf [mysqld] section, and restart MySQL"
    if not pls.db.mysql_using_innodb_strict_mode():
        logger.error("NOT USING innodb_strict_mode; please insert "
                     "'innodb_strict_mode = 1'" + INSERTMSG)
        return
    max_allowed_packet = pls.db.mysql_get_max_allowed_packet()
    if max_allowed_packet < 32 * 1024 * 1024:
        logger.error("MySQL max_allowed_packet < 32M; please insert "
                     "'max_allowed_packet = 32M'" + INSERTMSG)
        return
    if not pls.db.mysql_using_file_per_table():
        logger.error(
            "NOT USING innodb_file_per_table; please insert "
            "'innodb_file_per_table = 1'" + INSERTMSG)
        return
    if not pls.db.mysql_using_innodb_barracuda():
        logger.warning(
            "innodb_file_format IS NOT Barracuda; please insert "
            "'innodb_file_per_table = Barracuda'" + INSERTMSG)
        return

    # Database settings
    cc_db.set_db_to_utf8(pls.db)

    # Special system table, in which old database version number is kept
    cc_storedvar.ServerStoredVar.make_tables(drop_superfluous_columns)

    print(SEPARATOR_HYPHENS)
    print("Checking database version +/- upgrading.")
    print(SEPARATOR_HYPHENS)

    # Read old version number, and perform any special version-specific
    # upgrade tasks
    sv_version = cc_storedvar.ServerStoredVar("serverCamcopsVersion", "real")
    old_version = sv_version.getValue()
    upgrade_database(old_version)
    # Important that we write the new version now:
    sv_version.setValue(cc_version.CAMCOPS_SERVER_VERSION)
    # This value must only be written in conjunction with the database
    # upgrade process.

    print(SEPARATOR_HYPHENS)
    print("Making core tables")
    print(SEPARATOR_HYPHENS)

    # Other system tables
    cc_user.User.make_tables(drop_superfluous_columns)
    cc_device.Device.make_tables(drop_superfluous_columns)
    cc_hl7.HL7Run.make_tables(drop_superfluous_columns)
    cc_hl7.HL7Message.make_tables(drop_superfluous_columns)
    cc_session.Session.make_tables(drop_superfluous_columns)
    cc_specialnote.SpecialNote.make_tables(drop_superfluous_columns)

    # Core client tables
    cc_patient.Patient.make_tables(drop_superfluous_columns)
    cc_blob.Blob.make_tables(drop_superfluous_columns)
    cc_storedvar.DeviceStoredVar.make_tables(drop_superfluous_columns)

    # System tables without a class representation
    cc_db.create_or_update_table(
        DIRTY_TABLES_TABLENAME, DIRTY_TABLES_FIELDSPECS,
        drop_superfluous_columns=drop_superfluous_columns)
    pls.db.create_or_replace_primary_key(DIRTY_TABLES_TABLENAME,
                                         ["device", "tablename"])
    cc_db.create_or_update_table(
        SECURITY_AUDIT_TABLENAME, SECURITY_AUDIT_FIELDSPECS,
        drop_superfluous_columns=drop_superfluous_columns)

    # Task tables
    print(SEPARATOR_HYPHENS)
    print("Making task tables")
    print(SEPARATOR_HYPHENS)
    for cls in cc_task.Task.__subclasses__():
        print(
            "Making table(s) and view(s) for task: "
            + cls.get_taskshortname()
        )
        cls.make_tables(drop_superfluous_columns)

    audit("Created/recreated main tables", from_console=True)


def write_descriptions_comments(file, include_views=False):
    """Save database fields/comments to a file in HTML format."""

    sql = """
        SELECT
            t.table_type, c.table_name, c.column_name, c.column_type,
            c.is_nullable, c.column_comment
        FROM information_schema.columns c
        INNER JOIN information_schema.tables t
            ON c.table_schema = t.table_schema
            AND c.table_name = t.table_name
        WHERE (
                t.table_type='BASE TABLE'
    """
    if include_views:
        sql += """
                OR t.table_type='VIEW'
        """
    sql += """
            )
            AND c.table_schema='{}' /* database name */
    """.format(
        pls.DB_NAME
    )
    rows = pls.db.fetchall(sql)
    print(cc_html.COMMON_HEAD, file=file)
    # don't used fixed-width tables; they truncate contents
    print(u"""
            <table>
                <tr>
                    <th>Table type</th>
                    <th>Table</th>
                    <th>Column</th>
                    <th>Column type</th>
                    <th>May be NULL</th>
                    <th>Comment</th>
                </tr>
    """, file=file)
    for row in rows:
        outstring = u"<tr>"
        for i in range(len(row)):
            outstring += u"<td>{}</td>".format(ws.webify(row[i]))
        outstring += u"</tr>"
        print(outstring, file=file)
    print(u"""
            </table>
        </body>
    """, file=file)

    # Other methods:
    # - To view columns with comments:
    #        SHOW FULL COLUMNS FROM tablename;
    # - or other methods at http://stackoverflow.com/questions/6752169


def export_descriptions_comments():
    """Export an HTML version of database fields/comments to a file of the
    user's choice."""
    filename = ask_user("Output HTML file",
                        "camcops_table_descriptions.html")
    include_views = ask_user(
        "Include views (leave blank for no, anything else for yes)? "
    )
    with open(filename, 'wb') as file:
        write_descriptions_comments(file, include_views)
    print("Done.")


def get_descriptions_comments_html(include_views=False):
    """Returns HTML of database field descriptions/comments."""
    f = StringIO.StringIO()
    write_descriptions_comments(f, include_views)
    return f.getvalue()


def get_database_title():
    """Returns database title, or ""."""
    if not pls.DATABASE_TITLE:
        return ""
    return pls.DATABASE_TITLE


def reset_storedvars():
    """Copy key descriptions (database title, ID descriptions, policies) from
    the config file to the database.

    These are stored so researchers can access them from the database.
    However, they're not used directly by the server (or the database.pl upload
    script).
    """
    print("Setting database title/ID descriptions from configuration file")
    dbt = cc_storedvar.ServerStoredVar("databaseTitle", "text")
    dbt.setValue(pls.DATABASE_TITLE)
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        i = n - 1
        nstr = str(n)
        sv_id = cc_storedvar.ServerStoredVar("idDescription" + nstr, "text")
        sv_id.setValue(pls.IDDESC[i])
        sv_sd = cc_storedvar.ServerStoredVar("idShortDescription" + nstr,
                                             "text")
        sv_sd.setValue(pls.IDSHORTDESC[i])
    sv_id_policy_upload = cc_storedvar.ServerStoredVar("idPolicyUpload",
                                                       "text")
    sv_id_policy_upload.setValue(pls.ID_POLICY_UPLOAD_STRING)
    sv_id_policy_finalize = cc_storedvar.ServerStoredVar("idPolicyFinalize",
                                                         "text")
    sv_id_policy_finalize.setValue(pls.ID_POLICY_FINALIZE_STRING)
    audit("Reset stored variables", from_console=True)


def make_summary_tables(from_console=True):
    """Drop and rebuild summary tables."""
    # Don't use print; this may run from the web interface. Use the logger.
    LOCKED_ERROR = (
        "make_summary_tables: couldn't open lockfile ({}.lock); "
        "may not have permissions, or file may be locked by "
        "another process; aborting".format(
            pls.SUMMARY_TABLES_LOCKFILE)
    )
    MISCONFIGURED_ERROR = (
        "make_summary_tables: No SUMMARY_TABLES_LOCKFILE "
        "specified in config; can't proceed"
    )
    if not pls.SUMMARY_TABLES_LOCKFILE:
        logger.error(MISCONFIGURED_ERROR)
        return False, MISCONFIGURED_ERROR
    lock = lockfile.FileLock(pls.SUMMARY_TABLES_LOCKFILE)
    if lock.is_locked():
        logger.warning(LOCKED_ERROR)
        return False, LOCKED_ERROR
    try:
        with lock:
            logger.info("MAKING SUMMARY TABLES")
            for cls in cc_task.Task.__subclasses__():
                cls.make_summary_table()
            audit("Created/recreated summary tables",
                  from_console=from_console)
            pls.db.commit()  # make_summary_tables commit (prior to releasing
            # file lock)
        return True, ""
    except lockfile.LockFailed:
        logger.warning(LOCKED_ERROR)
        return False, LOCKED_ERROR


def make_superuser():
    """Make a superuser from the command line."""
    print("MAKE SUPERUSER")
    username = ask_user("New superuser")
    if cc_user.user_exists(username):
        print("... user already exists!")
        return
    password1 = ask_user_password("New superuser password")
    password2 = ask_user_password("New superuser password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = cc_user.create_superuser(username, password1)
    print("Success: " + str(result))


def reset_password():
    """Reset a password from the command line."""
    print("RESET PASSWORD")
    username = ask_user("Username")
    if not cc_user.user_exists(username):
        print("... user doesn't exist!")
        return
    password1 = ask_user_password("New password")
    password2 = ask_user_password("New password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = cc_user.set_password_directly(username, password1)
    print("Success: " + str(result))


def enable_user_cli():
    """Re-enable a locked user account from the command line."""
    print("ENABLE LOCKED USER ACCOUNT")
    username = ask_user("Username")
    if not cc_user.user_exists(username):
        print("... user doesn't exist!")
        return
    cc_user.enable_user(username)
    print("Enabled.")


def generate_anonymisation_staging_db():
    db = pls.get_anonymisation_database()  # may raise
    ddfilename = pls.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE
    classes = cc_task.Task.__subclasses__()
    classes.sort(key=lambda cls: cls.get_taskshortname())
    with codecs.open(ddfilename, mode="w", encoding="utf8") as f:
        written_header = False
        for cls in classes:
            if cls.is_anonymous():
                continue
            # Drop, make and populate tables
            cls.make_cris_tables(db)
            # Add info to data dictionary
            rows = cls.get_cris_dd_rows()
            if not rows:
                continue
            if not written_header:
                f.write(get_tsv_header_from_dict(rows[0]) + "\n")
                written_header = True
            for r in rows:
                f.write(get_tsv_line_from_dict(r) + "\n")
    db.commit()
    print("Draft data dictionary written to {}".format(ddfilename))


# =============================================================================
# Test rig
# =============================================================================

def test():
    """Run all unit tests."""

    # We do some rollbacks so as not to break performance of ongoing tasks.

    print("-- Testing camcopswebview")
    unit_tests()
    pls.db.rollback()

    print("-- Testing cc_analytics")
    import cc_analytics
    cc_analytics.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_blob")
    cc_blob.unit_tests()
    pls.db.rollback()

    # cc_constants: no functions

    print("-- Testing cc_device")
    cc_device.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_dump")
    cc_dump.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_hl7")
    cc_hl7.unit_tests()
    pls.db.rollback()

    # cc_namedtuples: simple, and doesn't need cc_shared

    print("-- Testing cc_patient")
    cc_patient.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_policy")
    cc_policy.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_report")
    cc_report.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_session")
    cc_session.unit_tests()
    pls.db.rollback()

    # at present only tested implicitly: cc_shared

    print("-- Testing cc_tracker")
    cc_tracker.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_user")
    cc_user.unit_tests()
    pls.db.rollback()

    # cc_version: no functions

    # Done last (slowest)
    print("-- Testing cc_task")
    cc_task.unit_tests()
    pls.db.rollback()


# =============================================================================
# WSGI application
# =============================================================================

def camcops_application_db_wrapper(environ, start_response):
    """WSGI application entry point.

    Provides a wrapper around the main WSGI application in order to trap
    database errors, so that a commit or rollback is guaranteed, and so a crash
    cannot leave the database in a locked state and thereby mess up other
    processes.
    """

    if environ["wsgi.multithread"]:
        logger.critical("Started in multithreaded mode")
        raise RuntimeError("Cannot be run in multithreaded mode")
    else:
        logger.debug("Started in single-threaded mode")

    # Set global variables, connect/reconnect to database, etc.
    pls.set_from_environ_and_ping_db(environ)

    # Trap any errors from here.
    # http://doughellmann.com/2009/06/19/python-exception-handling-techniques.html  # noqa

    try:
        result = camcops_application_main(environ, start_response)
        # ... it will commit (the earlier the better for speed)
        return result
    except Exception:
        try:
            raise  # re-raise the original error
        finally:
            try:
                pls.db.rollback()
            except:
                pass  # ignore errors in rollback


def camcops_application_main(environ, start_response):
    """Main WSGI application handler."""
    # Establish a session based on incoming details
    cc_session.establish_session(environ)  # writes to pls.session

    # Call main
    result = main_http_processor(environ)
    status = '200 OK'  # default unless overwritten
    # If it's a 3-value tuple, fine. Otherwise, assume HTML requiring encoding.
    if isinstance(result, tuple) and len(result) == 3:
        (contenttype, extraheaders, output) = result
    elif isinstance(result, tuple) and len(result) == 4:
        (contenttype, extraheaders, output, status) = result
    else:
        (contenttype, extraheaders, output) = ws.html_result(result)

    # Commit (e.g. password changes, audit events, session timestamps)
    pls.db.commit()  # WSGI route commit

    # Add cookie.
    extraheaders.extend(pls.session.get_cookies())
    # Wipe session details, as an additional safeguard
    pls.session = None

    # Return headers and output
    response_headers = [('Content-Type', contenttype),
                        ('Content-Length', str(len(output)))]
    if extraheaders is not None:
        response_headers.extend(extraheaders)  # not append!
    start_response(status, response_headers)
    return [output]


# =============================================================================
# Command-line processor
# =============================================================================

def cli_main():
    """Command-line entry point."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    import argparse

    # Fetch command-line options.
    silent = False
    parser = argparse.ArgumentParser(
        prog="camcops",  # name the user will use to call it
        description=("CamCOPS command-line tool. "
                     "Run with no arguments for an interactive menu.")
    )
    parser.add_argument("-v", "--version", action="version",
                        version="CamCOPS {}".format(
                            cc_version.CAMCOPS_SERVER_VERSION))
    parser.add_argument("-m", "--maketables",
                        action="store_true", default=False,
                        dest="maketables",
                        help="Make/remake tables and views")
    parser.add_argument("--dropsuperfluous", action="store_true",
                        help="Additional option to --maketables to drop "
                             "superfluous columns; requires both confirmatory "
                             "flags as well")
    parser.add_argument("--confirm_drop_superfluous_1", action="store_true",
                        help="Confirmatory flag 1/2 for --dropsuperfluous")
    parser.add_argument("--confirm_drop_superfluous_2", action="store_true",
                        help="Confirmatory flag 2/2 for --dropsuperfluous")
    parser.add_argument("-r", "--resetstoredvars",
                        action="store_true", default=False,
                        dest="resetstoredvars",
                        help=("Redefine database title/patient ID number "
                              "meanings/ID policy"))
    parser.add_argument("-t", "--title",
                        action="store_true", default=False,
                        dest="showtitle",
                        help="Show database title")
    parser.add_argument("-s", "--summarytables",
                        action="store_true", default=False,
                        dest="summarytables",
                        help="Make summary tables")
    parser.add_argument("-u", "--superuser",
                        action="store_true", default=False,
                        dest="superuser",
                        help="Make superuser")
    parser.add_argument("-p", "--password",
                        action="store_true", default=False,
                        dest="password",
                        help="Reset a user's password")
    parser.add_argument("-e", "--enableuser",
                        action="store_true", default=False,
                        dest="enableuser",
                        help="Re-enable a locked user account")
    parser.add_argument("-d", "--descriptions",
                        action="store_true", default=False,
                        dest="descriptions",
                        help="Export table descriptions")
    parser.add_argument("-7", "--hl7",
                        action="store_true", default=False,
                        dest="hl7",
                        help="Send pending HL7 messages and outbound files")
    parser.add_argument("-q", "--queue",
                        action="store_true", default=False,
                        dest="show_hl7_queue",
                        help="View outbound HL7/file queue (without sending)")
    parser.add_argument("-y", "--anonstaging",
                        action="store_true", default=False,
                        dest="anonstaging",
                        help=("Generate/regenerate anonymisation staging "
                              "database"))
    parser.add_argument("-x", "--test",
                        action="store_true", default=False,
                        dest="test",
                        help="Test internal code")
    parser.add_argument("configfilename", nargs="?", default=None,
                        help="Configuration file")
    args = parser.parse_args()
    if args.show_hl7_queue:
        silent = True

    # Say hello
    if not silent:
        print("CamCOPS version {}".format(cc_version.CAMCOPS_SERVER_VERSION))
        print("By Rudolf Cardinal. See " + CAMCOPS_URL)

    # If we don't know the config filename yet, ask the user
    if not args.configfilename:
        args.configfilename = ask_user("Configuration file",
                                       DEFAULT_CONFIG_FILENAME)
    # The set_from_environ_and_ping_db() function wants the config filename in
    # the environment:
    os.environ["CAMCOPS_CONFIG_FILE"] = args.configfilename
    if not silent:
        print("Using configuration file: {}".format(args.configfilename))

    # Set all other variables (inc. read from config file, open database)
    try:
        if not silent:
            print("Processing configuration information and connecting "
                  "to database (this may take some time)...")
        pls.set_from_environ_and_ping_db(os.environ)
    except ConfigParser.NoSectionError:
        print("""
You may not have the necessary privileges to read the configuration file, or it
may not exist, or be incomplete.
""")
        raise
    except rnc_db.NoDatabaseError():
        print("""
If the database failed to open, ensure it has been created. To create a
database, for example, in MySQL:
    CREATE DATABASE camcops;
""")
        raise

    # In order:
    n_actions = 0

    if args.maketables:
        drop_superfluous_columns = False
        if (args.dropsuperfluous and args.confirm_drop_superfluous_1
                and args.confirm_drop_superfluous_2):
            drop_superfluous_columns = True
        make_tables(drop_superfluous_columns)
        n_actions += 1

    if args.resetstoredvars:
        reset_storedvars()
        n_actions += 1

    if args.showtitle:
        print("Database title: {}".format(get_database_title()))
        n_actions += 1

    if args.summarytables:
        make_summary_tables()
        n_actions += 1

    if args.superuser:
        make_superuser()
        n_actions += 1

    if args.password:
        reset_password()
        n_actions += 1

    if args.descriptions:
        export_descriptions_comments()
        n_actions += 1

    if args.enableuser:
        enable_user_cli()
        n_actions += 1

    if args.hl7:
        cc_hl7.send_all_pending_hl7_messages()
        n_actions += 1

    if args.show_hl7_queue:
        cc_hl7.send_all_pending_hl7_messages(show_queue_only=True)
        n_actions += 1

    if args.anonstaging:
        generate_anonymisation_staging_db()
        n_actions += 1

    if args.test:
        test()
        n_actions += 1

    if n_actions > 0:
        pls.db.commit()  # command-line non-interactive route commit
        sys.exit()
        # ... otherwise proceed to the menu

    # Menu
    while True:
        print("""
{sep}
CamCOPS version {version} (command line).
Using database: {dbname} ({dbtitle}).

1) Make/remake tables and views
   ... MUST be the first action on a new database
   ... will not destroy existing data
   ... also performs item 3 below
2) Show database title
3) Copy database title/patient ID number meanings/ID policy into database
4) Make summary tables
5) Make superuser
6) Reset a user's password
7) Enable a locked user account
8) Export table descriptions with field comments
9) Test internal code (should always succeed)
10) Send all pending HL7 messages
11) Show HL7 queue without sending
12) Regenerate anonymisation staging database
13) Exit
""".format(sep=SEPARATOR_EQUALS,
           version=cc_version.CAMCOPS_SERVER_VERSION,
           dbname=pls.DB_NAME,
           dbtitle=get_database_title()))

        # avoid input():
        # http://www.gossamer-threads.com/lists/python/python/46911
        choice = raw_input("Choose: ")
        try:
            choice = int(choice)
        except ValueError:
            choice = None

        if choice == 1:
            make_tables(drop_superfluous_columns=False)
            reset_storedvars()
        elif choice == 2:
            print("Database title: {}".format(get_database_title()))
        elif choice == 3:
            reset_storedvars()
        elif choice == 4:
            make_summary_tables(from_console=True)
        elif choice == 5:
            make_superuser()
        elif choice == 6:
            reset_password()
        elif choice == 7:
            enable_user_cli()
        elif choice == 8:
            export_descriptions_comments()
        elif choice == 9:
            test()
        elif choice == 10:
            cc_hl7.send_all_pending_hl7_messages()
        elif choice == 11:
            cc_hl7.send_all_pending_hl7_messages(show_queue_only=True)
        elif choice == 12:
            generate_anonymisation_staging_db()
        elif choice == 13:
            sys.exit()

        # Must commit, or we may lock the database while watching the menu
        pls.db.commit()  # command-line interactive menu route commit


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests():
    """Unit tests for camcops.py"""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    import cgi
    from cc_unittest import unit_test_ignore

    session = cc_session.Session()
    form = cgi.FieldStorage()
    # suboptimal tests, as form isn't tailed to these things

    # skip: ask_user
    # skip: ask_user_password
    unit_test_ignore("", login_failed, "test_redirect")
    unit_test_ignore("", account_locked,
                     cc_dt.get_now_localtz(), "test_redirect")
    unit_test_ignore("", fail_not_user, "test_action", "test_redirect")
    unit_test_ignore("", fail_not_authorized_for_task)
    unit_test_ignore("", fail_task_not_found)
    unit_test_ignore("", fail_not_manager, "test_action")
    unit_test_ignore("", fail_unknown_action, "test_action")

    for ignorekey, func in ACTIONDICT.items():
        if func.__name__ == "crash":
            continue  # maybe skip this one!
        unit_test_ignore("", func, session, form)

    unit_test_ignore("", get_tracker, session, form)
    unit_test_ignore("", get_clinicaltextview, session, form)
    unit_test_ignore("", tsv_escape, "x\t\nhello")
    unit_test_ignore("", tsv_escape, None)
    unit_test_ignore("", tsv_escape, 3.45)
    # ignored: get_tsv_header_from_dict
    # ignored: get_tsv_line_from_dict

    unit_test_ignore("", get_url_next_page, 100)
    unit_test_ignore("", get_url_last_page, 100)
    unit_test_ignore("", get_url_introspect, "test_filename")
    unit_test_ignore("", redirect_to, "test_location")
    # ignored: main_http_processor
    # ignored: upgrade_database
    # ignored: make_tables

    f = StringIO.StringIO()
    unit_test_ignore("", write_descriptions_comments, f, False)
    unit_test_ignore("", write_descriptions_comments, f, True)
    # ignored: export_descriptions_comments
    unit_test_ignore("", get_database_title)
    # ignored: reset_storedvars
    # ignored: make_summary_tables
    # ignored: make_superuser
    # ignored: reset_password
    # ignored: enable_user_cli
    # ignored: camcops_application_db_wrapper


# =============================================================================
# WSGI entry point
# =============================================================================
# The WSGI framework looks for: def application(environ, start_response)
# ... must be called "application"

application = camcops_application_db_wrapper
# Don't apply ZIP compression here as middleware: it needs to be done
# selectively by content type, and is best applied automatically by Apache
# (which is easy).
if DEBUG_TO_HTTP_CLIENT:
    application = wsgi_errorreporter.ErrorReportingMiddleware(application)
if PROFILE:
    application = werkzeug.contrib.profiler.ProfilerMiddleware(application)


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == '__main__':
    cli_main()
