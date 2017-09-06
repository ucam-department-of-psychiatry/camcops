#!/usr/bin/env python
# camcops_server/webview.py

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

Quick tutorial on Pyramid views:

-   The configurator registers routes, and routes have URLs associated with
    them. Those URLs can be templatized, e.g. to accept numerical parameters.
    The configurator associates view callables ("views" for short) with routes,
    and one method for doing that is an automatic scan via Venusian for views
    decorated with @view_config().

-   All views take a Request object and return a Response or raise an exception
    that Pyramid will translate into a Response.

-   Having matched a route, Pyramid uses its "view lookup" process to choose
    one from potentially several views. For example, a single route might be
    associated with:

        @view_config(route_name="myroute")
        def myroute_default(req: Request) -> Response:
            pass

        @view_config(route_name="myroute", method="POST")
        def myroute_post(req: Request) -> Response:
            pass

    In this example, POST requests will go to the second; everything else will
    go to the first. Pyramid's view lookup rule is essentially: if multiple
    views match, choose the one with the most specifiers.

-   Specifiers include:

        route_name=ROUTENAME

            the route

        request_method="POST"

            requires HTTP GET, POST, etc.

        request_param="XXX"

            ... requires the presence of a GET/POST variable with this name in
            the request.params dictionary

        request_param="XXX=YYY"

            ... requires the presence of a GET/POST variable called XXX whose
            value is YYY, in the request.params dictionary

        match_param="XXX=YYY"

            .. requires the presence of this key/value pair in
            request.matchdict, which contains parameters from the URL

    https://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator.add_view  # noqa

-   Getting parameters

        request.params

            ... parameters from HTTP GET or POST, including both the query
            string (as in http://somewhere/path?key=value) and the body (e.g.
            POST).

        request.matchdict

            ... parameters from the URL, via URL dispatch; see
            https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#urldispatch-chapter  # noqa

-   Regarding rendering:

    There might be some simplicity benefits from converting to a template
    system like Mako. On the downside, that would entail a bit more work;
    likely a minor performance hit (relative to plain Python string rendering);
    and a loss of type checking. The type checking is also why we prefer:

        html = " ... {param_blah} ...".format(param_blah=PARAM.BLAH)

    to

        html = " ... {PARAM.BLAH} ...".format(PARAM=PARAM)

    as in the first situation, PyCharm will check that "BLAH" is present in
    "PARAM", and in the second it won't. Automatic checking is worth a lot.

"""

import cgi
import codecs
import collections
import datetime
import io
import logging
import typing
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import zipfile

from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_web import HEADERS_TYPE, WSGI_TUPLE_TYPE
from deform.exception import ValidationFailure
import pyramid.httpexceptions as exc
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
)
from pyramid.renderers import render, render_to_response
from pyramid.response import Response
from pyramid.security import Authenticated, NO_PERMISSION_REQUIRED
import pygments
import pygments.lexers
import pygments.lexers.web
import pygments.formatters
from sqlalchemy.sql.expression import desc, func

from .cc_audit import audit, AuditEntry
from .cc_constants import (
    ACTION,
    CAMCOPS_URL,
    DATEFORMAT,
    PARAM,
    RESTRICTED_WARNING,
    VALUE,
)
from .cc_blob import Blob
from camcops_server.cc_modules import cc_db
from .cc_device import (
    Device,
    get_device_filter_dropdown,
)
from .cc_dt import (
    get_now_localtz,
    format_datetime,
    format_datetime_string
)
from .cc_dump import (
    get_database_dump_as_sql,
    get_multiple_views_data_as_tsv_zip,
    get_permitted_tables_views_sorted_labelled,
    NOTHING_VALID_SPECIFIED,
)
from .cc_hl7 import HL7Message, HL7Run
from .cc_html import (
    get_generic_action_url,
    get_html_sex_picker,
    get_html_which_idnum_picker,
    get_url_enter_new_password,
    get_url_field_value_pair,
    get_url_main_menu,
)
from .cc_patient import Patient
from .cc_plot import ccplot_do_nothing
from .cc_policy import (
    get_finalize_id_policy_principal_numeric_id,
    get_upload_id_policy_principal_numeric_id,
    id_policies_valid,
)
from .cc_pyramid import (
    CamcopsPage,
    HttpMethod,
    PageUrl,
    PdfResponse,
    Permission,
    Routes,
    SqlalchemyOrmPage,
    SUBMIT,
    ViewArg,
    ViewParam,
    XmlResponse,
)
from .cc_report import (
    offer_individual_report,
    offer_report_menu,
    serve_report,
)
from .cc_request import CamcopsRequest
from .cc_session import CamcopsSession
from .cc_specialnote import SpecialNote
from .cc_storedvar import DeviceStoredVar
from .cc_task import (
    gen_tasks_for_patient_deletion,
    gen_tasks_live_on_tablet,
    gen_tasks_matching_session_filter,
    gen_tasks_using_patient,
    get_url_task_html,
    Task,
)
from .cc_taskfactory import task_factory, TaskCollection
from .cc_tracker import ClinicalTextView, Tracker
from .cc_unittest import unit_test_ignore
from .cc_user import (
    add_user,
    ask_delete_user_html,
    ask_to_add_user_html,
    change_user,
    delete_user,
    edit_user_form,
    enable_user_webview,
    manage_users_html,
    MINIMUM_PASSWORD_LENGTH,
    SecurityAccountLockout,
    SecurityLoginFailure,
    User,
)
from .cc_version import CAMCOPS_SERVER_VERSION
from .forms import (
    AuditTrailForm,
    ChangeOtherPasswordForm,
    ChangeOwnPasswordForm,
    DEFAULT_ROWS_PER_PAGE,
    get_head_form_html,
    HL7MessageLogForm,
    HL7RunLogForm,
    LoginForm,
    OfferTermsForm,
)

log = BraceStyleAdapter(logging.getLogger(__name__))
ccplot_do_nothing()


WSGI_TUPLE_TYPE_WITH_STATUS = Tuple[str, HEADERS_TYPE, bytes, str]
# ... contenttype, extraheaders, output, status

# =============================================================================
# Constants
# =============================================================================

ALLOWED_TASK_VIEW_TYPES = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
                           ViewArg.XML]
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


# =============================================================================
# Simple success/failure/redirection, and other snippets used by views
# =============================================================================

def simple_success(req: CamcopsRequest, msg: str,
                   extra_html: str = "") -> Response:
    """Simple success message."""
    return render_to_response("generic_success.mako",
                              dict(msg=msg,
                                   extra_html=extra_html),
                              request=req)


def simple_failure(req: CamcopsRequest, msg: str,
                   extra_html: str = "") -> Response:
    """Simple failure message."""
    return render_to_response("generic_failure.mako",
                              dict(msg=msg,
                                   extra_html=extra_html),
                              request=req)


# def query_result_html_core(req: CamcopsRequest,
#                            descriptions: Sequence[str],
#                            rows: Sequence[Sequence[Any]],
#                            null_html: str = "<i>NULL</i>") -> str:
#     return render("query_result_core.mako",
#                   dict(descriptions=descriptions,
#                        rows=rows,
#                        null_html=null_html),
#                   request=req)


# def query_result_html_orm(req: CamcopsRequest,
#                           attrnames: List[str],
#                           descriptions: List[str],
#                           orm_objects: Sequence[Sequence[Any]],
#                           null_html: str = "<i>NULL</i>") -> str:
#     return render("query_result_orm.mako",
#                   dict(attrnames=attrnames,
#                        descriptions=descriptions,
#                        orm_objects=orm_objects,
#                        null_html=null_html),
#                   request=req)


def fail_not_authorized_for_task(req: CamcopsRequest) -> Response:
    """Response given when user isn't allowed to see a specific task."""
    return simple_failure(req, "Not authorized to view that task.")


