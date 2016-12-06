#!/usr/bin/env python
# webview.py

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

import datetime
import sys
import typing
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

# =============================================================================
# Command-line "respond quickly" point
# =============================================================================

# if __name__ == '__main__':
#     print("CamCOPS loading...", file=sys.stderr)

# =============================================================================
# Imports
# =============================================================================

import cgi
import codecs
import collections
import io
import lockfile
import pygments
import pygments.lexers
import pygments.lexers.web
import pygments.formatters
import zipfile

# local:
from cardinal_pythonlib.rnc_lang import import_submodules
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_web import HEADERS_TYPE, WSGI_TUPLE_TYPE

# CamCOPS support modules
from .cc_modules.cc_audit import (
    audit,
    SECURITY_AUDIT_TABLENAME,
)
from .cc_modules.cc_constants import (
    ACTION,
    CAMCOPS_URL,
    COMMON_HEAD,
    DATEFORMAT,
    NUMBER_OF_IDNUMS,
    PARAM,
    RESTRICTED_WARNING,
    TASK_LIST_FOOTER,
    TASK_LIST_HEADER,
    VALUE,
    WEBEND,
)
from .cc_modules import cc_blob
from .cc_modules import cc_db
from .cc_modules.cc_device import (
    Device,
    get_device_filter_dropdown,
)
from .cc_modules.cc_dt import (
    get_now_localtz,
    format_datetime,
    format_datetime_string
)
from .cc_modules import cc_dump
from .cc_modules import cc_hl7
from .cc_modules import cc_html
from .cc_modules.cc_logger import log
from .cc_modules import cc_patient
from .cc_modules import cc_plot
from .cc_modules.cc_pls import pls
from .cc_modules import cc_policy
from .cc_modules import cc_report
from .cc_modules import cc_session
from .cc_modules.cc_session import Session
from .cc_modules.cc_specialnote import forcibly_preserve_special_notes
from .cc_modules.cc_storedvar import DeviceStoredVar
from .cc_modules.cc_string import WSTRING
from .cc_modules import cc_task
from .cc_modules.cc_task import Task
from .cc_modules.cc_tracker import ClinicalTextView, Tracker
from .cc_modules.cc_unittest import unit_test_ignore
from .cc_modules import cc_user
from .cc_modules.cc_version import CAMCOPS_SERVER_VERSION

cc_plot.do_nothing()

# Task imports
import_submodules(".tasks", __package__)


WSGI_TUPLE_TYPE_WITH_STATUS = Tuple[str, HEADERS_TYPE, bytes, str]
# ... contenttype, extraheaders, output, status

# =============================================================================
# Check Python version (the shebang is not a guarantee)
# =============================================================================

# if sys.version_info[0] != 2 or sys.version_info[1] != 7:
#     # ... sys.version_info.major (etc.) require Python 2.7 in any case!
#     raise RuntimeError(
#         "CamCOPS needs Python 2.7, and this Python version is: "
#         + sys.version)

if sys.version_info[0] != 3:
    raise RuntimeError(
        "CamCOPS needs Python 3, and this Python version is: " + sys.version)

# =============================================================================
# Constants
# =============================================================================

DEFAULT_N_AUDIT_ROWS = 100

AFFECTED_TASKS_HTML = "<h1>Affected tasks:</h1>"
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
NOT_ALL_PATIENTS_UNFILTERED_WARNING = """
    <div class="explanation">
        Your user isn’t configured to view all patients’ records when no
        patient filters are applied. Only anonymous records will be
        shown. Choose a patient to see their records.
    </div>"""
ID_POLICY_INVALID_DIV = """
    <div class="badidpolicy_severe">
        Server’s ID policies are missing or invalid.
        This needs fixing urgently by the system administrator.
    </div>
"""


# =============================================================================
# Page components
# =============================================================================

def login_failed(redirect: str = None) -> str:
    """HTML given after login failure."""
    return cc_html.fail_with_error_not_logged_in(
        "Invalid username/password. Try again.",
        redirect)


def account_locked(locked_until: datetime.datetime, 
                   redirect: str = None) -> str:
    """HTML given when account locked out."""
    return cc_html.fail_with_error_not_logged_in(
        "Account locked until {} due to multiple login failures. "
        "Try again later or contact your administrator.".format(
            format_datetime(
                locked_until,
                DATEFORMAT.LONG_DATETIME_WITH_DAY,
                "(never)"
            )
        ),
        redirect)


def fail_not_user(action: str, redirect: str = None) -> str:
    """HTML given when action failed because not logged in properly."""
    return cc_html.fail_with_error_not_logged_in(
        "Can't process action {} — not logged in as a valid user, "
        "or session has timed out.".format(action),
        redirect)


def fail_not_authorized_for_task() -> str:
    """HTML given when user isn't allowed to see a specific task."""
    return cc_html.fail_with_error_stay_logged_in(
        "Not authorized to view that task.")


def fail_task_not_found() -> str:
    """HTML given when task not found."""
    return cc_html.fail_with_error_stay_logged_in("Task not found.")


