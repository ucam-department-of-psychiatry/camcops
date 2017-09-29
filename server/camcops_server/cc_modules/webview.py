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
import io
import logging
import os
from pprint import pformat
import sqlite3
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Type
import zipfile

from cardinal_pythonlib.datetimefunc import (
    get_now_localtz,
    format_datetime,
)
from cardinal_pythonlib.deform_utils import get_head_form_html
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.dialect import get_dialect_name
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_orm_classes_from_base
from cardinal_pythonlib.sqlalchemy.orm_query import CountStarSpecializedQuery
from cardinal_pythonlib.sqlalchemy.session import get_engine_from_session
from deform.exception import ValidationFailure
from pendulum import Pendulum
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
)
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.security import Authenticated, NO_PERMISSION_REQUIRED
import pygments
import pygments.lexers
import pygments.lexers.sql
import pygments.lexers.web
import pygments.formatters
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session as SqlASession, sessionmaker
from sqlalchemy.sql.expression import desc, or_

from .cc_audit import audit, AuditEntry
from .cc_constants import CAMCOPS_URL, DateFormat, MINIMUM_PASSWORD_LENGTH
from .cc_blob import Blob
from camcops_server.cc_modules import cc_db
from .cc_db import GenericTabletRecordMixin
from .cc_device import Device
from .cc_dump import copy_tasks_and_summaries
from .cc_forms import (
    AddGroupForm,
    AddIdDefinitionForm,
    AddSpecialNoteForm,
    AddUserForm,
    AuditTrailForm,
    ChangeOtherPasswordForm,
    ChangeOwnPasswordForm,
    ChooseTrackerForm,
    DEFAULT_ROWS_PER_PAGE,
    DeleteGroupForm,
    DeleteIdDefinitionForm,
    DeleteUserForm,
    DIALECT_CHOICES,
    EditGroupForm,
    EditIdDefinitionForm,
    EditServerSettingsForm,
    EditUserForm,
    HL7MessageLogForm,
    HL7RunLogForm,
    LoginForm,
    OfferBasicDumpForm,
    OfferSqlDumpForm,
    OfferTermsForm,
    RefreshTasksForm,
    SetUserUploadGroupForm,
    EditTaskFilterForm,
    TasksPerPageForm,
    ViewDdlForm,
)
from .cc_group import Group
from .cc_hl7 import HL7Message, HL7Run
from .cc_patient import Patient
from .cc_patientidnum import (
    clear_idnum_definition_cache,
    IdNumDefinition,
    PatientIdNum,
)
from .cc_plot import ccplot_no_op
from .cc_pyramid import (
    CamcopsPage,
    Dialect,
    FormAction,
    PageUrl,
    PdfResponse,
    Permission,
    Routes,
    SqlalchemyOrmPage,
    SqliteBinaryResponse,
    TextAttachmentResponse,
    ViewArg,
    ViewParam,
    XmlResponse,
    ZipResponse,
)
from .cc_report import get_report_instance
from .cc_request import CamcopsRequest
from .cc_serversettings import get_database_title, set_database_title
from .cc_session import CamcopsSession
from .cc_simpleobjects import IdNumReference
from .cc_specialnote import SpecialNote
from .cc_sqlalchemy import Base, get_all_ddl
from .cc_task import (
    gen_tasks_for_patient_deletion,
    gen_tasks_live_on_tablet,
    gen_tasks_using_patient,
    Task,
)
from .cc_taskfactory import (
    task_factory,
    TaskFilter,
    TaskCollection,
    TaskSortMethod,
)
from .cc_taskfilter import (
    task_classes_from_table_names,
    TaskClassSortMethod,
)
from .cc_tracker import ClinicalTextView, Tracker
from .cc_tsv import TsvCollection
from .cc_unittest import unit_test_ignore
from .cc_user import SecurityAccountLockout, SecurityLoginFailure, User
from .cc_version import CAMCOPS_SERVER_VERSION

log = BraceStyleAdapter(logging.getLogger(__name__))
ccplot_no_op()

# =============================================================================
# Constants
# =============================================================================

ALLOWED_TASK_VIEW_TYPES = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
                           ViewArg.XML]
ALLOWED_TRACKER_VIEW_TYPE = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
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


# =============================================================================
# Unused
# =============================================================================

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


# =============================================================================
# Error views
# =============================================================================