def fail_task_not_found(req: CamcopsRequest) -> Response:
    """Response given when task not found."""
    return simple_failure(req, "Task not found.")


# =============================================================================
# Error views
# =============================================================================

@notfound_view_config(renderer="not_found.mako")
def not_found(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


@view_config(context=exc.HTTPBadRequest, renderer="bad_request.mako")
def bad_request(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


# =============================================================================
# Test pages
# =============================================================================
# Not on the menus...

@view_config(route_name=Routes.TESTPAGE_PUBLIC_1,
             permission=NO_PERMISSION_REQUIRED)
def test_page_1(req: CamcopsRequest) -> Response:
    return Response("Hello! This is a public CamCOPS test page.")


@view_config(route_name=Routes.TESTPAGE_PUBLIC_2,
             renderer="testpage.mako",
             permission=Permission.SUPERUSER)
def test_page_2(req: CamcopsRequest) -> Dict[str, Any]:
    # Contains POTENTIALLY SENSITIVE test information, including environment
    # variables
    return dict(param1="world")


@view_config(route_name=Routes.TESTPAGE_PRIVATE_1)
def test_page_private_1(req: CamcopsRequest) -> Response:
    return Response("Private test page.")


# Not on the menus...
@view_config(route_name=Routes.CRASH, permission=Permission.SUPERUSER)
def crash(req: CamcopsRequest) -> Response:
    """Deliberately raises an exception."""
    raise RuntimeError("Deliberately crashed. Should not affect other "
                       "processes.")


# =============================================================================
# Authorization: login, logout, login failures, terms/conditions
# =============================================================================

@view_config(route_name=Routes.LOGIN, permission=NO_PERMISSION_REQUIRED)
# Do NOT use extra parameters for functions decorated with @view_config;
# @view_config can take functions like "def view(request)" but also
# "def view(context, request)", so if you add additional parameters, it thinks
# you're doing the latter and sends parameters accordingly.
def login_view(req: CamcopsRequest) -> Response:
    cfg = req.config
    autocomplete_password = not cfg.DISABLE_PASSWORD_AUTOCOMPLETE

    form = LoginForm(request=req, autocomplete_password=autocomplete_password)

    if SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            # log.critical("controls from POST: {!r}", controls)
            appstruct = form.validate(controls)
            # log.critical("appstruct from POST: {!r}", appstruct)
            log.debug("Validating user login.")
            ccsession = req.camcops_session
            username = appstruct.get(ViewParam.USERNAME)
            password = appstruct.get(ViewParam.PASSWORD)
            redirect_url = appstruct.get(ViewParam.REDIRECT_URL)
            # 1. If we don't have a username, let's stop quickly.
            if not username:
                ccsession.logout(req)
                return login_failed(req)
            # 2. Is the user locked?
            if SecurityAccountLockout.is_user_locked_out(req, username):
                return account_locked(req,
                                      User.user_locked_out_until(username))
            # 3. Is the username/password combination correct?
            user = User.get_user_from_username_password(
                req, username, password)  # checks password
            if user is not None and user.may_use_webviewer:
                # Successful login.
                user.login(req)  # will clear login failure record
                ccsession.login(user)
                audit(req, "Login")
            elif user is not None:
                # This means a user who can upload from tablet but who cannot
                # log in via the web front end.
                return login_failed(req)
            else:
                # Unsuccessful. Note that the username may/may not be genuine.
                SecurityLoginFailure.act_on_login_failure(req, username)
                # ... may lock the account
                # Now, call audit() before session.logout(), as the latter
                # will wipe the session IP address:
                ccsession.logout(req)
                return login_failed(req)

            # OK, logged in.
            # Redirect to the main menu, or wherever the user was heading.
            # HOWEVER, that may lead us to a "change password" or "agree terms"
            # page, via the permissions system (Permission.HAPPY or not).

            if redirect_url:
                # log.critical("Redirecting to {!r}", redirect_url)
                raise exc.HTTPFound(redirect_url)  # redirect
            raise exc.HTTPFound(req.route_url(Routes.HOME))  # redirect

        except ValidationFailure as e:
            rendered_form = e.render()

    else:
        redirect_url = req.get_str_param(ViewParam.REDIRECT_URL, "")
        # ... use default of "", because None gets serialized to "None", which
        #     gets read back as "None".
        appstruct = {ViewParam.REDIRECT_URL: redirect_url}
        # log.critical("appstruct from GET/POST: {!r}", appstruct)
        rendered_form = form.render(appstruct)

    return render_to_response(
        "login.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, form)),
        request=req
    )


def login_failed(req: CamcopsRequest) -> Response:
    """
    HTML given after login failure.
    Returned by login_view() only.
    """
    return render_to_response(
        "login_failed.mako",
        dict(),
        request=req
    )


def account_locked(req: CamcopsRequest,
                   locked_until: datetime.datetime) -> Response:
    """
    HTML given when account locked out.
    Returned by login_view() only.
    """
    return render_to_response(
        "accounted_locked.mako",
        dict(
            locked_until=format_datetime(locked_until,
                                         DATEFORMAT.LONG_DATETIME_WITH_DAY,
                                         "(never)")
        ),
        request=req
    )


@view_config(route_name=Routes.LOGOUT, renderer="logged_out.mako")
def logout(req: CamcopsRequest) -> Dict[str, Any]:
    """Logs a session out."""
    audit(req, "Logout")
    ccsession = req.camcops_session
    ccsession.logout(req)
    return dict()


@view_config(route_name=Routes.OFFER_TERMS, renderer="offer_terms.mako")
def offer_terms(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML offering terms/conditions and requesting acknowledgement."""
    form = OfferTermsForm(
        request=req,
        agree_button_text=req.wappstring("disclaimer_agree"))

    if SUBMIT in req.POST:
        req.camcops_session.agree_terms(req)
        raise exc.HTTPFound(req.route_url(Routes.HOME))  # redirect

    return dict(
        title=req.wappstring("disclaimer_title"),
        subtitle=req.wappstring("disclaimer_subtitle"),
        content=req.wappstring("disclaimer_content"),
        form=form.render(),
        head_form_html=get_head_form_html(req, form),
    )


@forbidden_view_config()
def forbidden(req: CamcopsRequest) -> Dict[str, Any]:
    if req.has_permission(Authenticated):
        user = req.user
        assert user, "Bug! Authenticated but no user...!?"
        if user.must_change_password():
            raise exc.HTTPFound(req.route_url(Routes.CHANGE_OWN_PASSWORD))
        if user.must_agree_terms():
            raise exc.HTTPFound(req.route_url(Routes.OFFER_TERMS))
    # Otherwise...
    redirect_url = req.url
    # Redirects to login page, with onwards redirection to requested
    # destination once logged in:
    querydict = {ViewParam.REDIRECT_URL: redirect_url}
    return render_to_response("forbidden.mako",
                              dict(querydict=querydict),
                              request=req)


# =============================================================================
# Changing passwords
# =============================================================================

@view_config(route_name=Routes.CHANGE_OWN_PASSWORD)
def change_own_password(req: CamcopsRequest) -> Response:
    ccsession = req.camcops_session
    expired = ccsession.user_must_change_password()
    form = ChangeOwnPasswordForm(request=req, must_differ=True)
    user = req.user
    assert user is not None
    extra_msg = ""
    if SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            new_password = appstruct.get(ViewParam.NEW_PASSWORD)
            # ... form will validate old password, etc.
            # OK
            user.set_password(req, new_password)
            return password_changed(req, user.username, own_password=True)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "change_own_password.mako",
        dict(form=rendered_form,
             expired=expired,
             extra_msg=extra_msg,
             min_pw_length=MINIMUM_PASSWORD_LENGTH,
             head_form_html=get_head_form_html(req, form)),
        request=req)


@view_config(route_name=Routes.CHANGE_OTHER_PASSWORD,
             permission=Permission.SUPERUSER,
             renderer="change_own_password.mako")
def change_other_password(req: CamcopsRequest) -> Response:
    """For administrators, to change another's password."""
    form = ChangeOtherPasswordForm(request=req)
    username = None  # for type checker
    if SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user_id = appstruct.get(ViewParam.USER_ID)
            must_change_pw = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)
            new_password = appstruct.get(ViewParam.NEW_PASSWORD)
            user = User.get_user_by_id(req.dbsession, user_id)
            if not user:
                raise exc.HTTPBadRequest(
                    "Missing user for id {}".format(user_id))
            user.set_password(req, new_password)
            if must_change_pw:
                user.force_password_change()
            return password_changed(req, user.username, own_password=False)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        user_id_str = req.get_str_param(ViewParam.USER_ID, None)
        try:
            user_id = int(user_id_str)
        except (TypeError, ValueError):
            raise exc.HTTPBadRequest("Improper user_id of {}".format(
                repr(user_id_str)))
        if user_id == req.user_id:
            # Change own password
            raise exc.HTTPFound(req.route_url(Routes.CHANGE_OWN_PASSWORD))
        other_user = User.get_user_by_id(req.dbsession, user_id)
        if other_user is None:
            raise exc.HTTPBadRequest("Missing user for id {}".format(user_id))
        username = other_user.username
        appstruct = {ViewParam.USER_ID: user_id}
        rendered_form = form.render(appstruct)
    return render_to_response(
        "change_other_password.mako",
        dict(username=username,
             form=rendered_form,
             min_pw_length=MINIMUM_PASSWORD_LENGTH,
             head_form_html=get_head_form_html(req, form)),
        request=req)


def password_changed(req: CamcopsRequest,
                     username: str,
                     own_password: bool) -> Response:
    return render_to_response("password_changed.mako",
                              dict(username=username,
                                   own_password=own_password),
                              request=req)


# =============================================================================
# Main menu; simple information things
# =============================================================================

@view_config(route_name=Routes.HOME, renderer="main_menu.mako")
def main_menu(req: CamcopsRequest) -> Dict[str, Any]:
    """Main HTML menu."""
    ccsession = req.camcops_session
    cfg = req.config
    return dict(
        authorized_as_superuser=ccsession.authorized_as_superuser(),
        authorized_for_reports=ccsession.authorized_for_reports(),
        authorized_to_dump=ccsession.authorized_to_dump(),
        camcops_url=CAMCOPS_URL,
        id_policies_valid=id_policies_valid(),
        introspection=cfg.INTROSPECTION,
        now=format_datetime(req.now_arrow,
                            DATEFORMAT.SHORT_DATETIME_SECONDS),
        server_version=CAMCOPS_SERVER_VERSION,
    )


# =============================================================================
# Tasks
# =============================================================================

@view_config(route_name=Routes.VIEW_TASKS, renderer="view_tasks.mako")
def view_tasks(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML displaying tasks and applicable filters."""
    ccsession = req.camcops_session

    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    # In principle, for some filter settings (single task, no "complete"
    # preference...) we could produce an ORM query and use SqlalchemyOrmPage,
    # which would apply LIMIT/OFFSET (or equivalent) to the query, and be
    # very nippy. In practice, this is probably an unusual setting, so we'll
    # simplify things here with a Python list regardless of the settings.

    collection = TaskCollection(req, restrict_by_session_filter=True)
    page = CamcopsPage(collection=collection.all_tasks,
                       page=page_num,
                       items_per_page=rows_per_page,
                       url_maker=PageUrl(req))

    # refresh_tasks_button = """
    #     <form class="filter" method="POST" action="{script}">
    #         <input type="hidden" name="{PARAM.ACTION}"
    #             value="{ACTION.VIEW_TASKS}">
    #         <input type="submit" value="Refresh">
    #     </form>
    # """.format(
    #     script=pls.SCRIPT_NAME,
    #     PARAM=PARAM,
    #     ACTION=ACTION,
    # )
    # http://stackoverflow.com/questions/2906582/how-to-create-an-html-button-that-acts-like-a-link  # noqa

    return dict(
        page=page,
        head_form_html="", # ***
        no_patient_selected_and_user_restricted=(
            not ccsession.user_may_view_all_patients_when_unfiltered() and
            not ccsession.any_specific_patient_filtering()
        ),
    )


def change_number_to_view(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Change the number of tasks visible on a single screen."""

    session.change_number_to_view(form)
    return view_tasks(session, form)


def first_page(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Navigate to the first page of tasks."""

    session.first_page()
    return view_tasks(session, form)


def previous_page(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Navigate to the previous page of tasks."""

    session.previous_page()
    return view_tasks(session, form)


def next_page(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Navigate to the next page of tasks."""

    ntasks = ws.get_cgi_parameter_int(form, PARAM.NTASKS)
    session.next_page(ntasks)
    return view_tasks(session, form)


def last_page(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Navigate to the last page of tasks."""
    ntasks = ws.get_cgi_parameter_int(form, PARAM.NTASKS)
    session.last_page(ntasks)
    return view_tasks(session, form)


@view_config(route_name=Routes.TASK)
def serve_task(req: CamcopsRequest) -> Response:
    """Serves an individual task."""
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML, lower=True)
    tablename = req.get_str_param(ViewParam.TABLENAME)
    server_pk = req.get_int_param(ViewParam.SERVER_PK)
    anonymise = req.get_bool_param(ViewParam.ANONYMISE, False)

    if viewtype not in ALLOWED_TASK_VIEW_TYPES:
        raise exc.HTTPBadRequest(
            "Bad output type: {!r} (permissible: {!r}".format(
                viewtype, ALLOWED_TASK_VIEW_TYPES))

    task = task_factory(req, tablename, server_pk)

    if task is None:
        raise exc.HTTPBadRequest(
            "Task not found or not permitted: tablename={!r}, "
            "server_pk={!r}".format(tablename, server_pk))

    task.audit(req, "Viewed " + viewtype.upper())

    if viewtype == ViewArg.HTML:
        return Response(
            task.get_html(req=req, anonymise=anonymise)
        )
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            content=task.get_pdf(req),
            filename=task.suggested_pdf_filename()
        )
    elif viewtype == VALUE.OUTPUTTYPE_PDFHTML:  # debugging option
        return Response(
            task.get_pdf_html(req)
        )
    elif viewtype == VALUE.OUTPUTTYPE_XML:
        include_blobs = req.get_bool_param(ViewParam.INCLUDE_BLOBS, True)
        include_calculated = req.get_bool_param(ViewParam.INCLUDE_CALCULATED,
                                                True)
        include_patient = req.get_bool_param(ViewParam.INCLUDE_PATIENT, True)
        include_comments = req.get_bool_param(ViewParam.INCLUDE_COMMENTS, True)
        return XmlResponse(
            task.get_xml(req=req,
                         include_blobs=include_blobs,
                         include_calculated=include_calculated,
                         include_patient=include_patient,
                         include_comments=include_comments)
        )
    else:
        assert False, "Bug in logic above"


# =============================================================================
# Trackers, CTVs
# =============================================================================

# noinspection PyUnusedLocal
def choose_tracker(session: CamcopsSession, form: cgi.FieldStorage) -> str:
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
        which_idnum_picker=get_html_which_idnum_picker(PARAM.WHICH_IDNUM),
        PARAM=PARAM,
    )
    classes = get_all_task_classes()
    for cls in classes:
        if cls.provides_trackers:
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


def serve_tracker(session: CamcopsSession, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Serve up a tracker."""

    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    allowed_types = [VALUE.OUTPUTTYPE_PDF,
                     VALUE.OUTPUTTYPE_HTML,
                     VALUE.OUTPUTTYPE_XML]
    if outputtype not in allowed_types:
        return fail_with_error_stay_logged_in(
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
def choose_clinicaltextview(session: CamcopsSession, form: cgi.FieldStorage) -> str:
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
        which_idnum_picker=get_html_which_idnum_picker(PARAM.WHICH_IDNUM),
        PARAM=PARAM,
        VALUE=VALUE,
        ACTION=ACTION,
    )
    return html + WEBEND


def serve_clinicaltextview(session: CamcopsSession, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Returns a CTV."""

    outputtype = ws.get_cgi_parameter_str(form, PARAM.OUTPUTTYPE)
    if outputtype is not None:
        outputtype = outputtype.lower()
    allowed_types = [VALUE.OUTPUTTYPE_PDF,
                     VALUE.OUTPUTTYPE_HTML,
                     VALUE.OUTPUTTYPE_XML]
    if outputtype not in allowed_types:
        return fail_with_error_stay_logged_in(
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


def change_task_filters(session: CamcopsSession, form: cgi.FieldStorage) -> str:
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


# =============================================================================
# Reports
# =============================================================================

# noinspection PyUnusedLocal
def reports_menu(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Offer a menu of reports."""

    if not session.authorized_for_reports():
        return fail_with_error_stay_logged_in(CANNOT_REPORT)
    return offer_report_menu(session)


def offer_report(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Offer configuration options for a single report."""

    if not session.authorized_for_reports():
        return fail_with_error_stay_logged_in(CANNOT_REPORT)
    return offer_individual_report(session, form)


def provide_report(session: CamcopsSession,
                   form: cgi.FieldStorage) -> Union[str, WSGI_TUPLE_TYPE]:
    """Serve up a configured report."""

    if not session.authorized_for_reports():
        return fail_with_error_stay_logged_in(CANNOT_REPORT)
    return serve_report(session, form)
    # ... unusual: manages the content type itself


# =============================================================================
# Research downloads
# =============================================================================

# noinspection PyUnusedLocal
def offer_basic_dump(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Offer options for a basic research data dump."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
    classes = get_all_task_classes()
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
        view_tasks=get_generic_action_url(ACTION.VIEW_TASKS),
        table_dump=get_generic_action_url(ACTION.OFFER_TABLE_DUMP),
        possible_tasks=possible_tasks,
    ) + WEBEND


def basic_dump(session: CamcopsSession, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Provides a basic research dump (ZIP of TSV files)."""

    # Permissions
    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)

    # Parameters
    dump_type = ws.get_cgi_parameter_str(form, PARAM.BASIC_DUMP_TYPE)
    permitted_dump_types = [VALUE.DUMPTYPE_EVERYTHING,
                            VALUE.DUMPTYPE_AS_TASK_FILTER,
                            VALUE.DUMPTYPE_SPECIFIC_TASKS]
    if dump_type not in permitted_dump_types:
        return fail_with_error_stay_logged_in(
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
    classes = get_all_task_classes()
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
def offer_table_dump(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """HTML form to request dump of table data."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
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

    for x in get_permitted_tables_views_sorted_labelled():
        if x["name"] == Blob.TABLENAME:
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


def serve_table_dump(session: CamcopsSession, form: cgi.FieldStorage) \
        -> Union[str, WSGI_TUPLE_TYPE]:
    """Serve a dump of table +/- view data."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
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
            get_database_dump_as_sql(tables), [], filename
        )
    elif outputtype == VALUE.OUTPUTTYPE_TSV:
        zip_contents = get_multiple_views_data_as_tsv_zip(tables)
        if zip_contents is None:
            return fail_with_error_stay_logged_in(NOTHING_VALID_SPECIFIED)
        filename = "CamCOPS_dump_" + format_datetime(
            pls.NOW_LOCAL_TZ,
            DATEFORMAT.FILENAME
        ) + ".zip"
        # atypical content type
        return ws.zip_result(zip_contents, [], filename)
    else:
        return fail_with_error_stay_logged_in(
            "Dump: outputtype must be '{}' or '{}'".format(
                VALUE.OUTPUTTYPE_SQL,
                VALUE.OUTPUTTYPE_TSV
            )
        )


# =============================================================================
# View policies
# =============================================================================

@view_config(route_name=Routes.VIEW_POLICIES, renderer="view_policies.mako")
def view_policies(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML showing server's ID policies."""
    cfg = req.config
    which_idnums = cfg.get_which_idnums()
    return dict(
        cfg=cfg,
        which_idnums=which_idnums,
        descriptions=[cfg.get_id_desc(n) for n in which_idnums],
        short_descriptions=[cfg.get_id_shortdesc(n) for n in which_idnums],
        upload=cfg.ID_POLICY_UPLOAD_STRING,
        finalize=cfg.ID_POLICY_FINALIZE_STRING,
        upload_principal=get_upload_id_policy_principal_numeric_id(),
        finalize_principal=get_finalize_id_policy_principal_numeric_id(),
    )


# =============================================================================
# View table definitions
# =============================================================================

# noinspection PyUnusedLocal
def inspect_table_defs(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Inspect table definitions with field comments."""

    if not session.authorized_to_dump():
        return fail_with_error_stay_logged_in(CANNOT_DUMP)
    return get_descriptions_comments_html(include_views=False)


# =============================================================================
# View audit trail
# =============================================================================

@view_config(route_name=Routes.OFFER_AUDIT_TRAIL,
             permission=Permission.SUPERUSER)
def offer_audit_trail(req: CamcopsRequest) -> Response:
    form = AuditTrailForm(request=req)
    if SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
                ViewParam.SOURCE,
                ViewParam.REMOTE_IP_ADDR,
                ViewParam.USERNAME,
                ViewParam.TABLENAME,
                ViewParam.SERVER_PK,
                ViewParam.TRUNCATE,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET:
            # (the parameters are NOT sensitive)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_AUDIT_TRAIL,
                                              _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "audit_trail_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, form)),
        request=req)


AUDIT_TRUNCATE_AT = 100


@view_config(route_name=Routes.VIEW_AUDIT_TRAIL,
             permission=Permission.SUPERUSER)
def view_audit_trail(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    source = req.get_str_param(ViewParam.SOURCE, None)
    remote_addr = req.get_str_param(ViewParam.REMOTE_IP_ADDR, None)
    username = req.get_str_param(ViewParam.USERNAME, None)
    table_name = req.get_str_param(ViewParam.TABLENAME, None)
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    truncate = req.get_bool_param(ViewParam.TRUNCATE, True)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append("{} = {}".format(key, value))

    dbsession = req.dbsession
    q = dbsession.query(AuditEntry)
    if start_datetime:
        q = q.filter(AuditEntry.when_access_utc >= start_datetime)
        add_condition(ViewParam.START_DATETIME, start_datetime)
    if end_datetime:
        q = q.filter(AuditEntry.when_access_utc <= end_datetime)
        add_condition(ViewParam.END_DATETIME, end_datetime)
    if source:
        q = q.filter(AuditEntry.source == source)
        add_condition(ViewParam.SOURCE, source)
    if remote_addr:
        q = q.filter(AuditEntry.remote_addr == remote_addr)
        add_condition(ViewParam.REMOTE_IP_ADDR, remote_addr)
    if username:
        # https://stackoverflow.com/questions/8561470/sqlalchemy-filtering-by-relationship-attribute  # noqa
        q = q.join(User).filter(User.username == username)
        add_condition(ViewParam.USERNAME, username)
    if table_name:
        q = q.filter(AuditEntry.table_name == table_name)
        add_condition(ViewParam.TABLENAME, table_name)
    if server_pk is not None:
        q = q.filter(AuditEntry.server_pk == server_pk)
        add_condition(ViewParam.SERVER_PK, server_pk)

    q = q.order_by(desc(AuditEntry.id))

    # audit_entries = dbsession.execute(q).fetchall()
    # ... no! That executes to give you row-type results.
    # audit_entries = q.all()
    # ... yes! But let's paginate, too:
    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return render_to_response("audit_trail_view.mako",
                              dict(conditions="; ".join(conditions),
                                   page=page,
                                   truncate=truncate,
                                   truncate_at=AUDIT_TRUNCATE_AT),
                              request=req)


# =============================================================================
# View HL7 message log
# =============================================================================

@view_config(route_name=Routes.OFFER_HL7_MESSAGE_LOG,
             permission=Permission.SUPERUSER)
def offer_hl7_message_log(req: CamcopsRequest) -> Response:
    form = HL7MessageLogForm(request=req)
    if SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.TABLENAME,
                ViewParam.SERVER_PK,
                ViewParam.HL7_RUN_ID,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET
            # (the parameters are NOT sensitive)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_HL7_MESSAGE_LOG,
                                              _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "hl7_message_log_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, form)),
        request=req)


@view_config(route_name=Routes.VIEW_HL7_MESSAGE_LOG,
             permission=Permission.SUPERUSER)
def view_hl7_message_log(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    table_name = req.get_str_param(ViewParam.TABLENAME, None)
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    hl7_run_id = req.get_int_param(ViewParam.HL7_RUN_ID, None)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append("{} = {}".format(key, value))

    dbsession = req.dbsession
    q = dbsession.query(HL7Message)
    if table_name:
        q = q.filter(HL7Message.basetable == table_name)
        add_condition(ViewParam.TABLENAME, table_name)
    if server_pk is not None:
        q = q.filter(HL7Message.serverpk == server_pk)
        add_condition(ViewParam.SERVER_PK, server_pk)
    if hl7_run_id is not None:
        q = q.filter(HL7Message.run_id == hl7_run_id)
        add_condition(ViewParam.HL7_RUN_ID, hl7_run_id)
    if start_datetime:
        q = q.filter(HL7Message.sent_at_utc >= start_datetime)
        add_condition(ViewParam.START_DATETIME, start_datetime)
    if end_datetime:
        q = q.filter(HL7Message.sent_at_utc <= end_datetime)
        add_condition(ViewParam.END_DATETIME, end_datetime)

    q = q.order_by(desc(HL7Message.msg_id))

    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return render_to_response("hl7_message_log_view.mako",
                              dict(conditions="; ".join(conditions),
                                   page=page),
                              request=req)



@view_config(route_name=Routes.VIEW_HL7_MESSAGE,
             permission=Permission.SUPERUSER)
def view_hl7_message(req: CamcopsRequest) -> Response:
    hl7_msg_id = req.get_int_param(ViewParam.HL7_MSG_ID, None)
    dbsession = req.dbsession
    hl7msg = dbsession.query(HL7Message)\
        .filter(HL7Message.msg_id == hl7_msg_id)\
        .first()
    if hl7msg is None:
        raise exc.HTTPBadRequest("Bad HL7 message ID {}".format(hl7_msg_id))
    return render_to_response("hl7_message_view.mako",
                              dict(msg=hl7msg),
                              request=req)


# =============================================================================
# View HL7 run log and individual runs
# =============================================================================

@view_config(route_name=Routes.OFFER_HL7_RUN_LOG,
             permission=Permission.SUPERUSER)
def offer_hl7_run_log(req: CamcopsRequest) -> Response:
    form = HL7RunLogForm(request=req)
    if SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.HL7_RUN_ID,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET
            # (the parameters are NOT sensitive)
            raise exc.HTTPFound(req.route_url(Routes.VIEW_HL7_RUN_LOG,
                                              _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "hl7_run_log_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, form)),
        request=req)


@view_config(route_name=Routes.VIEW_HL7_RUN_LOG,
             permission=Permission.SUPERUSER)
def view_hl7_run_log(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    hl7_run_id = req.get_int_param(ViewParam.HL7_RUN_ID, None)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append("{} = {}".format(key, value))

    dbsession = req.dbsession
    q = dbsession.query(HL7Run)
    if hl7_run_id is not None:
        q = q.filter(HL7Run.run_id == hl7_run_id)
        add_condition("hl7_run_id", hl7_run_id)
    if start_datetime:
        q = q.filter(HL7Run.start_at_utc >= start_datetime)
        add_condition("start_datetime", start_datetime)
    if end_datetime:
        q = q.filter(HL7Run.start_at_utc <= end_datetime)
        add_condition("end_datetime", end_datetime)

    q = q.order_by(desc(HL7Run.run_id))

    page = SqlalchemyOrmPage(collection=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return render_to_response("hl7_run_log_view.mako",
                              dict(conditions="; ".join(conditions),
                                   page=page),
                              request=req)


@view_config(route_name=Routes.VIEW_HL7_RUN,
             permission=Permission.SUPERUSER)
def view_hl7_run(req: CamcopsRequest) -> Response:
    hl7_run_id = req.get_int_param(ViewParam.HL7_RUN_ID, None)
    dbsession = req.dbsession
    hl7run = dbsession.query(HL7Run)\
        .filter(HL7Run.run_id == hl7_run_id)\
        .first()
    if hl7run is None:
        raise exc.HTTPBadRequest("Bad HL7 run ID {}".format(hl7_run_id))
    return render_to_response("hl7_run_view.mako",
                              dict(hl7run=hl7run),
                              request=req)


# =============================================================================
# Introspection of source code
# =============================================================================

@view_config(route_name=Routes.OFFER_INTROSPECTION)
def offer_introspection(req: CamcopsRequest) -> Response:
    """Page to offer CamCOPS server source code."""
    cfg = req.config
    if not cfg.INTROSPECTION:
        return simple_failure(NO_INTROSPECTION_MSG)
    return render_to_response(
        "introspection_file_list.mako",
        dict(ifd_list=cfg.INTROSPECTION_FILES),
        request=req
    )


@view_config(route_name=Routes.INTROSPECT)
def introspect(req: CamcopsRequest) -> Response:
    """Provide formatted source code."""
    cfg = req.config
    if not cfg.INTROSPECTION:
        return simple_failure(NO_INTROSPECTION_MSG)
    filename = req.get_str_param(ViewParam.FILENAME, None)
    try:
        ifd = next(ifd for ifd in cfg.INTROSPECTION_FILES
                   if ifd.prettypath == filename)
    except StopIteration:
        return simple_failure(INTROSPECTION_INVALID_FILE_MSG)
    fullpath = ifd.fullpath

    if fullpath.endswith(".jsx"):
        lexer = pygments.lexers.web.JavascriptLexer()
    else:
        lexer = pygments.lexers.get_lexer_for_filename(fullpath)
    formatter = pygments.formatters.HtmlFormatter()
    try:
        with codecs.open(fullpath, "r", "utf8") as f:
            code = f.read()
    except Exception as e:
        log.debug("INTROSPECTION ERROR: {}", e)
        return simple_failure(INTROSPECTION_FAILED_MSG)
    code_html = pygments.highlight(code, lexer, formatter)
    css = formatter.get_style_defs('.highlight')
    return render_to_response("introspect_file.mako",
                              dict(css=css,
                                   code_html=code_html),
                              request=req)


# =============================================================================
# Altering data
# =============================================================================

def add_special_note(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Add a special note to a task (after confirmation)."""

    if not session.authorized_to_add_special_note():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 2
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    note = ws.get_cgi_parameter_str(form, PARAM.NOTE)
    task = task_factory(tablename, serverpk)
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
            cancelurl=get_url_task_html(tablename, serverpk),
        ) + WEBEND
    # If we get here, we'll apply the note.
    task.apply_special_note(note, session.user_id)
    return simple_success(
        "Note applied ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(get_url_task_html(tablename, serverpk))
    )


def erase_task(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Wipe all data from a task (after confirmation).

    Leaves the task record as a placeholder.
    """
    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    tablename = ws.get_cgi_parameter_str(form, PARAM.TABLENAME)
    serverpk = ws.get_cgi_parameter_int(form, PARAM.SERVERPK)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    task = task_factory(tablename, serverpk)
    if task is None:
        return fail_task_not_found()
    if task.is_erased():
        return fail_with_error_stay_logged_in("Task already erased.")
    if task.is_live_on_tablet():
        return fail_with_error_stay_logged_in(ERROR_TASK_LIVE)
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
            cancelurl=get_url_task_html(tablename, serverpk),
        ) + WEBEND
    # If we get here, we'll do the erasure.
    task.manually_erase(session.user_id)
    return simple_success(
        "Task erased ({}, server PK {}).".format(
            tablename,
            serverpk
        ),
        """
            <div><a href={}>View amended task</div>
        """.format(get_url_task_html(tablename, serverpk))
    )


def delete_patient(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Completely delete all data from a patient (after confirmation)."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
    idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    patient_server_pks = get_patient_server_pks_by_idnum(
        which_idnum, idnum_value, current_only=False)
    if which_idnum is not None or idnum_value is not None:
        # A patient was asked for...
        if not patient_server_pks:
            # ... but not found
            return fail_with_error_stay_logged_in("No such patient found.")
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = ""
        if which_idnum is not None and idnum_value is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                gen_tasks_for_patient_deletion(which_idnum, idnum_value))
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
                which_idnum_picker=get_html_which_idnum_picker(
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
            cancelurl=get_url_main_menu(),
            tasks=tasks,
        ) + WEBEND
    if not patient_server_pks:
        return fail_with_error_stay_logged_in("No such patient found.")
    # If we get here, we'll do the erasure.
    # Delete tasks (with subtables)
    for cls in get_all_task_classes():
        tablename = cls.tablename
        serverpks = cls.get_task_pks_for_patient_deletion(which_idnum,
                                                          idnum_value)
        for serverpk in serverpks:
            task = task_factory(tablename, serverpk)
            task.delete_entirely()
    # Delete patients
    for ppk in patient_server_pks:
        pls.db.db_exec("DELETE FROM patient WHERE _pk = ?", ppk)
        audit("Patient deleted", patient_server_pk=ppk)
    msg = "Patient with idnum{} = {} and associated tasks DELETED".format(
        which_idnum, idnum_value)
    audit(msg)
    return simple_success(msg)


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


def edit_patient(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
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
    idnum_changes = {}  # type: Dict[int, int]  # which_idnum, idnum_value
    if changes["forename"]:
        changes["forename"] = changes["forename"].upper()
    if changes["surname"]:
        changes["surname"] = changes["surname"].upper()
    changes["dob"] = format_datetime(
        changes["dob"], DATEFORMAT.ISO8601_DATE_ONLY, default="")
    for n in pls.get_which_idnums():
        val = ws.get_cgi_parameter_int(form, PARAM.IDNUM_PREFIX + str(n))
        if val is not None:
            idnum_changes[n] = val
    # Calculations
    n_confirmations = 2
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    patient = Patient(patient_server_pk)
    if patient.get_pk() is None:
        return fail_with_error_stay_logged_in(
            "No such patient found.")
    if not patient.is_preserved():
        return fail_with_error_stay_logged_in(
            "Patient record is still live on tablet; cannot edit.")
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
            gen_tasks_using_patient(
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
            for n in pls.get_which_idnums():
                oldvalue = patient.get_idnum_value(n)
                newvalue = idnum_changes.get(n, None)
                if newvalue is None:
                    newvalue = oldvalue
                desc = pls.get_id_desc(n)
                details += info_html_for_patient_edit(
                    "ID number {} ({})".format(n, desc),
                    str(newvalue),
                    PARAM.IDNUM_PREFIX + str(n),
                    str(newvalue),
                    str(oldvalue))
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
                sex_picker=get_html_sex_picker(param=PARAM.SEX,
                                               selected=patient.sex,
                                               offer_all=False),
                address=patient.address or "",
                gp=patient.gp or "",
                other=patient.other or "",
            )
            for n in pls.get_which_idnums():
                details += """
                    ID number {n} ({desc}):
                    <input type="number" name="{paramprefix}{n}"
                            value="{value}"><br>
                """.format(
                    n=n,
                    desc=pls.get_id_desc(n),
                    paramprefix=PARAM.IDNUM_PREFIX,
                    value=patient.get_idnum_value(n),
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
            cancelurl=get_url_main_menu(),
            tasks=tasks,
        ) + WEBEND
    # Line up the changes and validate, but DO NOT SAVE THE PATIENT as yet.
    changemessages = []
    for k, v in changes.items():
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
    for which_idnum, idnum_value in idnum_changes.items():
        oldvalue = patient.get_idnum_value(which_idnum)
        if idnum_value != oldvalue:
            patient.set_idnum_value(which_idnum, idnum_value)
    # Valid?
    if (not patient.satisfies_upload_id_policy() or
            not patient.satisfies_finalize_id_policy()):
        return fail_with_error_stay_logged_in(
            "New version does not satisfy uploading or finalizing policy; "
            "no changes made.")
    # Anything to do?
    if not changemessages:
        return simple_success("No changes made.")
    # If we get here, we'll make the change.
    patient.save()
    msg = "Patient details edited. Changes: "
    msg += "; ".join(changemessages) + "."
    patient.apply_special_note(msg, session.user_id,
                               audit_msg="Patient details edited")
    for task in gen_tasks_using_patient(patient.id,
                                        patient.get_device_id(),
                                        patient.get_era()):
        # Patient details changed, so resend any tasks via HL7
        task.delete_from_hl7_message_log()
    return simple_success(msg)


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


def forcibly_finalize(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Force-finalize all live (_era == ERA_NOW) records from a device."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    n_confirmations = 3
    device_id = ws.get_cgi_parameter_int(form, PARAM.DEVICE)
    confirmation_sequence = ws.get_cgi_parameter_int(
        form, PARAM.CONFIRMATION_SEQUENCE)
    if (confirmation_sequence is None or
            confirmation_sequence < 0 or
            confirmation_sequence > n_confirmations):
        confirmation_sequence = 0
    if confirmation_sequence > 0 and device_id is None:
        return fail_with_error_stay_logged_in("Device not specified.")
    d = None
    if device_id is not None:
        # A device was asked for...
        d = Device(device_id)
        if not d.is_valid():
            # ... but not found
            return fail_with_error_stay_logged_in("No such device found.")
        device_id = d.id
    if confirmation_sequence < n_confirmations:
        # First call. Offer method.
        tasks = ""
        if device_id is not None:
            tasks = AFFECTED_TASKS_HTML + task_list_from_generator(
                gen_tasks_live_on_tablet(device_id))
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
            cancelurl=get_url_main_menu(),
            tasks=tasks
        ) + WEBEND

    # If we get here, we'll do the forced finalization.
    # Force-finalize tasks (with subtables)
    tables = [
        # non-task but tablet-based tables
        Patient.TABLENAME,
        Blob.TABLENAME,
        DeviceStoredVar.TABLENAME,
    ]
    for cls in get_all_task_classes():
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
    return simple_success(msg)


# =============================================================================
# User management
# =============================================================================

# noinspection PyUnusedLocal
def manage_users(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Offer user management menu."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return manage_users_html(session)


# noinspection PyUnusedLocal
def ask_to_add_user(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Ask for details to add a user."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return ask_to_add_user_html(session)


def add_user_if_auth(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Adds a user using the details supplied."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return add_user(form)


def edit_user(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Offers a user editing page."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_edit = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return edit_user_form(session, user_to_edit)


def change_user_if_auth(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Applies edits to a user."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    return change_user(form)


def ask_delete_user(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Asks for confirmation to delete a user."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_delete = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return ask_delete_user_html(session, user_to_delete)


def delete_user_if_auth(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Deletes a user."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_delete = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return delete_user(user_to_delete)


def enable_user(session: CamcopsSession, form: cgi.FieldStorage) -> str:
    """Enables a user (unlocks, clears login failures)."""

    if not session.authorized_as_superuser():
        return fail_with_error_stay_logged_in(NOT_AUTHORIZED_MSG)
    user_to_enable = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    return enable_user_webview(user_to_enable)


# =============================================================================
# Ancillary to the main pages/actions
# =============================================================================

def get_tracker(session: CamcopsSession, form: cgi.FieldStorage) -> Tracker:
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


def get_clinicaltextview(session: CamcopsSession,
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
        get_generic_action_url(ACTION.NEXT_PAGE) +
        get_url_field_value_pair(PARAM.NTASKS, ntasks)
    )


def get_url_last_page(ntasks: int) -> str:
    """URL to move to last page in task list."""
    return (
        get_generic_action_url(ACTION.LAST_PAGE) +
        get_url_field_value_pair(PARAM.NTASKS, ntasks)
    )


def get_url_introspect(filename: str) -> str:
    """URL to view specific source code file."""
    return (
        get_generic_action_url(ACTION.INTROSPECT) +
        get_url_field_value_pair(PARAM.FILENAME, filename)
    )


# =============================================================================
# Main HTTP processor
# =============================================================================

# -------------------------------------------------------------------------
# Main set of action mappings.
# All functions take parameters (session, form)
# -------------------------------------------------------------------------
ACTIONDICT = {
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
    ACTION.INSPECT_TABLE_DEFS: inspect_table_defs,

    # User management
    ACTION.MANAGE_USERS: manage_users,
    ACTION.ASK_TO_ADD_USER: ask_to_add_user,
    ACTION.ADD_USER: add_user_if_auth,
    ACTION.EDIT_USER: edit_user,
    ACTION.CHANGE_USER: change_user_if_auth,
    ACTION.ASK_DELETE_USER: ask_delete_user,
    ACTION.DELETE_USER: delete_user_if_auth,
    ACTION.ENABLE_USER: enable_user,

    # Amending and deleting data
    ACTION.ADD_SPECIAL_NOTE: add_special_note,
    ACTION.ERASE_TASK: erase_task,
    ACTION.DELETE_PATIENT: delete_patient,
    ACTION.EDIT_PATIENT: edit_patient,
    ACTION.FORCIBLY_FINALIZE: forcibly_finalize,
}



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



# =============================================================================
# Unit tests
# =============================================================================

def webview_unit_tests() -> None:
    """Unit tests for camcops.py"""
    session = CamcopsSession()
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