def fail_not_manager(action: str) -> str:
    """HTML given when user doesn't have management rights."""
    return cc_html.fail_with_error_stay_logged_in(
        "Can't process action {} - not logged in as a manager.".format(action)
    )


def fail_unknown_action(action: str) -> str:
    """HTML given when action unknown."""
    return cc_html.fail_with_error_stay_logged_in(
        "Can't process action {} - action not recognized.".format(action)
    )


# =============================================================================
# Pages/actions
# =============================================================================

def login(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE_WITH_STATUS]:
    """Processes a login request."""

    log.debug("Validating user login.")
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
    # noinspection PyUnresolvedReferences
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
            session, session.username,
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


# noinspection PyUnusedLocal
def logout(session: Session, form: cgi.FieldStorage) -> str:
    """Logs a session out."""

    audit("Logout")
    session.logout()
    return cc_html.login_page()


def agree_terms(session: Session, form: cgi.FieldStorage) -> str:
    """The user has agreed the terms. Log this, then offer the main menu."""

    session.agree_terms()
    return main_menu(session, form)


# noinspection PyUnusedLocal
def main_menu(session: Session, form: cgi.FieldStorage) -> str:
    """Main HTML menu."""

    # Main clinical/task section
    html = pls.WEBSTART + """
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
        html += """<ul>"""
    if session.authorized_for_reports():
        html += """
            <li><a href="{reports}">Run reports</a></li>
        """.format(
            reports=cc_html.get_generic_action_url(ACTION.REPORTS_MENU),
        )
    if session.authorized_to_dump():
        html += """
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
        html += """</ul>"""

    # Administrative
    if session.authorized_as_superuser():
        html += """
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
        introspection = """
            <li><a href="{}">Introspect source code</a></li>
        """.format(
            cc_html.get_generic_action_url(ACTION.OFFER_INTROSPECTION),
        )
    else:
        introspection = ""
    html += """
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
        chpw=cc_html.get_url_enter_new_password(session.username),
        logout=cc_html.get_generic_action_url(ACTION.LOGOUT),
        now=format_datetime(pls.NOW_LOCAL_TZ,
                            DATEFORMAT.SHORT_DATETIME_SECONDS),
        sv=CAMCOPS_SERVER_VERSION,
        camcops_url=CAMCOPS_URL,
        invalid_policy_warning=(
            "" if cc_policy.id_policies_valid() else ID_POLICY_INVALID_DIV
        ),
    ) + WEBEND
    return html


# noinspection PyUnusedLocal
def offer_terms(session: Session, form: cgi.FieldStorage) -> str:
    """HTML offering terms/conditions and requesting acknowledgement."""

    html = pls.WEBSTART + """
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
    ) + WEBEND
    return html


# noinspection PyUnusedLocal
def view_policies(session: Session, form: cgi.FieldStorage) -> str:
    """HTML showing server's ID policies."""

    html = pls.WEBSTART + """
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
        html += """<tr> <td>{}</td> <td>{}</td> <td>{}</td> </tr>""".format(
            n,
            pls.get_id_desc(n),
            pls.get_id_shortdesc(n),
        )
    html += """
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
    return html + WEBEND


# noinspection PyUnusedLocal
def view_tasks(session: Session, form: cgi.FieldStorage) -> str:
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
    task_rows = ""
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
    page_navigation = """
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
        warn_restricted = RESTRICTED_WARNING
    else:
        warn_restricted = ""
    if (not session.user_may_view_all_patients_when_unfiltered() and
            not session.any_specific_patient_filtering()):
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

    refresh_tasks_button = """
        <form class="filter" method="POST" action="{script}">
            <input type="hidden" name="{PARAM.ACTION}"
                value="{ACTION.VIEW_TASKS}">
            <input type="submit" value="Refresh">
        </form>
    """.format(
        script=pls.SCRIPT_NAME,
        PARAM=PARAM,
        ACTION=ACTION,
    )
    # http://stackoverflow.com/questions/2906582/how-to-create-an-html-button-that-acts-like-a-link  # noqa

    return pls.WEBSTART + """
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
        <div class="filter">
            {refresh_tasks_button}
        </div>
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
        refresh_tasks_button=refresh_tasks_button,
        page_nav=page_navigation,
        task_list_header_table_start=TASK_LIST_HEADER,
        task_rows=task_rows,
        task_list_footer=TASK_LIST_FOOTER,
        info_no_tasks=info_no_tasks,
    ) + WEBEND


def change_number_to_view(session: Session, form: cgi.FieldStorage) -> str:
    """Change the number of tasks visible on a single screen."""

    session.change_number_to_view(form)
    return view_tasks(session, form)


def first_page(session: Session, form: cgi.FieldStorage) -> str:
    """Navigate to the first page of tasks."""

    session.first_page()
    return view_tasks(session, form)


def previous_page(session: Session, form: cgi.FieldStorage) -> str:
    """Navigate to the previous page of tasks."""

    session.previous_page()
    return view_tasks(session, form)