@notfound_view_config(renderer="not_found.mako")
def not_found(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


@view_config(context=HTTPBadRequest, renderer="bad_request.mako")
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


@view_config(route_name=Routes.TESTPAGE_PRIVATE_1)
def test_page_private_1(req: CamcopsRequest) -> Response:
    return Response("Private test page.")


@view_config(route_name=Routes.TESTPAGE_PRIVATE_2,
             renderer="testpage.mako",
             permission=Permission.SUPERUSER)
def test_page_2(req: CamcopsRequest) -> Dict[str, Any]:
    # Contains POTENTIALLY SENSITIVE test information, including environment
    # variables
    return dict(param1="world")


@view_config(route_name=Routes.TESTPAGE_PRIVATE_3,
             renderer="inherit_cache_test_child.mako",
             permission=Permission.SUPERUSER)
def test_page_3(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


@view_config(route_name=Routes.CRASH, permission=Permission.SUPERUSER)
def crash(req: CamcopsRequest) -> Response:
    """Deliberately raises an exception."""
    raise RuntimeError("Deliberately crashed. Should not affect other "
                       "processes.")


# =============================================================================
# Authorization: login, logout, login failures, terms/conditions
# =============================================================================

# Do NOT use extra parameters for functions decorated with @view_config;
# @view_config can take functions like "def view(request)" but also
# "def view(context, request)", so if you add additional parameters, it thinks
# you're doing the latter and sends parameters accordingly.

@view_config(route_name=Routes.LOGIN, permission=NO_PERMISSION_REQUIRED)
def login_view(req: CamcopsRequest) -> Response:
    cfg = req.config
    autocomplete_password = not cfg.disable_password_autocomplete

    form = LoginForm(request=req, autocomplete_password=autocomplete_password)

    if FormAction.SUBMIT in req.POST:
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
                return HTTPFound(redirect_url)  # redirect
            return HTTPFound(req.route_url(Routes.HOME))  # redirect

        except ValidationFailure as e:
            rendered_form = e.render()

    else:
        redirect_url = req.get_str_param(ViewParam.REDIRECT_URL, "")
        # ... use default of "", because None gets serialized to "None", which
        #     would then get read back later as "None".
        appstruct = {ViewParam.REDIRECT_URL: redirect_url}
        # log.critical("appstruct from GET/POST: {!r}", appstruct)
        rendered_form = form.render(appstruct)

    return render_to_response(
        "login.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
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


def account_locked(req: CamcopsRequest, locked_until: Pendulum) -> Response:
    """
    HTML given when account locked out.
    Returned by login_view() only.
    """
    return render_to_response(
        "accounted_locked.mako",
        dict(
            locked_until=format_datetime(locked_until,
                                         DateFormat.LONG_DATETIME_WITH_DAY,
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


@view_config(route_name=Routes.OFFER_TERMS,
             permission=Authenticated,
             renderer="offer_terms.mako")
def offer_terms(req: CamcopsRequest) -> Response:
    """HTML offering terms/conditions and requesting acknowledgement."""
    form = OfferTermsForm(
        request=req,
        agree_button_text=req.wappstring("disclaimer_agree"))

    if FormAction.SUBMIT in req.POST:
        req.camcops_session.agree_terms(req)
        return HTTPFound(req.route_url(Routes.HOME))  # redirect

    return render_to_response(
        "offer_terms.mako",
        dict(
            title=req.wappstring("disclaimer_title"),
            subtitle=req.wappstring("disclaimer_subtitle"),
            content=req.wappstring("disclaimer_content"),
            form=form.render(),
            head_form_html=get_head_form_html(req, [form]),
        ),
        request=req
    )


@forbidden_view_config()
def forbidden(req: CamcopsRequest) -> Response:
    # I was doing this:
    if req.has_permission(Authenticated):
        user = req.user
        assert user, "Bug! Authenticated but no user...!?"
        if user.must_change_password:
            return HTTPFound(req.route_url(Routes.CHANGE_OWN_PASSWORD))
        if user.must_agree_terms():
            return HTTPFound(req.route_url(Routes.OFFER_TERMS))
    # ... but with "raise HTTPFound" instead.
    # BUT there is only one level of exception handling in Pyramid, i.e. you
    # can't raise exceptions from exceptions:
    #       https://github.com/Pylons/pyramid/issues/436
    # The simplest way round is to use "return", not "raise".

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

@view_config(route_name=Routes.CHANGE_OWN_PASSWORD, permission=Authenticated)
def change_own_password(req: CamcopsRequest) -> Response:
    ccsession = req.camcops_session
    expired = ccsession.user_must_change_password()
    form = ChangeOwnPasswordForm(request=req, must_differ=True)
    user = req.user
    assert user is not None
    extra_msg = ""
    if FormAction.SUBMIT in req.POST:
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
             head_form_html=get_head_form_html(req, [form])),
        request=req)


@view_config(route_name=Routes.CHANGE_OTHER_PASSWORD,
             permission=Permission.SUPERUSER,
             renderer="change_other_password.mako")
def change_other_password(req: CamcopsRequest) -> Response:
    """For administrators, to change another's password."""
    form = ChangeOtherPasswordForm(request=req)
    username = None  # for type checker
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user_id = appstruct.get(ViewParam.USER_ID)
            must_change_pw = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)
            new_password = appstruct.get(ViewParam.NEW_PASSWORD)
            user = User.get_user_by_id(req.dbsession, user_id)
            if not user:
                raise HTTPBadRequest("Missing user for id {}".format(user_id))
            user.set_password(req, new_password)
            if must_change_pw:
                user.force_password_change()
            return password_changed(req, user.username, own_password=False)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        user_id = req.get_int_param(ViewParam.USER_ID)
        if user_id is None:
            raise HTTPBadRequest("Improper user_id of {}".format(
                repr(user_id)))
        user = User.get_user_by_id(req.dbsession, user_id)
        if user is None:
            raise HTTPBadRequest("Missing user for id {}".format(user_id))
        username = user.username
        appstruct = {ViewParam.USER_ID: user_id}
        rendered_form = form.render(appstruct)
    return render_to_response(
        "change_other_password.mako",
        dict(username=username,
             form=rendered_form,
             min_pw_length=MINIMUM_PASSWORD_LENGTH,
             head_form_html=get_head_form_html(req, [form])),
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
    if req.user.superuser:
        groups = req.dbsession.query(Group)  # type: Iterable[Group]
        warn_bad_id_policies = any(
            (not g.tokenized_upload_policy().is_valid_from_req(req)) or
            (not g.tokenized_finalize_policy().is_valid_from_req(req))
            for g in groups
        )
    else:
        # Let's make things a little faster for non-superusers:
        warn_bad_id_policies = False
    return dict(
        authorized_as_superuser=ccsession.authorized_as_superuser(),
        authorized_for_reports=ccsession.authorized_for_reports(),
        authorized_to_dump=ccsession.authorized_to_dump(),
        camcops_url=CAMCOPS_URL,
        warn_bad_id_policies=warn_bad_id_policies,
        introspection=cfg.introspection,
        now=format_datetime(req.now, DateFormat.SHORT_DATETIME_SECONDS),
        server_version=CAMCOPS_SERVER_VERSION,
    )


# =============================================================================
# Tasks
# =============================================================================

def edit_filter(req: CamcopsRequest, task_filter: TaskFilter,
                redirect_url: str) -> Response:
    if FormAction.SET_FILTERS in req.POST:
        form = EditTaskFilterForm(request=req)
        try:
            controls = list(req.POST.items())
            fa = form.validate(controls)

            who = fa.get(ViewParam.WHO)
            what = fa.get(ViewParam.WHAT)
            when = fa.get(ViewParam.WHEN)
            admin = fa.get(ViewParam.ADMIN)
            task_filter.surname = who.get(ViewParam.SURNAME)
            task_filter.forename = who.get(ViewParam.FORENAME)
            task_filter.dob = who.get(ViewParam.DOB)
            task_filter.sex = who.get(ViewParam.SEX)
            task_filter.idnum_criteria = [
                IdNumReference(which_idnum=x[ViewParam.WHICH_IDNUM],
                               idnum_value=x[ViewParam.IDNUM_VALUE])
                for x in who.get(ViewParam.ID_REFERENCES)
            ]
            task_filter.task_types = what.get(ViewParam.TASKS)
            task_filter.text_contents = what.get(ViewParam.TEXT_CONTENTS)
            task_filter.complete_only = what.get(ViewParam.COMPLETE_ONLY)
            task_filter.start_datetime = when.get(ViewParam.START_DATETIME)
            task_filter.end_datetime = when.get(ViewParam.END_DATETIME)
            task_filter.device_ids = admin.get(ViewParam.DEVICE_IDS)
            task_filter.adding_user_ids = admin.get(ViewParam.USER_IDS)
            task_filter.group_ids = admin.get(ViewParam.GROUP_IDS)

            return HTTPFound(redirect_url)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        if FormAction.CLEAR_FILTERS in req.POST:
            # skip validation
            task_filter.clear()
        who = {
            ViewParam.SURNAME: task_filter.surname,
            ViewParam.FORENAME: task_filter.forename,
            ViewParam.DOB: task_filter.dob,
            ViewParam.SEX: task_filter.sex or "",
            ViewParam.ID_REFERENCES: [
                {ViewParam.WHICH_IDNUM: x.which_idnum,
                 ViewParam.IDNUM_VALUE: x.idnum_value}
                for x in task_filter.idnum_criteria
            ],
        }
        what = {
            ViewParam.TASKS: task_filter.task_types,
            ViewParam.TEXT_CONTENTS: task_filter.text_contents,
            ViewParam.COMPLETE_ONLY: task_filter.complete_only,
        }
        when = {
            ViewParam.START_DATETIME: task_filter.start_datetime,
            ViewParam.END_DATETIME: task_filter.end_datetime,
        }
        admin = {
            ViewParam.DEVICE_IDS: task_filter.device_ids,
            ViewParam.USER_IDS: task_filter.adding_user_ids,
            ViewParam.GROUP_IDS: task_filter.group_ids,
        }
        open_who = any(i for i in who.values())
        open_what = any(i for i in what.values())
        open_when = any(i for i in when.values())
        open_admin = any(i for i in admin.values())
        fa = {
            ViewParam.WHO: who,
            ViewParam.WHAT: what,
            ViewParam.WHEN: when,
            ViewParam.ADMIN: admin,
        }
        form = EditTaskFilterForm(request=req,
                                  open_admin=open_admin,
                                  open_what=open_what,
                                  open_when=open_when,
                                  open_who=open_who)
        rendered_form = form.render(fa)

    return render_to_response(
        "filter_edit.mako",
        dict(
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form])
        ),
        request=req
    )


@view_config(route_name=Routes.SET_FILTERS)
def set_filters(req: CamcopsRequest) -> Response:
    redirect_url = req.get_str_param(ViewParam.REDIRECT_URL,
                                     req.route_url(Routes.VIEW_TASKS))
    task_filter = req.camcops_session.get_task_filter()
    return edit_filter(req, task_filter=task_filter, redirect_url=redirect_url)


@view_config(route_name=Routes.VIEW_TASKS, renderer="view_tasks.mako")
def view_tasks(req: CamcopsRequest) -> Dict[str, Any]:
    """HTML displaying tasks and applicable filters."""
    ccsession = req.camcops_session
    user = req.user
    taskfilter = ccsession.get_task_filter()

    # Read from the GET parameters (or in some cases potentially POST but those
    # will be re-read).
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE,
        ccsession.number_to_view or DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    errors = False

    # "Number of tasks per page" form
    tpp_form = TasksPerPageForm(request=req, css_class="form-inline")
    if FormAction.SUBMIT_TASKS_PER_PAGE in req.POST:
        try:
            controls = list(req.POST.items())
            tpp_appstruct = tpp_form.validate(controls)
            rows_per_page = tpp_appstruct.get(ViewParam.ROWS_PER_PAGE)
            ccsession.number_to_view = rows_per_page
        except ValidationFailure:
            errors = True
        rendered_tpp_form = tpp_form.render()
    else:
        tpp_appstruct = {ViewParam.ROWS_PER_PAGE: rows_per_page}
        rendered_tpp_form = tpp_form.render(tpp_appstruct)

    # Refresh tasks. Slightly pointless. Doesn't need validating. The user
    # could just press the browser's refresh button, but this improves the UI
    # slightly.
    refresh_form = RefreshTasksForm(request=req)
    rendered_refresh_form = refresh_form.render()

    # Get tasks, unless there have been form errors.
    # In principle, for some filter settings (single task, no "complete"
    # preference...) we could produce an ORM query and use SqlalchemyOrmPage,
    # which would apply LIMIT/OFFSET (or equivalent) to the query, and be
    # very nippy. In practice, this is probably an unusual setting, so we'll
    # simplify things here with a Python list regardless of the settings.
    if errors:
        collection = []
    else:
        collection = TaskCollection(
            req=req,
            taskfilter=taskfilter,
            sort_method_global=TaskSortMethod.CREATION_DATE_DESC
        ).all_tasks
    page = CamcopsPage(collection=collection,
                       page=page_num,
                       items_per_page=rows_per_page,
                       url_maker=PageUrl(req))
    return dict(
        page=page,
        head_form_html=get_head_form_html(req, [tpp_form,
                                                refresh_form]),
        tpp_form=rendered_tpp_form,
        refresh_form=rendered_refresh_form,
        no_patient_selected_and_user_restricted=(
            not ccsession.user_may_view_all_patients_when_unfiltered() and
            not taskfilter.any_specific_patient_filtering()
        ),
        user=user,
    )


@view_config(route_name=Routes.TASK)
def serve_task(req: CamcopsRequest) -> Response:
    """Serves an individual task."""
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML, lower=True)
    tablename = req.get_str_param(ViewParam.TABLE_NAME)
    server_pk = req.get_int_param(ViewParam.SERVER_PK)
    anonymise = req.get_bool_param(ViewParam.ANONYMISE, False)

    if viewtype not in ALLOWED_TASK_VIEW_TYPES:
        return HTTPBadRequest(
            "Bad output type: {!r} (permissible: {!r}".format(
                viewtype, ALLOWED_TASK_VIEW_TYPES))

    task = task_factory(req, tablename, server_pk)

    if task is None:
        return HTTPNotFound(
            "Task not found or not permitted: tablename={!r}, "
            "server_pk={!r}".format(tablename, server_pk))

    task.audit(req, "Viewed " + viewtype.upper())

    if viewtype == ViewArg.HTML:
        return Response(
            task.get_html(req=req, anonymise=anonymise)
        )
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            body=task.get_pdf(req, anonymise=anonymise),
            filename=task.suggested_pdf_filename(req)
        )
    elif viewtype == ViewArg.PDFHTML:  # debugging option
        return Response(
            task.get_pdf_html(req, anonymise=anonymise)
        )
    elif viewtype == ViewArg.XML:
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

