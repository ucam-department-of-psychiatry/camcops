#!/usr/bin/env python
# camcops_server/webview.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

    .. code-block:: python

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

    .. code-block:: none

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

    .. code-block:: none

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

    .. code-block:: python

        html = " ... {param_blah} ...".format(param_blah=PARAM.BLAH)

    to

    .. code-block:: python

        html = " ... {PARAM.BLAH} ...".format(PARAM=PARAM)

    as in the first situation, PyCharm will check that "BLAH" is present in
    "PARAM", and in the second it won't. Automatic checking is worth a lot.

"""

import codecs
from collections import OrderedDict
import io
import logging
import os
# from pprint import pformat
import sqlite3
import tempfile
from typing import Any, Dict, Iterable, List, Tuple, Type
import zipfile

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.deform_utils import get_head_form_html
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import (
    PdfResponse,
    SqliteBinaryResponse,
    TextAttachmentResponse,
    XmlResponse,
    ZipResponse,
)
from cardinal_pythonlib.sqlalchemy.dialect import (
    get_dialect_name,
    SqlaDialectName,
)
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_orm_classes_from_base
from cardinal_pythonlib.sqlalchemy.orm_query import CountStarSpecializedQuery
from cardinal_pythonlib.sqlalchemy.session import get_engine_from_session
from deform.exception import ValidationFailure
from pendulum import DateTime as Pendulum
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
)
from pyramid.renderers import render_to_response
from pyramid.response import FileResponse, Response
from pyramid.security import Authenticated, NO_PERMISSION_REQUIRED
import pygments
import pygments.lexers
import pygments.lexers.sql
import pygments.lexers.web
import pygments.formatters
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session as SqlASession, sessionmaker
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import (and_, desc, exists, not_, or_,
                                       select, update)

from .cc_audit import audit, AuditEntry
from .cc_all_models import CLIENT_TABLE_MAP
from .cc_baseconstants import STATIC_ROOT_DIR
from .cc_constants import (
    CAMCOPS_URL,
    DateFormat,
    ERA_NOW,
    MINIMUM_PASSWORD_LENGTH,
    USER_NAME_FOR_SYSTEM,
)
from .cc_db import GenericTabletRecordMixin
from .cc_device import Device
from .cc_dump import copy_tasks_and_summaries
from .cc_forms import (
    AddGroupForm,
    AddIdDefinitionForm,
    AddSpecialNoteForm,
    AddUserGroupadminForm,
    AddUserSuperuserForm,
    AuditTrailForm,
    ChangeOtherPasswordForm,
    ChangeOwnPasswordForm,
    ChooseTrackerForm,
    DEFAULT_ROWS_PER_PAGE,
    DeleteGroupForm,
    DeleteIdDefinitionForm,
    DeletePatientChooseForm,
    DeletePatientConfirmForm,
    DeleteUserForm,
    DIALECT_CHOICES,
    EditGroupForm,
    EditIdDefinitionForm,
    EditPatientForm,
    EDIT_PATIENT_SIMPLE_PARAMS,
    EditServerSettingsForm,
    EditUserFullForm,
    EditUserGroupAdminForm,
    EditUserGroupMembershipFullForm,
    EditUserGroupMembershipGroupAdminForm,
    EraseTaskForm,
    ForciblyFinalizeChooseDeviceForm,
    ForciblyFinalizeConfirmForm,
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
from .cc_idnumdef import IdNumDefinition
from .cc_membership import UserGroupMembership
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_plot  # import side effects (configure matplotlib)  # noqa
from .cc_pyramid import (
    CamcopsPage,
    FormAction,
    HTTPFoundDebugVersion,
    PageUrl,
    Permission,
    Routes,
    SqlalchemyOrmPage,
    ViewArg,
    ViewParam,
)
from .cc_report import get_report_instance
from .cc_request import CamcopsRequest
from .cc_simpleobjects import IdNumReference
from .cc_specialnote import SpecialNote
from .cc_sqlalchemy import get_all_ddl
from .cc_task import Task
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
from .cc_user import SecurityAccountLockout, SecurityLoginFailure, User
from .cc_version import CAMCOPS_SERVER_VERSION

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_REDIRECT = False

if DEBUG_REDIRECT:
    log.warning("Debugging options enabled!")

if DEBUG_REDIRECT:
    HTTPFound = HTTPFoundDebugVersion


# =============================================================================
# Constants
# =============================================================================

ALLOWED_TASK_VIEW_TYPES = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
                           ViewArg.XML]
ALLOWED_TRACKER_VIEW_TYPE = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML,
                             ViewArg.XML]
CANNOT_DUMP = "User not authorized to dump data (for any group)."
CANNOT_REPORT = "User not authorized to run reports (for any group)."
# CAN_ONLY_CHANGE_OWN_PASSWORD = "You can only change your own password!"
# TASK_FAIL_MSG = "Task not found or user not authorized."
# NOT_AUTHORIZED_MSG = "User not authorized."
NO_INTROSPECTION_MSG = "Introspection has been disabled by your administrator."
INTROSPECTION_INVALID_FILE_MSG = "Invalid file for introspection"
INTROSPECTION_FAILED_MSG = "Failed to read file for introspection"
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

# noinspection PyUnusedLocal
@notfound_view_config(renderer="not_found.mako")
def not_found(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


# noinspection PyUnusedLocal
@view_config(context=HTTPBadRequest, renderer="bad_request.mako")
def bad_request(req: CamcopsRequest) -> Dict[str, Any]:
    """
    NOTE that this view only gets used from

    .. code-block:: python

        raise HTTPBadRequest("message")

    and not

    .. code-block:: python

        return HTTPBadRequest("message")

    ... so always raise it.
    """
    return {}


# =============================================================================
# Test pages
# =============================================================================
# Not on the menus...

# noinspection PyUnusedLocal
@view_config(route_name=Routes.TESTPAGE_PUBLIC_1,
             permission=NO_PERMISSION_REQUIRED)
def test_page_1(req: CamcopsRequest) -> Response:
    return Response("Hello! This is a public CamCOPS test page.")


# noinspection PyUnusedLocal
@view_config(route_name=Routes.TESTPAGE_PRIVATE_1)
def test_page_private_1(req: CamcopsRequest) -> Response:
    return Response("Private test page.")


# noinspection PyUnusedLocal
@view_config(route_name=Routes.TESTPAGE_PRIVATE_2,
             renderer="testpage.mako",
             permission=Permission.SUPERUSER)
def test_page_2(req: CamcopsRequest) -> Dict[str, Any]:
    # Contains POTENTIALLY SENSITIVE test information, including environment
    # variables
    return dict(param1="world")


# noinspection PyUnusedLocal
@view_config(route_name=Routes.TESTPAGE_PRIVATE_3,
             renderer="inherit_cache_test_child.mako",
             permission=Permission.SUPERUSER)
def test_page_3(req: CamcopsRequest) -> Dict[str, Any]:
    return {}


# noinspection PyUnusedLocal
@view_config(route_name=Routes.CRASH, permission=Permission.SUPERUSER)
def crash(req: CamcopsRequest) -> Response:
    """Deliberately raises an exception."""
    raise RuntimeError("Deliberately crashed. Should not affect other "
                       "processes.")


# noinspection PyUnusedLocal
@view_config(route_name=Routes.DEVELOPER, permission=Permission.SUPERUSER,
             renderer="developer.mako")
def developer_page(req: CamcopsRequest) -> Dict[str, Any]:
    """Shows developer menu."""
    return {}


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
                audit(req, "Login", user_id=user.id)
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
        req.user.agree_terms(req)
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
        if user.must_agree_terms:
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
    user = req.user
    assert user is not None
    expired = user.must_change_password
    form = ChangeOwnPasswordForm(request=req, must_differ=True)
    extra_msg = ""
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # -----------------------------------------------------------------
            # Change the password
            # -----------------------------------------------------------------
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
             permission=Permission.GROUPADMIN,
             renderer="change_other_password.mako")
def change_other_password(req: CamcopsRequest) -> Response:
    """For administrators, to change another's password."""
    form = ChangeOtherPasswordForm(request=req)
    username = None  # for type checker
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # -----------------------------------------------------------------
            # Change the password
            # -----------------------------------------------------------------
            user_id = appstruct.get(ViewParam.USER_ID)
            if user_id == req.user_id:
                return change_own_password(req)
            must_change_pw = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)
            new_password = appstruct.get(ViewParam.NEW_PASSWORD)
            user = User.get_user_by_id(req.dbsession, user_id)
            if not user:
                raise HTTPBadRequest("Missing user for id {}".format(user_id))
            assert_may_edit_user(req, user)
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
        if user_id == req.user_id:
            return change_own_password(req)
        user = User.get_user_by_id(req.dbsession, user_id)
        if user is None:
            raise HTTPBadRequest("Missing user for id {}".format(user_id))
        assert_may_edit_user(req, user)
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
    user = req.user
    cfg = req.config
    if user.superuser:
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
        authorized_as_groupadmin=user.authorized_as_groupadmin,
        authorized_as_superuser=user.superuser,
        authorized_for_reports=user.authorized_for_reports,
        authorized_to_dump=user.authorized_to_dump,
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
            # -----------------------------------------------------------------
            # Apply the changes
            # -----------------------------------------------------------------
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
            not user.may_view_all_patients_when_unfiltered and
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
        raise HTTPBadRequest(
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
            raise HTTPBadRequest("Invalid tasks specified")
        if not all(c.provides_trackers for c in task_classes):
            raise HTTPBadRequest("Not all tasks specified provide trackers")

    if viewtype not in ALLOWED_TRACKER_VIEW_TYPE:
        raise HTTPBadRequest("Invalid view type")

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
    elif viewtype == ViewArg.PDFHTML:  # debugging option
        return Response(
            tracker.get_pdf_html()
        )
    elif viewtype == ViewArg.XML:
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

@view_config(route_name=Routes.REPORTS_MENU, renderer="reports_menu.mako")
def reports_menu(req: CamcopsRequest) -> Dict[str, Any]:
    """Offer a menu of reports."""
    if not req.user.authorized_for_reports:
        raise HTTPBadRequest(CANNOT_REPORT)
    # Reports are not group-specific.
    # If you're authorized to see any, you'll see the whole menu.
    # (The *data* you get will be restricted to the group's you're authorized
    # to run reports for.)
    return {}


@view_config(route_name=Routes.OFFER_REPORT)
def offer_report(req: CamcopsRequest) -> Response:
    """
    Offer configuration options for a single report, or (following submission)
    redirect to serve that report
    """
    if not req.user.authorized_for_reports:
        raise HTTPBadRequest(CANNOT_REPORT)
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
            appstruct = form.validate(controls)  # may raise
            keys = report.get_http_query_keys()
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.REPORT_ID] = report_id
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET: this allows page
            # navigation whilst maintaining any report-specific parameters.
            raise HTTPFound(req.route_url(Routes.REPORT, _query=querydict))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render({ViewParam.REPORT_ID: report_id})
    return render_to_response(
        "report_offer.mako",
        dict(
            report=report,
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form])
        ),
        request=req
    )