def next_page(session: Session, form: cgi.FieldStorage) -> str:
    """Navigate to the next page of tasks."""

    ntasks = ws.get_cgi_parameter_int(form, PARAM.NTASKS)
    session.next_page(ntasks)
    return view_tasks(session, form)


def last_page(session: Session, form: cgi.FieldStorage) -> str:
    """Navigate to the last page of tasks."""
    ntasks = ws.get_cgi_parameter_int(form, PARAM.NTASKS)
    session.last_page(ntasks)
    return view_tasks(session, form)


def serve_task(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
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
    task = cc_task.task_factory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    # Is the user restricted so they can't see this particular one?
    if (session.restricted_to_viewing_user() is not None and
            session.restricted_to_viewing_user() != task.get_adding_user_id()):
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


# noinspection PyUnusedLocal
def choose_tracker(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form for tracker selection."""

    if session.restricted_to_viewing_user():
        warning_restricted = RESTRICTED_WARNING
    else:
        warning_restricted = ""
    html = pls.WEBSTART + """
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
    classes = cc_task.get_all_task_classes()
    for cls in classes:
        if hasattr(cls, 'get_trackers'):
            html += """
                <label>
                    <input type="checkbox" name="{PARAM.TASKTYPES}"
                            value="{tablename}" checked>
                    {shortname}
                </label><br>
            """.format(
                PARAM=PARAM,
                tablename=cls.tablename,
                shortname=cls.shortname,
            )
    html += """
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
    return html + WEBEND


def serve_tracker(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
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


# noinspection PyUnusedLocal
def choose_clinicaltextview(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form for CTV selection."""

    if session.restricted_to_viewing_user():
        warning_restricted = RESTRICTED_WARNING
    else:
        warning_restricted = ""
    html = pls.WEBSTART + """
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
    return html + WEBEND


def serve_clinicaltextview(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
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


def change_task_filters(session: Session, form: cgi.FieldStorage) -> str:
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


# noinspection PyUnusedLocal
def reports_menu(session: Session, form: cgi.FieldStorage) -> str:
    """Offer a menu of reports."""

    if not session.authorized_for_reports():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_REPORT)
    return cc_report.offer_report_menu(session)


def offer_report(session: Session, form: cgi.FieldStorage) -> str:
    """Offer configuration options for a single report."""

    if not session.authorized_for_reports():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_REPORT)
    return cc_report.offer_individual_report(session, form)


def provide_report(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Serve up a configured report."""

    if not session.authorized_for_reports():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_REPORT)
    return cc_report.provide_report(session, form)
    # ... unusual: manages the content type itself


# noinspection PyUnusedLocal
def offer_regenerate_summary_tables(session: Session,
                                    form: cgi.FieldStorage) -> str:
    """Ask for confirmation to regenerate summary tables."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    return pls.WEBSTART + """
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
    ) + WEBEND


# noinspection PyUnusedLocal
def regenerate_summary_tables(session: Session, form: cgi.FieldStorage) -> str:
    """Drop and regenerated cached/temporary summary data tables."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    success, errormsg = make_summary_tables()
    if success:
        return cc_html.simple_success_message("Summary tables regenerated.")
    else:
        return cc_html.fail_with_error_stay_logged_in(
            "Couldn’t regenerate summary tables. Error was: " + errormsg)


# noinspection PyUnusedLocal
def inspect_table_defs(session: Session, form: cgi.FieldStorage) -> str:
    """Inspect table definitions with field comments."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    return get_descriptions_comments_html(include_views=False)