def choose_tracker_or_ctv(req: CamcopsRequest,
                          as_ctv: bool) -> Dict[str, Any]:
    """HTML form for tracker selection."""

    form = ChooseTrackerForm(req, as_ctv=as_ctv, css_class="form-inline")

    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.WHICH_IDNUM,
                ViewParam.IDNUM_VALUE,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
                ViewParam.TASKS,
                ViewParam.ALL_TASKS,
                ViewParam.VIEWTYPE,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            # Not so obvious this can be redirected cleanly via POST.
            # It is possible by returning a form that then autosubmits: see
            # https://stackoverflow.com/questions/46582/response-redirect-with-post-instead-of-get  # noqa
            # However, since everything's on this server, we could just return
            # an appropriate Response directly. But the request information is
            # not sensitive, so we lose nothing by using a GET redirect:
            raise HTTPFound(req.route_url(
                Routes.CTV if as_ctv else Routes.TRACKER,
                _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.CHOOSE_TRACKER, renderer="choose_tracker.mako")
def choose_tracker(req: CamcopsRequest) -> Dict[str, Any]:
    return choose_tracker_or_ctv(req, as_ctv=False)


@view_config(route_name=Routes.CHOOSE_CTV, renderer="choose_ctv.mako")
def choose_ctv(req: CamcopsRequest) -> Dict[str, Any]:
    return choose_tracker_or_ctv(req, as_ctv=True)


def serve_tracker_or_ctv(req: CamcopsRequest,
                         as_ctv: bool) -> Response:
    which_idnum = req.get_int_param(ViewParam.WHICH_IDNUM)
    idnum_value = req.get_int_param(ViewParam.IDNUM_VALUE)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    tasks = req.get_str_list_param(ViewParam.TASKS)
    all_tasks = req.get_bool_param(ViewParam.ALL_TASKS, True)
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML)

    if all_tasks:
        task_classes = []  # type: List[Type[Task]]
    else:
        try:
            task_classes = task_classes_from_table_names(
                tasks, sortmethod=TaskClassSortMethod.SHORTNAME)
        except KeyError:
            return HTTPBadRequest("Invalid tasks specified")
        if not all(c.provides_trackers for c in task_classes):
            return HTTPBadRequest("Not all tasks specified provide trackers")

    if viewtype not in ALLOWED_TRACKER_VIEW_TYPE:
        return HTTPBadRequest("Invalid view type")

    iddefs = [IdNumReference(which_idnum, idnum_value)]

    as_tracker = not as_ctv
    taskfilter = TaskFilter()
    taskfilter.task_types = [tc.__tablename__ for tc in task_classes]  # a bit silly...  # noqa
    taskfilter.idnum_criteria = iddefs
    taskfilter.start_datetime = start_datetime
    taskfilter.end_datetime = end_datetime
    taskfilter.complete_only = True  # trackers require complete tasks
    taskfilter.sort_method = TaskClassSortMethod.SHORTNAME
    taskfilter.tasks_offering_trackers_only = as_tracker
    taskfilter.tasks_with_patient_only = True

    tracker_ctv_class = ClinicalTextView if as_ctv else Tracker
    tracker = tracker_ctv_class(req=req, taskfilter=taskfilter)

    if viewtype == ViewArg.HTML:
        return Response(
            tracker.get_html()
        )
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            body=tracker.get_pdf(),
            filename=tracker.suggested_pdf_filename()
        )
    elif viewtype == VALUE.OUTPUTTYPE_PDFHTML:  # debugging option
        return Response(
            tracker.get_pdf_html()
        )
    elif viewtype == VALUE.OUTPUTTYPE_XML:
        include_comments = req.get_bool_param(ViewParam.INCLUDE_COMMENTS, True)
        return XmlResponse(
            tracker.get_xml(include_comments=include_comments)
        )
    else:
        assert False, "Bug in logic above"