@view_config(route_name=Routes.REPORT)
def serve_report(req: CamcopsRequest) -> Response:
    """
    Serve a configured report.
    """
    if not req.user.authorized_for_reports:
        raise HTTPBadRequest(CANNOT_REPORT)
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    if not report:
        raise HTTPBadRequest("No such report ID: {!r}".format(report_id))
    if report.superuser_only and not req.user.superuser:
        raise HTTPBadRequest("Report {!r} is restricted to the "
                             "superuser".format(report_id))

    return report.get_response(req)


# =============================================================================
# Research downloads
# =============================================================================

@view_config(route_name=Routes.OFFER_TSV_DUMP)
def offer_tsv_dump(req: CamcopsRequest) -> Response:
    """Form for basic research dump selection."""
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(CANNOT_DUMP)
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
            return HTTPFound(req.route_url(Routes.TSV_DUMP,
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


@view_config(route_name=Routes.TSV_DUMP)
def serve_tsv_dump(req: CamcopsRequest) -> Response:
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(CANNOT_DUMP)
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
        raise HTTPBadRequest("Bad {} parameter".format(ViewParam.DUMP_METHOD))
    collection = TaskCollection(
        req=req,
        taskfilter=taskfilter,
        as_dump=True,
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
            tsv_pages = task.get_tsv_pages(req)
            tsvcoll.add_pages(tsv_pages)

        if sort_by_heading:
            tsvcoll.sort_headings_within_all_pages()

        audit_descriptions.append("{}: {}".format(
            cls.__tablename__, ",".join(str(pk) for pk in pks)))

        # Write to ZIP.
        # If there are no valid task instances, there'll be no TSV; that's OK.
        for filename_stem in tsvcoll.get_page_names():
            tsv_filename = filename_stem + ".tsv"
            tsv_contents = tsvcoll.get_tsv_file(filename_stem)
            z.writestr(tsv_filename, tsv_contents.encode("utf-8"))

        # Attempt a little memory efficiency:
        collection.forget_task_class(cls)

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


@view_config(route_name=Routes.OFFER_SQL_DUMP)
def offer_sql_dump(req: CamcopsRequest) -> Response:
    """Form for SQL research dump selection."""
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(CANNOT_DUMP)
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


@view_config(route_name=Routes.SQL_DUMP)
def sql_dump(req: CamcopsRequest) -> Response:
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(CANNOT_DUMP)
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
        raise HTTPBadRequest("Bad {} parameter".format(ViewParam.DUMP_METHOD))
    collection = TaskCollection(
        req=req,
        taskfilter=taskfilter,
        as_dump=True,
        sort_method_by_class=TaskSortMethod.CREATION_DATE_ASC
    )

    if sqlite_method not in [ViewArg.SQL, ViewArg.SQLITE]:
        raise HTTPBadRequest("Bad {} parameter".format(
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
            # noinspection PyProtectedMember
            audit_descriptions.append("{}: {}".format(
                cls.__tablename__, ",".join(str(task._pk) for task in tasks)))
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
    SqlaDialectName.MYSQL: pygments.lexers.sql.MySqlLexer,
    SqlaDialectName.MSSQL: pygments.lexers.sql.SqlLexer,  # generic
    SqlaDialectName.ORACLE: pygments.lexers.sql.SqlLexer,  # generic
    SqlaDialectName.FIREBIRD: pygments.lexers.sql.SqlLexer,  # generic
    SqlaDialectName.POSTGRES: pygments.lexers.sql.PostgresLexer,
    SqlaDialectName.SQLITE: pygments.lexers.sql.SqlLexer,  # generic; SqliteConsoleLexer is wrong  # noqa
    SqlaDialectName.SYBASE: pygments.lexers.sql.SqlLexer,  # generic
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
        raise HTTPBadRequest("Bad HL7 message ID {}".format(hl7_msg_id))
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
        raise HTTPBadRequest("Bad HL7 run ID {}".format(hl7_run_id))
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
        all_task_classes=Task.all_subclasses_by_longname(),
    )


# =============================================================================
# User management
# =============================================================================

EDIT_USER_KEYS_GROUPADMIN = [
    # SPECIAL HANDLING # ViewParam.USER_ID,
    ViewParam.USERNAME,
    ViewParam.FULLNAME,
    ViewParam.EMAIL,
    ViewParam.MUST_CHANGE_PASSWORD,
    # SPECIAL HANDLING # ViewParam.GROUP_IDS,
]
EDIT_USER_KEYS_SUPERUSER = EDIT_USER_KEYS_GROUPADMIN + [
    ViewParam.SUPERUSER,
]
EDIT_USER_GROUP_MEMBERSHIP_KEYS_GROUPADMIN = [
    ViewParam.MAY_UPLOAD,
    ViewParam.MAY_REGISTER_DEVICES,
    ViewParam.MAY_USE_WEBVIEWER,
    ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED,
    ViewParam.MAY_DUMP_DATA,
    ViewParam.MAY_RUN_REPORTS,
    ViewParam.MAY_ADD_NOTES,
]
EDIT_USER_GROUP_MEMBERSHIP_KEYS_SUPERUSER = EDIT_USER_GROUP_MEMBERSHIP_KEYS_GROUPADMIN + [  # noqa
    ViewParam.GROUPADMIN,
]


def get_user_from_request_user_id_or_raise(req: CamcopsRequest) -> User:
    user_id = req.get_int_param(ViewParam.USER_ID)
    user = User.get_user_by_id(req.dbsession, user_id)
    if not user:
        raise HTTPBadRequest("No such user ID: {}".format(repr(user_id)))
    return user


@view_config(route_name=Routes.VIEW_ALL_USERS,
             permission=Permission.GROUPADMIN,
             renderer="users_view.mako")
def view_all_users(req: CamcopsRequest) -> Dict[str, Any]:
    rows_per_page = req.get_int_param(ViewParam.ROWS_PER_PAGE,
                                      DEFAULT_ROWS_PER_PAGE)
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    dbsession = req.dbsession
    q = (
        dbsession.query(User)
        .filter(User.username != USER_NAME_FOR_SYSTEM)
        .order_by(User.username)
    )
    if not req.user.superuser:
        # LOGIC SHOULD MATCH assert_may_edit_user
        # Restrict to users who are members of groups that I am an admin for:
        groupadmin_group_ids = req.user.ids_of_groups_user_is_admin_for
        ugm2 = UserGroupMembership.__table__.alias("ugm2")
        q = q.join(User.user_group_memberships)\
            .filter(not_(User.superuser))\
            .filter(UserGroupMembership.group_id.in_(groupadmin_group_ids))\
            .filter(
                ~exists().select_from(ugm2).where(
                    and_(
                        ugm2.c.user_id == User.id,
                        ugm2.c.groupadmin
                    )
                )
            )
        # ... no superusers
        # ... user must be a member of one of our groups
        # ... no groupadmins
        # https://stackoverflow.com/questions/14600619/using-not-exists-clause-in-sqlalchemy-orm-query  # noqa
        # log.critical(str(q))
    page = SqlalchemyOrmPage(query=q,
                             page=page_num,
                             items_per_page=rows_per_page,
                             url_maker=PageUrl(req))
    return dict(page=page,
                as_superuser=req.user.superuser)


def assert_may_edit_user(req: CamcopsRequest, user: User) -> None:
    """
    Checks that the requesting user (req.user) is allowed to edit the other
    user (user). Raises HTTPBadRequest otherwise.
    """
    # LOGIC SHOULD MATCH view_all_users
    if user.username == USER_NAME_FOR_SYSTEM:
        raise HTTPBadRequest("Nobody may edit the system user")
    if not req.user.superuser:
        if user.superuser:
            raise HTTPBadRequest("You may not edit a superuser")
        if user.is_a_groupadmin:
            raise HTTPBadRequest("You may not edit a group administrator")
        groupadmin_group_ids = req.user.ids_of_groups_user_is_admin_for
        if not any(gid in groupadmin_group_ids for gid in user.group_ids):
            raise HTTPBadRequest("You are not a group administrator for any "
                                 "groups that this user is in")


@view_config(route_name=Routes.VIEW_USER,
             permission=Permission.GROUPADMIN,
             renderer="view_other_user_info.mako")
def view_user(req: CamcopsRequest) -> Dict[str, Any]:
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    return dict(user=user)
    # Groupadmins may see some information regarding groups that aren't theirs
    # here, but can't alter it.


@view_config(route_name=Routes.EDIT_USER,
             permission=Permission.GROUPADMIN,
             renderer="user_edit.mako")
def edit_user(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ALL_USERS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    # Superusers can do everything, of course.
    # Groupadmins can change group memberships only for groups they control
    # (here: "fluid"). That means that there may be a subset of group
    # memberships for this user that they will neither see nor be able to
    # alter (here: "frozen"). They can also edit only a restricted set of
    # permissions.
    if req.user.superuser:
        form = EditUserFullForm(request=req)
        keys = EDIT_USER_KEYS_SUPERUSER
    else:
        form = EditUserGroupAdminForm(request=req)
        keys = EDIT_USER_KEYS_GROUPADMIN
    # Groups that we might change memberships for:
    all_fluid_groups = req.user.ids_of_groups_user_is_admin_for
    # All groups that the user is currently in:
    user_group_ids = user.group_ids
    # Group membership we won't touch:
    user_frozen_group_ids = list(set(user_group_ids) - set(all_fluid_groups))
    # Group memberships we might alter:
    user_fluid_group_ids = list(set(user_group_ids) & set(all_fluid_groups))
    # log.critical(
    #     "all_fluid_groups={}, user_group_ids={}, "
    #     "user_frozen_group_ids={}, user_fluid_group_ids={}".format(
    #         all_fluid_groups, user_group_ids,
    #         user_frozen_group_ids, user_fluid_group_ids)
    # )
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # -----------------------------------------------------------------
            # Apply the edits
            # -----------------------------------------------------------------
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
            for k in keys:
                setattr(user, k, appstruct.get(k))
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            # Add back in the groups we're not going to alter:
            final_group_ids = list(set(group_ids) | set(user_frozen_group_ids))
            user.set_group_ids(final_group_ids)
            # Also, if the user was uploading to a group that they are now no
            # longer a member of, we need to fix that
            if user.upload_group_id not in final_group_ids:
                user.upload_group_id = None
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {k: getattr(user, k) for k in keys}
        appstruct[ViewParam.USER_ID] = user.id
        appstruct[ViewParam.GROUP_IDS] = user_fluid_group_ids
        rendered_form = form.render(appstruct)
    return dict(user=user,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.EDIT_USER_GROUP_MEMBERSHIP,
             permission=Permission.GROUPADMIN,
             renderer="user_edit_group_membership.mako")
def edit_user_group_membership(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ALL_USERS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    ugm_id = req.get_int_param(ViewParam.USER_GROUP_MEMBERSHIP_ID)
    ugm = UserGroupMembership.get_ugm_by_id(req.dbsession, ugm_id)
    if not ugm:
        raise HTTPBadRequest("No such UserGroupMembership ID: {}".format(
            repr(ugm_id)))
    user = ugm.user
    assert_may_edit_user(req, user)
    if req.user.superuser:
        form = EditUserGroupMembershipFullForm(request=req)
        keys = EDIT_USER_GROUP_MEMBERSHIP_KEYS_SUPERUSER
    else:
        form = EditUserGroupMembershipGroupAdminForm(request=req)
        keys = EDIT_USER_GROUP_MEMBERSHIP_KEYS_GROUPADMIN
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # -----------------------------------------------------------------
            # Apply the changes
            # -----------------------------------------------------------------
            for k in keys:
                setattr(ugm, k, appstruct.get(k))
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {k: getattr(ugm, k) for k in keys}
        rendered_form = form.render(appstruct)
    return dict(ugm=ugm,
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
            # -----------------------------------------------------------------
            # Apply the changes
            # -----------------------------------------------------------------
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
             permission=Permission.GROUPADMIN)
def unlock_user(req: CamcopsRequest) -> Response:
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    user.enable(req)
    return simple_success(req, "User {} enabled".format(user.username))


@view_config(route_name=Routes.ADD_USER,
             permission=Permission.GROUPADMIN,
             renderer="user_add.mako")
def add_user(req: CamcopsRequest) -> Dict[str, Any]:
    route_back = Routes.VIEW_ALL_USERS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    if req.user.superuser:
        form = AddUserSuperuserForm(request=req)
    else:
        form = AddUserGroupadminForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # -----------------------------------------------------------------
            # Add the user
            # -----------------------------------------------------------------
            user = User()
            user.username = appstruct.get(ViewParam.USERNAME)
            user.set_password(req, appstruct.get(ViewParam.NEW_PASSWORD))
            user.must_change_password = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)  # noqa
            if User.get_user_by_name(dbsession, user.username):
                raise HTTPBadRequest("User with username {!r} already "
                                     "exists!".format(user.username))
            dbsession.add(user)
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            for gid in group_ids:
                user.user_group_memberships.append(UserGroupMembership(
                    user_id=user.id,
                    group_id=gid
                ))
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
             permission=Permission.GROUPADMIN,
             renderer="user_delete.mako")
def delete_user(req: CamcopsRequest) -> Dict[str, Any]:
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    form = DeleteUserForm(request=req)
    rendered_form = ""
    error = ""
    if user.id == req.user.id:
        error = "Can't delete your own user!"
    elif user.may_use_webviewer or user.may_upload:
        error = "Unable to delete user: user still has webviewer login " \
                "and/or tablet upload permission"
    elif ((not req.user.superuser) and
            bool(set(user.group_ids) -
                 set(req.user.ids_of_groups_user_is_admin_for))):
        error = "Unable to delete user: user belongs to groups that you do " \
                "not administer"
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
                    # ---------------------------------------------------------
                    # Delete the user and associated objects
                    # ---------------------------------------------------------
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
            # -----------------------------------------------------------------
            # Apply the changes
            # -----------------------------------------------------------------
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
            # -----------------------------------------------------------------
            # Add the group
            # -----------------------------------------------------------------
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
                    # ---------------------------------------------------------
                    # Delete the group
                    # ---------------------------------------------------------
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
            title = appstruct.get(ViewParam.DATABASE_TITLE)
            # -----------------------------------------------------------------
            # Apply changes
            # -----------------------------------------------------------------
            req.set_database_title(title)
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
            # -----------------------------------------------------------------
            # Alter the ID definition
            # -----------------------------------------------------------------
            iddef.description = appstruct.get(ViewParam.DESCRIPTION)
            iddef.short_description = appstruct.get(ViewParam.SHORT_DESCRIPTION)  # noqa
            iddef.hl7_id_type = appstruct.get(ViewParam.HL7_ID_TYPE)
            iddef.hl7_assigning_authority = appstruct.get(ViewParam.HL7_ASSIGNING_AUTHORITY)  # noqa
            # REMOVED # clear_idnum_definition_cache()  # SPECIAL
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.WHICH_IDNUM: iddef.which_idnum,
            ViewParam.DESCRIPTION: iddef.description or "",
            ViewParam.SHORT_DESCRIPTION: iddef.short_description or "",
            ViewParam.HL7_ID_TYPE: iddef.hl7_id_type or "",
            ViewParam.HL7_ASSIGNING_AUTHORITY: iddef.hl7_assigning_authority or "",  # noqa
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
            # -----------------------------------------------------------------
            # Add ID definition
            # -----------------------------------------------------------------
            dbsession.add(iddef)
            # REMOVED # clear_idnum_definition_cache()  # SPECIAL
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
                # -------------------------------------------------------------
                # Delete ID definition
                # -------------------------------------------------------------
                req.dbsession.delete(iddef)
                # REMOVED # clear_idnum_definition_cache()  # SPECIAL
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
# Altering data. Some of the more complex logic is here.
# =============================================================================

@view_config(route_name=Routes.ADD_SPECIAL_NOTE,
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
    user = req.user
    # noinspection PyProtectedMember
    if not user.authorized_to_add_special_note(task._group_id):
        raise HTTPBadRequest("Not authorized to add special notes for this "
                             "task's group")
    form = AddSpecialNoteForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            note = appstruct.get(ViewParam.NOTE)
            # -----------------------------------------------------------------
            # Apply special note
            # -----------------------------------------------------------------
            task.apply_special_note(req, note)
            raise HTTPFound(url_back)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.TABLE_NAME: table_name,
            ViewParam.SERVER_PK: server_pk,
        }
        rendered_form = form.render(appstruct)
    return dict(task=task,
                form=rendered_form,
                head_form_html=get_head_form_html(req, [form]))


@view_config(route_name=Routes.ERASE_TASK,
             permission=Permission.GROUPADMIN)
def erase_task(req: CamcopsRequest) -> Response:
    """
    Wipe all data from a task (after confirmation).

    Leaves the task record as a placeholder.
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
        return HTTPFound(url_back)
    task = task_factory(req, table_name, server_pk)
    if task is None:
        raise HTTPBadRequest("No such task: {}, PK={}".format(
            table_name, server_pk))
    if task.is_erased():
        raise HTTPBadRequest("Task already erased")
    if task.is_live_on_tablet():
        raise HTTPBadRequest(ERROR_TASK_LIVE)
    user = req.user
    # noinspection PyProtectedMember
    if not user.authorized_to_erase_tasks(task._group_id):
        raise HTTPBadRequest("Not authorized to erase tasks for this "
                             "task's group")
    form = EraseTaskForm(request=req)
    if FormAction.DELETE in req.POST:
        try:
            controls = list(req.POST.items())
            form.validate(controls)
            # -----------------------------------------------------------------
            # Erase task
            # -----------------------------------------------------------------
            task.manually_erase(req)
            return simple_success(
                req,
                "Task erased ({t}, server PK {pk}).".format(t=table_name,
                                                            pk=server_pk),
                '<a href="{url}">View amended task</a>.'.format(url=url_back)
            )
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.TABLE_NAME: table_name,
            ViewParam.SERVER_PK: server_pk,
        }
        rendered_form = form.render(appstruct)
    return render_to_response(
        "task_erase.mako",
        dict(
            task=task,
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form])
        ),
        request=req
    )


@view_config(route_name=Routes.DELETE_PATIENT,
             permission=Permission.GROUPADMIN)
def delete_patient(req: CamcopsRequest) -> Response:
    """
    Completely delete all data from a patient (after confirmation),
    within a specific group.
    """
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(Routes.HOME))

    first_form = DeletePatientChooseForm(request=req)
    second_form = DeletePatientConfirmForm(request=req)
    form = None
    final_phase = False
    if FormAction.SUBMIT in req.POST:
        # FIRST form has been submitted
        form = first_form
    elif FormAction.DELETE in req.POST:
        # SECOND AND FINAL form has been submitted
        form = second_form
        final_phase = True
    if form is not None:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            which_idnum = appstruct.get(ViewParam.WHICH_IDNUM)
            idnum_value = appstruct.get(ViewParam.IDNUM_VALUE)
            group_id = appstruct.get(ViewParam.GROUP_ID)
            if group_id not in req.user.ids_of_groups_user_is_admin_for:
                # rare occurrence; form should prevent it;
                # unless superuser has changed status since form was read
                raise HTTPBadRequest("You're not an admin for this group")
            # -----------------------------------------------------------------
            # Fetch tasks to be deleted.
            # -----------------------------------------------------------------
            dbsession = req.dbsession
            # Tasks first:
            idnum_ref = IdNumReference(which_idnum=which_idnum,
                                       idnum_value=idnum_value)
            taskfilter = TaskFilter()
            taskfilter.idnum_criteria = [idnum_ref]
            taskfilter.group_ids = [group_id]
            collection = TaskCollection(
                req=req,
                taskfilter=taskfilter,
                sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
                current_only=False  # unusual option!
            )
            tasks = collection.all_tasks
            n_tasks = len(tasks)
            patient_lineage_instances = Patient.get_patients_by_idnum(
                dbsession=dbsession,
                which_idnum=which_idnum,
                idnum_value=idnum_value,
                group_id=group_id,
                current_only=False
            )
            n_patient_instances = len(patient_lineage_instances)

            # -----------------------------------------------------------------
            # Bin out at this stage and offer confirmation page?
            # -----------------------------------------------------------------
            if not final_phase:
                # New appstruct; we don't want the validation code persisting
                appstruct = {
                    ViewParam.WHICH_IDNUM: which_idnum,
                    ViewParam.IDNUM_VALUE: idnum_value,
                    ViewParam.GROUP_ID: group_id,
                }
                rendered_form = second_form.render(appstruct)
                return render_to_response(
                    "patient_delete_confirm.mako",
                    dict(
                        form=rendered_form,
                        tasks=tasks,
                        n_patient_instances=n_patient_instances,
                        head_form_html=get_head_form_html(req, [form])
                    ),
                    request=req
                )

            # -----------------------------------------------------------------
            # Delete patient and associated tasks
            # -----------------------------------------------------------------
            for task in tasks:
                task.delete_entirely(req)
            # Then patients:
            for p in patient_lineage_instances:
                p.delete_with_dependants(req)
            msg = (
                "Patient with idnum{wi} = {iv} and associated tasks DELETED "
                "from group {g}. Deleted {nt} task records and {np} patient "
                "records (current and/or old).".format(
                    wi=which_idnum,
                    iv=idnum_value,
                    g=group_id,
                    nt=n_tasks,
                    np=n_patient_instances,
                )
            )
            audit(req, msg)
            return simple_success(req, msg)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        form = first_form
        rendered_form = first_form.render()
    return render_to_response(
        "patient_delete_choose.mako",
        dict(
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form])
        ),
        request=req
    )


@view_config(route_name=Routes.EDIT_PATIENT, permission=Permission.GROUPADMIN)
def edit_patient(req: CamcopsRequest) -> Response:
    if FormAction.CANCEL in req.POST:
        return HTTPFound(req.route_url(Routes.HOME))

    server_pk = req.get_int_param(ViewParam.SERVER_PK)
    patient = Patient.get_patient_by_pk(req.dbsession, server_pk)

    if not patient:
        raise HTTPBadRequest("No such patient")
    if not patient.group:
        raise HTTPBadRequest("Bad patient: not in a group")
    if not patient.user_may_edit(req):
        raise HTTPBadRequest("Not authorized to edit this patient")
    if not patient.is_editable:
        raise HTTPBadRequest(
            "Patient is not editable (likely: not finalized, so a copy is "
            "still on a client device")

    taskfilter = TaskFilter()
    taskfilter.device_ids = [patient.get_device_id()]
    taskfilter.group_ids = [patient.group.id]
    taskfilter.era = patient.get_era()
    collection = TaskCollection(
        req=req,
        taskfilter=taskfilter,
        sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
        current_only=False  # unusual option!
    )
    affected_tasks = collection.all_tasks

    form = EditPatientForm(request=req)
    dbsession = req.dbsession
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # -----------------------------------------------------------------
            # Apply edits
            # -----------------------------------------------------------------
            # Calculate the changes, and apply them to the Patient object
            changes = OrderedDict()  # type: Dict[str, Tuple[Any, Any]]
            for k in EDIT_PATIENT_SIMPLE_PARAMS:
                new_value = appstruct.get(k)
                if k in [ViewParam.FORENAME, ViewParam.SURNAME]:
                    new_value = new_value.upper()
                old_value = getattr(patient, k)
                if new_value == old_value:
                    continue
                if new_value in [None, ""] and old_value in [None, ""]:
                    # Nothing really changing!
                    continue
                changes[k] = (old_value, new_value)
                setattr(patient, k, new_value)
            # The ID numbers are more complex.
            # log.critical("{}", pformat(appstruct))
            new_idrefs = [
                IdNumReference(which_idnum=idrefdict[ViewParam.WHICH_IDNUM],
                               idnum_value=idrefdict[ViewParam.IDNUM_VALUE])
                for idrefdict in appstruct.get(ViewParam.ID_REFERENCES)
            ]
            for idnum in patient.idnums:
                matching_idref = next(
                    (idref for idref in new_idrefs
                     if idref.which_idnum == idnum.which_idnum), None)
                if not matching_idref:
                    # Delete ID numbers not present in the new set
                    changes["idnum{} ({})".format(
                        idnum.which_idnum,
                        req.get_id_desc(idnum.which_idnum))
                    ] = (idnum.idnum_value, None)
                    idnum.mark_as_deleted(req)
                elif matching_idref.idnum_value != idnum.idnum_value:
                    # Modify altered ID numbers present in the old + new sets
                    changes["idnum{} ({})".format(
                        idnum.which_idnum,
                        req.get_id_desc(idnum.which_idnum))
                    ] = (idnum.idnum_value, matching_idref.idnum_value)
                    new_idnum = PatientIdNum()
                    new_idnum.id = idnum.id
                    new_idnum.patient_id = idnum.patient_id
                    new_idnum.which_idnum = idnum.which_idnum
                    new_idnum.idnum_value = matching_idref.idnum_value
                    new_idnum.set_predecessor(req, idnum)
            max_existing_pidnum_id = None
            for idref in new_idrefs:
                matching_idnum = next(
                    (idnum for idnum in patient.idnums
                     if idnum.which_idnum == idref.which_idnum), None)
                if not matching_idnum:
                    # Create ID numbers where they were absent
                    changes["idnum{} ({})".format(
                        idref.which_idnum,
                        req.get_id_desc(idref.which_idnum))
                    ] = (None, idref.idnum_value)
                    # We need to establish an "id" field, which is the PK as
                    # seen by the tablet. The tablet has lost interest in these
                    # records, since _era != ERA_NOW, so all we have to do is
                    # pick a number that's not in use.
                    if max_existing_pidnum_id is None:
                        # noinspection PyProtectedMember
                        max_existing_pidnum_id = dbsession\
                            .query(func.max(PatientIdNum.id))\
                            .filter(PatientIdNum._device_id ==
                                    patient.get_device_id())\
                            .filter(PatientIdNum._era == patient.get_era())\
                            .scalar()
                        if max_existing_pidnum_id is None:
                            max_existing_pidnum_id = 0  # so start at 1
                    new_idnum = PatientIdNum()
                    new_idnum.id = max_existing_pidnum_id + 1
                    max_existing_pidnum_id += 1
                    new_idnum.patient_id = patient.id
                    new_idnum.which_idnum = idref.which_idnum
                    new_idnum.idnum_value = idref.idnum_value
                    new_idnum.create_fresh(req,
                                           device_id=patient.get_device_id(),
                                           era=patient.get_era(),
                                           group_id=patient.get_group_id())
                    dbsession.add(new_idnum)
            if not changes:
                return simple_success(
                    req,
                    "No changes required for patient record with server PK {} "
                    "(all new values matched old values)".format(server_pk))

            # Below here, changes have definitely been made.
            change_msg = "Patient details edited. Changes: " + "; ".join(
                "{k}: {old!r} → {new!r}".format(k=k, old=old, new=new)
                for k, (old, new) in changes.items()
            )

            # Apply special note to patient
            patient.apply_special_note(req, change_msg, "Patient edited")

            # Patient details changed, so resend any tasks via HL7
            for task in affected_tasks:
                task.delete_from_hl7_message_log(req)

            # Done
            return simple_success(
                req,
                "Amended patient record with server PK {}. Changes were: "
                "{}".format(server_pk, change_msg))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {k: getattr(patient, k)
                     for k in EDIT_PATIENT_SIMPLE_PARAMS}
        appstruct[ViewParam.SERVER_PK] = server_pk
        appstruct[ViewParam.GROUP_ID] = patient.group.id
        appstruct[ViewParam.ID_REFERENCES] = [
            {ViewParam.WHICH_IDNUM: pidnum.which_idnum,
             ViewParam.IDNUM_VALUE: pidnum.idnum_value}
            for pidnum in patient.idnums
        ]
        rendered_form = form.render(appstruct)
    return render_to_response(
        "patient_edit.mako",
        dict(
            patient=patient,
            form=rendered_form,
            tasks=affected_tasks,
            head_form_html=get_head_form_html(req, [form])
        ),
        request=req
    )


@view_config(route_name=Routes.FORCIBLY_FINALIZE,
             permission=Permission.GROUPADMIN)
def forcibly_finalize(req: CamcopsRequest) -> Response:
    """
    Force-finalize all live (_era == ERA_NOW) records from a device.
    Available to group administrators if all those records are within their
    groups (otherwise, it's a superuser operation).

    This is a superuser permission, since we can't guarantee to know what group
    the device relates to.
    """
    if FormAction.CANCEL in req.POST:
        return HTTPFound(req.route_url(Routes.HOME))

    dbsession = req.dbsession
    first_form = ForciblyFinalizeChooseDeviceForm(request=req)
    second_form = ForciblyFinalizeConfirmForm(request=req)
    form = None
    final_phase = False
    if FormAction.SUBMIT in req.POST:
        # FIRST form has been submitted
        form = first_form
    elif FormAction.FINALIZE in req.POST:
        # SECOND form has been submitted:
        form = second_form
        final_phase = True
    if form is not None:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # log.critical("{}", pformat(appstruct))
            device_id = appstruct.get(ViewParam.DEVICE_ID)
            device = Device.get_device_by_id(dbsession, device_id)
            if device is None:
                raise HTTPBadRequest("No such device: {!r}".format(device_id))
            # -----------------------------------------------------------------
            # If at the first stage, bin out and offer confirmation page
            # -----------------------------------------------------------------
            if not final_phase:
                appstruct = {ViewParam.DEVICE_ID: device_id}
                rendered_form = second_form.render(appstruct)
                taskfilter = TaskFilter()
                taskfilter.device_ids = [device_id]
                taskfilter.era = ERA_NOW
                collection = TaskCollection(
                    req=req,
                    taskfilter=taskfilter,
                    sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
                    current_only=False  # unusual option!
                )
                tasks = collection.all_tasks
                return render_to_response(
                    "device_forcibly_finalize_confirm.mako",
                    dict(form=rendered_form,
                         tasks=tasks,
                         head_form_html=get_head_form_html(req, [form])),
                    request=req
                )
            # -----------------------------------------------------------------
            # Check it's permitted
            # -----------------------------------------------------------------
            if not req.user.superuser:
                admin_group_ids = req.user.ids_of_groups_user_is_admin_for
                for clienttable in CLIENT_TABLE_MAP.values():
                    # noinspection PyProtectedMember
                    count_query = (
                        select([func.count()])
                        .select_from(clienttable)
                        .where(clienttable.c._device_id == device_id)
                        .where(clienttable.c._era == ERA_NOW)
                        .where(clienttable.c._group_id.notin_(admin_group_ids))
                    )
                    n = dbsession.execute(count_query).scalar()
                    if n > 0:
                        raise HTTPBadRequest(
                            "Some records for this device are in groups for "
                            "which you are not an administrator")
            # -----------------------------------------------------------------
            # Forcibly finalize
            # -----------------------------------------------------------------
            new_era = req.now_iso8601_era_format
            for clienttable in CLIENT_TABLE_MAP.values():
                # noinspection PyProtectedMember
                finalize_statement = (
                    update(clienttable)
                    .where(clienttable.c._device_id == device_id)
                    .where(clienttable.c._era == ERA_NOW)
                    .values(_era=new_era,
                            _preserving_user_id=req.user_id,
                            _forcibly_preserved=True)
                )
                dbsession.execute(finalize_statement)
            # Field names are different in server-side tables, so they need
            # special handling:
            SpecialNote.forcibly_preserve_special_notes_for_device(req,
                                                                   device_id)
            # -----------------------------------------------------------------
            # Done
            # -----------------------------------------------------------------
            msg = "Live records for device {} ({}) forcibly finalized".format(
                device_id, device.friendly_name)
            audit(req, msg)
            return simple_success(req, msg)

        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        form = first_form
        rendered_form = form.render()  # no appstruct
    return render_to_response(
        "device_forcibly_finalize_choose.mako",
        dict(form=rendered_form,
             head_form_html=get_head_form_html(req, [form])),
        request=req
    )


# =============================================================================
# Static assets
# =============================================================================
# https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#advanced-static  # noqa

DEFORM_MISSING_GLYPH = os.path.join(STATIC_ROOT_DIR,
                                    "glyphicons-halflings-regular.woff2")


@view_config(route_name=Routes.BUGFIX_DEFORM_MISSING_GLYPHS,
             permission=NO_PERMISSION_REQUIRED)
def static_bugfix_deform_missing_glyphs(req: CamcopsRequest) -> Response:
    """
    Hack for a missing-file bug in deform==2.0.4:
    """
    return FileResponse(DEFORM_MISSING_GLYPH, request=req)