# noinspection PyUnusedLocal
def inspect_table_view_defs(session: Session, form: cgi.FieldStorage) -> str:
    """Inspect table and view definitions with field comments."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    return get_descriptions_comments_html(include_views=True)


# noinspection PyUnusedLocal
def offer_basic_dump(session: Session, form: cgi.FieldStorage) -> str:
    """Offer options for a basic research data dump."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    classes = cc_task.get_all_task_classes()
    possible_tasks = "".join([
        """
            <label>
                <input type="checkbox" name="{PARAM.TASKTYPES}"
                    value="{tablename}" checked>
                {shortname}
            </label><br>
        """.format(PARAM=PARAM,
                   tablename=cls.tablename,
                   shortname=cls.shortname)
        for cls in classes])

    return pls.WEBSTART + """
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
    ) + WEBEND


def basic_dump(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
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
    classes = cc_task.get_all_task_classes()
    processed_tables = []
    for cls in classes:
        if dump_type == VALUE.DUMPTYPE_AS_TASK_FILTER:
            if not cls.filter_allows_task_type(session):
                continue
        table = cls.tablename
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
    filename = "CamCOPS_dump_" + format_datetime(
        pls.NOW_LOCAL_TZ,
        DATEFORMAT.FILENAME
    ) + ".zip"
    # atypical content type
    return ws.zip_result(zip_contents, [], filename)


# noinspection PyUnusedLocal
def offer_table_dump(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form to request dump of table data."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    # POST, not GET, or the URL exceeds the Apache limit
    html = pls.WEBSTART + """
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
        html += """
            <label>
                <input type="checkbox" name="{}" value="{}" {}>{}
            </label><br>
        """.format(name, x["name"], checked, x["name"])

    html += """
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
    return html + WEBEND


def serve_table_dump(session: Session, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Serve a dump of table +/- view data."""

    if not session.authorized_to_dump():
        return cc_html.fail_with_error_stay_logged_in(CANNOT_DUMP)
    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    tables = (
        ws.get_cgi_parameter_list(form, PARAM.TABLES) +
        ws.get_cgi_parameter_list(form, PARAM.VIEWS) +
        ws.get_cgi_parameter_list(form, PARAM.TABLES_BLOB)
    )
    if outputtype == VALUE.OUTPUTTYPE_SQL:
        filename = "CamCOPS_dump_" + format_datetime(
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
        filename = "CamCOPS_dump_" + format_datetime(
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


# noinspection PyUnusedLocal
def offer_audit_trail_options(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form to request audit trail."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return pls.WEBSTART + """
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


def view_audit_trail(session: Session, form: cgi.FieldStorage) -> str:
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
            , user_id
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
    html = pls.WEBSTART + """
        {user}
        <h1>Audit trail</h1>
        <h2>
            Conditions: nrows={nrows}, start_datetime={start_datetime},
            end_datetime={end_datetime}
        </h2>
    """.format(
        user=session.get_current_user_html(),
        nrows=nrows,
        start_datetime=format_datetime(start_datetime,
                                       DATEFORMAT.ISO8601_DATE_ONLY),
        end_datetime=format_datetime(end_datetime,
                                     DATEFORMAT.ISO8601_DATE_ONLY),
    ) + ws.html_table_from_query(rows, descriptions) + WEBEND
    return html


# noinspection PyUnusedLocal
def offer_hl7_log_options(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form to request HL7 message log view."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return pls.WEBSTART + """
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


def view_hl7_log(session: Session, form: cgi.FieldStorage) -> str:
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
    html = pls.WEBSTART + """
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
        start_datetime=format_datetime(start_datetime,
                                       DATEFORMAT.ISO8601_DATE_ONLY),
        end_datetime=format_datetime(end_datetime,
                                     DATEFORMAT.ISO8601_DATE_ONLY),
    )
    html += cc_hl7.HL7Message.get_html_header_row(showmessage=showmessage,
                                                  showreply=showreply)
    for pk in pks:
        hl7msg = cc_hl7.HL7Message(pk)
        html += hl7msg.get_html_data_row(showmessage=showmessage,
                                         showreply=showreply)
    return html + """
        </table>
    """ + WEBEND


# noinspection PyUnusedLocal
def offer_hl7_run_options(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form to request HL7 run log view."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return pls.WEBSTART + """
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


def view_hl7_run(session: Session, form: cgi.FieldStorage) -> str:
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

    html = pls.WEBSTART + """
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
        start_datetime=format_datetime(start_datetime,
                                       DATEFORMAT.ISO8601_DATE_ONLY),
        end_datetime=format_datetime(end_datetime,
                                     DATEFORMAT.ISO8601_DATE_ONLY),
    )
    html += cc_hl7.HL7Run.get_html_header_row()
    for pk in pks:
        hl7run = cc_hl7.HL7Run(pk)
        html += hl7run.get_html_data_row()
    return html + """
        </table>
    """ + WEBEND


# noinspection PyUnusedLocal
def offer_introspection(session: Session, form: cgi.FieldStorage) -> str:
    """HTML form to offer CamCOPS server source code."""

    if not pls.INTROSPECTION:
        return cc_html.fail_with_error_stay_logged_in(NO_INTROSPECTION_MSG)
    html = pls.WEBSTART + """
        {user}
        <h1>Introspection into CamCOPS source code</h1>
    """.format(
        user=session.get_current_user_html(),
    )
    for ft in pls.INTROSPECTION_FILES:
        html += """
            <div>
                <a href="{url}">{prettypath}</a>
            </div>
        """.format(
            url=get_url_introspect(ft.searchterm),
            prettypath=ft.prettypath,
        )
    return html + WEBEND


# noinspection PyUnusedLocal
def introspect(session: Session, form: cgi.FieldStorage) -> str:
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
    # log.debug("INTROSPECTION: " + str(ft))
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
        log.debug("INTROSPECTION ERROR: " + str(e))
        return cc_html.fail_with_error_not_logged_in(INTROSPECTION_FAILED_MSG)
    body = pygments.highlight(code, lexer, formatter)
    css = formatter.get_style_defs('.highlight')
    return """
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


def add_special_note(session: Session, form: cgi.FieldStorage) -> str:
    """Add a special note to a task (after confirmation)."""

    if not session.authorized_to_add_special_note():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 2
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    note = ws.get_cgi_parameter_str(form, PARAM.NOTE)
    task = cc_task.task_factory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    textarea = ""
    if confirmation_sequence == n_confirmations - 1:
        textarea = """
                <textarea name="{PARAM.NOTE}" rows="20" cols="80"></textarea>
                <br>
        """.format(
            PARAM=PARAM,
        )
    if confirmation_sequence < n_confirmations:
        return pls.WEBSTART + """
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
        ) + WEBEND
    # If we get here, we'll apply the note.
    task.apply_special_note(note, session.user_id)
    return cc_html.simple_success_message(
        "Note applied ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(cc_task.get_url_task_html(tablename, serverpk))
    )


def erase_task(session: Session, form: cgi.FieldStorage) -> str:
    """Wipe all data from a task (after confirmation).

    Leaves the task record as a placeholder.
    """

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    task = cc_task.task_factory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if task.is_erased():
        return cc_html.fail_with_error_stay_logged_in("Task already erased.")
    if task.is_live_on_tablet():
        return cc_html.fail_with_error_stay_logged_in(ERROR_TASK_LIVE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    if confirmation_sequence < n_confirmations:
        return pls.WEBSTART + """
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
        ) + WEBEND
    # If we get here, we'll do the erasure.
    task.manually_erase(session.user_id)
    return cc_html.simple_success_message(
        "Task erased ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(cc_task.get_url_task_html(tablename, serverpk))
    )


def delete_patient(session: Session, form: cgi.FieldStorage) -> str:
    """Completely delete all data from a patient (after confirmation)."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    patient_server_pks = cc_patient.get_patient_server_pks_by_idnum(
        which_idnum, idnum_value, current_only=False)
    if which_idnum is not None or idnum_value is not None:
        # A patient was asked for...
        if not patient_server_pks:
            # ... but not found
            return cc_html.fail_with_error_stay_logged_in(
                "No such patient found.")
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = ""
        if which_idnum is not None and idnum_value is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                cc_task.gen_tasks_for_patient_deletion(which_idnum,
                                                       idnum_value))
        if confirmation_sequence > 0:
            warning = """
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO ERASE THIS PATIENT AND
                    ALL ASSOCIATED TASKS?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            patient_picker_or_label = """
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
            patient_picker_or_label = """
                ID number: {which_idnum_picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}"
                        value="{idnum_value}">
            """.format(
                PARAM=PARAM,
                which_idnum_picker=cc_html.get_html_which_idnum_picker(
                    PARAM.WHICH_IDNUM, selected=which_idnum),
                idnum_value="" if idnum_value is None else idnum_value,
            )
        return pls.WEBSTART + """
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
        ) + WEBEND
    if not patient_server_pks:
        return cc_html.fail_with_error_stay_logged_in("No such patient found.")
    # If we get here, we'll do the erasure.
    # Delete tasks (with subtables)
    for cls in cc_task.get_all_task_classes():
        tablename = cls.tablename
        serverpks = cls.get_task_pks_for_patient_deletion(which_idnum,
                                                          idnum_value)
        for serverpk in serverpks:
            task = cc_task.task_factory(tablename, serverpk)
            task.delete_entirely()
    # Delete patients
    for ppk in patient_server_pks:
        pls.db.db_exec("DELETE FROM patient WHERE _pk = ?", ppk)
        audit("Patient deleted", patient_server_pk=ppk)
    msg = "Patient with idnum{} = {} and associated tasks DELETED".format(
        which_idnum, idnum_value)
    audit(msg)
    return cc_html.simple_success_message(msg)


def info_html_for_patient_edit(title: str,
                               display: str,
                               param: str,
                               value: Optional[str],
                               oldvalue: Optional[str]) -> str:
    different = value != oldvalue
    newblank = (value is None or value == "")
    oldblank = (oldvalue is None or oldvalue == "")
    changetonull = different and (newblank and not oldblank)
    titleclass = ' class="important"' if changetonull else ''
    spanclass = ' class="important"' if different else ''
    return """
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


def edit_patient(session: Session, form: cgi.FieldStorage) -> str:
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
    changes["dob"] = format_datetime(
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
    n_confirmations = 2
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    patient = cc_patient.Patient(patient_server_pk)
    if patient.get_pk() is None:
        return cc_html.fail_with_error_stay_logged_in(
            "No such patient found.")
    if not patient.is_preserved():
        return cc_html.fail_with_error_stay_logged_in(
            "Patient record is still live on tablet; cannot edit.")
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
            cc_task.gen_tasks_using_patient(
                patient.id, patient.get_device_id(), patient.get_era()))
        if confirmation_sequence > 0:
            warning = """
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
                                           patient.forename) +
                info_html_for_patient_edit("Surname", changes["surname"],
                                           PARAM.SURNAME, changes["surname"],
                                           patient.surname) +
                info_html_for_patient_edit("DOB", changes["dob"],
                                           PARAM.DOB, changes["dob"],
                                           patient.dob) +
                info_html_for_patient_edit("Sex", changes["sex"],
                                           PARAM.SEX, changes["sex"],
                                           patient.sex) +
                info_html_for_patient_edit("Address", changes["address"],
                                           PARAM.ADDRESS, changes["address"],
                                           patient.address) +
                info_html_for_patient_edit("GP", changes["gp"],
                                           PARAM.GP, changes["gp"],
                                           patient.gp) +
                info_html_for_patient_edit("Other", changes["other"],
                                           PARAM.OTHER, changes["other"],
                                           patient.other)
            )
            for n in range(1, NUMBER_OF_IDNUMS + 1):
                desc = pls.get_id_desc(n)
                details += info_html_for_patient_edit(
                    "ID number {} ({})".format(n, desc),
                    changes["idnum" + str(n)],
                    PARAM.IDNUM_PREFIX + str(n),
                    changes["idnum" + str(n)],
                    patient.get_idnum(n))
        else:
            warning = ""
            dob_for_html = format_datetime_string(
                patient.dob, DATEFORMAT.ISO8601_DATE_ONLY, default="")
            details = """
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
                details += """
                    ID number {n} ({desc}):
                    <input type="number" name="{paramprefix}{n}"
                            value="{value}"><br>
                """.format(
                    n=n,
                    desc=pls.get_id_desc(n),
                    paramprefix=PARAM.IDNUM_PREFIX,
                    value=patient.get_idnum(n),
                )
        return pls.WEBSTART + """
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
        ) + WEBEND
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
            changemessages.append(" {key}, {oldval} → {newval}".format(
                key=k,
                oldval=oldval,
                newval=v
            ))
            setattr(patient, k, v)
    # Valid?
    if (not patient.satisfies_upload_id_policy() or
            not patient.satisfies_finalize_id_policy()):
        return cc_html.fail_with_error_stay_logged_in(
            "New version does not satisfy uploading or finalizing policy; "
            "no changes made.")
    # Anything to do?
    if not changemessages:
        return cc_html.simple_success_message("No changes made.")
    # If we get here, we'll make the change.
    patient.save()
    msg = "Patient details edited. Changes: "
    msg += "; ".join(changemessages) + "."
    patient.apply_special_note(msg, session.user_id,
                               audit_msg="Patient details edited")
    for task in cc_task.gen_tasks_using_patient(patient.id,
                                                patient.get_device_id(),
                                                patient.get_era()):
        # Patient details changed, so resend any tasks via HL7
        task.delete_from_hl7_message_log()
    return cc_html.simple_success_message(msg)