@view_config(route_name=Routes.TRACKER)
def serve_tracker(req: CamcopsRequest) -> Response:
    return serve_tracker_or_ctv(req, as_ctv=False)


@view_config(route_name=Routes.CTV)
def serve_ctv(req: CamcopsRequest) -> Response:
    return serve_tracker_or_ctv(req, as_ctv=True)


# =============================================================================
# Reports
# =============================================================================

@view_config(route_name=Routes.REPORTS_MENU, renderer="reports_menu.mako",
             permission=Permission.REPORTS)
def reports_menu(req: CamcopsRequest) -> Dict[str, Any]:
    """Offer a menu of reports."""
    return {}


@view_config(route_name=Routes.OFFER_REPORT, renderer="report_offer.mako",
             permission=Permission.REPORTS)
def offer_report(req: CamcopsRequest) -> Dict[str, Any]:
    """Offer configuration options for a single report."""
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        raise HTTPBadRequest("No such report ID: {!r}".format(report_id))
    if report.superuser_only and not req.user.superuser:
        raise HTTPBadRequest("Report {!r} is restricted to the "
                             "superuser".format(report_id))
    form = report.get_form(req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            querydict = {k: v for k, v in appstruct.items()
                         if k != ViewParam.CSRF_TOKEN}
            raise HTTPFound(req.route_url(Routes.REPORT, _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render({ViewParam.REPORT_ID: report_id})
    return dict(
        report=report,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form])
    )


@view_config(route_name=Routes.REPORT, permission=Permission.REPORTS)
def provide_report(req: CamcopsRequest) -> Response:
    """Serve up a configured report."""
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        return HTTPBadRequest("No such report ID: {}".format(repr(report_id)))
    return report.get_response(req)


# =============================================================================
# Research downloads
# =============================================================================

@view_config(route_name=Routes.OFFER_BASIC_DUMP, permission=Permission.DUMP)
def offer_basic_dump(req: CamcopsRequest) -> Response:
    """Form for basic research dump selection."""
    form = OfferBasicDumpForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            manual = appstruct.get(ViewParam.MANUAL)
            querydict = {
                ViewParam.DUMP_METHOD: appstruct.get(ViewParam.DUMP_METHOD),
                ViewParam.SORT: appstruct.get(ViewParam.SORT),
                ViewParam.GROUP_IDS: manual.get(ViewParam.GROUP_IDS),
                ViewParam.TASKS: manual.get(ViewParam.TASKS),
            }
            # We could return a response, or redirect via GET.
            # The request is not sensitive, so let's redirect.
            return HTTPFound(req.route_url(Routes.BASIC_DUMP,
                                           _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "dump_basic_offer.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req
    )


@view_config(route_name=Routes.BASIC_DUMP, permission=Permission.DUMP)
def serve_basic_dump(req: CamcopsRequest) -> Response:
    # -------------------------------------------------------------------------
    # Get parameters
    # -------------------------------------------------------------------------
    dump_method = req.get_str_param(ViewParam.DUMP_METHOD)
    sort_by_heading = req.get_bool_param(ViewParam.SORT, False)
    group_ids = req.get_int_list_param(ViewParam.GROUP_IDS)
    task_names = req.get_str_list_param(ViewParam.TASKS)

    # -------------------------------------------------------------------------
    # Select tasks
    # -------------------------------------------------------------------------
    if dump_method == ViewArg.EVERYTHING:
        taskfilter = TaskFilter()
    elif dump_method == ViewArg.USE_SESSION_FILTER:
        taskfilter = req.camcops_session.get_task_filter()
    elif dump_method == ViewArg.SPECIFIC_TASKS_GROUPS:
        taskfilter = TaskFilter()
        taskfilter.task_types = task_names
        taskfilter.group_ids = group_ids
    else:
        return HTTPBadRequest("Bad {} parameter".format(ViewParam.DUMP_METHOD))
    collection = TaskCollection(
        req=req,
        taskfilter=taskfilter,
        sort_method_by_class=TaskSortMethod.CREATION_DATE_ASC
    )

    # -------------------------------------------------------------------------
    # Create memory file and ZIP file within it
    # -------------------------------------------------------------------------
    memfile = io.BytesIO()
    z = zipfile.ZipFile(memfile, "w")

    # -------------------------------------------------------------------------
    # Iterate through tasks
    # -------------------------------------------------------------------------
    audit_descriptions = []  # type: List[str]
    for cls in collection.task_classes():
        tasks = collection.tasks_for_task_class(cls)
        # Task may return >1 file for TSV output (e.g. for subtables).
        tsvcoll = TsvCollection()
        pks = []  # type: List[int]

        for task in tasks:
            # noinspection PyProtectedMember
            pks.append(task._pk)
            tsv_elements = task.get_tsv_chunks(req)
            tsvcoll.add_chunks(tsv_elements)

        if sort_by_heading:
            tsvcoll.sort_by_headings()

        audit_descriptions.append("{}: {}".format(
            cls.__tablename__, ",".join(str(pk) for pk in pks)))

        # Write to ZIP.
        # If there are no valid task instances, there'll be no TSV; that's OK.
        for filename_stem in tsvcoll.get_filename_stems():
            tsv_filename = filename_stem + ".tsv"
            tsv_contents = tsvcoll.get_tsv_file(filename_stem)
            z.writestr(tsv_filename, tsv_contents.encode("utf-8"))

    # -------------------------------------------------------------------------
    # Finish and serve
    # -------------------------------------------------------------------------
    z.close()

    # Audit
    audit(req, "Basic dump: {}".format("; ".join(audit_descriptions)))

    # Return the result
    zip_contents = memfile.getvalue()
    memfile.close()
    zip_filename = "CamCOPS_dump_{}.zip".format(
        format_datetime(req.now, DateFormat.FILENAME))
    return ZipResponse(body=zip_contents, filename=zip_filename)


@view_config(route_name=Routes.OFFER_SQL_DUMP, permission=Permission.DUMP)
def offer_sql_dump(req: CamcopsRequest) -> Response:
    """Form for SQL research dump selection."""
    form = OfferSqlDumpForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            manual = appstruct.get(ViewParam.MANUAL)
            querydict = {
                ViewParam.DUMP_METHOD: appstruct.get(ViewParam.DUMP_METHOD),
                ViewParam.SQLITE_METHOD: appstruct.get(ViewParam.SQLITE_METHOD),  # noqa
                ViewParam.INCLUDE_BLOBS: appstruct.get(ViewParam.INCLUDE_BLOBS),  # noqa
                ViewParam.GROUP_IDS: manual.get(ViewParam.GROUP_IDS),
                ViewParam.TASKS: manual.get(ViewParam.TASKS),
            }
            # We could return a response, or redirect via GET.
            # The request is not sensitive, so let's redirect.
            return HTTPFound(req.route_url(Routes.SQL_DUMP, _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "dump_sql_offer.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req
    )


@view_config(route_name=Routes.SQL_DUMP, permission=Permission.DUMP)
def sql_dump(req: CamcopsRequest) -> Response:
    # -------------------------------------------------------------------------
    # Get parameters
    # -------------------------------------------------------------------------
    dump_method = req.get_str_param(ViewParam.DUMP_METHOD)
    sqlite_method = req.get_str_param(ViewParam.SQLITE_METHOD)
    include_blobs = req.get_bool_param(ViewParam.INCLUDE_BLOBS, False)
    group_ids = req.get_int_list_param(ViewParam.GROUP_IDS)
    task_names = req.get_str_list_param(ViewParam.TASKS)

    # -------------------------------------------------------------------------
    # Select tasks
    # -------------------------------------------------------------------------
    if dump_method == ViewArg.EVERYTHING:
        taskfilter = TaskFilter()
    elif dump_method == ViewArg.USE_SESSION_FILTER:
        taskfilter = req.camcops_session.get_task_filter()
    elif dump_method == ViewArg.SPECIFIC_TASKS_GROUPS:
        taskfilter = TaskFilter()
        taskfilter.task_types = task_names
        taskfilter.group_ids = group_ids
    else:
        return HTTPBadRequest("Bad {} parameter".format(ViewParam.DUMP_METHOD))
    collection = TaskCollection(
        req=req,
        taskfilter=taskfilter,
        sort_method_by_class=TaskSortMethod.CREATION_DATE_ASC
    )

    if sqlite_method not in [ViewArg.SQL, ViewArg.SQLITE]:
        return HTTPBadRequest("Bad {} parameter".format(
            ViewParam.SQLITE_METHOD))

    # -------------------------------------------------------------------------
    # Create memory file, dumper, and engine
    # -------------------------------------------------------------------------

    # This approach failed:
    #
    #   memfile = io.StringIO()
    #
    #   def dump(querysql, *multiparams, **params):
    #       compsql = querysql.compile(dialect=engine.dialect)
    #       memfile.write("{};\n".format(compsql))
    #
    #   engine = create_engine('{dialect}://'.format(dialect=dialect_name),
    #                          strategy='mock', executor=dump)
    #   dst_session = sessionmaker(bind=engine)()  # type: SqlASession
    #
    # ... you get the error
    #   AttributeError: 'MockConnection' object has no attribute 'begin'
    # ... which is fair enough.
    #
    # Next best thing: SQLite database.
    # Two ways to deal with it:
    # (a) duplicate our C++ dump code (which itself duplicate the SQLite
    #     command-line executable's dump facility), then create the database,
    #     dump it to a string, serve the string; or
    # (b) offer the binary SQLite file.
    # Or... (c) both.
    # Aha! pymysqlite.iterdump does this for us.
    #
    # If we create an in-memory database using create_engine('sqlite://'),
    # can we get the binary contents out? Don't think so.
    #
    # So we should first create a temporary on-disk file, then use that.

    # -------------------------------------------------------------------------
    # Make temporary file (one whose filename we can know).
    # We use tempfile.mkstemp() for security, or NamedTemporaryFile,
    # which is a bit easier. However, you can't necessarily open the file
    # again under all OSs, so that's no good. The final option is
    # TemporaryDirectory, which is secure and convenient.
    #
    # https://docs.python.org/3/library/tempfile.html
    # https://security.openstack.org/guidelines/dg_using-temporary-files-securely.html  # noqa
    # https://stackoverflow.com/questions/3924117/how-to-use-tempfile-namedtemporaryfile-in-python  # noqa
    # -------------------------------------------------------------------------
    db_basename = "temp.sqlite3"
    with tempfile.TemporaryDirectory() as tmpdirname:
        db_filename = os.path.join(tmpdirname, db_basename)
        # ---------------------------------------------------------------------
        # Make SQLAlchemy session
        # ---------------------------------------------------------------------
        url = "sqlite:///" + db_filename
        engine = create_engine(url, echo=False)
        dst_session = sessionmaker(bind=engine)()  # type: SqlASession
        # ---------------------------------------------------------------------
        # Iterate through tasks, creating tables as we need them.
        # ---------------------------------------------------------------------
        # Must treat tasks all together, because otherwise we will insert
        # duplicate dependency objects like Group objects.
        audit_descriptions = []  # type: List[str]
        all_tasks = []  # type: List[Task]
        for cls in collection.task_classes():
            tasks = collection.tasks_for_task_class(cls)
            all_tasks.extend(tasks)
            pks = [task._pk for task in tasks]
            audit_descriptions.append("{}: {}".format(
                cls.__tablename__, ",".join(str(pk) for pk in pks)))
        # ---------------------------------------------------------------------
        # Next bit very tricky. We're trying to achieve several things:
        # - a copy of part of the database structure
        # - a copy of part of the data, with relationships intact
        # - nothing sensitive (e.g. full User records) going through
        # - adding new columns for Task objects offering summary values
        # ---------------------------------------------------------------------
        copy_tasks_and_summaries(tasks=all_tasks,
                                 dst_engine=engine,
                                 dst_session=dst_session,
                                 include_blobs=include_blobs,
                                 req=req)
        dst_session.commit()
        # ---------------------------------------------------------------------
        # Audit
        # ---------------------------------------------------------------------
        audit(req, "SQL dump: {}".format("; ".join(audit_descriptions)))
        # ---------------------------------------------------------------------
        # Fetch file contents, either as binary, or as SQL
        # ---------------------------------------------------------------------
        filename_stem = "CamCOPS_dump_{}".format(
            format_datetime(req.now, DateFormat.FILENAME))
        if sqlite_method == ViewArg.SQLITE:
            with open(db_filename, 'rb') as f:
                binary_contents = f.read()
            return SqliteBinaryResponse(body=binary_contents,
                                        filename=filename_stem + ".sqlite3")
        else:  # SQL
            con = sqlite3.connect(db_filename)
            with io.StringIO() as f:
                for line in con.iterdump():
                    f.write(line + "\n")
                con.close()
                f.flush()
                sql_text = f.getvalue()
            return TextAttachmentResponse(body=sql_text,
                                          filename=filename_stem + ".sql")


# =============================================================================
# View DDL (table definitions)
# =============================================================================

LEXERMAP = {
    Dialect.MYSQL: pygments.lexers.sql.MySqlLexer,
    Dialect.MSSQL: pygments.lexers.sql.SqlLexer,  # generic
    Dialect.ORACLE: pygments.lexers.sql.SqlLexer,  # generic
    Dialect.FIREBIRD: pygments.lexers.sql.SqlLexer,  # generic
    Dialect.POSTGRES: pygments.lexers.sql.PostgresLexer,
    Dialect.SQLITE: pygments.lexers.sql.SqlLexer,  # generic; SqliteConsoleLexer is wrong  # noqa
    Dialect.SYBASE: pygments.lexers.sql.SqlLexer,  # generic
}


@view_config(route_name=Routes.VIEW_DDL)
def view_ddl(req: CamcopsRequest) -> Response:
    """Inspect table definitions with field comments."""
    form = ViewDdlForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            dialect = appstruct.get(ViewParam.DIALECT)
            ddl = get_all_ddl(dialect_name=dialect)
            lexer = LEXERMAP[dialect]()
            formatter = pygments.formatters.HtmlFormatter()
            html = pygments.highlight(ddl, lexer, formatter)
            css = formatter.get_style_defs('.highlight')
            return render_to_response("introspect_file.mako",
                                      dict(css=css,
                                           code_html=html),
                                      request=req)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    current_dialect = get_dialect_name(get_engine_from_session(req.dbsession))
    current_dialect_description = {k: v for k, v in DIALECT_CHOICES}.get(
        current_dialect, "?")
    return render_to_response(
        "view_ddl_choose_dialect.mako",
        dict(current_dialect=current_dialect,
             current_dialect_description=current_dialect_description,
             form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


# =============================================================================
# View audit trail
# =============================================================================

@view_config(route_name=Routes.OFFER_AUDIT_TRAIL,
             permission=Permission.SUPERUSER)
def offer_audit_trail(req: CamcopsRequest) -> Response:
    form = AuditTrailForm(request=req)
    if FormAction.SUBMIT in req.POST:
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
                ViewParam.TABLE_NAME,
                ViewParam.SERVER_PK,
                ViewParam.TRUNCATE,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET:
            # (the parameters are NOT sensitive)
            raise HTTPFound(req.route_url(Routes.VIEW_AUDIT_TRAIL,
                                          _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "audit_trail_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
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
    table_name = req.get_str_param(ViewParam.TABLE_NAME, None)
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
        add_condition(ViewParam.TABLE_NAME, table_name)
    if server_pk is not None:
        q = q.filter(AuditEntry.server_pk == server_pk)
        add_condition(ViewParam.SERVER_PK, server_pk)

    q = q.order_by(desc(AuditEntry.id))

    # audit_entries = dbsession.execute(q).fetchall()
    # ... no! That executes to give you row-type results.
    # audit_entries = q.all()
    # ... yes! But let's paginate, too:
    page = SqlalchemyOrmPage(query=q,
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
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.TABLE_NAME,
                ViewParam.SERVER_PK,
                ViewParam.HL7_RUN_ID,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET
            # (the parameters are NOT sensitive)
            return HTTPFound(req.route_url(Routes.VIEW_HL7_MESSAGE_LOG,
                                           _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "hl7_message_log_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req)


@view_config(route_name=Routes.VIEW_HL7_MESSAGE_LOG,
             permission=Permission.SUPERUSER)
def view_hl7_message_log(req: CamcopsRequest) -> Response:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    table_name = req.get_str_param(ViewParam.TABLE_NAME, None)
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
        add_condition(ViewParam.TABLE_NAME, table_name)
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

    page = SqlalchemyOrmPage(query=q,
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
        return HTTPBadRequest("Bad HL7 message ID {}".format(hl7_msg_id))
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
    if FormAction.SUBMIT in req.POST:
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
            return HTTPFound(req.route_url(Routes.VIEW_HL7_RUN_LOG,
                                           _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "hl7_run_log_choices.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
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

    page = SqlalchemyOrmPage(query=q,
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
        return HTTPBadRequest("Bad HL7 run ID {}".format(hl7_run_id))
    return render_to_response("hl7_run_view.mako",
                              dict(hl7run=hl7run),
                              request=req)


# =============================================================================
# User/server info views
# =============================================================================

@view_config(route_name=Routes.VIEW_OWN_USER_INFO,
             renderer="view_own_user_info.mako")
def view_own_user_info(req: CamcopsRequest) -> Dict[str, Any]:
    groups_page = CamcopsPage(req.user.groups,
                              url_maker=PageUrl(req))
    return dict(user=req.user,
                groups_page=groups_page)


@view_config(route_name=Routes.VIEW_SERVER_INFO,
             renderer="view_server_info.mako")
def view_server_info(req: CamcopsRequest) -> Dict[str, Any]:
    """
    HTML showing server's ID policies, etc..
    """
    return dict(
        idnum_definitions=req.idnum_definitions,
        string_families=req.extrastring_families(),
    )


# =============================================================================
# User management
# =============================================================================

EDIT_USER_KEYS = [
    # SPECIAL HANDLING # ViewParam.USER_ID,
    ViewParam.USERNAME,
    ViewParam.FULLNAME,
    ViewParam.EMAIL,
    ViewParam.MAY_UPLOAD,
    ViewParam.MAY_REGISTER_DEVICES,
    ViewParam.MAY_USE_WEBVIEWER,
    ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED,
    ViewParam.SUPERUSER,
    ViewParam.MAY_DUMP_DATA,
    ViewParam.MAY_RUN_REPORTS,
    ViewParam.MAY_ADD_NOTES,
    ViewParam.MUST_CHANGE_PASSWORD,
    # SPECIAL HANDLING # ViewParam.GROUP_IDS,
]


def get_user_from_request_user_id_or_raise(req: CamcopsRequest) -> User:
    user_id = req.get_int_param(ViewParam.USER_ID)
    user = User.get_user_by_id(req.dbsession, user_id)
    if not user:
        raise HTTPBadRequest("No such user ID: {}".format(repr(user_id)))
    return user


@view_config(route_name=Routes.VIEW_ALL_USERS,
             permission=Permission.SUPERUSER,
             renderer="users_view.mako")
def view_all_users(req: CamcopsRequest) -> Dict[str, Any]:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    dbsession = req.dbsession
    q = dbsession.query(User).order_by(User.username)
    page = SqlalchemyOrmPage(query=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return dict(page=page)


@view_config(route_name=Routes.VIEW_USER,
             permission=Permission.SUPERUSER,
             renderer="view_other_user_info.mako")
def view_user(req: CamcopsRequest) -> Dict[str, Any]:
    user = get_user_from_request_user_id_or_raise(req)
    return dict(user=user)


@view_config(route_name=Routes.EDIT_USER,
             permission=Permission.SUPERUSER,
             renderer="user_edit.mako")
def edit_user(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ALL_USERS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    user = get_user_from_request_user_id_or_raise(req)
    form = EditUserForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            dbsession = req.dbsession
            new_user_name = appstruct.get(ViewParam.USERNAME)
            existing_user = User.get_user_by_name(dbsession, new_user_name)
            if existing_user and existing_user.id != user.id:
                raise HTTPBadRequest(
                    "Can't rename user {!r} (ID {!r}) to {!r}; that "
                    "conflicts with existing user with ID {!r}".format(
                        user.name, user.id, new_user_name,
                        existing_user.id
                    ))
            for k in EDIT_USER_KEYS:
                setattr(user, k, appstruct.get(k))
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            user.set_group_ids(group_ids)
            # Also, if the user was uploading to a group that they are now no
            # longer a member of, we need to fix that
            if user.upload_group_id not in group_ids:
                user.upload_group_id = None
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {k: getattr(user, k) for k in EDIT_USER_KEYS}
        appstruct[ViewParam.USER_ID] = user.id
        appstruct[ViewParam.GROUP_IDS] = user.group_ids()
        rendered_form = form.render(appstruct)
    return dict(user=user,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def set_user_upload_group(req: CamcopsRequest,
                          user: User,
                          as_superuser: bool) -> Response:
    route_back = Routes.VIEW_ALL_USERS if as_superuser else Routes.HOME
    if FormAction.CANCEL in req.POST:
        return HTTPFound(req.route_url(route_back))
    form = SetUserUploadGroupForm(request=req, user=user)
    # ... need to show the groups permitted to THAT user, not OUR user
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user.upload_group_id = appstruct.get(ViewParam.UPLOAD_GROUP_ID)
            return HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.USER_ID: user.id,
            ViewParam.UPLOAD_GROUP_ID: user.upload_group_id
        }
        rendered_form = form.render(appstruct)
    return render_to_response(
        "set_user_upload_group.mako",
        dict(user=user,
             form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req
    )


@view_config(route_name=Routes.SET_OWN_USER_UPLOAD_GROUP)
def set_own_user_upload_group(req: CamcopsRequest) -> Response:
    return set_user_upload_group(req, req.user, False)


@view_config(route_name=Routes.SET_OTHER_USER_UPLOAD_GROUP,
             permission=Permission.SUPERUSER)
def set_other_user_upload_group(req: CamcopsRequest) -> Response:
    user = get_user_from_request_user_id_or_raise(req)
    return set_user_upload_group(req, user, True)


@view_config(route_name=Routes.UNLOCK_USER,
             permission=Permission.SUPERUSER)
def unlock_user(req: CamcopsRequest) -> Response:
    user = get_user_from_request_user_id_or_raise(req)
    user.enable(req)
    return simple_success(req, "User {} enabled".format(user.username))


@view_config(route_name=Routes.ADD_USER,
             permission=Permission.SUPERUSER,
             renderer="user_add.mako")
def add_user(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ALL_USERS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    form = AddUserForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            user = User()
            user.username = appstruct.get(ViewParam.USERNAME)
            user.set_password(req, appstruct.get(ViewParam.NEW_PASSWORD))
            user.must_change_password = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)  # noqa
            if User.get_user_by_name(dbsession, user.username):
                raise HTTPBadRequest("User with username {!r} already "
                                     "exists!".format(user.username))
            dbsession.add(user)
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def any_records_use_user(req: CamcopsRequest, user: User) -> bool:
    dbsession = req.dbsession
    user_id = user.id
    # Our own or users filtering on us?
    q = CountStarSpecializedQuery(CamcopsSession, session=dbsession)\
        .filter(CamcopsSession.filter_user_id == user_id)
    if q.count_star() > 0:
        return True
    # Device?
    q = CountStarSpecializedQuery(Device, session=dbsession)\
        .filter(or_(Device.registered_by_user_id == user_id,
                    Device.uploading_user_id == user_id))
    if q.count_star() > 0:
        return True
    # SpecialNote?
    q = CountStarSpecializedQuery(SpecialNote, session=dbsession)\
        .filter(SpecialNote.user_id == user_id)
    if q.count_star() > 0:
        return True
    # Uploaded records?
    for cls in gen_orm_classes_from_base(GenericTabletRecordMixin):  # type: Type[GenericTabletRecordMixin]  # noqa
        # noinspection PyProtectedMember
        q = CountStarSpecializedQuery(cls, session=dbsession)\
            .filter(or_(cls._adding_user_id == user_id,
                        cls._removing_user_id == user_id,
                        cls._preserving_user_id == user_id,
                        cls._manually_erasing_user_id == user_id))
        if q.count_star() > 0:
            return True
    # No; all clean.
    return False


@view_config(route_name=Routes.DELETE_USER,
             permission=Permission.SUPERUSER,
             renderer="user_delete.mako")
def delete_user(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
    user = get_user_from_request_user_id_or_raise(req)
    form = DeleteUserForm(request=req)
    rendered_form = ""
    error = ""
    if user.id == req.user.id:
        error = "Can't delete your own user!"
    elif user.may_use_webviewer or user.may_upload:
        error = "Unable to delete user; still has webviewer login and/or " \
                "tablet upload permission"
    else:
        if any_records_use_user(req, user):
            error = "Unable to delete user; records refer to that user. " \
                    "Disable login and upload permissions instead."
        else:
            if FormAction.DELETE in req.POST:
                try:
                    controls = list(req.POST.items())
                    appstruct = form.validate(controls)
                    assert appstruct.get(ViewParam.USER_ID) == user.id
                    # (*) Sessions belonging to this user
                    # ... done by modifying its ForeignKey to use "ondelete"
                    # (*) user_group_table mapping
                    # http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#relationships-many-to-many-deletion  # noqa
                    # Simplest way:
                    user.groups = []  # will delete the mapping entries
                    # (*) User itself
                    req.dbsession.delete(user)
                    # Done
                    raise HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
                except ValidationFailure as e:
                    rendered_form = e.render()
            else:
                appstruct = {ViewParam.USER_ID: user.id}
                rendered_form = form.render(appstruct)

    return dict(user=user,
                error=error,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


# =============================================================================
# Group management
# =============================================================================

@view_config(route_name=Routes.VIEW_GROUPS,
             permission=Permission.SUPERUSER,
             renderer="groups_view.mako")
def view_groups(req: CamcopsRequest) -> Dict[str, Any]:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    dbsession = req.dbsession
    q = dbsession.query(Group).order_by(Group.name)
    page = SqlalchemyOrmPage(query=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return dict(groups_page=page)


def get_group_from_request_group_id_or_raise(req: CamcopsRequest) -> Group:
    group_id = req.get_int_param(ViewParam.GROUP_ID)
    group = None
    if group_id is not None:
        dbsession = req.dbsession
        group = dbsession.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPBadRequest("No such group ID: {}".format(repr(group_id)))
    return group


@view_config(route_name=Routes.EDIT_GROUP,
             permission=Permission.SUPERUSER,
             renderer="group_edit.mako")
def edit_group(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_GROUPS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    group = get_group_from_request_group_id_or_raise(req)
    form = EditGroupForm(request=req, group=group)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # Simple attributes
            group.name = appstruct.get(ViewParam.NAME)
            group.description = appstruct.get(ViewParam.DESCRIPTION)
            group.upload_policy = appstruct.get(ViewParam.UPLOAD_POLICY)
            group.finalize_policy = appstruct.get(ViewParam.FINALIZE_POLICY)
            # Group cross-references
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            group_ids = [gid for gid in group_ids if gid != group.id]
            # ... don't bother saying "you can see yourself"
            other_groups = Group.get_groups_from_id_list(dbsession, group_ids)
            group.can_see_other_groups = other_groups
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        other_group_ids = list(group.ids_of_other_groups_group_may_see())
        other_groups = Group.get_groups_from_id_list(dbsession, other_group_ids)
        other_groups.sort(key=lambda g: g.name)
        appstruct = {
            ViewParam.GROUP_ID: group.id,
            ViewParam.NAME: group.name,
            ViewParam.DESCRIPTION: group.description or "",
            ViewParam.UPLOAD_POLICY: group.upload_policy or "",
            ViewParam.FINALIZE_POLICY: group.finalize_policy or "",
            ViewParam.GROUP_IDS: [g.id for g in other_groups],
        }
        rendered_form = form.render(appstruct)
    return dict(group=group,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.ADD_GROUP,
             permission=Permission.SUPERUSER,
             renderer="group_add.mako")
def add_group(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_GROUPS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    form = AddGroupForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            group = Group()
            group.name = appstruct.get(ViewParam.NAME)
            dbsession.add(group)
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def any_records_use_group(req: CamcopsRequest, group: Group) -> bool:
    dbsession = req.dbsession
    group_id = group.id
    # Our own or users filtering on us?
    # ... doesn't matter; see TaskFilter; stored as a CSV list so not part of
    #     database integrity checks.
    # Uploaded records?
    for cls in gen_orm_classes_from_base(GenericTabletRecordMixin):  # type: Type[GenericTabletRecordMixin]  # noqa
        # noinspection PyProtectedMember
        q = CountStarSpecializedQuery(cls, session=dbsession)\
            .filter(cls._group_id == group_id)
        if q.count_star() > 0:
            return True
    # No; all clean.
    return False


@view_config(route_name=Routes.DELETE_GROUP,
             permission=Permission.SUPERUSER,
             renderer="group_delete.mako")
def delete_group(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_GROUPS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    group = get_group_from_request_group_id_or_raise(req)
    form = DeleteGroupForm(request=req)
    rendered_form = ""
    error = ""
    if group.users:
        error = "Unable to delete group; there are users who are members!"
    else:
        if any_records_use_group(req, group):
            error = "Unable to delete group; records refer to it."
        else:
            if FormAction.DELETE in req.POST:
                try:
                    controls = list(req.POST.items())
                    appstruct = form.validate(controls)
                    assert appstruct.get(ViewParam.GROUP_ID) == group.id
                    req.dbsession.delete(group)
                    raise HTTPFound(req.route_url(route_back))
                except ValidationFailure as e:
                    rendered_form = e.render()
            else:
                appstruct = {ViewParam.GROUP_ID: group.id}
                rendered_form = form.render(appstruct)
    return dict(group=group,
                error=error,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


# =============================================================================
# Edit server settings
# =============================================================================

@view_config(route_name=Routes.EDIT_SERVER_SETTINGS,
             permission=Permission.SUPERUSER,
             renderer="server_settings_edit.mako")
def edit_server_settings(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(Routes.HOME))
    form = EditServerSettingsForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            dbsession = req.dbsession
            title = appstruct.get(ViewParam.DATABASE_TITLE)
            set_database_title(dbsession, title)
            raise HTTPFound(req.route_url(Routes.HOME))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        title = req.database_title
        appstruct = {ViewParam.DATABASE_TITLE: title}
        rendered_form = form.render(appstruct)
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.VIEW_ID_DEFINITIONS,
             permission=Permission.SUPERUSER,
             renderer="id_definitions_view.mako")
def view_id_definitions(req: CamcopsRequest) -> Dict[str, Any]:
    return dict(
        idnum_definitions=req.idnum_definitions,
    )


def get_iddef_from_request_which_idnum_or_raise(
        req: CamcopsRequest) -> IdNumDefinition:
    which_idnum = req.get_int_param(ViewParam.WHICH_IDNUM)
    iddef = req.dbsession.query(IdNumDefinition)\
        .filter(IdNumDefinition.which_idnum == which_idnum)\
        .first()
    if not iddef:
        raise HTTPBadRequest("No such ID definition: {}".format(
            repr(which_idnum)))
    return iddef


@view_config(route_name=Routes.EDIT_ID_DEFINITION,
             permission=Permission.SUPERUSER,
             renderer="id_definition_edit.mako")
def edit_id_definition(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ID_DEFINITIONS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    iddef = get_iddef_from_request_which_idnum_or_raise(req)
    form = EditIdDefinitionForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            iddef.description = appstruct.get(ViewParam.DESCRIPTION)
            iddef.short_description = appstruct.get(ViewParam.SHORT_DESCRIPTION)  # noqa
            clear_idnum_definition_cache()  # SPECIAL
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.WHICH_IDNUM: iddef.which_idnum,
            ViewParam.DESCRIPTION: iddef.description or "",
            ViewParam.SHORT_DESCRIPTION: iddef.short_description or "",
        }
        rendered_form = form.render(appstruct)
    return dict(iddef=iddef,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.ADD_ID_DEFINITION,
             permission=Permission.SUPERUSER,
             renderer="id_definition_add.mako")
def add_id_definition(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ID_DEFINITIONS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    form = AddIdDefinitionForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            iddef = IdNumDefinition(
                which_idnum=appstruct.get(ViewParam.WHICH_IDNUM),
                description=appstruct.get(ViewParam.DESCRIPTION),
                short_description=appstruct.get(ViewParam.SHORT_DESCRIPTION),
            )
            dbsession.add(iddef)
            clear_idnum_definition_cache()  # SPECIAL
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


def any_records_use_iddef(req: CamcopsRequest, iddef: IdNumDefinition) -> bool:
    # Helpfully, these are only referred to permanently from one place:
    q = CountStarSpecializedQuery(PatientIdNum, session=req.dbsession)\
        .filter(PatientIdNum.which_idnum == iddef.which_idnum)
    if q.count_star() > 0:
        return True
    # No; all clean.
    return False


@view_config(route_name=Routes.DELETE_ID_DEFINITION,
             permission=Permission.SUPERUSER,
             renderer="id_definition_delete.mako")
def delete_id_definition(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ID_DEFINITIONS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    iddef = get_iddef_from_request_which_idnum_or_raise(req)
    form = DeleteIdDefinitionForm(request=req)
    rendered_form = ""
    error = ""
    if any_records_use_iddef(req, iddef):
        error = "Unable to delete ID definition; records refer to it."
    else:
        if FormAction.DELETE in req.POST:
            try:
                controls = list(req.POST.items())
                appstruct = form.validate(controls)
                assert appstruct.get(ViewParam.WHICH_IDNUM) == iddef.which_idnum  # noqa
                req.dbsession.delete(iddef)
                clear_idnum_definition_cache()  # SPECIAL
                raise HTTPFound(req.route_url(route_back))
            except ValidationFailure as e:
                rendered_form = e.render()
        else:
            appstruct = {ViewParam.WHICH_IDNUM: iddef.which_idnum}
            rendered_form = form.render(appstruct)
    return dict(iddef=iddef,
                error=error,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


# =============================================================================
# Introspection of source code
# =============================================================================

@view_config(route_name=Routes.OFFER_INTROSPECTION)
def offer_introspection(req: CamcopsRequest) -> Response:
    """Page to offer CamCOPS server source code."""
    cfg = req.config
    if not cfg.introspection:
        return simple_failure(req, NO_INTROSPECTION_MSG)
    return render_to_response(
        "introspection_file_list.mako",
        dict(ifd_list=cfg.introspection_files),
        request=req
    )


@view_config(route_name=Routes.INTROSPECT)
def introspect(req: CamcopsRequest) -> Response:
    """Provide formatted source code."""
    cfg = req.config
    if not cfg.introspection:
        return simple_failure(req, NO_INTROSPECTION_MSG)
    filename = req.get_str_param(ViewParam.FILENAME, None)
    try:
        ifd = next(ifd for ifd in cfg.introspection_files
                   if ifd.prettypath == filename)
    except StopIteration:
        return simple_failure(req, INTROSPECTION_INVALID_FILE_MSG)
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
        return simple_failure(req, INTROSPECTION_FAILED_MSG)
    code_html = pygments.highlight(code, lexer, formatter)
    css = formatter.get_style_defs('.highlight')
    return render_to_response("introspect_file.mako",
                              dict(css=css,
                                   code_html=code_html),
                              request=req)


# =============================================================================
# Altering data
# =============================================================================

@view_config(route_name=Routes.ADD_SPECIAL_NOTE,
             permission=Permission.ADD_NOTES,
             renderer="special_note_add.mako")
def add_special_note(req: CamcopsRequest) -> Dict[str, Any]:
    """
    Add a special note to a task (after confirmation).
    """
    table_name = req.get_str_param(ViewParam.TABLE_NAME)
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    url_back = req.route_url(
        Routes.TASK,
        _query={
            ViewParam.TABLE_NAME: table_name,
            ViewParam.SERVER_PK: server_pk,
            ViewParam.VIEWTYPE: ViewArg.HTML,
        }
    )
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(url_back)
    task = task_factory(req, table_name, server_pk)
    if task is None:
        raise HTTPBadRequest("No such task: {}, PK={}".format(
            table_name, server_pk))
    form = AddSpecialNoteForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            note = appstruct.get(ViewParam.NOTE)
            task.apply_special_note(req, note)
            raise HTTPFound(url_back)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(task=task,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


# ***
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



# ***
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


# ***
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


# ***
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
        changes["dob"], DateFormat.ISO8601_DATE_ONLY, default="")
    for n in pls.valid_which_idnums():
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
            for n in pls.valid_which_idnums():
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
            dob_for_html = format_datetime(
                patient.dob, DateFormat.ISO8601_DATE_ONLY, default="")
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
            for n in pls.valid_which_idnums():
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


# ***
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


# ***
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
        Patient.__tablename__,
        Blob.__tablename__,
        DeviceStoredVar.__tablename__,
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