def task_list_from_generator(generator: Iterable[Task]) -> str:
    tasklist_html = ""
    for task in generator:
        tasklist_html += task.get_task_list_row()
    return """
        {TASK_LIST_HEADER}
        {tasklist_html}
        {TASK_LIST_FOOTER}
    """.format(
        TASK_LIST_HEADER=TASK_LIST_HEADER,
        tasklist_html=tasklist_html,
        TASK_LIST_FOOTER=TASK_LIST_FOOTER,
    )


def forcibly_finalize(session: Session, form: cgi.FieldStorage) -> str:
    """Force-finalize all live (_era == ERA_NOW) records from a device."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    device_id = ws.get_cgi_parameter_int(form, PARAM.DEVICE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    if confirmation_sequence > 0 and device_id is None:
        return cc_html.fail_with_error_stay_logged_in("Device not specified.")
    d = None
    if device_id is not None:
        # A device was asked for...
        d = Device(device_id)
        if not d.is_valid():
            # ... but not found
            return cc_html.fail_with_error_stay_logged_in(
                "No such device found.")
        device_id = d.id
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = ""
        if device_id is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                cc_task.gen_tasks_live_on_tablet(device_id))
        if confirmation_sequence > 0:
            warning = """
                <div class="warning">
                    <b>ARE YOU {really} SURE YOU WANT TO FORCIBLY
                    PRESERVE/FINALIZE RECORDS FROM THIS DEVICE?</b>
                </div>
            """.format(
                really=" REALLY" * confirmation_sequence,
            )
            device_picker_or_label = """
                <input type="hidden" name="{PARAM.DEVICE}"
                        value="{device_id}">
                <b>{device_nicename}</b>
            """.format(
                PARAM=PARAM,
                device_id=device_id,
                device_nicename=(ws.webify(d.get_friendly_name_and_id())
                                 if d is not None else ''),
            )
        else:
            warning = ""
            device_picker_or_label = get_device_filter_dropdown(device_id)
        return pls.WEBSTART + """
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
        ) + WEBEND

    # If we get here, we'll do the forced finalization.
    # Force-finalize tasks (with subtables)
    tables = [
        # non-task but tablet-based tables
        cc_patient.Patient.TABLENAME,
        cc_blob.Blob.TABLENAME,
        DeviceStoredVar.TABLENAME,
    ]
    for cls in cc_task.get_all_task_classes():
        tables.append(cls.tablename)
        tables.extend(cls.get_extra_table_names())
    for t in tables:
        cc_db.forcibly_preserve_client_table(t, device_id, pls.session.user_id)
    # Field names are different in server-side tables, so they need special
    # handling:
    forcibly_preserve_special_notes(device_id)
    # OK, done.
    msg = "Live records for device {} forcibly finalized".format(device_id)
    audit(msg)
    return cc_html.simple_success_message(msg)


def enter_new_password(session: Session, form: cgi.FieldStorage) -> str:
    """Ask for a new password."""

    user_to_change = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    if (user_to_change != session.username and
            not session.authorized_as_superuser()):
        return cc_html.fail_with_error_stay_logged_in(
            CAN_ONLY_CHANGE_OWN_PASSWORD)
    return cc_user.enter_new_password(
        session,
        user_to_change,
        user_to_change != session.username
    )


def change_password(session: Session, form: cgi.FieldStorage) -> str:
    """Implement a password change."""

    user_to_change = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    if user_to_change is None or session.username is None:
        return cc_html.fail_with_error_stay_logged_in(MISSING_PARAMETERS_MSG)
    if (user_to_change != session.username and
            not session.authorized_as_superuser()):
        return cc_html.fail_with_error_stay_logged_in(
            CAN_ONLY_CHANGE_OWN_PASSWORD)
    return cc_user.change_password(
        user_to_change,
        form,
        user_to_change != session.username
    )


# noinspection PyUnusedLocal
def manage_users(session: Session, form: cgi.FieldStorage) -> str:
    """Offer user management menu."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.manage_users(session)


# noinspection PyUnusedLocal
def ask_to_add_user(session: Session, form: cgi.FieldStorage) -> str:
    """Ask for details to add a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.ask_to_add_user(session)


def add_user(session: Session, form: cgi.FieldStorage) -> str:
    """Adds a user using the details supplied."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.add_user(form)


def edit_user(session: Session, form: cgi.FieldStorage) -> str:
    """Offers a user editing page."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_edit = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.edit_user(session, user_to_edit)


def change_user(session: Session, form: cgi.FieldStorage) -> str:
    """Applies edits to a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return cc_user.change_user(form)


def ask_delete_user(session: Session, form: cgi.FieldStorage) -> str:
    """Asks for confirmation to delete a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_delete = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.ask_delete_user(session, user_to_delete)


def delete_user(session: Session, form: cgi.FieldStorage) -> str:
    """Deletes a user."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_delete = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.delete_user(user_to_delete)


def enable_user(session: Session, form: cgi.FieldStorage) -> str:
    """Enables a user (unlocks, clears login failures)."""

    if not session.authorized_as_superuser():
        return cc_html.fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_enable = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return cc_user.enable_user_webview(user_to_enable)


# noinspection PyUnusedLocal
def crash(session: Session, form: cgi.FieldStorage) -> str:
    """Deliberately raises an exception."""

    raise RuntimeError("Deliberately crashed. Should not affect other "
                       "processes.")


# =============================================================================
# Ancillary to the main pages/actions
# =============================================================================

def get_tracker(session: Session, form: cgi.FieldStorage) -> Tracker:
    """Returns a Tracker() object specified by the CGI form."""

    task_tablename_list = ws.get_cgi_parameter_list(form, PARAM.TASKTYPES)
    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    return Tracker(
        session,
        task_tablename_list,
        which_idnum,
        idnum_value,
        start_datetime,
        end_datetime
    )


def get_clinicaltextview(session: Session,
                         form: cgi.FieldStorage) -> ClinicalTextView:
    """Returns a ClinicalTextView() object defined by the CGI form."""

    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    start_datetime = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
    end_datetime = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
    return ClinicalTextView(
        session,
        which_idnum,
        idnum_value,
        start_datetime,
        end_datetime
    )


def tsv_escape(x: Any) -> str:
    if x is None:
        return ""
    if not isinstance(x, str):
        x = str(x)
    return x.replace("\t", "\\t").replace("\n", "\\n")


def get_tsv_header_from_dict(d: Dict) -> str:
    """Returns a TSV header line from a dictionary."""
    return "\t".join([tsv_escape(x) for x in d.keys()])


def get_tsv_line_from_dict(d: Dict) -> str:
    """Returns a TSV data line from a dictionary."""
    return "\t".join([tsv_escape(x) for x in d.values()])


# =============================================================================
# URLs
# =============================================================================

def get_url_next_page(ntasks: int) -> str:
    """URL to move to next page in task list."""
    return (
        cc_html.get_generic_action_url(ACTION.NEXT_PAGE) +
        cc_html.get_url_field_value_pair(PARAM.NTASKS, ntasks)
    )


def get_url_last_page(ntasks: int) -> str:
    """URL to move to last page in task list."""
    return (
        cc_html.get_generic_action_url(ACTION.LAST_PAGE) +
        cc_html.get_url_field_value_pair(PARAM.NTASKS, ntasks)
    )


def get_url_introspect(filename: str) -> str:
    """URL to view specific source code file."""
    return (
        cc_html.get_generic_action_url(ACTION.INTROSPECT) +
        cc_html.get_url_field_value_pair(PARAM.FILENAME, filename)
    )


# =============================================================================
# Redirection
# =============================================================================

def redirect_to(location: str) -> WSGI_TUPLE_TYPE_WITH_STATUS:
    """Return an HTTP response redirecting to another location.

    Typically, this is used to allow a user to log in again after a timeout,
    but then to redirect where the user was wanting to go.
    """
    status = "303 See Other"
    extraheaders = [("Location", location)]
    contenttype = "text/plain"
    output = "Redirecting to {}".format(location)
    return contenttype, extraheaders, output, status


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


def main_http_processor(env: Dict[str, str]) \
        -> Union[
            str,
            WSGI_TUPLE_TYPE,
            WSGI_TUPLE_TYPE_WITH_STATUS]:
    """Main processor of HTTP requests."""

    # Sessions details are already in pls.session

    # -------------------------------------------------------------------------
    # Process requested action
    # -------------------------------------------------------------------------
    form = ws.get_cgi_fieldstorage_from_wsgi_env(env)
    action = ws.get_cgi_parameter_str(form, PARAM.ACTION)

    log.info(
        "Incoming connection from IP={i}, port={p}, user_id={ui}, "
        "username={un}, action={a}".format(
            i=pls.remote_addr,
            p=pls.remote_port,
            ui=pls.session.user_id,
            un=pls.session.username,
            a=action,
        )
    )

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
                pls.session, pls.session.username,
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
# Functions suitable for calling from the command line or webview
# =============================================================================

def write_descriptions_comments(file: typing.io.TextIO,
                                include_views: bool = False) -> None:
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
    print(COMMON_HEAD, file=file)
    # don't used fixed-width tables; they truncate contents
    print("""
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
        outstring = "<tr>"
        for i in range(len(row)):
            outstring += "<td>{}</td>".format(ws.webify(row[i]))
        outstring += "</tr>"
        print(outstring, file=file)
    print("""
            </table>
        </body>
    """, file=file)

    # Other methods:
    # - To view columns with comments:
    #        SHOW FULL COLUMNS FROM tablename;
    # - or other methods at http://stackoverflow.com/questions/6752169


def get_descriptions_comments_html(include_views: bool = False) -> str:
    """Returns HTML of database field descriptions/comments."""
    f = io.StringIO()
    write_descriptions_comments(f, include_views)
    return f.getvalue()


def get_database_title() -> str:
    """Returns database title, or ""."""
    if not pls.DATABASE_TITLE:
        return ""
    return pls.DATABASE_TITLE


def make_summary_tables(from_console: bool = True) -> Tuple[bool, str]:
    """Drop and rebuild summary tables."""
    # Don't use print; this may run from the web interface. Use the log.
    locked_error = (
        "make_summary_tables: couldn't open lockfile ({}.lock); "
        "may not have permissions, or file may be locked by "
        "another process; aborting".format(
            pls.SUMMARY_TABLES_LOCKFILE)
    )
    misconfigured_error = (
        "make_summary_tables: No SUMMARY_TABLES_LOCKFILE "
        "specified in config; can't proceed"
    )
    if not pls.SUMMARY_TABLES_LOCKFILE:
        log.error(misconfigured_error)
        return False, misconfigured_error
    lock = lockfile.FileLock(pls.SUMMARY_TABLES_LOCKFILE)
    if lock.is_locked():
        log.warning(locked_error)
        return False, locked_error
    try:
        with lock:
            log.info("MAKING SUMMARY TABLES")
            for cls in cc_task.get_all_task_classes():
                cls.make_summary_table()
            audit("Created/recreated summary tables",
                  from_console=from_console)
            pls.db.commit()  # make_summary_tables commit (prior to releasing
            # file lock)
        return True, ""
    except lockfile.LockFailed:
        log.warning(locked_error)
        return False, locked_error


# =============================================================================
# WSGI application
# =============================================================================

def webview_application(environ: Dict[str, str],
                        start_response: Callable[[str, HEADERS_TYPE], None]) \
        -> Iterable[bytes]:
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
    cookies = pls.session.get_cookies()
    extraheaders.extend(cookies)
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
# Unit tests
# =============================================================================

def unit_tests() -> None:
    """Unit tests for camcops.py"""
    session = cc_session.Session()
    form = cgi.FieldStorage()
    # suboptimal tests, as form isn't tailed to these things

    # skip: ask_user
    # skip: ask_user_password
    unit_test_ignore("", login_failed, "test_redirect")
    unit_test_ignore("", account_locked, get_now_localtz(), "test_redirect")
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

    f = io.StringIO()
    unit_test_ignore("", write_descriptions_comments, f, False)
    unit_test_ignore("", write_descriptions_comments, f, True)
    # ignored: export_descriptions_comments
    unit_test_ignore("", get_database_title)
    # ignored: reset_storedvars
    # ignored: make_summary_tables
    # ignored: make_superuser
    # ignored: reset_password
    # ignored: enable_user_cli
