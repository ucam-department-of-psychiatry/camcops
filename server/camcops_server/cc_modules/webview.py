#!/usr/bin/env python

"""
camcops_server/cc_modules/webview.py

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

**Implements the CamCOPS web front end.**

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

        @view_config(route_name="myroute", request_method="POST")
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
            string (as in https://somewhere/path?key=value) and the body (e.g.
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

from collections import OrderedDict
import json
import logging
import os

# from pprint import pformat
import time
from typing import (
    Any,
    cast,
    Dict,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TYPE_CHECKING,
)

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.deform_utils import get_head_form_html
from cardinal_pythonlib.httpconst import HttpMethod, MimeType
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import (
    BinaryResponse,
    JsonResponse,
    PdfResponse,
    XmlResponse,
)
from cardinal_pythonlib.sqlalchemy.dialect import (
    get_dialect_name,
    SqlaDialectName,
)
from cardinal_pythonlib.sizeformatter import bytes2human
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_orm_classes_from_base
from cardinal_pythonlib.sqlalchemy.orm_query import CountStarSpecializedQuery
from cardinal_pythonlib.sqlalchemy.session import get_engine_from_session
from deform.exception import ValidationFailure
from pendulum import DateTime as Pendulum
import pyotp
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
from sqlalchemy.orm import joinedload, Query
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import desc, or_, select, update

from camcops_server.cc_modules.cc_audit import audit, AuditEntry
from camcops_server.cc_modules.cc_all_models import CLIENT_TABLE_MAP
from camcops_server.cc_modules.cc_client_api_core import (
    BatchDetails,
    get_server_live_records,
    UploadTableChanges,
    values_preserve_now,
)
from camcops_server.cc_modules.cc_client_api_helpers import (
    upload_commit_order_sorter,
)
from camcops_server.cc_modules.cc_constants import (
    CAMCOPS_URL,
    DateFormat,
    ERA_NOW,
    GITHUB_RELEASES_URL,
    JSON_INDENT,
    MfaMethod,
)
from camcops_server.cc_modules.cc_db import (
    GenericTabletRecordMixin,
    FN_DEVICE_ID,
    FN_ERA,
    FN_GROUP_ID,
    FN_PK,
)
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_export import (
    DownloadOptions,
    make_exporter,
    UserDownloadFile,
)
from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportedTaskEmail,
    ExportedTaskFhir,
    ExportedTaskFhirEntry,
    ExportedTaskFileGroup,
    ExportedTaskHL7Message,
    ExportedTaskRedcap,
)
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_forms import (
    AddGroupForm,
    AddIdDefinitionForm,
    AddSpecialNoteForm,
    AddUserGroupadminForm,
    AddUserSuperuserForm,
    AuditTrailForm,
    ChangeOtherPasswordForm,
    ChangeOwnPasswordForm,
    ChooseTrackerForm,
    DEFORM_ACCORDION_BUG,
    DEFAULT_ROWS_PER_PAGE,
    DeleteGroupForm,
    DeleteIdDefinitionForm,
    DeletePatientChooseForm,
    DeletePatientConfirmForm,
    DeleteServerCreatedPatientForm,
    DeleteSpecialNoteForm,
    DeleteTaskScheduleForm,
    DeleteTaskScheduleItemForm,
    DeleteUserForm,
    EDIT_PATIENT_SIMPLE_PARAMS,
    EditFinalizedPatientForm,
    EditGroupForm,
    EditIdDefinitionForm,
    EditOtherUserMfaForm,
    EditServerCreatedPatientForm,
    EditServerSettingsForm,
    EditTaskFilterForm,
    EditTaskScheduleForm,
    EditTaskScheduleItemForm,
    EditUserFullForm,
    EditUserGroupAdminForm,
    EditUserGroupMembershipGroupAdminForm,
    EditUserGroupPermissionsFullForm,
    EraseTaskForm,
    ExportedTaskListForm,
    ForciblyFinalizeChooseDeviceForm,
    ForciblyFinalizeConfirmForm,
    get_sql_dialect_choices,
    LoginForm,
    MfaHotpEmailForm,
    MfaHotpSmsForm,
    MfaMethodForm,
    MfaTotpForm,
    OfferBasicDumpForm,
    OfferSqlDumpForm,
    OfferTermsForm,
    OtpTokenForm,
    RefreshTasksForm,
    SendEmailForm,
    SetUserUploadGroupForm,
    TasksPerPageForm,
    UserDownloadDeleteForm,
    UserFilterForm,
    ViewDdlForm,
)
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum

# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_plot  # import side effects (configure matplotlib)  # noqa
from camcops_server.cc_modules.cc_pyramid import (
    CamcopsPage,
    FlashQueue,
    FormAction,
    HTTPFoundDebugVersion,
    Icons,
    PageUrl,
    Permission,
    Routes,
    SqlalchemyOrmPage,
    ViewArg,
    ViewParam,
)
from camcops_server.cc_modules.cc_report import get_report_instance
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_simpleobjects import (
    IdNumReference,
    TaskExportOptions,
)
from camcops_server.cc_modules.cc_specialnote import SpecialNote
from camcops_server.cc_modules.cc_session import CamcopsSession
from camcops_server.cc_modules.cc_sqlalchemy import get_all_ddl
from camcops_server.cc_modules.cc_task import (
    tablename_to_task_class_dict,
    Task,
)
from camcops_server.cc_modules.cc_taskcollection import (
    TaskFilter,
    TaskCollection,
    TaskSortMethod,
)
from camcops_server.cc_modules.cc_taskfactory import task_factory
from camcops_server.cc_modules.cc_taskfilter import (
    task_classes_from_table_names,
    TaskClassSortMethod,
)
from camcops_server.cc_modules.cc_taskindex import (
    PatientIdNumIndexEntry,
    TaskIndexEntry,
    update_indexes_and_push_exports,
)
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    PatientTaskScheduleEmail,
    TaskSchedule,
    TaskScheduleItem,
    task_schedule_item_sort_order,
)
from camcops_server.cc_modules.cc_text import SS
from camcops_server.cc_modules.cc_tracker import ClinicalTextView, Tracker
from camcops_server.cc_modules.cc_user import (
    SecurityAccountLockout,
    SecurityLoginFailure,
    User,
)
from camcops_server.cc_modules.cc_validators import (
    validate_download_filename,
    validate_export_recipient_name,
    validate_ip_address,
    validate_task_tablename,
    validate_username,
)
from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION
from camcops_server.cc_modules.cc_view_classes import (
    CreateView,
    DeleteView,
    FormView,
    FormWizardMixin,
    UpdateView,
)

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from deform.form import Form

    # noinspection PyUnresolvedReferences
    from camcops_server.cc_modules.cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_REDIRECT = False

if DEBUG_REDIRECT:
    log.warning("Debugging options enabled!")

if DEBUG_REDIRECT:
    HTTPFound = HTTPFoundDebugVersion  # noqa: F811


# =============================================================================
# Cache control, for the http_cache parameter of view_config etc.
# =============================================================================

NEVER_CACHE = 0


# =============================================================================
# Constants -- for Mako templates
# =============================================================================
# Keys that will be added to a context dictionary that is passed to a Mako
# template. For example, a key of "title" can be rendered within the template
# as ${title}. Some are used frequently, so we have them here as constants.

MAKO_VAR_TITLE = "title"
TEMPLATE_GENERIC_FORM = "generic_form.mako"


# =============================================================================
# Constants -- mutated into translated phrases
# =============================================================================


def errormsg_cannot_dump(req: "CamcopsRequest") -> str:
    _ = req.gettext
    return _("User not authorized to dump data (for any group).")


def errormsg_cannot_report(req: "CamcopsRequest") -> str:
    _ = req.gettext
    return _("User not authorized to run reports (for any group).")


def errormsg_task_live(req: "CamcopsRequest") -> str:
    _ = req.gettext
    return _("Task is live on tablet; finalize (or force-finalize) first.")


# =============================================================================
# Unused
# =============================================================================

# def query_result_html_core(req: "CamcopsRequest",
#                            descriptions: Sequence[str],
#                            rows: Sequence[Sequence[Any]],
#                            null_html: str = "<i>NULL</i>") -> str:
#     return render("query_result_core.mako",
#                   dict(descriptions=descriptions,
#                        rows=rows,
#                        null_html=null_html),
#                   request=req)


# def query_result_html_orm(req: "CamcopsRequest",
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
@notfound_view_config(renderer="not_found.mako", http_cache=NEVER_CACHE)
def not_found(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    "Page not found" view.
    """
    return {"msg": "", "extra_html": ""}


# noinspection PyUnusedLocal
@view_config(
    context=HTTPBadRequest, renderer="bad_request.mako", http_cache=NEVER_CACHE
)
def bad_request(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    "Bad request" view.

    NOTE that this view only gets used from

    .. code-block:: python

        raise HTTPBadRequest("message")

    and not

    .. code-block:: python

        return HTTPBadRequest("message")

    ... so always raise it.
    """
    return {"msg": "", "extra_html": ""}


# =============================================================================
# Test pages
# =============================================================================

# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.TESTPAGE_PUBLIC_1,
    permission=NO_PERMISSION_REQUIRED,
    http_cache=NEVER_CACHE,
)
def test_page_1(req: "CamcopsRequest") -> Response:
    """
    A public test page with no content.
    """
    _ = req.gettext
    return Response(_("Hello! This is a public CamCOPS test page."))


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.TEST_NHS_NUMBERS,
    permission=NO_PERMISSION_REQUIRED,
    renderer="test_nhs_numbers.mako",
    http_cache=NEVER_CACHE,
)
def test_nhs_numbers(req: "CamcopsRequest") -> Response:
    """
    Random Test NHS numbers for testing
    """
    from cardinal_pythonlib.nhs import generate_random_nhs_number

    nhs_numbers = [generate_random_nhs_number() for _ in range(10)]
    return dict(test_nhs_numbers=nhs_numbers)


# noinspection PyUnusedLocal
@view_config(route_name=Routes.TESTPAGE_PRIVATE_1, http_cache=NEVER_CACHE)
def test_page_private_1(req: "CamcopsRequest") -> Response:
    """
    A private test page with no informative content, but which should only
    be accessible to authenticated users.
    """
    _ = req.gettext
    return Response(_("Private test page."))


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.TESTPAGE_PRIVATE_2,
    permission=Permission.SUPERUSER,
    renderer="testpage.mako",
    http_cache=NEVER_CACHE,
)
def test_page_2(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    A private test page containing POTENTIALLY SENSITIVE test information,
    including environment variables, that should only be accessible to
    superusers.
    """
    return dict(param1="world")


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.TESTPAGE_PRIVATE_3,
    permission=Permission.SUPERUSER,
    renderer="inherit_cache_test_child.mako",
    http_cache=NEVER_CACHE,
)
def test_page_3(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    A private test page that tests template inheritance.
    """
    return {}


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.TESTPAGE_PRIVATE_4,
    permission=Permission.SUPERUSER,
    renderer="test_template_filters.mako",
    http_cache=NEVER_CACHE,
)
def test_page_4(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    A private test page that tests Mako filtering.
    """
    return dict(test_strings=["plain", "normal <b>bold</b> normal"])


# noinspection PyUnusedLocal,PyTypeChecker
@view_config(
    route_name=Routes.CRASH,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def crash(req: "CamcopsRequest") -> Response:
    """
    A view that deliberately raises an exception.
    """
    _ = req.gettext
    raise RuntimeError(
        _("Deliberately crashed. Should not affect other processes.")
    )


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.DEVELOPER,
    permission=Permission.SUPERUSER,
    renderer="developer.mako",
    http_cache=NEVER_CACHE,
)
def developer_page(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Shows the developer menu.
    """
    return {}


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.AUDIT_MENU,
    permission=Permission.SUPERUSER,
    renderer="audit_menu.mako",
    http_cache=NEVER_CACHE,
)
def audit_menu(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Shows the auditing menu.
    """
    return {}


# =============================================================================
# Authorization: login, logout, login failures, terms/conditions
# =============================================================================

# Do NOT use extra parameters for functions decorated with @view_config;
# @view_config can take functions like "def view(request)" but also
# "def view(context, request)", so if you add additional parameters, it thinks
# you're doing the latter and sends parameters accordingly.


class MfaMixin(FormWizardMixin):
    """
    Enhances FormWizardMixin to include a multi-factor authentication step.
    This must be named "mfa" in the subclass, via the ``SELF_MFA`` variable.

    This handles:

    - Timing out
    - Generating, sending and checking the six-digit code used for
      authentication

    The subclass should:

    - Set ``mfa_user`` on the class to be an instance of the User to be
      authenticated.
    - Call ``handle_authentication_type()`` in the appropriate step.
    - Call ``otp_is_valid()`` and ``fail_bad_mfa_code()`` in the appropriate
      step.

    See ``LoginView`` for an example that works with the yet-to-be-logged-in
    user.
    See ``ChangeOwnPasswordView`` for an example with the logged-in user.
    """

    STEP_PASSWORD = "password"
    STEP_MFA = "mfa"

    KEY_TITLE_HTML = "title_html"
    KEY_INSTRUCTIONS = "instructions"
    KEY_MFA_TIME = "mfa_time"

    def __init__(self, *args, **kwargs) -> None:
        self._mfa_user: Optional[User] = None
        super().__init__(*args, **kwargs)

    # -------------------------------------------------------------------------
    # mfa_user
    # -------------------------------------------------------------------------
    # Set during __init__ by LoggedInUserMfaMixin, or via a more complex
    # process by LoginView.

    @property
    def mfa_user(self) -> Optional[User]:
        """
        The user undergoing authentication.
        """
        return self._mfa_user

    @mfa_user.setter
    def mfa_user(self, user: Optional[User]) -> None:
        """
        Sets the current user being authenticated.
        """
        self._mfa_user = user

    # -------------------------------------------------------------------------
    # Dispatch and timeouts
    # -------------------------------------------------------------------------

    def dispatch(self) -> Response:
        # Docstring in superclass.
        if self.timed_out():
            self.fail_timed_out()  # will raise

        return super().dispatch()

    def timed_out(self) -> bool:
        """
        Has authentication timed out?
        """
        if self.step != self.STEP_MFA:
            return False

        timeout = self.request.config.mfa_timeout_s
        if timeout == 0:
            return False

        login_time = self.state.get(self.KEY_MFA_TIME)
        if login_time is None:
            return False

        return int(time.time()) > login_time + timeout

    # -------------------------------------------------------------------------
    # Extra context for templates
    # -------------------------------------------------------------------------

    def get_extra_context(self) -> Dict[str, Any]:
        # Docstring in superclass.
        if self.step == self.STEP_MFA:
            context = {
                self.KEY_TITLE_HTML: self.request.icon_text(
                    icon=self.get_mfa_icon(), text=self.get_mfa_title()
                ),
                self.KEY_INSTRUCTIONS: self.get_mfa_instructions(),
            }
            return context
        else:
            return {}

    def get_mfa_icon(self) -> str:
        """
        Returns an icon to let the user know which MFA method is being used.
        """
        method = self.mfa_user.mfa_method

        if method == MfaMethod.TOTP:
            return "shield-shaded"

        elif method == MfaMethod.HOTP_EMAIL:
            return "envelope"

        elif method == MfaMethod.HOTP_SMS:
            return "chat-left-dots"

        else:
            return "Error: get_mfa_icon() called for invalid MFA method"

    def get_mfa_title(self) -> str:
        """
        Returns a title for the page that requests the code itself.
        """
        _ = self.request.gettext
        method = self.mfa_user.mfa_method

        if method == MfaMethod.TOTP:
            return _("Authenticate via your authentication app")

        elif method == MfaMethod.HOTP_EMAIL:
            return _("Authenticate via e-mail")

        elif method == MfaMethod.HOTP_SMS:
            return _("Authenticate via SMS")

        else:
            return "Error: get_mfa_title() called for invalid MFA method"

    def get_mfa_instructions(self) -> str:
        """
        Return user instructions for the relevant MFA method.
        """
        _ = self.request.gettext
        method = self.mfa_user.mfa_method

        if method == MfaMethod.TOTP:
            return _(
                "Enter the code for CamCOPS displayed on your "
                "authentication app."
            )

        elif method == MfaMethod.HOTP_EMAIL:
            return _("We've sent a code by email to {}.").format(
                self.mfa_user.partial_email
            )

        elif method == MfaMethod.HOTP_SMS:
            return _("We've sent a code by text message to {}").format(
                self.mfa_user.partial_phone_number
            )

        else:
            return "Error: get_mfa_instruction() called for invalid MFA method"

    # -------------------------------------------------------------------------
    # MFA handling
    # -------------------------------------------------------------------------

    def handle_authentication_type(self) -> None:
        """
        Function to be called when we want an MFA code to be created.
        """
        mfa_user = self.mfa_user
        mfa_user.ensure_mfa_info()
        mfa_method = mfa_user.mfa_method

        if mfa_method == MfaMethod.TOTP:
            # Nothing to do. The app generates the code.
            return

        # Record the time of code creation:
        self.state[self.KEY_MFA_TIME] = int(time.time())

        if mfa_method == MfaMethod.HOTP_EMAIL:
            self.send_authentication_email()
        elif mfa_method == MfaMethod.HOTP_SMS:
            self.send_authentication_sms()
        else:
            raise ValueError(
                f"MfaMixin.handle_authentication_type: "
                f"unexpected mfa_method {mfa_method!r}"
            )

    def send_authentication_email(self) -> None:
        """
        E-mail the code to the user.
        """
        _ = self.request.gettext
        config = self.request.config
        kwargs = dict(
            from_addr=config.email_from,
            to=self.mfa_user.email,
            subject=_("CamCOPS authentication"),
            body=self.get_hotp_message(),
            content_type=MimeType.TEXT,
        )

        email = Email(**kwargs)
        success = email.send(
            host=config.email_host,
            username=config.email_host_username,
            password=config.email_host_password,
            port=config.email_port,
            use_tls=config.email_use_tls,
        )
        if success:
            msg = _("E-mail sent")
            queue = FlashQueue.SUCCESS
        else:
            msg = _(
                "Failed to send e-mail! "
                "Please try again or contact your administrator."
            )
            queue = FlashQueue.DANGER
        self.request.session.flash(msg, queue=queue)

    def send_authentication_sms(self) -> None:
        """
        Send a code to the user via SMS (text message).
        """
        backend = self.request.config.sms_backend
        backend.send_sms(
            self.mfa_user.raw_phone_number, self.get_hotp_message()
        )

    def get_hotp_message(self) -> str:
        """
        Return a human-readable message containing an HOTP (HMAC-Based One-Time
        Password).
        """
        self.mfa_user.hotp_counter += 1
        self.request.dbsession.add(self.mfa_user)
        _ = self.request.gettext
        key = self.mfa_user.mfa_secret_key
        assert key, f"Bug: self.mfa_user.mfa_secret_key = {key!r}"
        handler = pyotp.HOTP(key)
        code = handler.at(self.mfa_user.hotp_counter)
        return _("Your CamCOPS verification code is {}").format(code)

    def otp_is_valid(self, appstruct: Dict[str, Any]) -> bool:
        """
        Is the code being offered by the user the right one?
        """
        otp = appstruct.get(ViewParam.ONE_TIME_PASSWORD)
        return self.mfa_user.verify_one_time_password(otp)

    # -------------------------------------------------------------------------
    # Ways to fail
    # -------------------------------------------------------------------------

    def fail_bad_mfa_code(self) -> NoReturn:
        """
        Fail because the code was wrong.
        """
        _ = self.request.gettext
        self.fail(_("You entered an invalid code. Please try again."))

    def fail_timed_out(self) -> NoReturn:
        """
        Fail because the process timed out.
        """
        _ = self.request.gettext
        self.fail(_("Your code expired. Please try again."))


class LoggedInUserMfaMixin(MfaMixin):
    """
    Handles multi-factor authentication for the currently logged in user
    (everything except :class:`LoginView`).
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.mfa_user = self.request.user


class LoginView(MfaMixin, FormView):
    """
    Multi-factor authentication for the login process.
    Sequences is: (1) password; (2) MFA, if enabled.

    Inheritance (as of 2021-10-06):

    - webview.LoginView

      - webview.MfaMixin

        - cc_view_classes.FormWizardMixin

      - cc_view_classes.FormView

        - cc_view_classes.TemplateResponseMixin

        - cc_view_classes.BaseFormView

          - cc_view_classes.FormMixin

            - cc_view_classes.ContextMixin

          - cc_view_classes.ProcessFormView -- provides ``get()``, ``post()``

            - cc_view_classes.View -- owns ``request``, provides ``dispatch()``
    """

    KEY_MFA_USER_ID = "mfa_user_id"

    _mfa_user: Optional[User]
    wizard_first_step = MfaMixin.STEP_PASSWORD
    wizard_forms = {
        MfaMixin.STEP_PASSWORD: LoginForm,  # 1. enter username/password
        MfaMixin.STEP_MFA: OtpTokenForm,  # 2. enter one-time code
    }
    wizard_templates = {
        MfaMixin.STEP_PASSWORD: "login.mako",
        MfaMixin.STEP_MFA: "login_token.mako",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    # -------------------------------------------------------------------------
    # mfa_user
    # -------------------------------------------------------------------------
    # Slightly more complex here, since our user isn't logged in properly yet.

    @property
    def mfa_user(self) -> Optional[User]:
        # Docstring in superclass.
        if self._mfa_user is None:
            try:
                user_id = self.state[self.KEY_MFA_USER_ID]
                self.mfa_user = (
                    self.request.dbsession.query(User)
                    .filter(User.id == user_id)
                    .one_or_none()
                )
            except KeyError:
                pass

        return self._mfa_user

    @mfa_user.setter
    def mfa_user(self, user: Optional[User]) -> None:
        # Docstring in superclass.
        self._mfa_user = user
        if user is None:
            self.state[self.KEY_MFA_USER_ID] = None
            return

        self.state[self.KEY_MFA_USER_ID] = user.id

    # -------------------------------------------------------------------------
    # Content for forms
    # -------------------------------------------------------------------------

    def get_form_values(self) -> Dict:
        # Docstring in superclass.
        return {ViewParam.REDIRECT_URL: self.get_redirect_url()}

    def get_form_kwargs(self) -> Dict[str, Any]:
        # Docstring in superclass.
        kwargs = super().get_form_kwargs()

        cfg = self.request.config
        autocomplete_password = not cfg.disable_password_autocomplete
        kwargs["autocomplete_password"] = autocomplete_password

        return kwargs

    # -------------------------------------------------------------------------
    # Form validation, and sequence handling
    # -------------------------------------------------------------------------

    def form_valid_process_data(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> None:
        # Docstring in superclass.
        if self.step == self.STEP_PASSWORD:
            self._form_valid_password(appstruct)
        else:
            self._form_valid_mfa(appstruct)

        super().form_valid_process_data(form, appstruct)

    def _form_valid_password(self, appstruct: Dict[str, Any]) -> None:
        """
        Called when the user has entered a username/password (via a validated
        form).
        """
        username = appstruct.get(ViewParam.USERNAME)

        # Is the user locked?
        locked_out_until = SecurityAccountLockout.user_locked_out_until(
            self.request, username
        )
        if locked_out_until is not None:
            self.fail_locked_out(locked_out_until)  # will raise

        password = appstruct.get(ViewParam.PASSWORD)

        # Is the username/password combination correct?
        user = User.get_user_from_username_password(
            self.request, username, password
        )  # checks password

        # Some trade-off between usability and security here.
        # For failed attempts, the user has some idea as to what the problem
        # is.
        if user is None:
            # Unsuccessful. Note that the username may/may not be genuine.
            SecurityLoginFailure.act_on_login_failure(self.request, username)
            # ... may lock the account
            # Now, call audit() before session.logout(), as the latter
            # will wipe the session IP address:
            self.request.camcops_session.logout()
            self.fail_not_authorized()  # will raise

        if not user.may_use_webviewer:
            # This means a user who can upload from tablet but who cannot
            # log in via the web front end.
            self.fail_not_authorized()  # will raise

        self.mfa_user = user
        self._password_next_step()
        self._form_valid_success()

    def _password_next_step(self) -> None:
        """
        The user has entered a password correctly; what's the next step?
        """
        method = self.mfa_user.mfa_method
        if MfaMethod.requires_second_step(method):
            self.step = self.STEP_MFA
            self.handle_authentication_type()
        else:
            self.finish()
            # Guaranteed to be valid; see constructor.

    def _form_valid_mfa(self, appstruct: Dict[str, Any]) -> None:
        """
        Called when the user has entered an MFA code (via a validated form).
        """
        if not self.otp_is_valid(appstruct):
            self.fail_bad_mfa_code()  # will raise

        self.finish()
        self._form_valid_success()

    def _form_valid_success(self) -> None:
        """
        Called when the next step has been determined. One possible outcome is
        a successful login.
        """
        if self.finished():
            # Successful login.
            self.mfa_user.login(
                self.request
            )  # will clear login failure record
            self.request.camcops_session.login(self.mfa_user)
            audit(self.request, "Login", user_id=self.mfa_user.id)

            # OK, logged in.
            # Redirect to the main menu, or wherever the user was heading.
            # HOWEVER, that may lead us to a "change password" or "agree terms"
            # page, via the permissions system (Permission.HAPPY or not).

    # -------------------------------------------------------------------------
    # Next destinations
    # -------------------------------------------------------------------------

    def get_success_url(self) -> str:
        # Docstring in superclass.
        if self.finished():
            return self.get_redirect_url()

        return self.request.route_url(
            Routes.LOGIN,
            _query={ViewParam.REDIRECT_URL: self.get_redirect_url()},
        )

    def get_failure_url(self) -> None:
        # Docstring in superclass.
        return self.request.route_url(
            Routes.LOGIN,
            _query={ViewParam.REDIRECT_URL: self.get_redirect_url()},
        )

    def get_redirect_url(self) -> str:
        """
        We may be logging in after a timeout, in which case we can redirect the
        user back to where they were before. Otherwise, they go to the main
        page.
        """
        return self.request.get_redirect_url_param(
            ViewParam.REDIRECT_URL, default=self.request.route_url(Routes.HOME)
        )

    # -------------------------------------------------------------------------
    # Ways to fail
    # -------------------------------------------------------------------------

    def fail_not_authorized(self) -> NoReturn:
        """
        Fail because the user has not logged in correctly or is not authorized
        to log in.

        Pretends to the type checker that it returns a response, so callers can
        use ``return`` for code safety.
        """
        _ = self.request.gettext
        self.fail(
            _("Invalid username/password (or user not authorized).")
        )  # will raise
        # assert False, "Bug: LoginView.fail_not_authorized() falling through"

    def fail_locked_out(self, locked_until: Pendulum) -> NoReturn:
        """
        Raises a failure because the user is locked out.

        Pretends to the type checker that it returns a response, so callers can
        use ``return`` for code safety.
        """
        _ = self.request.gettext
        locked_until = format_datetime(
            locked_until, DateFormat.LONG_DATETIME_WITH_DAY, _("(never)")
        )
        message = _(
            "Account locked until {} due to multiple login failures. "
            "Try again later or contact your administrator."
        ).format(locked_until)
        self.fail(message)  # will raise
        # assert False, "Bug: LoginView.fail_locked_out() falling through"


@view_config(
    route_name=Routes.LOGIN,
    permission=NO_PERMISSION_REQUIRED,
    http_cache=NEVER_CACHE,
)
def login_view(req: "CamcopsRequest") -> Response:
    """
    Login view.

    - GET: presents the login screen
    - POST/submit: attempts to log in (with optional multi-factor
      authentication);

      - failure: returns a login failure view or an account lockout view
      - success:

        - redirects to the redirection view if one was specified;
        - redirects to the home view if not.
    """
    return LoginView(req).dispatch()


@view_config(
    route_name=Routes.LOGOUT,
    permission=Authenticated,
    renderer="logged_out.mako",
    http_cache=NEVER_CACHE,
)
def logout(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Logs a session out, and returns the "logged out" view.
    """
    audit(req, "Logout")
    ccsession = req.camcops_session
    ccsession.logout()
    return dict()


@view_config(
    route_name=Routes.OFFER_TERMS,
    permission=Authenticated,
    renderer="offer_terms.mako",
    http_cache=NEVER_CACHE,
)
def offer_terms(req: "CamcopsRequest") -> Response:
    """
    - GET: show terms/conditions and request acknowledgement
    - POST/submit: note the user's agreement; redirect to the home view.
    """
    form = OfferTermsForm(
        request=req, agree_button_text=req.wsstring(SS.DISCLAIMER_AGREE)
    )

    if FormAction.SUBMIT in req.POST:
        req.user.agree_terms(req)
        return HTTPFound(req.route_url(Routes.HOME))  # redirect

    return render_to_response(
        "offer_terms.mako",
        dict(
            title=req.wsstring(SS.DISCLAIMER_TITLE),
            subtitle=req.wsstring(SS.DISCLAIMER_SUBTITLE),
            content=req.wsstring(SS.DISCLAIMER_CONTENT),
            form=form.render(),
            head_form_html=get_head_form_html(req, [form]),
        ),
        request=req,
    )


@forbidden_view_config(http_cache=NEVER_CACHE)
def forbidden(req: "CamcopsRequest") -> Response:
    """
    Generic place that Pyramid comes when permission is denied for a view.

    We will offer one of these:

    - Must change password? Redirect to "change own password" view.
    - Must agree terms? Redirect to "offer terms" view.
    - Otherwise: a generic "forbidden" view.
    """
    # I was doing this:
    if req.has_permission(Authenticated):
        user = req.user
        assert user, "Bug! Authenticated but no user...!?"
        if user.must_change_password:
            return HTTPFound(req.route_url(Routes.CHANGE_OWN_PASSWORD))
        if user.must_agree_terms:
            return HTTPFound(req.route_url(Routes.OFFER_TERMS))
        if user.must_set_mfa_method(req):
            return HTTPFound(req.route_url(Routes.EDIT_OWN_USER_MFA))
    # ... but with "raise HTTPFound" instead.
    # BUT there is only one level of exception handling in Pyramid, i.e. you
    # can't raise exceptions from exceptions:
    #       https://github.com/Pylons/pyramid/issues/436
    # The simplest way round is to use "return", not "raise".

    redirect_url = req.url
    # Redirects to login page, with onwards redirection to requested
    # destination once logged in:
    querydict = {ViewParam.REDIRECT_URL: redirect_url}
    return render_to_response(
        "forbidden.mako", dict(querydict=querydict), request=req
    )


# =============================================================================
# Changing passwords
# =============================================================================


class ChangeOwnPasswordView(LoggedInUserMfaMixin, UpdateView):
    """
    View to change one's own password.

    If MFA is enabled, you need to (re-)authenticate via MFA to do so.
    Then, you need to supply your own password to change it (regardless).
    Sequence is therefore (1) MFA, optionally; (2) change password.

    Most documentation in superclass.
    """

    model_form_dict: Dict[str, "Form"] = {}
    STEP_CHANGE_PASSWORD = "change_password"

    wizard_forms = {
        MfaMixin.STEP_MFA: OtpTokenForm,
        STEP_CHANGE_PASSWORD: ChangeOwnPasswordForm,
    }

    wizard_templates = {
        MfaMixin.STEP_MFA: "login_token.mako",
        STEP_CHANGE_PASSWORD: "change_own_password.mako",
    }

    wizard_extra_contexts: Dict[str, Dict[str, Any]] = {
        MfaMixin.STEP_MFA: {},
        STEP_CHANGE_PASSWORD: {},
    }

    def get_first_step(self) -> str:
        if self.request.user.mfa_method == MfaMethod.NO_MFA:
            return self.STEP_CHANGE_PASSWORD

        return self.STEP_MFA

    def get(self) -> Response:
        if self.step == self.STEP_MFA:
            self.handle_authentication_type()

        _ = self.request.gettext

        if self.request.user.must_change_password:
            self.request.session.flash(
                _("Your password has expired and must be changed."),
                queue=FlashQueue.DANGER,
            )
        return super().get()

    def get_object(self) -> User:
        return self.request.user

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs.update(must_differ=True)
        return kwargs

    def get_success_url(self) -> str:
        if self.finished():
            return self.request.route_url(Routes.HOME)

        return self.request.route_url(Routes.CHANGE_OWN_PASSWORD)

    def get_failure_url(self) -> str:
        return self.request.route_url(Routes.HOME)

    def form_valid_process_data(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> None:
        if self.step == self.STEP_MFA:
            if not self.otp_is_valid(appstruct):
                self.fail_bad_mfa_code()  # will raise

        super().form_valid_process_data(form, appstruct)

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        # Superclass method overridden, not called.
        if self.step == self.STEP_MFA:
            self.step = self.STEP_CHANGE_PASSWORD
        elif self.step == self.STEP_CHANGE_PASSWORD:
            self.set_password(appstruct)
            self.finish()
        else:
            assert f"ChangeOwnPasswordView: bad step {self.step!r}"

    def set_password(self, appstruct: Dict[str, Any]) -> None:
        """
        Success; change the user's password.
        """
        user = cast(User, self.object)
        # ... form has validated old password, etc.
        new_password = appstruct[ViewParam.NEW_PASSWORD]
        user.set_password(self.request, new_password)

        _ = self.request.gettext
        self.request.session.flash(
            _(
                "You have changed your password. "
                "If you store your password in your CamCOPS tablet "
                "application, remember to change it there as well."
            ),
            queue=FlashQueue.SUCCESS,
        )


@view_config(
    route_name=Routes.CHANGE_OWN_PASSWORD,
    permission=Authenticated,
    http_cache=NEVER_CACHE,
)
def change_own_password(req: "CamcopsRequest") -> Response:
    """
    For any user: to change their own password.

    - GET: offer "change own password" view
    - POST/submit: change the password and display success message.
    """
    view = ChangeOwnPasswordView(req)

    return view.dispatch()


class EditUserAuthenticationView(LoggedInUserMfaMixin, UpdateView):
    """
    View to edit aspects of another user.
    """

    model_form_dict: Dict[str, "Form"] = {}
    object_class = User
    pk_param = ViewParam.USER_ID
    server_pk_name = "id"

    def get(self) -> Response:
        if self.step == self.STEP_MFA:
            self.handle_authentication_type()

        return super().get()

    def get_object(self) -> User:
        user = cast(User, super().get_object())
        assert_may_edit_user(self.request, user)

        return user

    def get_extra_context(self) -> Dict[str, Any]:
        if self.step == self.STEP_MFA:
            return super().get_extra_context()

        user = cast(User, self.object)

        return {"username": user.username}

    def form_valid_process_data(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> None:
        if self.step == self.STEP_MFA:
            if not self.otp_is_valid(appstruct):
                self.fail_bad_mfa_code()  # will raise

        super().form_valid_process_data(form, appstruct)

    def get_failure_url(self) -> str:
        return self.request.route_url(Routes.VIEW_ALL_USERS)


class ChangeOtherPasswordView(EditUserAuthenticationView):
    """
    View to change the password for another user.
    """

    STEP_CHANGE_PASSWORD = "change_password"

    wizard_forms = {
        MfaMixin.STEP_MFA: OtpTokenForm,
        STEP_CHANGE_PASSWORD: ChangeOtherPasswordForm,
    }

    wizard_templates = {
        MfaMixin.STEP_MFA: "login_token.mako",
        STEP_CHANGE_PASSWORD: "change_other_password.mako",
    }

    def get(self) -> Response:
        if self.get_pk_value() == self.request.user_id:
            raise HTTPFound(self.request.route_url(Routes.CHANGE_OWN_PASSWORD))

        return super().get()

    def get_first_step(self) -> str:
        if self.request.user.mfa_method != MfaMethod.NO_MFA:
            return self.STEP_MFA

        return self.STEP_CHANGE_PASSWORD

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        # Superclass method overridden, not called.
        if self.step == self.STEP_CHANGE_PASSWORD:
            self.set_password(appstruct)
            self.finish()
            return

        if self.step == self.STEP_MFA:
            self.step = self.STEP_CHANGE_PASSWORD

    def set_password(self, appstruct: Dict[str, Any]) -> None:
        """
        Success; change the password for the other user.
        """
        user = cast(User, self.object)
        _ = self.request.gettext
        new_password = appstruct[ViewParam.NEW_PASSWORD]
        user.set_password(self.request, new_password)
        must_change_pw = appstruct.get(ViewParam.MUST_CHANGE_PASSWORD)
        if must_change_pw:
            user.force_password_change()
        self.request.session.flash(
            _("Password changed for user '{username}'").format(
                username=user.username
            ),
            queue=FlashQueue.SUCCESS,
        )

    def get_success_url(self) -> str:
        if self.finished():
            return self.request.route_url(Routes.VIEW_ALL_USERS)

        user = cast(User, self.object)

        return self.request.route_url(
            Routes.CHANGE_OTHER_PASSWORD, _query={ViewParam.USER_ID: user.id}
        )


@view_config(
    route_name=Routes.CHANGE_OTHER_PASSWORD,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def change_other_password(req: "CamcopsRequest") -> Response:
    """
    For administrators, to change another's password.

    - GET: offer "change another's password" view (except that if you're
      changing your own password, return :func:`change_own_password`.
    - POST/submit: change the password and display success message.
    """
    view = ChangeOtherPasswordView(req)
    return view.dispatch()


class EditOtherUserMfaView(EditUserAuthenticationView):
    """
    View to edit the MFA method for another user. Only permits disabling of
    MFA. (If MFA is mandatory, that will require the other user to set their
    MFA method at next logon.)
    """

    STEP_OTHER_USER_MFA = "other_user_mfa"

    wizard_forms = {
        MfaMixin.STEP_MFA: OtpTokenForm,
        STEP_OTHER_USER_MFA: EditOtherUserMfaForm,
    }

    wizard_templates = {
        MfaMixin.STEP_MFA: "login_token.mako",
        STEP_OTHER_USER_MFA: "edit_other_user_mfa.mako",
    }

    def get(self) -> Response:
        if self.get_pk_value() == self.request.user_id:
            raise HTTPFound(self.request.route_url(Routes.EDIT_OWN_USER_MFA))

        return super().get()

    def get_first_step(self) -> str:
        if self.request.user.mfa_method != MfaMethod.NO_MFA:
            return self.STEP_MFA

        return self.STEP_OTHER_USER_MFA

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        # Superclass method overridden, not called.
        if self.step == self.STEP_OTHER_USER_MFA:
            self.maybe_disable_mfa(appstruct)
            self.finish()
            return

        if self.step == self.STEP_MFA:
            self.step = self.STEP_OTHER_USER_MFA

    def maybe_disable_mfa(self, appstruct: Dict[str, Any]) -> None:
        """
        If our user asked for it, disable MFA for the user being edited.
        """
        if appstruct.get(ViewParam.DISABLE_MFA):
            user = cast(User, self.object)
            _ = self.request.gettext

            user.mfa_method = MfaMethod.NO_MFA
            self.request.session.flash(
                _(
                    "Multi-factor authentication disabled for user "
                    "'{username}'"
                ).format(username=user.username),
                queue=FlashQueue.SUCCESS,
            )

    def get_success_url(self) -> str:
        if self.finished():
            return self.request.route_url(Routes.VIEW_ALL_USERS)

        user = cast(User, self.object)

        return self.request.route_url(
            Routes.EDIT_OTHER_USER_MFA, _query={ViewParam.USER_ID: user.id}
        )


@view_config(
    route_name=Routes.EDIT_OTHER_USER_MFA,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def edit_other_user_mfa(req: "CamcopsRequest") -> Response:
    """
    For administrators, to change another users's Multi-factor Authentication.
    Currently it is only possible to disable Multi-factor authentication for
    a user.

    - GET: offer "edit another's MFA" view (except that if you're
      changing your own MFA, return :func:`edit_own_user_mfa`.
    - POST/submit: edit MFA  and display success message.
    """
    view = EditOtherUserMfaView(req)
    return view.dispatch()


class EditOwnUserMfaView(LoggedInUserMfaMixin, UpdateView):
    """
    View to edit your own MFA method.

    The inheritance (as of 2021-10-06) illustrates a typical situation:

    SPECIMEN VIEW CLASS:

    - webview.EditOwnUserMfaView

      - webview.LoggedInUserMfaMixin

        - webview.MfaMixin

          - cc_view_classes.FormWizardMixin -- with typehint for FormMixin --
            implements ``state``.

      - cc_view_classes.UpdateView

        - cc_view_classes.TemplateResponseMixin

        - cc_view_classes.BaseUpdateView

          - cc_view_classes.ModelFormMixin -- implements ``form_valid()`` -->
            ``save_object()`` > ``set_object_properties()``

            - cc_view_classes.FormMixin -- implements ``form_valid()``,
              ``get_context_data()``, etc.

              - cc_view_classes.ContextMixin

            - cc_view_classes.SingleObjectMixin -- implements ``get_object()``
              etc.

              - cc_view_classes.ContextMixin

          - cc_view_classes.ProcessFormView -- implements ``get()``, ``post()``

            - cc_view_classes.View -- owns ``request``, implements
              ``dispatch()`` (which calls ``get()``, ``post()``).

    SPECIMEN FORM WITHIN THAT VIEW:

    - cc_forms.MfaMethodForm

      - cc_forms.InformativeNonceForm

        - cc_forms.InformativeForm

          - deform.Form

    If you subclass A(B, C), then B's superclass methods are called before C's:
    https://www.python.org/download/releases/2.3/mro/;
    https://makina-corpus.com/blog/metier/2014/python-tutorial-understanding-python-mro-class-search-path;
    """  # noqa

    STEP_MFA_METHOD = "mfa_method"
    STEP_TOTP = MfaMethod.TOTP
    STEP_HOTP_EMAIL = MfaMethod.HOTP_EMAIL
    STEP_HOTP_SMS = MfaMethod.HOTP_SMS
    wizard_first_step = STEP_MFA_METHOD

    wizard_forms = {
        STEP_MFA_METHOD: MfaMethodForm,  # 1. choose your MFA method
        STEP_TOTP: MfaTotpForm,  # 2a. show TOTP (auth app) QR/alphanumeric code  # noqa: E501
        STEP_HOTP_EMAIL: MfaHotpEmailForm,  # 2b. choose e-mail address
        STEP_HOTP_SMS: MfaHotpSmsForm,  # 2c. choose phone number for SMS
        MfaMixin.STEP_MFA: OtpTokenForm,  # 4. request code from user
    }

    FORM_WITH_TITLE_TEMPLATE = "form_with_title.mako"

    wizard_templates = {
        STEP_MFA_METHOD: FORM_WITH_TITLE_TEMPLATE,
        STEP_TOTP: FORM_WITH_TITLE_TEMPLATE,
        STEP_HOTP_EMAIL: FORM_WITH_TITLE_TEMPLATE,
        STEP_HOTP_SMS: FORM_WITH_TITLE_TEMPLATE,
        MfaMixin.STEP_MFA: "login_token.mako",
    }

    hotp_steps = (STEP_HOTP_EMAIL, STEP_HOTP_SMS)
    secret_key_steps = (STEP_TOTP, STEP_HOTP_EMAIL, STEP_HOTP_SMS)

    def get(self) -> Response:
        if self.step == self.STEP_MFA:
            self.handle_authentication_type()

        return super().get()

    def get_model_form_dict(self) -> Dict[str, Any]:
        model_form_dict = {}

        # Dictionary keys here are attribute names of the User object.
        # Values are form attributes.

        if self.step == self.STEP_MFA_METHOD:
            model_form_dict["mfa_method"] = ViewParam.MFA_METHOD

        elif self.step == self.STEP_HOTP_EMAIL:
            model_form_dict["email"] = ViewParam.EMAIL

        elif self.step == self.STEP_HOTP_SMS:
            model_form_dict["phone_number"] = ViewParam.PHONE_NUMBER

        if self.step in self.secret_key_steps:
            model_form_dict["mfa_secret_key"] = ViewParam.MFA_SECRET_KEY

        return model_form_dict

    def get_object(self) -> User:
        return self.request.user

    def get_form_values(self) -> Dict[str, Any]:
        # Will call get_model_form_dict()
        form_values = super().get_form_values()

        if self.step in self.secret_key_steps:
            # Always create a new secret key. This will be written to the
            # user object at the next step, via set_object_properties.
            form_values[ViewParam.MFA_SECRET_KEY] = pyotp.random_base32()

        return form_values

    def get_extra_context(self) -> Dict[str, Any]:
        req = self.request
        _ = req.gettext
        if self.step == self.STEP_MFA:
            test_msg = _("Let's test it!") + " "
            context = super().get_extra_context()
            context[self.KEY_INSTRUCTIONS] = (
                test_msg + self.get_mfa_instructions()
            )
            return context

        titles = {
            self.STEP_MFA_METHOD: req.icon_text(
                icon=Icons.MFA,
                text=_("Configure multi-factor authentication settings"),
            ),
            self.STEP_TOTP: req.icon_text(
                icon=Icons.APP_AUTHENTICATOR,
                text=_("Configure authentication with app"),
            ),
            self.STEP_HOTP_EMAIL: req.icon_text(
                icon=Icons.EMAIL_SEND,
                text=_("Configure authentication by email"),
            ),
            self.STEP_HOTP_SMS: req.icon_text(
                icon=Icons.SMS,
                text=_("Configure authentication by text message"),
            ),
        }
        return {MAKO_VAR_TITLE: titles[self.step]}

    def get_success_url(self) -> str:
        if self.finished():
            return self.request.route_url(Routes.HOME)

        return self.request.route_url(Routes.EDIT_OWN_USER_MFA)

    def get_failure_url(self) -> str:
        # We get here because the user, who has already logged in successfully,
        # has changed their MFA method. Failure doesn't mean they should be
        # logged out instantly -- they may have (for example) misconfigured
        # their phone number, and if they are forcibly logged out now, they are
        # stuffed and require administrator assistance. Instead, we return them
        # to the home screen.
        return self.request.route_url(Routes.HOME)

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        # Called by ModelFormMixin.form_valid_process_data() ->
        # ModelFormMixin.save_object().

        super().set_object_properties(appstruct)

        if self.step == self.STEP_MFA_METHOD:
            # We are setting the MFA method, including secret key etc.
            user = cast(User, self.object)
            user.set_mfa_method(appstruct.get(ViewParam.MFA_METHOD))

        elif self.step == self.STEP_MFA:
            # Code entered.
            if self.otp_is_valid(appstruct):
                _ = self.request.gettext
                self.request.session.flash(
                    _("Multi-factor authentication: success!"),
                    queue=FlashQueue.SUCCESS,
                )
                # ... and continue as below
            else:
                return self.fail_bad_mfa_code()

        self._next_step(appstruct)

    def _next_step(self, appstruct: Dict[str, Any]) -> None:
        if self.step == self.STEP_MFA_METHOD:
            # The user has just chosen their method.
            # 2. Offer them method-specific options
            mfa_method = appstruct.get(ViewParam.MFA_METHOD)
            if mfa_method == MfaMethod.NO_MFA:
                self.finish()
            else:
                self.step = mfa_method

        elif self.step in (
            self.STEP_TOTP,
            self.STEP_HOTP_EMAIL,
            self.STEP_HOTP_SMS,
        ):
            # Coming from one of the method-specific steps.
            # 3. Ask for the authentication code.
            self.step = self.STEP_MFA

        elif self.step == self.STEP_MFA:
            # Authentication code provided. End.
            self.finish()

        else:
            raise AssertionError(
                f"EditOwnUserMfaView.next_step(): " f"Bad step {self.step!r}"
            )


@view_config(
    route_name=Routes.EDIT_OWN_USER_MFA,
    permission=Authenticated,
    http_cache=NEVER_CACHE,
)
def edit_own_user_mfa(request: "CamcopsRequest") -> Response:
    """
    Edit your own MFA method.
    """
    view = EditOwnUserMfaView(request)
    return view.dispatch()


# =============================================================================
# Main menu; simple information things
# =============================================================================


@view_config(
    route_name=Routes.HOME, renderer="main_menu.mako", http_cache=NEVER_CACHE
)
def main_menu(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Main CamCOPS menu view.
    """
    user = req.user
    result = dict(
        authorized_as_groupadmin=user.authorized_as_groupadmin,
        authorized_as_superuser=user.superuser,
        authorized_for_reports=user.authorized_for_reports,
        authorized_to_dump=user.authorized_to_dump,
        authorized_to_manage_patients=user.authorized_to_manage_patients,
        camcops_url=CAMCOPS_URL,
        now=format_datetime(req.now, DateFormat.SHORT_DATETIME_SECONDS),
        server_version=CAMCOPS_SERVER_VERSION,
    )
    return result


# =============================================================================
# Tasks
# =============================================================================


def edit_filter(
    req: "CamcopsRequest", task_filter: TaskFilter, redirect_url: str
) -> Response:
    """
    Edit the task filter for the current user.

    Args:
        req: the :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        task_filter: the user's
            :class:`camcops_server.cc_modules.cc_taskfilter.TaskFilter`
        redirect_url: URL to redirect (back) to upon success
    """
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
                IdNumReference(
                    which_idnum=x[ViewParam.WHICH_IDNUM],
                    idnum_value=x[ViewParam.IDNUM_VALUE],
                )
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
                {
                    ViewParam.WHICH_IDNUM: x.which_idnum,
                    ViewParam.IDNUM_VALUE: x.idnum_value,
                }
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
        form = EditTaskFilterForm(
            request=req,
            open_admin=open_admin,
            open_what=open_what,
            open_when=open_when,
            open_who=open_who,
        )
        rendered_form = form.render(fa)

    return render_to_response(
        "filter_edit.mako",
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


@view_config(route_name=Routes.SET_FILTERS, http_cache=NEVER_CACHE)
def set_filters(req: "CamcopsRequest") -> Response:
    """
    View to set the task filters for the current user.
    """
    redirect_url = req.get_redirect_url_param(
        ViewParam.REDIRECT_URL, req.route_url(Routes.VIEW_TASKS)
    )
    task_filter = req.camcops_session.get_task_filter()
    return edit_filter(req, task_filter=task_filter, redirect_url=redirect_url)


@view_config(
    route_name=Routes.VIEW_TASKS,
    renderer="view_tasks.mako",
    http_cache=NEVER_CACHE,
)
def view_tasks(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Main view displaying tasks and applicable filters.
    """
    ccsession = req.camcops_session
    user = req.user
    taskfilter = ccsession.get_task_filter()

    # Read from the GET parameters (or in some cases potentially POST but those
    # will be re-read).
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE,
        ccsession.number_to_view or DEFAULT_ROWS_PER_PAGE,
    )
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    via_index = req.get_bool_param(ViewParam.VIA_INDEX, True)

    errors = False

    # "Number of tasks per page" form
    tpp_form = TasksPerPageForm(request=req)
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
        collection = (
            TaskCollection(  # SECURITY APPLIED HERE
                req=req,
                taskfilter=taskfilter,
                sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
                via_index=via_index,
            ).all_tasks_or_indexes_or_query
            or []
        )
    paginator = (
        SqlalchemyOrmPage if isinstance(collection, Query) else CamcopsPage
    )
    page = paginator(
        collection,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )
    return dict(
        page=page,
        head_form_html=get_head_form_html(req, [tpp_form, refresh_form]),
        tpp_form=rendered_tpp_form,
        refresh_form=rendered_refresh_form,
        no_patient_selected_and_user_restricted=(
            not user.may_view_all_patients_when_unfiltered
            and not taskfilter.any_specific_patient_filtering()
        ),
        user=user,
    )


@view_config(route_name=Routes.TASK, http_cache=NEVER_CACHE)
def serve_task(req: "CamcopsRequest") -> Response:
    """
    View that serves an individual task, in a variety of possible formats
    (e.g. HTML, PDF, XML).
    """
    _ = req.gettext
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML, lower=True)
    tablename = req.get_str_param(
        ViewParam.TABLE_NAME, validator=validate_task_tablename
    )
    server_pk = req.get_int_param(ViewParam.SERVER_PK)
    anonymise = req.get_bool_param(ViewParam.ANONYMISE, False)

    task = task_factory(req, tablename, server_pk)  # SECURITY APPLIED HERE

    if task is None:
        raise HTTPNotFound(  # raise, don't return
            f"{_('Task not found or not permitted:')} "
            f"tablename={tablename!r}, server_pk={server_pk!r}"
        )

    task.audit(req, "Viewed " + viewtype.upper())

    if viewtype == ViewArg.HTML:
        return Response(task.get_html(req=req, anonymise=anonymise))
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            body=task.get_pdf(req, anonymise=anonymise),
            filename=task.suggested_pdf_filename(req, anonymise=anonymise),
        )
    elif viewtype == ViewArg.PDFHTML:  # debugging option; no direct hyperlink
        return Response(task.get_pdf_html(req, anonymise=anonymise))
    elif viewtype == ViewArg.XML:
        options = TaskExportOptions(
            xml_include_ancillary=True,
            include_blobs=req.get_bool_param(ViewParam.INCLUDE_BLOBS, True),
            xml_include_comments=req.get_bool_param(
                ViewParam.INCLUDE_COMMENTS, True
            ),
            xml_include_calculated=req.get_bool_param(
                ViewParam.INCLUDE_CALCULATED, True
            ),
            xml_include_patient=req.get_bool_param(
                ViewParam.INCLUDE_PATIENT, True
            ),
            xml_include_plain_columns=True,
            xml_include_snomed=req.get_bool_param(
                ViewParam.INCLUDE_SNOMED, True
            ),
            xml_with_header_comments=True,
        )
        return XmlResponse(task.get_xml(req=req, options=options))
    elif viewtype == ViewArg.FHIRJSON:  # debugging option
        dummy_recipient = ExportRecipient()
        bundle = task.get_fhir_bundle(
            req, dummy_recipient, skip_docs_if_other_content=True
        )
        return JsonResponse(json.dumps(bundle.as_json(), indent=JSON_INDENT))
    else:
        permissible = (
            ViewArg.FHIRJSON,
            ViewArg.HTML,
            ViewArg.PDF,
            ViewArg.PDFHTML,
            ViewArg.XML,
        )
        raise HTTPBadRequest(
            f"{_('Bad output type:')} {viewtype!r} "
            f"({_('permissible:')} {permissible!r})"
        )


def view_patient(req: "CamcopsRequest", patient_server_pk: int) -> Response:
    """
    Primarily for FHIR views: show just a patient's details.
    Must check security carefully for this one.
    """
    user = req.user
    patient = Patient.get_patient_by_pk(req.dbsession, patient_server_pk)
    if not patient or not patient.user_may_view(user):
        _ = req.gettext
        raise HTTPBadRequest(_("No such patient or not authorized"))
    return render_to_response(
        "patient.mako",
        dict(patient=patient, viewtype=ViewArg.HTML),
        request=req,
    )


# =============================================================================
# Trackers, CTVs
# =============================================================================


def choose_tracker_or_ctv(
    req: "CamcopsRequest", as_ctv: bool
) -> Dict[str, Any]:
    """
    Returns a dictionary for a Mako template to configure a
    :class:`camcops_server.cc_modules.cc_tracker.Tracker` or
    :class:`camcops_server.cc_modules.cc_tracker.ClinicalTextView`.

    Upon success, it redirects to the tracker or CTV view itself, with the
    tracker's parameters embedded as URL parameters.

    Args:
        req: the :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        as_ctv: CTV, rather than tracker?
    """

    form = ChooseTrackerForm(req, as_ctv=as_ctv)  # , css_class="form-inline")

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
                ViewParam.VIA_INDEX,
                ViewParam.VIEWTYPE,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            # Not so obvious this can be redirected cleanly via POST.
            # It is possible by returning a form that then autosubmits: see
            # https://stackoverflow.com/questions/46582/response-redirect-with-post-instead-of-get  # noqa
            # However, since everything's on this server, we could just return
            # an appropriate Response directly. But the request information is
            # not sensitive, so we lose nothing by using a GET redirect:
            raise HTTPFound(
                req.route_url(
                    Routes.CTV if as_ctv else Routes.TRACKER, _query=querydict
                )
            )
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(
        form=rendered_form, head_form_html=get_head_form_html(req, [form])
    )


@view_config(
    route_name=Routes.CHOOSE_TRACKER,
    renderer="choose_tracker.mako",
    http_cache=NEVER_CACHE,
)
def choose_tracker(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to choose/configure a
    :class:`camcops_server.cc_modules.cc_tracker.Tracker`.
    """
    return choose_tracker_or_ctv(req, as_ctv=False)


@view_config(
    route_name=Routes.CHOOSE_CTV,
    renderer="choose_ctv.mako",
    http_cache=NEVER_CACHE,
)
def choose_ctv(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to choose/configure a
    :class:`camcops_server.cc_modules.cc_tracker.ClinicalTextView`.
    """
    return choose_tracker_or_ctv(req, as_ctv=True)


def serve_tracker_or_ctv(req: "CamcopsRequest", as_ctv: bool) -> Response:
    """
    Returns a response to show a
    :class:`camcops_server.cc_modules.cc_tracker.Tracker` or
    :class:`camcops_server.cc_modules.cc_tracker.ClinicalTextView`, in a
    variety of formats (e.g. HTML, PDF, XML).

    Args:
        req: the :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        as_ctv: CTV, rather than tracker?
    """
    as_tracker = not as_ctv
    _ = req.gettext
    which_idnum = req.get_int_param(ViewParam.WHICH_IDNUM)
    idnum_value = req.get_int_param(ViewParam.IDNUM_VALUE)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    tasks = req.get_str_list_param(
        ViewParam.TASKS, validator=validate_task_tablename
    )
    all_tasks = req.get_bool_param(ViewParam.ALL_TASKS, True)
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.HTML)
    via_index = req.get_bool_param(ViewParam.VIA_INDEX, True)

    if all_tasks:
        task_classes = []  # type: List[Type[Task]]
    else:
        try:
            task_classes = task_classes_from_table_names(
                tasks, sortmethod=TaskClassSortMethod.SHORTNAME
            )
        except KeyError:
            raise HTTPBadRequest(_("Invalid tasks specified"))
        if as_tracker and not all(c.provides_trackers for c in task_classes):
            raise HTTPBadRequest(_("Not all tasks specified provide trackers"))

    iddefs = [IdNumReference(which_idnum, idnum_value)]

    taskfilter = TaskFilter()
    taskfilter.task_types = [
        tc.__tablename__ for tc in task_classes
    ]  # a bit silly...  # noqa
    taskfilter.idnum_criteria = iddefs
    taskfilter.start_datetime = start_datetime
    taskfilter.end_datetime = end_datetime
    taskfilter.complete_only = True  # trackers require complete tasks
    taskfilter.set_sort_method(TaskClassSortMethod.SHORTNAME)
    taskfilter.tasks_offering_trackers_only = as_tracker
    taskfilter.tasks_with_patient_only = True

    tracker_ctv_class = ClinicalTextView if as_ctv else Tracker
    tracker = tracker_ctv_class(
        req=req, taskfilter=taskfilter, via_index=via_index
    )

    if viewtype == ViewArg.HTML:
        return Response(tracker.get_html())
    elif viewtype == ViewArg.PDF:
        return PdfResponse(
            body=tracker.get_pdf(), filename=tracker.suggested_pdf_filename()
        )
    elif viewtype == ViewArg.PDFHTML:  # debugging option
        return Response(tracker.get_pdf_html())
    elif viewtype == ViewArg.XML:
        include_comments = req.get_bool_param(ViewParam.INCLUDE_COMMENTS, True)
        return XmlResponse(tracker.get_xml(include_comments=include_comments))
    else:
        permissible = [ViewArg.HTML, ViewArg.PDF, ViewArg.PDFHTML, ViewArg.XML]
        raise HTTPBadRequest(
            f"{_('Invalid view type:')} {viewtype!r} "
            f"({_('permissible:')} {permissible!r})"
        )


@view_config(route_name=Routes.TRACKER, http_cache=NEVER_CACHE)
def serve_tracker(req: "CamcopsRequest") -> Response:
    """
    View to serve a :class:`camcops_server.cc_modules.cc_tracker.Tracker`; see
    :func:`serve_tracker_or_ctv`.
    """
    return serve_tracker_or_ctv(req, as_ctv=False)


@view_config(route_name=Routes.CTV, http_cache=NEVER_CACHE)
def serve_ctv(req: "CamcopsRequest") -> Response:
    """
    View to serve a
    :class:`camcops_server.cc_modules.cc_tracker.ClinicalTextView`; see
    :func:`serve_tracker_or_ctv`.
    """
    return serve_tracker_or_ctv(req, as_ctv=True)


# =============================================================================
# Reports
# =============================================================================


@view_config(
    route_name=Routes.REPORTS_MENU,
    renderer="reports_menu.mako",
    http_cache=NEVER_CACHE,
)
def reports_menu(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Offer a menu of reports.

    Note: Reports are not group-specific.
    If you're authorized to see any, you'll see the whole menu.
    (The *data* you get will be restricted to the group's you're authorized
    to run reports for.)
    """
    if not req.user.authorized_for_reports:
        raise HTTPBadRequest(errormsg_cannot_report(req))
    return {}


@view_config(route_name=Routes.OFFER_REPORT, http_cache=NEVER_CACHE)
def offer_report(req: "CamcopsRequest") -> Response:
    """
    Offer configuration options for a single report, or (following submission)
    redirect to serve that report (with configuration parameters in the URL).
    """
    if not req.user.authorized_for_reports:
        raise HTTPBadRequest(errormsg_cannot_report(req))
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    _ = req.gettext
    if not report:
        raise HTTPBadRequest(f"{_('No such report ID:')} {report_id!r}")
    if report.superuser_only and not req.user.superuser:
        raise HTTPBadRequest(
            f"{_('Report is restricted to the superuser:')} {report_id!r}"
        )
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
            head_form_html=get_head_form_html(req, [form]),
        ),
        request=req,
    )


@view_config(route_name=Routes.REPORT, http_cache=NEVER_CACHE)
def serve_report(req: "CamcopsRequest") -> Response:
    """
    Serve a configured report.
    """
    if not req.user.authorized_for_reports:
        raise HTTPBadRequest(errormsg_cannot_report(req))
    report_id = req.get_str_param(ViewParam.REPORT_ID)
    report = get_report_instance(report_id)
    _ = req.gettext
    if not report:
        raise HTTPBadRequest(f"{_('No such report ID:')} {report_id!r}")
    if report.superuser_only and not req.user.superuser:
        raise HTTPBadRequest(
            f"{_('Report is restricted to the superuser:')} {report_id!r}"
        )

    return report.get_response(req)


# =============================================================================
# Research downloads
# =============================================================================


@view_config(route_name=Routes.OFFER_BASIC_DUMP, http_cache=NEVER_CACHE)
def offer_basic_dump(req: "CamcopsRequest") -> Response:
    """
    View to configure a basic research dump.
    Following submission success, it redirects to a view serving a TSV/ZIP
    dump.
    """
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(errormsg_cannot_dump(req))
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
                ViewParam.VIEWTYPE: appstruct.get(ViewParam.VIEWTYPE),
                ViewParam.DELIVERY_MODE: appstruct.get(
                    ViewParam.DELIVERY_MODE
                ),
                ViewParam.INCLUDE_SCHEMA: appstruct.get(
                    ViewParam.INCLUDE_SCHEMA
                ),
                ViewParam.SIMPLIFIED: appstruct.get(ViewParam.SIMPLIFIED),
            }
            # We could return a response, or redirect via GET.
            # The request is not sensitive, so let's redirect.
            return HTTPFound(
                req.route_url(Routes.BASIC_DUMP, _query=querydict)
            )
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "dump_basic_offer.mako",
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


def get_dump_collection(req: "CamcopsRequest") -> TaskCollection:
    """
    Returns the collection of tasks being requested for a dump operation.
    Raises an error if the request is bad.
    """
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(errormsg_cannot_dump(req))
    # -------------------------------------------------------------------------
    # Get parameters
    # -------------------------------------------------------------------------
    dump_method = req.get_str_param(ViewParam.DUMP_METHOD)
    group_ids = req.get_int_list_param(ViewParam.GROUP_IDS)
    task_names = req.get_str_list_param(
        ViewParam.TASKS, validator=validate_task_tablename
    )

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
        _ = req.gettext
        raise HTTPBadRequest(
            f"{_('Bad parameter:')} "
            f"{ViewParam.DUMP_METHOD}={dump_method!r}"
        )
    return TaskCollection(
        req=req,
        taskfilter=taskfilter,
        as_dump=True,
        sort_method_by_class=TaskSortMethod.CREATION_DATE_ASC,
    )


@view_config(route_name=Routes.BASIC_DUMP, http_cache=NEVER_CACHE)
def serve_basic_dump(req: "CamcopsRequest") -> Response:
    """
    View serving a spreadsheet-style basic research dump.
    """
    # Get view-specific parameters
    simplified = req.get_bool_param(ViewParam.SIMPLIFIED, False)
    sort_by_heading = req.get_bool_param(ViewParam.SORT, False)
    viewtype = req.get_str_param(ViewParam.VIEWTYPE, ViewArg.XLSX, lower=True)
    delivery_mode = req.get_str_param(
        ViewParam.DELIVERY_MODE, ViewArg.EMAIL, lower=True
    )
    include_schema = req.get_bool_param(ViewParam.INCLUDE_SCHEMA, False)

    # Get tasks (and perform checks)
    collection = get_dump_collection(req)
    # Create object that knows how to export
    exporter = make_exporter(
        req=req,
        collection=collection,
        options=DownloadOptions(
            # Exporting to spreadsheets
            user_id=req.user_id,
            viewtype=viewtype,
            delivery_mode=delivery_mode,
            spreadsheet_simplified=simplified,
            spreadsheet_sort_by_heading=sort_by_heading,
            include_information_schema_columns=include_schema,
            include_summary_schema=True,
        ),
    )  # may raise
    # Export, or schedule an email/download
    return exporter.immediate_response(req)


@view_config(route_name=Routes.OFFER_SQL_DUMP, http_cache=NEVER_CACHE)
def offer_sql_dump(req: "CamcopsRequest") -> Response:
    """
    View to configure a SQL research dump.
    Following submission success, it redirects to a view serving the SQL dump.
    """
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(errormsg_cannot_dump(req))
    form = OfferSqlDumpForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            manual = appstruct.get(ViewParam.MANUAL)
            querydict = {
                ViewParam.DUMP_METHOD: appstruct.get(ViewParam.DUMP_METHOD),
                ViewParam.SQLITE_METHOD: appstruct.get(
                    ViewParam.SQLITE_METHOD
                ),
                ViewParam.INCLUDE_BLOBS: appstruct.get(
                    ViewParam.INCLUDE_BLOBS
                ),
                ViewParam.PATIENT_ID_PER_ROW: appstruct.get(
                    ViewParam.PATIENT_ID_PER_ROW
                ),
                ViewParam.GROUP_IDS: manual.get(ViewParam.GROUP_IDS),
                ViewParam.TASKS: manual.get(ViewParam.TASKS),
                ViewParam.DELIVERY_MODE: appstruct.get(
                    ViewParam.DELIVERY_MODE
                ),
                ViewParam.INCLUDE_SCHEMA: appstruct.get(
                    ViewParam.INCLUDE_SCHEMA
                ),
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
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


@view_config(route_name=Routes.SQL_DUMP, http_cache=NEVER_CACHE)
def sql_dump(req: "CamcopsRequest") -> Response:
    """
    View serving an SQL dump in the chosen format (e.g. SQLite binary, SQL).
    """
    # Get view-specific parameters
    sqlite_method = req.get_str_param(ViewParam.SQLITE_METHOD)
    include_blobs = req.get_bool_param(ViewParam.INCLUDE_BLOBS, False)
    patient_id_per_row = req.get_bool_param(ViewParam.PATIENT_ID_PER_ROW, True)
    delivery_mode = req.get_str_param(
        ViewParam.DELIVERY_MODE, ViewArg.EMAIL, lower=True
    )
    include_schema = req.get_bool_param(ViewParam.INCLUDE_SCHEMA, False)

    # Get tasks (and perform checks)
    collection = get_dump_collection(req)
    # Create object that knows how to export
    exporter = make_exporter(
        req=req,
        collection=collection,
        options=DownloadOptions(
            # Exporting to SQL
            user_id=req.user_id,
            viewtype=sqlite_method,
            delivery_mode=delivery_mode,
            db_include_blobs=include_blobs,
            db_patient_id_per_row=patient_id_per_row,
            include_information_schema_columns=include_schema,
            include_summary_schema=include_schema,  # doesn't do much for SQL export at present  # noqa
        ),
    )  # may raise
    # Export, or schedule an email/download
    return exporter.immediate_response(req)


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.DOWNLOAD_AREA,
    renderer="download_area.mako",
    http_cache=NEVER_CACHE,
)
def download_area(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Shows the user download area.
    """
    userdir = req.user_download_dir
    if userdir:
        files = UserDownloadFile.from_directory_scan(
            directory=userdir,
            permitted_lifespan_min=req.config.user_download_file_lifetime_min,
            req=req,
        )
    else:
        files = []  # type: List[UserDownloadFile]
    return dict(
        files=files,
        available=bytes2human(req.user_download_bytes_available),
        permitted=bytes2human(req.user_download_bytes_permitted),
        used=bytes2human(req.user_download_bytes_used),
        lifetime_min=req.config.user_download_file_lifetime_min,
    )


@view_config(route_name=Routes.DOWNLOAD_FILE, http_cache=NEVER_CACHE)
def download_file(req: "CamcopsRequest") -> Response:
    """
    Downloads a file.
    """
    _ = req.gettext
    filename = req.get_str_param(
        ViewParam.FILENAME, "", validator=validate_download_filename
    )
    # Security comes here: we do NOT permit any path information in the
    # filename. It MUST be relative to and within the user download directory.
    # We cannot trust the input.
    filename = os.path.basename(filename)
    udf = UserDownloadFile(directory=req.user_download_dir, filename=filename)
    if not udf.exists:
        raise HTTPBadRequest(f'{_("No such file:")} {filename}')
    try:
        return BinaryResponse(
            body=udf.contents,
            filename=udf.filename,
            content_type=MimeType.BINARY,
            as_inline=False,
        )
    except OSError:
        raise HTTPBadRequest(f'{_("Error reading file:")} {filename}')


@view_config(
    route_name=Routes.DELETE_FILE,
    request_method=HttpMethod.POST,
    http_cache=NEVER_CACHE,
)
def delete_file(req: "CamcopsRequest") -> Response:
    """
    Deletes a file.
    """
    form = UserDownloadDeleteForm(request=req)
    controls = list(req.POST.items())
    appstruct = form.validate(controls)  # CSRF; may raise ValidationError
    filename = appstruct.get(ViewParam.FILENAME, "")
    # Security comes here: we do NOT permit any path information in the
    # filename. It MUST be relative to and within the user download directory.
    # We cannot trust the input.
    filename = os.path.basename(filename)
    udf = UserDownloadFile(directory=req.user_download_dir, filename=filename)
    if not udf.exists:
        _ = req.gettext
        raise HTTPBadRequest(f'{_("No such file:")} {filename}')
    udf.delete()
    return HTTPFound(req.route_url(Routes.DOWNLOAD_AREA))  # redirect


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


def format_sql_as_html(
    sql: str, dialect: str = SqlaDialectName.MYSQL
) -> Tuple[str, str]:
    """
    Formats SQL as HTML with CSS.
    """
    lexer = LEXERMAP[dialect]()
    # noinspection PyUnresolvedReferences
    formatter = pygments.formatters.HtmlFormatter()
    html = pygments.highlight(sql, lexer, formatter)
    css = formatter.get_style_defs(".highlight")
    return html, css


@view_config(route_name=Routes.VIEW_DDL, http_cache=NEVER_CACHE)
def view_ddl(req: "CamcopsRequest") -> Response:
    """
    Inspect table definitions (data definition language, DDL) with field
    comments.

    2021-04-30: restricted to users with "dump" authority -- not because this
    is a vulnerability, as the penetration testers suggested, but just to make
    it consistent with the menu item for this.
    """
    if not req.user.authorized_to_dump:
        raise HTTPBadRequest(errormsg_cannot_dump(req))
    form = ViewDdlForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            dialect = appstruct.get(ViewParam.DIALECT)
            ddl = get_all_ddl(dialect_name=dialect)
            html, css = format_sql_as_html(ddl, dialect)
            return render_to_response(
                "introspect_file.mako",
                dict(css=css, code_html=html),
                request=req,
            )
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    current_dialect = get_dialect_name(get_engine_from_session(req.dbsession))
    sql_dialect_choices = get_sql_dialect_choices(req)
    current_dialect_description = {k: v for k, v in sql_dialect_choices}.get(
        current_dialect, "?"
    )
    return render_to_response(
        "view_ddl_choose_dialect.mako",
        dict(
            current_dialect=current_dialect,
            current_dialect_description=current_dialect_description,
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form]),
        ),
        request=req,
    )


# =============================================================================
# View audit trail
# =============================================================================


@view_config(
    route_name=Routes.OFFER_AUDIT_TRAIL,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def offer_audit_trail(req: "CamcopsRequest") -> Response:
    """
    View to configure how we'll view the audit trail. Once configured, it
    redirects to a view that shows the audit trail (with query parameters in
    the URL).
    """
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
            raise HTTPFound(
                req.route_url(Routes.VIEW_AUDIT_TRAIL, _query=querydict)
            )
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "audit_trail_choices.mako",
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


AUDIT_TRUNCATE_AT = 100


@view_config(
    route_name=Routes.VIEW_AUDIT_TRAIL,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_audit_trail(req: "CamcopsRequest") -> Response:
    """
    View to serve the audit trail.
    """
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    source = req.get_str_param(ViewParam.SOURCE, None)
    remote_addr = req.get_str_param(
        ViewParam.REMOTE_IP_ADDR, None, validator=validate_ip_address
    )
    username = req.get_str_param(
        ViewParam.USERNAME, None, validator=validate_username
    )
    table_name = req.get_str_param(
        ViewParam.TABLE_NAME, None, validator=validate_task_tablename
    )
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    truncate = req.get_bool_param(ViewParam.TRUNCATE, True)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append(f"{key} = {value}")

    dbsession = req.dbsession
    q = dbsession.query(AuditEntry)
    if start_datetime:
        q = q.filter(AuditEntry.when_access_utc >= start_datetime)
        add_condition(ViewParam.START_DATETIME, start_datetime)
    if end_datetime:
        q = q.filter(AuditEntry.when_access_utc < end_datetime)
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
    page = SqlalchemyOrmPage(
        query=q,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )
    return render_to_response(
        "audit_trail_view.mako",
        dict(
            conditions="; ".join(conditions),
            page=page,
            truncate=truncate,
            truncate_at=AUDIT_TRUNCATE_AT,
        ),
        request=req,
    )


# =============================================================================
# View export logs
# =============================================================================
# Overview:
# - View exported tasks (ExportedTask) collectively
#   ... option to filter by recipient_name
#   ... option to filter by date/etc.
# - View exported tasks (ExportedTask) individually
#   ... hyperlinks to individual views of:
#       Email (not necessary: ExportedTaskEmail)
#       ExportRecipient
#       ExportedTaskFileGroup
#       ExportedTaskHL7Message


@view_config(
    route_name=Routes.OFFER_EXPORTED_TASK_LIST,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def offer_exported_task_list(req: "CamcopsRequest") -> Response:
    """
    View to choose how we'll view the exported task log.
    """
    form = ExportedTaskListForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            keys = [
                ViewParam.ROWS_PER_PAGE,
                ViewParam.RECIPIENT_NAME,
                ViewParam.TABLE_NAME,
                ViewParam.SERVER_PK,
                ViewParam.ID,
                ViewParam.START_DATETIME,
                ViewParam.END_DATETIME,
            ]
            querydict = {k: appstruct.get(k) for k in keys}
            querydict[ViewParam.PAGE] = 1
            # Send the user to the actual data using GET
            # (the parameters are NOT sensitive)
            return HTTPFound(
                req.route_url(Routes.VIEW_EXPORTED_TASK_LIST, _query=querydict)
            )
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return render_to_response(
        "exported_task_choose.mako",
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_LIST,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_list(req: "CamcopsRequest") -> Response:
    """
    View to serve the exported task log.
    """
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    recipient_name = req.get_str_param(
        ViewParam.RECIPIENT_NAME,
        None,
        validator=validate_export_recipient_name,
    )
    table_name = req.get_str_param(
        ViewParam.TABLE_NAME, None, validator=validate_task_tablename
    )
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    et_id = req.get_int_param(ViewParam.ID, None)
    start_datetime = req.get_datetime_param(ViewParam.START_DATETIME)
    end_datetime = req.get_datetime_param(ViewParam.END_DATETIME)
    page_num = req.get_int_param(ViewParam.PAGE, 1)

    conditions = []  # type: List[str]

    def add_condition(key: str, value: Any) -> None:
        conditions.append(f"{key} = {value}")

    dbsession = req.dbsession
    q = dbsession.query(ExportedTask)

    if recipient_name:
        q = q.join(ExportRecipient).filter(
            ExportRecipient.recipient_name == recipient_name
        )
        add_condition(ViewParam.RECIPIENT_NAME, recipient_name)
    if table_name:
        q = q.filter(ExportedTask.basetable == table_name)
        add_condition(ViewParam.TABLE_NAME, table_name)
    if server_pk is not None:
        q = q.filter(ExportedTask.task_server_pk == server_pk)
        add_condition(ViewParam.SERVER_PK, server_pk)
    if et_id is not None:
        q = q.filter(ExportedTask.id == et_id)
        add_condition(ViewParam.ID, et_id)
    if start_datetime:
        q = q.filter(ExportedTask.start_at_utc >= start_datetime)
        add_condition(ViewParam.START_DATETIME, start_datetime)
    if end_datetime:
        q = q.filter(ExportedTask.start_at_utc < end_datetime)
        add_condition(ViewParam.END_DATETIME, end_datetime)

    q = q.order_by(desc(ExportedTask.id))

    page = SqlalchemyOrmPage(
        query=q,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )
    return render_to_response(
        "exported_task_list.mako",
        dict(conditions="; ".join(conditions), page=page),
        request=req,
    )


# =============================================================================
# View helpers for ORM objects
# =============================================================================


def _view_generic_object_by_id(
    req: "CamcopsRequest",
    cls: Type,
    instance_name_for_mako: str,
    mako_template: str,
) -> Response:
    """
    Boilerplate code to view an individual SQLAlchemy ORM object. The object
    must have an integer ``id`` field as its primary key, and the ID value must
    be present in the ``ViewParam.ID`` field of the request.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        cls: the SQLAlchemy ORM class
        instance_name_for_mako: what will the object be called when it's
        mako_template: Mako template filename

    Returns:
        :class:`pyramid.response.Response`
    """
    item_id = req.get_int_param(ViewParam.ID, None)
    dbsession = req.dbsession
    # noinspection PyUnresolvedReferences
    obj = dbsession.query(cls).filter(cls.id == item_id).first()
    if obj is None:
        _ = req.gettext
        raise HTTPBadRequest(
            f"{_('Bad ID for object type')} " f"{cls.__name__}: {item_id}"
        )
    d = {instance_name_for_mako: obj}
    return render_to_response(mako_template, d, request=req)


# =============================================================================
# Specialized views for ORM objects
# =============================================================================


@view_config(
    route_name=Routes.VIEW_EMAIL,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_email(req: "CamcopsRequest") -> Response:
    """
    View on an individual :class:`camcops_server.cc_modules.cc_email.Email`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=Email,
        instance_name_for_mako="email",
        mako_template="view_email.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORT_RECIPIENT,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_export_recipient(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTask`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportRecipient,
        instance_name_for_mako="recipient",
        mako_template="export_recipient.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTask`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTask,
        instance_name_for_mako="et",
        mako_template="exported_task.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_EMAIL,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_email(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskEmail`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTaskEmail,
        instance_name_for_mako="ete",
        mako_template="exported_task_email.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_FILE_GROUP,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_file_group(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskFileGroup`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTaskFileGroup,
        instance_name_for_mako="fg",
        mako_template="exported_task_file_group.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_HL7_MESSAGE,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_hl7_message(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskHL7Message`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTaskHL7Message,
        instance_name_for_mako="msg",
        mako_template="exported_task_hl7_message.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_REDCAP,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_redcap(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskRedcap`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTaskRedcap,
        instance_name_for_mako="etr",
        mako_template="exported_task_redcap.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_FHIR,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_fhir(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskRedcap`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTaskFhir,
        instance_name_for_mako="etf",
        mako_template="exported_task_fhir.mako",
    )


@view_config(
    route_name=Routes.VIEW_EXPORTED_TASK_FHIR_ENTRY,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def view_exported_task_fhir_entry(req: "CamcopsRequest") -> Response:
    """
    View on an individual
    :class:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskRedcap`.
    """
    return _view_generic_object_by_id(
        req=req,
        cls=ExportedTaskFhirEntry,
        instance_name_for_mako="etfe",
        mako_template="exported_task_fhir_entry.mako",
    )


# =============================================================================
# User/server info views
# =============================================================================


@view_config(
    route_name=Routes.VIEW_OWN_USER_INFO,
    renderer="view_own_user_info.mako",
    http_cache=NEVER_CACHE,
)
def view_own_user_info(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to provide information about your own user.
    """
    groups_page = CamcopsPage(
        req.user.groups, url_maker=PageUrl(req), request=req
    )
    return dict(
        user=req.user,
        groups_page=groups_page,
        valid_which_idnums=req.valid_which_idnums,
    )


@view_config(
    route_name=Routes.VIEW_SERVER_INFO,
    renderer="view_server_info.mako",
    http_cache=NEVER_CACHE,
)
def view_server_info(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to show the server's ID policies, etc.
    """
    _ = req.gettext
    now = req.now
    recent_activity = OrderedDict(
        [
            (
                _("Last 1 minute"),
                CamcopsSession.n_sessions_active_since(
                    req, now.subtract(minutes=1)
                ),
            ),
            (
                _("Last 5 minutes"),
                CamcopsSession.n_sessions_active_since(
                    req, now.subtract(minutes=5)
                ),
            ),
            (
                _("Last 10 minutes"),
                CamcopsSession.n_sessions_active_since(
                    req, now.subtract(minutes=10)
                ),
            ),
            (
                _("Last 1 hour"),
                CamcopsSession.n_sessions_active_since(
                    req, now.subtract(hours=1)
                ),
            ),
        ]
    )
    return dict(
        idnum_definitions=req.idnum_definitions,
        string_families=req.extrastring_families(),
        recent_activity=recent_activity,
        session_timeout_minutes=req.config.session_timeout_minutes,
        restricted_tasks=req.config.restricted_tasks,
    )


# =============================================================================
# User management
# =============================================================================


def get_user_from_request_user_id_or_raise(req: "CamcopsRequest") -> User:
    """
    Returns the :class:`camcops_server.cc_modules.cc_user.User` represented by
    the request's ``ViewParam.USER_ID`` parameter, or raise
    :exc:`HTTPBadRequest`.
    """
    user_id = req.get_int_param(ViewParam.USER_ID)
    user = User.get_user_by_id(req.dbsession, user_id)
    if not user:
        _ = req.gettext
        raise HTTPBadRequest(f"{_('No such user ID:')} {user_id!r}")
    return user


def query_users_that_i_manage(req: "CamcopsRequest") -> Query:
    me = req.user
    return me.managed_users()


@view_config(
    route_name=Routes.VIEW_ALL_USERS,
    permission=Permission.GROUPADMIN,
    renderer="users_view.mako",
    http_cache=NEVER_CACHE,
)
def view_all_users(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View all users that the current user administers. The view has hyperlinks
    to edit those users too.
    """
    include_auto_generated = req.get_bool_param(
        ViewParam.INCLUDE_AUTO_GENERATED, False
    )
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    q = query_users_that_i_manage(req)
    if not include_auto_generated:
        q = q.filter(User.auto_generated == False)  # noqa: E712
    page = SqlalchemyOrmPage(
        query=q,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )

    form = UserFilterForm(request=req)
    appstruct = {ViewParam.INCLUDE_AUTO_GENERATED: include_auto_generated}
    rendered_form = form.render(appstruct)

    return dict(
        page=page,
        head_form_html=get_head_form_html(req, [form]),
        form=rendered_form,
    )


@view_config(
    route_name=Routes.VIEW_USER_EMAIL_ADDRESSES,
    permission=Permission.GROUPADMIN,
    renderer="view_user_email_addresses.mako",
    http_cache=NEVER_CACHE,
)
def view_user_email_addresses(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View e-mail addresses of all users that the requesting user is authorized
    to manage.
    """
    q = query_users_that_i_manage(req).filter(
        User.auto_generated == False  # noqa: E712
    )
    return dict(query=q)


def assert_may_edit_user(req: "CamcopsRequest", user: User) -> None:
    """
    Checks that the requesting user (``req.user``) is allowed to edit the other
    user (``user``). Raises :exc:`HTTPBadRequest` otherwise.
    """
    may_edit, why_not = req.user.may_edit_user(req, user)
    if not may_edit:
        raise HTTPBadRequest(why_not)


def assert_may_administer_group(req: "CamcopsRequest", group_id: int) -> None:
    """
    Checks that the requesting user (``req.user``) is allowed to adminster the
    specified group (specified by ``group_id``). Raises :exc:`HTTPBadRequest`
    otherwise.
    """
    if not req.user.may_administer_group(group_id):
        _ = req.gettext
        raise HTTPBadRequest(_("You may not administer this group"))


@view_config(
    route_name=Routes.VIEW_USER,
    permission=Permission.GROUPADMIN,
    renderer="view_other_user_info.mako",
    http_cache=NEVER_CACHE,
)
def view_user(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to show details of another user, for administrators.
    """
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    return dict(user=user)
    # Groupadmins may see some information regarding groups that aren't theirs
    # here, but can't alter it.


class EditUserBaseView(UpdateView):
    """
    Django-style view to edit a user and their groups
    """

    model_form_dict = {
        "username": ViewParam.USERNAME,
        "fullname": ViewParam.FULLNAME,
        "email": ViewParam.EMAIL,
        "must_change_password": ViewParam.MUST_CHANGE_PASSWORD,
        "language": ViewParam.LANGUAGE,
    }
    object_class = User
    pk_param = ViewParam.USER_ID
    server_pk_name = "id"
    template_name = "user_edit.mako"

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_ALL_USERS)

    def get_object(self) -> Any:
        user = cast(User, super().get_object())

        assert_may_edit_user(self.request, user)

        return user

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        user = cast(User, self.object)
        _ = self.request.gettext

        new_user_name = appstruct.get(ViewParam.USERNAME)
        existing_user = User.get_user_by_name(
            self.request.dbsession, new_user_name
        )
        if existing_user and existing_user.id != user.id:
            # noinspection PyUnresolvedReferences
            cant_rename_user = _("Can't rename user")
            conflicts = _("that conflicts with an existing user with ID")
            raise HTTPBadRequest(
                f"{cant_rename_user} {user.username!r} (#{user.id!r}) → "
                f"{new_user_name!r}; {conflicts} {existing_user.id!r}"
            )

        email = appstruct.get(ViewParam.EMAIL)
        if not email and user.mfa_method == MfaMethod.HOTP_EMAIL:
            message = _(
                "This user's email address is used for multi-factor "
                "authentication. If you want to remove their email "
                "address, you must first disable multi-factor "
                "authentication"
            )

            raise HTTPBadRequest(message)

        super().set_object_properties(appstruct)

        # Groups that we might change memberships for:
        all_fluid_groups = self.request.user.ids_of_groups_user_is_admin_for
        # All groups that the user is currently in:
        user_group_ids = user.group_ids
        # Group membership we won't touch:
        user_frozen_group_ids = list(
            set(user_group_ids) - set(all_fluid_groups)
        )
        group_ids = appstruct.get(ViewParam.GROUP_IDS)
        # Add back in the groups we're not going to alter:
        final_group_ids = list(set(group_ids) | set(user_frozen_group_ids))
        user.set_group_ids(final_group_ids)
        # Also, if the user was uploading to a group that they are now no
        # longer a member of, we need to fix that
        if user.upload_group_id not in final_group_ids:
            user.upload_group_id = None

    def get_form_values(self) -> Dict[str, Any]:
        # will populate with model_form_dict
        form_values = super().get_form_values()

        user = cast(User, self.object)

        # Superusers can do everything, of course.
        # Groupadmins can change group memberships only for groups they control
        # (here: "fluid"). That means that there may be a subset of group
        # memberships for this user that they will neither see nor be able to
        # alter (here: "frozen"). They can also edit only a restricted set of
        # permissions.

        # Groups that we might change memberships for:
        all_fluid_groups = self.request.user.ids_of_groups_user_is_admin_for
        # All groups that the user is currently in:
        user_group_ids = user.group_ids
        # Group memberships we might alter:
        user_fluid_group_ids = list(
            set(user_group_ids) & set(all_fluid_groups)
        )
        form_values.update(
            {
                ViewParam.USER_ID: user.id,
                ViewParam.GROUP_IDS: user_fluid_group_ids,
            }
        )

        return form_values


class EditUserGroupAdminView(EditUserBaseView):
    """
    For group administrators to edit a user.
    """

    form_class = EditUserGroupAdminForm


class EditUserSuperUserView(EditUserBaseView):
    """
    For superusers to edit a user.
    """

    form_class = EditUserFullForm

    def get_model_form_dict(self) -> Dict[str, Any]:
        model_form_dict = super().get_model_form_dict()
        model_form_dict["superuser"] = ViewParam.SUPERUSER

        return model_form_dict


@view_config(
    route_name=Routes.EDIT_USER,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def edit_user(req: "CamcopsRequest") -> Response:
    """
    View to edit a user (for administrators).
    """
    view: EditUserBaseView

    if req.user.superuser:
        view = EditUserSuperUserView(req)
    else:
        view = EditUserGroupAdminView(req)

    return view.dispatch()


class EditUserGroupMembershipBaseView(UpdateView):
    """
    Django-style view to edit a user's group membership permissions.
    """

    model_form_dict = {
        "may_upload": ViewParam.MAY_UPLOAD,
        "may_register_devices": ViewParam.MAY_REGISTER_DEVICES,
        "may_use_webviewer": ViewParam.MAY_USE_WEBVIEWER,
        "view_all_patients_when_unfiltered": ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED,  # noqa: E501
        "may_dump_data": ViewParam.MAY_DUMP_DATA,
        "may_run_reports": ViewParam.MAY_RUN_REPORTS,
        "may_add_notes": ViewParam.MAY_ADD_NOTES,
        "may_manage_patients": ViewParam.MAY_MANAGE_PATIENTS,
        "may_email_patients": ViewParam.MAY_EMAIL_PATIENTS,
    }

    object_class = UserGroupMembership
    pk_param = ViewParam.USER_GROUP_MEMBERSHIP_ID
    server_pk_name = "id"
    template_name = "user_edit_group_membership.mako"

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_ALL_USERS)

    def get_object(self) -> Any:
        # noinspection PyUnresolvedReferences
        ugm = cast(UserGroupMembership, super().get_object())
        user = ugm.user
        assert_may_edit_user(self.request, user)
        assert_may_administer_group(self.request, ugm.group_id)

        return ugm


class EditUserGroupMembershipSuperUserView(EditUserGroupMembershipBaseView):
    """
    For superusers to edit a user's group memberships.
    """

    form_class = EditUserGroupPermissionsFullForm

    def get_model_form_dict(self) -> Dict[str, str]:
        model_form_dict = super().get_model_form_dict()
        model_form_dict["groupadmin"] = ViewParam.GROUPADMIN

        return model_form_dict


class EditUserGroupMembershipGroupAdminView(EditUserGroupMembershipBaseView):
    """
    For group administrators to edit a user's group memberships.
    """

    form_class = EditUserGroupMembershipGroupAdminForm


@view_config(
    route_name=Routes.EDIT_USER_GROUP_MEMBERSHIP,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def edit_user_group_membership(req: "CamcopsRequest") -> Response:
    """
    View to edit the group memberships of a user (for administrators).
    """
    if req.user.superuser:
        view = EditUserGroupMembershipSuperUserView(req)
    else:
        view = EditUserGroupMembershipGroupAdminView(req)

    return view.dispatch()


def set_user_upload_group(
    req: "CamcopsRequest", user: User, by_another: bool
) -> Response:
    """
    Provides a view to choose which group a user uploads into.

    TRUSTS ITS CALLER that this is permitted.

    Args:
        req: the :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        user: the :class:`camcops_server.cc_modules.cc_user.User` to edit
        by_another: is the current user a superuser/group administrator, i.e.
            another user? Determines the screen we return to afterwards.
    """
    route_back = Routes.VIEW_ALL_USERS if by_another else Routes.HOME
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
            ViewParam.UPLOAD_GROUP_ID: user.upload_group_id,
        }
        rendered_form = form.render(appstruct)
    return render_to_response(
        "set_user_upload_group.mako",
        dict(
            user=user,
            form=rendered_form,
            head_form_html=get_head_form_html(req, [form]),
        ),
        request=req,
    )


@view_config(
    route_name=Routes.SET_OWN_USER_UPLOAD_GROUP, http_cache=NEVER_CACHE
)
def set_own_user_upload_group(req: "CamcopsRequest") -> Response:
    """
    View to set the upload group for your own user.
    """
    return set_user_upload_group(req, req.user, False)


@view_config(
    route_name=Routes.SET_OTHER_USER_UPLOAD_GROUP,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def set_other_user_upload_group(req: "CamcopsRequest") -> Response:
    """
    View to set the upload group for another user.
    """
    user = get_user_from_request_user_id_or_raise(req)
    if user.id != req.user.id:
        assert_may_edit_user(req, user)
    # ... but always OK to edit this for your own user; no such check required
    return set_user_upload_group(req, user, True)


# noinspection PyTypeChecker
@view_config(
    route_name=Routes.UNLOCK_USER,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def unlock_user(req: "CamcopsRequest") -> Response:
    """
    View to unlock a locked user account.
    """
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    user.enable(req)
    _ = req.gettext

    req.session.flash(
        _("User {username} enabled").format(username=user.username),
        queue=FlashQueue.SUCCESS,
    )
    raise HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))


@view_config(
    route_name=Routes.ADD_USER,
    permission=Permission.GROUPADMIN,
    renderer="user_add.mako",
    http_cache=NEVER_CACHE,
)
def add_user(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to add a user.
    """
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
            user.must_change_password = appstruct.get(
                ViewParam.MUST_CHANGE_PASSWORD
            )
            # We don't ask for language initially; that can be configured
            # later. But is is a reasonable guess that it should be the same
            # language as used by the person creating the new user.
            user.language = req.language
            if User.get_user_by_name(dbsession, user.username):
                raise HTTPBadRequest(
                    f"User with username {user.username!r} already exists!"
                )
            dbsession.add(user)
            group_ids = appstruct.get(ViewParam.GROUP_IDS)
            for gid in group_ids:
                # noinspection PyUnresolvedReferences
                user.user_group_memberships.append(
                    UserGroupMembership(user_id=user.id, group_id=gid)
                )
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        rendered_form = form.render()
    return dict(
        form=rendered_form, head_form_html=get_head_form_html(req, [form])
    )


def any_records_use_user(req: "CamcopsRequest", user: User) -> bool:
    """
    Do any records in the database refer to the specified user?

    (Used when we're thinking about deleting a user; would it leave broken
    references? If so, we will prevent deletion; see :func:`delete_user`.)
    """
    dbsession = req.dbsession
    user_id = user.id
    # Device?
    q = CountStarSpecializedQuery(Device, session=dbsession).filter(
        or_(
            Device.registered_by_user_id == user_id,
            Device.uploading_user_id == user_id,
        )
    )
    if q.count_star() > 0:
        return True
    # SpecialNote?
    q = CountStarSpecializedQuery(SpecialNote, session=dbsession).filter(
        SpecialNote.user_id == user_id
    )
    if q.count_star() > 0:
        return True
    # Audit trail?
    q = CountStarSpecializedQuery(AuditEntry, session=dbsession).filter(
        AuditEntry.user_id == user_id
    )
    if q.count_star() > 0:
        return True
    # Uploaded records?
    for cls in gen_orm_classes_from_base(
        GenericTabletRecordMixin
    ):  # type: Type[GenericTabletRecordMixin]  # noqa
        # noinspection PyProtectedMember
        q = CountStarSpecializedQuery(cls, session=dbsession).filter(
            or_(
                cls._adding_user_id == user_id,
                cls._removing_user_id == user_id,
                cls._preserving_user_id == user_id,
                cls._manually_erasing_user_id == user_id,
            )
        )
        if q.count_star() > 0:
            return True
    # No; all clean.
    return False


@view_config(
    route_name=Routes.DELETE_USER,
    permission=Permission.GROUPADMIN,
    renderer="user_delete.mako",
    http_cache=NEVER_CACHE,
)
def delete_user(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to delete a user (and make it hard work).
    """
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(Routes.VIEW_ALL_USERS))
    user = get_user_from_request_user_id_or_raise(req)
    assert_may_edit_user(req, user)
    form = DeleteUserForm(request=req)
    rendered_form = ""
    error = ""
    _ = req.gettext
    if user.id == req.user.id:
        error = _("Can't delete your own user!")
    elif user.may_use_webviewer or user.may_upload:
        error = _(
            "Unable to delete user: user still has webviewer login "
            "and/or tablet upload permission"
        )
    elif user.superuser and (not req.user.superuser):
        error = _(
            "Unable to delete user: " "they are a superuser and you are not"
        )
    elif (not req.user.superuser) and bool(
        set(user.group_ids) - set(req.user.ids_of_groups_user_is_admin_for)
    ):
        error = _(
            "Unable to delete user: "
            "user belongs to groups that you do not administer"
        )
    else:
        if any_records_use_user(req, user):
            error = _(
                "Unable to delete user; records (or audit trails) refer to "
                "that user. Disable login and upload permissions instead."
            )
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
                    # https://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#relationships-many-to-many-deletion  # noqa
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

    return dict(
        user=user,
        error=error,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form]),
    )


# =============================================================================
# Group management
# =============================================================================


@view_config(
    route_name=Routes.VIEW_GROUPS,
    permission=Permission.SUPERUSER,
    renderer="groups_view.mako",
    http_cache=NEVER_CACHE,
)
def view_groups(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to show all groups (with hyperlinks to edit them).
    Superusers only.
    """
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    dbsession = req.dbsession
    groups = (
        dbsession.query(Group).order_by(Group.name).all()
    )  # type: List[Group]  # noqa
    page = CamcopsPage(
        collection=groups,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )

    valid_which_idnums = req.valid_which_idnums

    return dict(groups_page=page, valid_which_idnums=valid_which_idnums)


def get_group_from_request_group_id_or_raise(req: "CamcopsRequest") -> Group:
    """
    Returns the :class:`camcops_server.cc_modules.cc_group.Group` represented
    by the request's ``ViewParam.GROUP_ID`` parameter, or raise
    :exc:`HTTPBadRequest`.
    """
    group_id = req.get_int_param(ViewParam.GROUP_ID)
    group = None
    if group_id is not None:
        dbsession = req.dbsession
        group = dbsession.query(Group).filter(Group.id == group_id).first()
    if not group:
        _ = req.gettext
        raise HTTPBadRequest(f"{_('No such group ID:')} {group_id!r}")
    return group


class EditGroupView(UpdateView):
    """
    Django-style view to edit a CamCOPS group.
    """

    form_class = EditGroupForm
    model_form_dict = {
        "name": ViewParam.NAME,
        "description": ViewParam.DESCRIPTION,
        "upload_policy": ViewParam.UPLOAD_POLICY,
        "finalize_policy": ViewParam.FINALIZE_POLICY,
    }
    object_class = Group
    pk_param = ViewParam.GROUP_ID
    server_pk_name = "id"
    template_name = "group_edit.mako"

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()

        group = cast(Group, self.object)
        kwargs.update(group=group)

        return kwargs

    def get_form_values(self) -> Dict:
        # will populate with model_form_dict
        form_values = super().get_form_values()

        group = cast(Group, self.object)

        other_group_ids = list(group.ids_of_other_groups_group_may_see())
        other_groups = Group.get_groups_from_id_list(
            self.request.dbsession, other_group_ids
        )
        other_groups.sort(key=lambda g: g.name)

        form_values.update(
            {
                ViewParam.IP_USE: group.ip_use,
                ViewParam.GROUP_ID: group.id,
                ViewParam.GROUP_IDS: [g.id for g in other_groups],
            }
        )

        return form_values

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_GROUPS)

    def save_object(self, appstruct: Dict[str, Any]) -> None:
        super().save_object(appstruct)

        group = cast(Group, self.object)

        # Group cross-references
        group_ids = appstruct.get(ViewParam.GROUP_IDS)
        # The form validation will prevent our own group from being in here
        other_groups = Group.get_groups_from_id_list(
            self.request.dbsession, group_ids
        )
        group.can_see_other_groups = other_groups

        ip_use = appstruct.get(ViewParam.IP_USE)
        if group.ip_use is not None:
            ip_use.id = group.ip_use.id

        group.ip_use = ip_use


@view_config(
    route_name=Routes.EDIT_GROUP,
    permission=Permission.SUPERUSER,
    http_cache=NEVER_CACHE,
)
def edit_group(req: "CamcopsRequest") -> Response:
    """
    View to edit a group. Superusers only.
    """
    return EditGroupView(req).dispatch()


@view_config(
    route_name=Routes.ADD_GROUP,
    permission=Permission.SUPERUSER,
    renderer="group_add.mako",
    http_cache=NEVER_CACHE,
)
def add_group(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to add a group. Superusers only.
    """
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
    return dict(
        form=rendered_form, head_form_html=get_head_form_html(req, [form])
    )


def any_records_use_group(req: "CamcopsRequest", group: Group) -> bool:
    """
    Do any records in the database refer to the specified group?

    (Used when we're thinking about deleting a group; would it leave broken
    references? If so, we will prevent deletion; see :func:`delete_group`.)
    """
    dbsession = req.dbsession
    group_id = group.id
    # Our own or users filtering on us?
    # ... doesn't matter; see TaskFilter; stored as a CSV list so not part of
    #     database integrity checks.
    # Uploaded records?
    for cls in gen_orm_classes_from_base(
        GenericTabletRecordMixin
    ):  # type: Type[GenericTabletRecordMixin]  # noqa
        # noinspection PyProtectedMember
        q = CountStarSpecializedQuery(cls, session=dbsession).filter(
            cls._group_id == group_id
        )
        if q.count_star() > 0:
            return True
    # No; all clean.
    return False


@view_config(
    route_name=Routes.DELETE_GROUP,
    permission=Permission.SUPERUSER,
    renderer="group_delete.mako",
    http_cache=NEVER_CACHE,
)
def delete_group(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to delete a group. Superusers only.
    """
    route_back = Routes.VIEW_GROUPS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    group = get_group_from_request_group_id_or_raise(req)
    form = DeleteGroupForm(request=req)
    rendered_form = ""
    error = ""
    _ = req.gettext
    if group.users:
        error = _("Unable to delete group; there are users who are members!")
    else:
        if any_records_use_group(req, group):
            error = _("Unable to delete group; records refer to it.")
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
    return dict(
        group=group,
        error=error,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form]),
    )


# =============================================================================
# Edit server settings
# =============================================================================


@view_config(
    route_name=Routes.EDIT_SERVER_SETTINGS,
    permission=Permission.SUPERUSER,
    renderer="server_settings_edit.mako",
    http_cache=NEVER_CACHE,
)
def edit_server_settings(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to edit server settings (like the database title).
    """
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
    return dict(
        form=rendered_form, head_form_html=get_head_form_html(req, [form])
    )


@view_config(
    route_name=Routes.VIEW_ID_DEFINITIONS,
    permission=Permission.SUPERUSER,
    renderer="id_definitions_view.mako",
    http_cache=NEVER_CACHE,
)
def view_id_definitions(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to show all ID number definitions (with hyperlinks to edit them).
    Superusers only.
    """
    return dict(idnum_definitions=req.idnum_definitions)


def get_iddef_from_request_which_idnum_or_raise(
    req: "CamcopsRequest",
) -> IdNumDefinition:
    """
    Returns the :class:`camcops_server.cc_modules.cc_idnumdef.IdNumDefinition`
    represented by the request's ``ViewParam.WHICH_IDNUM`` parameter, or raise
    :exc:`HTTPBadRequest`.
    """
    which_idnum = req.get_int_param(ViewParam.WHICH_IDNUM)
    iddef = (
        req.dbsession.query(IdNumDefinition)
        .filter(IdNumDefinition.which_idnum == which_idnum)
        .first()
    )
    if not iddef:
        _ = req.gettext
        raise HTTPBadRequest(f"{_('No such ID definition:')} {which_idnum!r}")
    return iddef


@view_config(
    route_name=Routes.EDIT_ID_DEFINITION,
    permission=Permission.SUPERUSER,
    renderer="id_definition_edit.mako",
    http_cache=NEVER_CACHE,
)
def edit_id_definition(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to edit an ID number definition. Superusers only.
    """
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
            iddef.short_description = appstruct.get(
                ViewParam.SHORT_DESCRIPTION
            )
            iddef.validation_method = appstruct.get(
                ViewParam.VALIDATION_METHOD
            )
            iddef.hl7_id_type = appstruct.get(ViewParam.HL7_ID_TYPE)
            iddef.hl7_assigning_authority = appstruct.get(
                ViewParam.HL7_ASSIGNING_AUTHORITY
            )
            iddef.fhir_id_system = appstruct.get(ViewParam.FHIR_ID_SYSTEM)
            # REMOVED # clear_idnum_definition_cache()  # SPECIAL
            raise HTTPFound(req.route_url(route_back))
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {
            ViewParam.WHICH_IDNUM: iddef.which_idnum,
            ViewParam.DESCRIPTION: iddef.description or "",
            ViewParam.SHORT_DESCRIPTION: iddef.short_description or "",
            ViewParam.VALIDATION_METHOD: iddef.validation_method or "",
            ViewParam.HL7_ID_TYPE: iddef.hl7_id_type or "",
            ViewParam.HL7_ASSIGNING_AUTHORITY: iddef.hl7_assigning_authority
            or "",  # noqa
            ViewParam.FHIR_ID_SYSTEM: iddef.fhir_id_system or "",
        }
        rendered_form = form.render(appstruct)
    return dict(
        iddef=iddef,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form]),
    )


@view_config(
    route_name=Routes.ADD_ID_DEFINITION,
    permission=Permission.SUPERUSER,
    renderer="id_definition_add.mako",
    http_cache=NEVER_CACHE,
)
def add_id_definition(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to add an ID number definition. Superusers only.
    """
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
                # we skip hl7_id_type at this stage
                # we skip hl7_assigning_authority at this stage
                validation_method=appstruct.get(ViewParam.VALIDATION_METHOD),
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
    return dict(
        form=rendered_form, head_form_html=get_head_form_html(req, [form])
    )


def any_records_use_iddef(
    req: "CamcopsRequest", iddef: IdNumDefinition
) -> bool:
    """
    Do any records in the database refer to the specified ID number definition?

    (Used when we're thinking about deleting one; would it leave broken
    references? If so, we will prevent deletion; see
    :func:`delete_id_definition`.)
    """
    # Helpfully, these are only referred to permanently from one place:
    q = CountStarSpecializedQuery(PatientIdNum, session=req.dbsession).filter(
        PatientIdNum.which_idnum == iddef.which_idnum
    )
    if q.count_star() > 0:
        return True
    # No; all clean.
    return False


@view_config(
    route_name=Routes.DELETE_ID_DEFINITION,
    permission=Permission.SUPERUSER,
    renderer="id_definition_delete.mako",
    http_cache=NEVER_CACHE,
)
def delete_id_definition(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to delete an ID number definition. Superusers only.
    """
    route_back = Routes.VIEW_ID_DEFINITIONS
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(req.route_url(route_back))
    iddef = get_iddef_from_request_which_idnum_or_raise(req)
    form = DeleteIdDefinitionForm(request=req)
    rendered_form = ""
    error = ""
    if any_records_use_iddef(req, iddef):
        _ = req.gettext
        error = _("Unable to delete ID definition; records refer to it.")
    else:
        if FormAction.DELETE in req.POST:
            try:
                controls = list(req.POST.items())
                appstruct = form.validate(controls)
                assert (
                    appstruct.get(ViewParam.WHICH_IDNUM) == iddef.which_idnum
                )
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
    return dict(
        iddef=iddef,
        error=error,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form]),
    )


# =============================================================================
# Altering data. Some of the more complex logic is here.
# =============================================================================


@view_config(
    route_name=Routes.ADD_SPECIAL_NOTE,
    renderer="special_note_add.mako",
    http_cache=NEVER_CACHE,
)
def add_special_note(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to add a special note to a task (after confirmation).

    (Note that users can't add special notes to patients -- those get added
    automatically when a patient is edited. So the context here is always of a
    task.)
    """
    table_name = req.get_str_param(
        ViewParam.TABLE_NAME, validator=validate_task_tablename
    )
    server_pk = req.get_int_param(ViewParam.SERVER_PK, None)
    url_back = req.route_url(
        Routes.TASK,
        _query={
            ViewParam.TABLE_NAME: table_name,
            ViewParam.SERVER_PK: server_pk,
            ViewParam.VIEWTYPE: ViewArg.HTML,
        },
    )
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(url_back)
    task = task_factory(req, table_name, server_pk)
    _ = req.gettext
    if task is None:
        raise HTTPBadRequest(
            f"{_('No such task:')} {table_name}, PK={server_pk}"
        )
    user = req.user
    if not user.authorized_to_add_special_note(task.group_id):
        raise HTTPBadRequest(
            _("Not authorized to add special notes for this task's group")
        )
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
    return dict(
        task=task,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form]),
        viewtype=ViewArg.HTML,
    )


@view_config(
    route_name=Routes.DELETE_SPECIAL_NOTE,
    renderer="special_note_delete.mako",
    http_cache=NEVER_CACHE,
)
def delete_special_note(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View to delete a special note (after confirmation).
    """
    note_id = req.get_int_param(ViewParam.NOTE_ID, None)
    sn = SpecialNote.get_specialnote_by_id(req.dbsession, note_id)
    _ = req.gettext
    if sn is None:
        raise HTTPBadRequest(f"{_('No such SpecialNote:')} note_id={note_id}")
    if sn.hidden:
        raise HTTPBadRequest(
            f"{_('SpecialNote already deleted/hidden:')} " f"note_id={note_id}"
        )
    if not sn.user_may_delete_specialnote(req.user):
        raise HTTPBadRequest(_("Not authorized to delete this special note"))
    url_back = req.route_url(Routes.VIEW_TASKS)  # default
    if sn.refers_to_patient():
        # Special note on a patient.
        # We might have come here from any number of tasks relating to this
        # patient. In principle this information is retrievable; in practice it
        # is a considerable faff for a rare operation, since special notes are
        # displayed via special_notes.mako, which only looks at information
        # stored with the note itself.
        pass
    else:
        # Special note on a task.
        task = sn.target_task()
        if task:
            url_back = req.route_url(
                Routes.TASK,
                _query={
                    ViewParam.TABLE_NAME: task.tablename,
                    ViewParam.SERVER_PK: task.pk,
                    ViewParam.VIEWTYPE: ViewArg.HTML,
                },
            )
    if FormAction.CANCEL in req.POST:
        raise HTTPFound(url_back)
    form = DeleteSpecialNoteForm(request=req)
    if FormAction.SUBMIT in req.POST:
        try:
            controls = list(req.POST.items())
            form.validate(controls)
            # -----------------------------------------------------------------
            # Delete special note
            # -----------------------------------------------------------------
            sn.hidden = True
            raise HTTPFound(url_back)
        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        appstruct = {ViewParam.NOTE_ID: note_id}
        rendered_form = form.render(appstruct)
    return dict(
        sn=sn,
        form=rendered_form,
        head_form_html=get_head_form_html(req, [form]),
    )


class EraseTaskBaseView(DeleteView):
    """
    Django-style view to erase a task.
    """

    form_class = EraseTaskForm

    def get_object(self) -> Any:
        # noinspection PyAttributeOutsideInit
        self.table_name = self.request.get_str_param(
            ViewParam.TABLE_NAME, validator=validate_task_tablename
        )
        # noinspection PyAttributeOutsideInit
        self.server_pk = self.request.get_int_param(ViewParam.SERVER_PK, None)

        task = task_factory(self.request, self.table_name, self.server_pk)
        _ = self.request.gettext
        if task is None:
            raise HTTPBadRequest(
                f"{_('No such task:')} {self.table_name}, PK={self.server_pk}"
            )
        if task.is_live_on_tablet():
            raise HTTPBadRequest(errormsg_task_live(self.request))
        self.check_user_is_authorized(task)

        return task

    def check_user_is_authorized(self, task: Task) -> None:
        if not self.request.user.authorized_to_erase_tasks(task.group_id):
            _ = self.request.gettext
            raise HTTPBadRequest(
                _("Not authorized to erase tasks for this task's group")
            )

    def get_cancel_url(self) -> str:
        return self.request.route_url(
            Routes.TASK,
            _query={
                ViewParam.TABLE_NAME: self.table_name,
                ViewParam.SERVER_PK: self.server_pk,
                ViewParam.VIEWTYPE: ViewArg.HTML,
            },
        )


class EraseTaskLeavingPlaceholderView(EraseTaskBaseView):
    """
    Django-style view to erase data from a task, leaving an empty
    "placeholder".
    """

    template_name = "task_erase.mako"

    def get_object(self) -> Any:
        task = cast(Task, super().get_object())
        if task.is_erased():
            _ = self.request.gettext
            raise HTTPBadRequest(_("Task already erased"))

        return task

    def delete(self) -> None:
        task = cast(Task, self.object)

        task.manually_erase(self.request)

    def get_success_url(self) -> str:
        return self.request.route_url(
            Routes.TASK,
            _query={
                ViewParam.TABLE_NAME: self.table_name,
                ViewParam.SERVER_PK: self.server_pk,
                ViewParam.VIEWTYPE: ViewArg.HTML,
            },
        )


class EraseTaskEntirelyView(EraseTaskBaseView):
    """
    Django-style view to erase (delete) a task entirely.
    """

    template_name = "task_erase_entirely.mako"

    def delete(self) -> None:
        task = cast(Task, self.object)

        TaskIndexEntry.unindex_task(task, self.request.dbsession)
        task.delete_entirely(self.request)

        _ = self.request.gettext

        msg_erased = _("Task erased:")

        self.request.session.flash(
            f"{msg_erased} ({self.table_name}, server PK {self.server_pk}).",
            queue=FlashQueue.SUCCESS,
        )

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_TASKS)


@view_config(
    route_name=Routes.ERASE_TASK_LEAVING_PLACEHOLDER,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def erase_task_leaving_placeholder(req: "CamcopsRequest") -> Response:
    """
    View to wipe all data from a task (after confirmation).

    Leaves the task record as a placeholder.
    """
    return EraseTaskLeavingPlaceholderView(req).dispatch()


@view_config(
    route_name=Routes.ERASE_TASK_ENTIRELY,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def erase_task_entirely(req: "CamcopsRequest") -> Response:
    """
    View to erase a task from the database entirely (after confirmation).
    """
    return EraseTaskEntirelyView(req).dispatch()


@view_config(
    route_name=Routes.DELETE_PATIENT,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def delete_patient(req: "CamcopsRequest") -> Response:
    """
    View to delete completely all data for a patient (after confirmation),
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
    _ = req.gettext
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
                raise HTTPBadRequest(_("You're not an admin for this group"))
            # -----------------------------------------------------------------
            # Fetch tasks to be deleted.
            # -----------------------------------------------------------------
            dbsession = req.dbsession
            # Tasks first:
            idnum_ref = IdNumReference(
                which_idnum=which_idnum, idnum_value=idnum_value
            )
            taskfilter = TaskFilter()
            taskfilter.idnum_criteria = [idnum_ref]
            taskfilter.group_ids = [group_id]
            collection = TaskCollection(
                req=req,
                taskfilter=taskfilter,
                sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
                current_only=False,  # unusual option!
            )
            tasks = collection.all_tasks
            n_tasks = len(tasks)
            patient_lineage_instances = Patient.get_patients_by_idnum(
                dbsession=dbsession,
                which_idnum=which_idnum,
                idnum_value=idnum_value,
                group_id=group_id,
                current_only=False,
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
                        head_form_html=get_head_form_html(req, [form]),
                    ),
                    request=req,
                )

            # -----------------------------------------------------------------
            # Delete patient and associated tasks
            # -----------------------------------------------------------------
            for task in tasks:
                TaskIndexEntry.unindex_task(task, req.dbsession)
                task.delete_entirely(req)
            # Then patients:
            for p in patient_lineage_instances:
                PatientIdNumIndexEntry.unindex_patient(p, req.dbsession)
                p.delete_with_dependants(req)
            msg = (
                f"{_('Patient and associated tasks DELETED from group')} "
                f"{group_id}: idnum{which_idnum} = {idnum_value}. "
                f"{_('Task records deleted:')} {n_tasks}."
                f"{_('Patient records (current and/or old) deleted')} "
                f"{n_patient_instances}."
            )
            audit(req, msg)

            req.session.flash(msg, FlashQueue.SUCCESS)
            raise HTTPFound(req.route_url(Routes.HOME))

        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        form = first_form
        rendered_form = first_form.render()
    return render_to_response(
        "patient_delete_choose.mako",
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


@view_config(
    route_name=Routes.FORCIBLY_FINALIZE,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def forcibly_finalize(req: "CamcopsRequest") -> Response:
    """
    View to force-finalize all live (``_era == ERA_NOW``) records from a
    device. Available to group administrators if all those records are within
    their groups (otherwise, it's a superuser operation).
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
    _ = req.gettext
    if form is not None:
        try:
            controls = list(req.POST.items())
            appstruct = form.validate(controls)
            # log.debug("{}", pformat(appstruct))
            device_id = appstruct.get(ViewParam.DEVICE_ID)
            device = Device.get_device_by_id(dbsession, device_id)
            if device is None:
                raise HTTPBadRequest(f"{_('No such device:')} {device_id!r}")
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
                    current_only=False,  # unusual option!
                    via_index=False,  # required for current_only=False
                )
                tasks = collection.all_tasks
                return render_to_response(
                    "device_forcibly_finalize_confirm.mako",
                    dict(
                        form=rendered_form,
                        tasks=tasks,
                        head_form_html=get_head_form_html(req, [form]),
                    ),
                    request=req,
                )
            # -----------------------------------------------------------------
            # Check it's permitted
            # -----------------------------------------------------------------
            if not req.user.superuser:
                admin_group_ids = req.user.ids_of_groups_user_is_admin_for
                for clienttable in CLIENT_TABLE_MAP.values():
                    # noinspection PyPropertyAccess
                    count_query = (
                        select([func.count()])
                        .select_from(clienttable)
                        .where(clienttable.c[FN_DEVICE_ID] == device_id)
                        .where(clienttable.c[FN_ERA] == ERA_NOW)
                        .where(
                            clienttable.c[FN_GROUP_ID].notin_(admin_group_ids)
                        )
                    )
                    n = dbsession.execute(count_query).scalar()
                    if n > 0:
                        raise HTTPBadRequest(
                            _(
                                "Some records for this device are in groups "
                                "for which you are not an administrator"
                            )
                        )
            # -----------------------------------------------------------------
            # Forcibly finalize
            # -----------------------------------------------------------------
            msgs = []  # type: List[str]
            batchdetails = BatchDetails(batchtime=req.now_utc)
            alltables = sorted(
                CLIENT_TABLE_MAP.values(), key=upload_commit_order_sorter
            )
            for clienttable in alltables:
                liverecs = get_server_live_records(
                    req, device_id, clienttable, current_only=False
                )
                preservation_pks = [r.server_pk for r in liverecs]
                if not preservation_pks:
                    continue
                current_pks = [r.server_pk for r in liverecs if r.current]
                tablechanges = UploadTableChanges(clienttable)
                tablechanges.note_preservation_pks(preservation_pks)
                tablechanges.note_current_pks(current_pks)
                dbsession.execute(
                    update(clienttable)
                    .where(clienttable.c[FN_PK].in_(preservation_pks))
                    .values(
                        values_preserve_now(
                            req, batchdetails, forcibly_preserved=True
                        )
                    )
                )
                update_indexes_and_push_exports(
                    req, batchdetails, tablechanges
                )
                msgs.append(f"{clienttable.name} {preservation_pks}")
            # Field names are different in server-side tables, so they need
            # special handling:
            SpecialNote.forcibly_preserve_special_notes_for_device(
                req, device_id
            )
            # -----------------------------------------------------------------
            # Done
            # -----------------------------------------------------------------
            msg = (
                f"{_('Live records for device')} {device_id} "
                f"({device.friendly_name}) {_('forcibly finalized')} "
                f"(PKs: {'; '.join(msgs)})"
            )
            audit(req, msg)
            log.info(msg)

            req.session.flash(msg, queue=FlashQueue.SUCCESS)
            raise HTTPFound(req.route_url(Routes.HOME))

        except ValidationFailure as e:
            rendered_form = e.render()
    else:
        form = first_form
        rendered_form = form.render()  # no appstruct
    return render_to_response(
        "device_forcibly_finalize_choose.mako",
        dict(
            form=rendered_form, head_form_html=get_head_form_html(req, [form])
        ),
        request=req,
    )


# =============================================================================
# Patient creation/editing (primarily for task scheduling)
# =============================================================================


class PatientMixin(object):
    """
    Mixin for views involving a patient.
    """

    object: Any
    object_class = Patient
    server_pk_name = "_pk"

    model_form_dict = {
        "forename": ViewParam.FORENAME,
        "surname": ViewParam.SURNAME,
        "dob": ViewParam.DOB,
        "sex": ViewParam.SEX,
        "email": ViewParam.EMAIL,
        "address": ViewParam.ADDRESS,
        "gp": ViewParam.GP,
        "other": ViewParam.OTHER,
    }

    def get_form_values(self) -> Dict:
        # will populate with model_form_dict
        # noinspection PyUnresolvedReferences
        form_values = super().get_form_values()

        patient = cast(Patient, self.object)

        if patient is not None:
            form_values[ViewParam.SERVER_PK] = patient.pk
            form_values[ViewParam.GROUP_ID] = patient.group.id
            form_values[ViewParam.ID_REFERENCES] = [
                {
                    ViewParam.WHICH_IDNUM: pidnum.which_idnum,
                    ViewParam.IDNUM_VALUE: pidnum.idnum_value,
                }
                for pidnum in patient.idnums
            ]
            ts_list = []  # type: List[Dict]
            for pts in patient.task_schedules:
                ts_dict = {
                    ViewParam.PATIENT_TASK_SCHEDULE_ID: pts.id,
                    ViewParam.SCHEDULE_ID: pts.schedule_id,
                    ViewParam.START_DATETIME: pts.start_datetime,
                }
                if DEFORM_ACCORDION_BUG:
                    ts_dict[ViewParam.SETTINGS] = pts.settings
                else:
                    ts_dict[ViewParam.ADVANCED] = {
                        ViewParam.SETTINGS: pts.settings
                    }
                ts_list.append(ts_dict)
            form_values[ViewParam.TASK_SCHEDULES] = ts_list

        return form_values


class EditPatientBaseView(PatientMixin, UpdateView):
    """
    View to edit details for a patient.
    """

    pk_param = ViewParam.SERVER_PK

    def get_object(self) -> Any:
        patient = cast(Patient, super().get_object())

        _ = self.request.gettext

        if not patient.group:
            raise HTTPBadRequest(_("Bad patient: not in a group"))

        if not patient.user_may_edit(self.request):
            raise HTTPBadRequest(_("Not authorized to edit this patient"))

        return patient

    def save_object(self, appstruct: Dict[str, Any]) -> None:
        # -----------------------------------------------------------------
        # Apply edits
        # -----------------------------------------------------------------
        # Calculate the changes, and apply them to the Patient object
        _ = self.request.gettext

        patient = cast(Patient, self.object)

        changes = OrderedDict()  # type: OrderedDict

        self.save_changes(appstruct, changes)

        if not changes:
            self.request.session.flash(
                f"{_('No changes required for patient record with server PK')} "  # noqa
                f"{patient.pk} {_('(all new values matched old values)')}",
                queue=FlashQueue.INFO,
            )
            return

        formatted_changes = []

        for k, details in changes.items():
            if len(details) == 1:
                change = f"{k}: {details[0]}"  # usually a plain message
            else:
                change = f"{k}: {details[0]!r} → {details[1]!r}"

            formatted_changes.append(change)

        # Below here, changes have definitely been made.
        change_msg = (
            _("Patient details edited. Changes:")
            + " "
            + "; ".join(formatted_changes)
        )

        # Apply special note to patient
        patient.apply_special_note(self.request, change_msg, "Patient edited")

        # Patient details changed, so resend any tasks via HL7
        for task in self.get_affected_tasks():
            task.cancel_from_export_log(self.request)

        # Done
        self.request.session.flash(
            f"{_('Amended patient record with server PK')} "
            f"{patient.pk}. "
            f"{_('Changes were:')} {change_msg}",
            queue=FlashQueue.SUCCESS,
        )

    def save_changes(
        self, appstruct: Dict[str, Any], changes: OrderedDict
    ) -> None:
        self._save_simple_params(appstruct, changes)
        self._save_idrefs(appstruct, changes)

    def _save_simple_params(
        self, appstruct: Dict[str, Any], changes: OrderedDict
    ) -> None:
        patient = cast(Patient, self.object)
        for k in EDIT_PATIENT_SIMPLE_PARAMS:
            new_value = appstruct.get(k)
            old_value = getattr(patient, k)
            if new_value == old_value:
                continue
            if new_value in (None, "") and old_value in (None, ""):
                # Nothing really changing!
                continue
            changes[k] = (old_value, new_value)
            setattr(patient, k, new_value)

    def _save_idrefs(
        self, appstruct: Dict[str, Any], changes: OrderedDict
    ) -> None:

        # The ID numbers are more complex.
        # log.debug("{}", pformat(appstruct))
        patient = cast(Patient, self.object)
        new_idrefs = [
            IdNumReference(
                which_idnum=idrefdict[ViewParam.WHICH_IDNUM],
                idnum_value=idrefdict[ViewParam.IDNUM_VALUE],
            )
            for idrefdict in appstruct.get(ViewParam.ID_REFERENCES, {})
        ]
        for idnum in patient.idnums:
            matching_idref = next(
                (
                    idref
                    for idref in new_idrefs
                    if idref.which_idnum == idnum.which_idnum
                ),
                None,
            )
            if not matching_idref:
                # Delete ID numbers not present in the new set
                changes[
                    "idnum{} ({})".format(
                        idnum.which_idnum,
                        self.request.get_id_desc(idnum.which_idnum),
                    )
                ] = (idnum.idnum_value, None)
                idnum.mark_as_deleted(self.request)
            elif matching_idref.idnum_value != idnum.idnum_value:
                # Modify altered ID numbers present in the old + new sets
                changes[
                    "idnum{} ({})".format(
                        idnum.which_idnum,
                        self.request.get_id_desc(idnum.which_idnum),
                    )
                ] = (idnum.idnum_value, matching_idref.idnum_value)
                new_idnum = PatientIdNum()
                new_idnum.id = idnum.id
                new_idnum.patient_id = idnum.patient_id
                new_idnum.which_idnum = idnum.which_idnum
                new_idnum.idnum_value = matching_idref.idnum_value
                new_idnum.set_predecessor(self.request, idnum)

        for idref in new_idrefs:
            matching_idnum = next(
                (
                    idnum
                    for idnum in patient.idnums
                    if idnum.which_idnum == idref.which_idnum
                ),
                None,
            )
            if not matching_idnum:
                # Create ID numbers where they were absent
                changes[
                    "idnum{} ({})".format(
                        idref.which_idnum,
                        self.request.get_id_desc(idref.which_idnum),
                    )
                ] = (None, idref.idnum_value)
                # We need to establish an "id" field, which is the PK as
                # seen by the tablet. The tablet has lost interest in these
                # records, since _era != ERA_NOW, so all we have to do is
                # pick a number that's not in use.
                new_idnum = PatientIdNum()
                new_idnum.patient_id = patient.id
                new_idnum.which_idnum = idref.which_idnum
                new_idnum.idnum_value = idref.idnum_value
                new_idnum.create_fresh(
                    self.request,
                    device_id=patient.device_id,
                    era=patient.era,
                    group_id=patient.group_id,
                )
                new_idnum.save_with_next_available_id(
                    self.request, patient.device_id, era=patient.era
                )

    def get_context_data(self, **kwargs: Any) -> Any:
        # This parameter is (I think) used by Mako templates such as
        # finalized_patient_edit.mako
        # Todo:
        #   Potential inefficiency: we fetch tasks regardless of the stage
        #   of this form.
        kwargs["tasks"] = self.get_affected_tasks()

        return super().get_context_data(**kwargs)

    def get_affected_tasks(self) -> Optional[List[Task]]:
        patient = cast(Patient, self.object)

        taskfilter = TaskFilter()
        taskfilter.device_ids = [patient.device_id]
        taskfilter.group_ids = [patient.group.id]
        taskfilter.era = patient.era
        collection = TaskCollection(
            req=self.request,
            taskfilter=taskfilter,
            sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
            current_only=False,  # unusual option!
            via_index=False,  # for current_only=False, or we'll get a warning
        )
        return collection.all_tasks


class EditServerCreatedPatientView(EditPatientBaseView):
    """
    View to edit a patient created on the server (as part of task scheduling).
    """

    template_name = "server_created_patient_edit.mako"
    form_class = EditServerCreatedPatientForm

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_PATIENT_TASK_SCHEDULES)

    def get_object(self) -> Any:
        patient = cast(Patient, super().get_object())

        if not patient.created_on_server(self.request):
            _ = self.request.gettext

            raise HTTPBadRequest(
                _("Patient is not editable - was not created on the server")
            )

        return patient

    def save_changes(
        self, appstruct: Dict[str, Any], changes: OrderedDict
    ) -> None:
        self._save_group(appstruct, changes)
        super().save_changes(appstruct, changes)
        self._save_task_schedules(appstruct, changes)

    def _save_group(
        self, appstruct: Dict[str, Any], changes: OrderedDict
    ) -> None:
        patient = cast(Patient, self.object)

        old_group_id = patient.group.id
        old_group_name = patient.group.name
        new_group_id = appstruct.get(ViewParam.GROUP_ID, None)
        new_group = (
            self.request.dbsession.query(Group)
            .filter(Group.id == new_group_id)
            .first()
        )

        if old_group_id != new_group_id:
            patient._group_id = new_group_id
            changes["group"] = (old_group_name, new_group.name)

    def _save_task_schedules(
        self, appstruct: Dict[str, Any], changes: OrderedDict
    ) -> None:

        _ = self.request.gettext
        patient = cast(Patient, self.object)
        ids_to_delete = [pts.id for pts in patient.task_schedules]

        anything_changed = False

        for schedule_dict in appstruct.get(ViewParam.TASK_SCHEDULES, {}):
            pts_id = schedule_dict[ViewParam.PATIENT_TASK_SCHEDULE_ID]
            schedule_id = schedule_dict[ViewParam.SCHEDULE_ID]
            start_datetime = schedule_dict[ViewParam.START_DATETIME]
            if DEFORM_ACCORDION_BUG:
                settings = schedule_dict[ViewParam.SETTINGS]
            else:
                settings = schedule_dict[ViewParam.ADVANCED][
                    ViewParam.SETTINGS
                ]  # noqa

            if pts_id is None:
                pts = PatientTaskSchedule()
                pts.patient_pk = patient.pk
                pts.schedule_id = schedule_id
                pts.start_datetime = start_datetime
                pts.settings = settings

                self.request.dbsession.add(pts)
                anything_changed = True
            else:
                old_pts = (
                    self.request.dbsession.query(PatientTaskSchedule)
                    .filter(PatientTaskSchedule.id == pts_id)
                    .first()
                )

                updates = {}
                if old_pts.start_datetime != start_datetime:
                    updates[
                        PatientTaskSchedule.start_datetime
                    ] = start_datetime

                if old_pts.schedule_id != schedule_id:
                    updates[PatientTaskSchedule.schedule_id] = schedule_id

                if old_pts.settings != settings:
                    updates[PatientTaskSchedule.settings] = settings

                if updates:
                    anything_changed = True
                    self.request.dbsession.query(PatientTaskSchedule).filter(
                        PatientTaskSchedule.id == pts_id
                    ).update(updates, synchronize_session="fetch")

                ids_to_delete.remove(pts_id)

        pts_to_delete = self.request.dbsession.query(
            PatientTaskSchedule
        ).filter(PatientTaskSchedule.id.in_(ids_to_delete))

        # Previously we had:
        # pts_to_delete.delete(synchronize_session="fetch")
        #
        # This won't cascade the deletion because we are calling delete() on
        # the query object. We could set up cascade at the database level
        # instead but there is little performance gain here.
        # https://stackoverflow.com/questions/19243964/sqlalchemy-delete-doesnt-cascade

        for pts in pts_to_delete:
            self.request.dbsession.delete(pts)
            anything_changed = True

        if anything_changed:
            changes[_("Task schedules")] = (_("Updated"),)


class EditFinalizedPatientView(EditPatientBaseView):
    """
    View to edit a finalized patient.
    """

    template_name = "finalized_patient_edit.mako"
    form_class = EditFinalizedPatientForm

    def __init__(
        self,
        req: CamcopsRequest,
        task_tablename: str = None,
        task_server_pk: int = None,
    ) -> None:
        """
        The two additional parameters are for returning the user to the task
        from which editing was initiated.
        """
        super().__init__(req)
        self.task_tablename = task_tablename
        self.task_server_pk = task_server_pk

    def get_success_url(self) -> str:
        """
        We got here by editing a patient from an uploaded task, so that's our
        return point.
        """
        if self.task_tablename and self.task_server_pk:
            return self.request.route_url(
                Routes.TASK,
                _query={
                    ViewParam.TABLE_NAME: self.task_tablename,
                    ViewParam.SERVER_PK: self.task_server_pk,
                    ViewParam.VIEWTYPE: ViewArg.HTML,
                },
            )
        else:
            # Likely in a testing environment!
            return self.request.route_url(Routes.HOME)

    def get_object(self) -> Any:
        patient = cast(Patient, super().get_object())

        if not patient.is_finalized():
            _ = self.request.gettext

            raise HTTPBadRequest(
                _(
                    "Patient is not editable (likely: not finalized, so a "
                    "copy still on a client device)"
                )
            )

        return patient


@view_config(
    route_name=Routes.EDIT_FINALIZED_PATIENT,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def edit_finalized_patient(req: "CamcopsRequest") -> Response:
    """
    View to edit details for a patient.
    """
    task_table_name = req.get_str_param(
        ViewParam.BACK_TASK_TABLENAME, validator=validate_task_tablename
    )
    task_server_pk = req.get_int_param(ViewParam.BACK_TASK_SERVER_PK, None)

    return EditFinalizedPatientView(
        req, task_tablename=task_table_name, task_server_pk=task_server_pk
    ).dispatch()


@view_config(
    route_name=Routes.EDIT_SERVER_CREATED_PATIENT, http_cache=NEVER_CACHE
)
def edit_server_created_patient(req: "CamcopsRequest") -> Response:
    """
    View to edit details for a patient created on the server (for scheduling
    tasks).
    """
    return EditServerCreatedPatientView(req).dispatch()


class AddPatientView(PatientMixin, CreateView):
    """
    View to add a patient (for task scheduling).
    """

    form_class = EditServerCreatedPatientForm
    template_name = "patient_add.mako"

    def dispatch(self) -> Response:
        if not self.request.user.authorized_to_manage_patients:
            _ = self.request.gettext
            raise HTTPBadRequest(_("Not authorized to manage patients"))

        return super().dispatch()

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_PATIENT_TASK_SCHEDULES)

    def save_object(self, appstruct: Dict[str, Any]) -> None:
        server_device = Device.get_server_device(self.request.dbsession)

        patient = Patient()
        patient.create_fresh(
            self.request,
            device_id=server_device.id,
            era=ERA_NOW,
            group_id=appstruct.get(ViewParam.GROUP_ID),
        )

        for k in EDIT_PATIENT_SIMPLE_PARAMS:
            new_value = appstruct.get(k)
            setattr(patient, k, new_value)

        patient.save_with_next_available_id(self.request, server_device.id)

        new_idrefs = [
            IdNumReference(
                which_idnum=idrefdict[ViewParam.WHICH_IDNUM],
                idnum_value=idrefdict[ViewParam.IDNUM_VALUE],
            )
            for idrefdict in appstruct.get(ViewParam.ID_REFERENCES)
        ]

        for idref in new_idrefs:
            new_idnum = PatientIdNum()
            new_idnum.patient_id = patient.id
            new_idnum.which_idnum = idref.which_idnum
            new_idnum.idnum_value = idref.idnum_value
            new_idnum.create_fresh(
                self.request,
                device_id=server_device.id,
                era=ERA_NOW,
                group_id=appstruct.get(ViewParam.GROUP_ID),
            )

            new_idnum.save_with_next_available_id(
                self.request, server_device.id
            )

        task_schedules = appstruct.get(ViewParam.TASK_SCHEDULES)

        self.request.dbsession.commit()

        for task_schedule in task_schedules:
            schedule_id = task_schedule[ViewParam.SCHEDULE_ID]
            start_datetime = task_schedule[ViewParam.START_DATETIME]
            if DEFORM_ACCORDION_BUG:
                settings = task_schedule[ViewParam.SETTINGS]
            else:
                settings = task_schedule[ViewParam.ADVANCED][
                    ViewParam.SETTINGS
                ]  # noqa
            patient_task_schedule = PatientTaskSchedule()
            patient_task_schedule.patient_pk = patient.pk
            patient_task_schedule.schedule_id = schedule_id
            patient_task_schedule.start_datetime = start_datetime
            patient_task_schedule.settings = settings

            self.request.dbsession.add(patient_task_schedule)

        self.object = patient


@view_config(route_name=Routes.ADD_PATIENT, http_cache=NEVER_CACHE)
def add_patient(req: "CamcopsRequest") -> Response:
    """
    View to add a patient.
    """
    return AddPatientView(req).dispatch()


class DeleteServerCreatedPatientView(DeleteView):
    """
    View to delete a patient that had been created on the server.
    """

    form_class = DeleteServerCreatedPatientForm
    object_class = Patient
    pk_param = ViewParam.SERVER_PK
    server_pk_name = "_pk"
    template_name = TEMPLATE_GENERIC_FORM

    def get_object(self) -> Any:
        patient = cast(Patient, super().get_object())
        if not patient.user_may_edit(self.request):
            _ = self.request.gettext
            raise HTTPBadRequest(_("Not authorized to delete this patient"))
        return patient

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext
        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.DELETE, text=_("Delete patient")
            )
        }

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_PATIENT_TASK_SCHEDULES)

    def delete(self) -> None:
        patient = cast(Patient, self.object)

        PatientIdNumIndexEntry.unindex_patient(patient, self.request.dbsession)

        patient.delete_with_dependants(self.request)


@view_config(
    route_name=Routes.DELETE_SERVER_CREATED_PATIENT, http_cache=NEVER_CACHE
)
def delete_server_created_patient(req: "CamcopsRequest") -> Response:
    """
    Page to delete a patient created on the server (as part of task
    scheduling).
    """
    return DeleteServerCreatedPatientView(req).dispatch()


# =============================================================================
# Task scheduling
# =============================================================================


@view_config(
    route_name=Routes.VIEW_TASK_SCHEDULES,
    permission=Permission.GROUPADMIN,
    renderer="view_task_schedules.mako",
    http_cache=NEVER_CACHE,
)
def view_task_schedules(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View whole task schedules.
    """
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    group_ids = req.user.ids_of_groups_user_is_admin_for
    q = (
        req.dbsession.query(TaskSchedule)
        .join(TaskSchedule.group)
        .filter(TaskSchedule.group_id.in_(group_ids))
        .order_by(Group.name, TaskSchedule.name)
    )
    page = SqlalchemyOrmPage(
        query=q,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )
    return dict(page=page)


@view_config(
    route_name=Routes.VIEW_TASK_SCHEDULE_ITEMS,
    permission=Permission.GROUPADMIN,
    renderer="view_task_schedule_items.mako",
    http_cache=NEVER_CACHE,
)
def view_task_schedule_items(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View items within a task schedule.
    """
    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    schedule_id = req.get_int_param(ViewParam.SCHEDULE_ID)

    schedule = (
        req.dbsession.query(TaskSchedule)
        .filter(TaskSchedule.id == schedule_id)
        .one_or_none()
    )

    if schedule is None:
        _ = req.gettext
        raise HTTPBadRequest(_("Schedule does not exist"))

    q = (
        req.dbsession.query(TaskScheduleItem)
        .filter(TaskScheduleItem.schedule_id == schedule_id)
        .order_by(*task_schedule_item_sort_order())
    )
    page = SqlalchemyOrmPage(
        query=q,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )
    return dict(page=page, schedule_name=schedule.name)


@view_config(
    route_name=Routes.VIEW_PATIENT_TASK_SCHEDULES,
    renderer="view_patient_task_schedules.mako",
    http_cache=NEVER_CACHE,
)
def view_patient_task_schedules(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View all patients and their assigned schedules (as well as their access
    keys, etc.).
    """
    server_device = Device.get_server_device(req.dbsession)

    rows_per_page = req.get_int_param(
        ViewParam.ROWS_PER_PAGE, DEFAULT_ROWS_PER_PAGE
    )
    page_num = req.get_int_param(ViewParam.PAGE, 1)
    allowed_group_ids = req.user.ids_of_groups_user_may_manage_patients_in
    # noinspection PyProtectedMember
    q = (
        req.dbsession.query(Patient)
        .filter(Patient._era == ERA_NOW)
        .filter(Patient._group_id.in_(allowed_group_ids))
        .filter(Patient._device_id == server_device.id)
        .order_by(Patient.surname, Patient.forename)
        .options(joinedload("task_schedules"))
        .options(joinedload("idnums"))
    )

    page = SqlalchemyOrmPage(
        query=q,
        page=page_num,
        items_per_page=rows_per_page,
        url_maker=PageUrl(req),
        request=req,
    )
    return dict(page=page)


@view_config(
    route_name=Routes.VIEW_PATIENT_TASK_SCHEDULE,
    renderer="view_patient_task_schedule.mako",
    http_cache=NEVER_CACHE,
)
def view_patient_task_schedule(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View scheduled tasks for one patient's specific task schedule.
    """
    pts_id = req.get_int_param(ViewParam.PATIENT_TASK_SCHEDULE_ID)

    pts = (
        req.dbsession.query(PatientTaskSchedule)
        .filter(PatientTaskSchedule.id == pts_id)
        .options(
            joinedload("patient.idnums"), joinedload("task_schedule.items")
        )
        .one_or_none()
    )

    _ = req.gettext
    if pts is None:
        raise HTTPBadRequest(_("Patient's task schedule does not exist"))

    if not pts.patient.user_may_edit(req):
        raise HTTPBadRequest(_("Not authorized to manage this patient"))

    patient_descriptor = pts.patient.prettystr(req)

    return dict(
        pts=pts,
        patient_descriptor=patient_descriptor,
        schedule_name=pts.task_schedule.name,
        task_list=pts.get_list_of_scheduled_tasks(req),
    )


class TaskScheduleMixin(object):
    """
    Mixin for viewing/editing a task schedule.
    """

    form_class = EditTaskScheduleForm
    model_form_dict = {
        "name": ViewParam.NAME,
        "group_id": ViewParam.GROUP_ID,
        "email_bcc": ViewParam.EMAIL_BCC,
        "email_cc": ViewParam.EMAIL_CC,
        "email_from": ViewParam.EMAIL_FROM,
        "email_subject": ViewParam.EMAIL_SUBJECT,
        "email_template": ViewParam.EMAIL_TEMPLATE,
    }
    object_class = TaskSchedule
    request: "CamcopsRequest"
    server_pk_name = "id"
    template_name = TEMPLATE_GENERIC_FORM

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_TASK_SCHEDULES)

    def get_object(self) -> Any:
        # noinspection PyUnresolvedReferences
        schedule = cast(TaskSchedule, super().get_object())

        if not schedule.user_may_edit(self.request):
            _ = self.request.gettext
            raise HTTPBadRequest(
                _(
                    "You a not a group administrator for this "
                    "task schedule's group"
                )
            )

        return schedule


class AddTaskScheduleView(TaskScheduleMixin, CreateView):
    """
    Django-style view class to add a task schedule.
    """

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext
        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.TASK_SCHEDULE_ADD, text=_("Add a task schedule")
            )
        }


class EditTaskScheduleView(TaskScheduleMixin, UpdateView):
    """
    Django-style view class to edit a task schedule.
    """

    pk_param = ViewParam.SCHEDULE_ID

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext
        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.TASK_SCHEDULE,
                text=_("Edit details for a task schedule"),
            )
        }


class DeleteTaskScheduleView(TaskScheduleMixin, DeleteView):
    """
    Django-style view class to delete a task schedule.
    """

    form_class = DeleteTaskScheduleForm
    pk_param = ViewParam.SCHEDULE_ID

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext
        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.DELETE, text=_("Delete a task schedule")
            )
        }


@view_config(
    route_name=Routes.ADD_TASK_SCHEDULE,
    permission=Permission.GROUPADMIN,
    http_cache=NEVER_CACHE,
)
def add_task_schedule(req: "CamcopsRequest") -> Response:
    """
    View to add a task schedule.
    """
    return AddTaskScheduleView(req).dispatch()


@view_config(
    route_name=Routes.EDIT_TASK_SCHEDULE, permission=Permission.GROUPADMIN
)
def edit_task_schedule(req: "CamcopsRequest") -> Response:
    """
    View to edit a task schedule.
    """
    return EditTaskScheduleView(req).dispatch()


@view_config(
    route_name=Routes.DELETE_TASK_SCHEDULE, permission=Permission.GROUPADMIN
)
def delete_task_schedule(req: "CamcopsRequest") -> Response:
    """
    View to delete a task schedule.
    """
    return DeleteTaskScheduleView(req).dispatch()


class TaskScheduleItemMixin(object):
    """
    Mixin for viewing/editing a task schedule items.
    """

    form_class = EditTaskScheduleItemForm
    template_name = TEMPLATE_GENERIC_FORM
    model_form_dict = {
        "schedule_id": ViewParam.SCHEDULE_ID,
        "task_table_name": ViewParam.TABLE_NAME,
        "due_from": ViewParam.DUE_FROM,
        # we need to convert due_within to due_by
    }
    object: Any
    # noinspection PyTypeChecker
    object_class = cast(Type["Base"], TaskScheduleItem)
    pk_param = ViewParam.SCHEDULE_ITEM_ID
    request: "CamcopsRequest"
    server_pk_name = "id"

    def get_success_url(self) -> str:
        # noinspection PyUnresolvedReferences
        return self.request.route_url(
            Routes.VIEW_TASK_SCHEDULE_ITEMS,
            _query={ViewParam.SCHEDULE_ID: self.get_schedule_id()},
        )


class EditTaskScheduleItemMixin(TaskScheduleItemMixin):
    """
    Django-style view class to edit a task schedule item.
    """

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        # noinspection PyUnresolvedReferences
        super().set_object_properties(appstruct)

        due_from = appstruct.get(ViewParam.DUE_FROM)
        due_within = appstruct.get(ViewParam.DUE_WITHIN)

        setattr(self.object, "due_by", due_from + due_within)

    def get_schedule(self) -> TaskSchedule:
        # noinspection PyUnresolvedReferences
        schedule_id = self.get_schedule_id()

        schedule = (
            self.request.dbsession.query(TaskSchedule)
            .filter(TaskSchedule.id == schedule_id)
            .one_or_none()
        )

        if schedule is None:
            _ = self.request.gettext
            raise HTTPBadRequest(
                f"{_('Missing Task Schedule for id')} {schedule_id}"
            )

        if not schedule.user_may_edit(self.request):
            _ = self.request.gettext
            raise HTTPBadRequest(
                _(
                    "You a not a group administrator for this "
                    "task schedule's group"
                )
            )

        return schedule


class AddTaskScheduleItemView(EditTaskScheduleItemMixin, CreateView):
    """
    Django-style view class to add a task schedule item.
    """

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext

        schedule = self.get_schedule()

        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.TASK_SCHEDULE_ITEM_ADD,
                text=_("Add an item to the {schedule_name} schedule").format(
                    schedule_name=schedule.name
                ),
            )
        }

    def get_schedule_id(self) -> int:
        return self.request.get_int_param(ViewParam.SCHEDULE_ID)

    def get_form_values(self) -> Dict:
        schedule = self.get_schedule()

        form_values = super().get_form_values()
        form_values[ViewParam.SCHEDULE_ID] = schedule.id

        return form_values


class EditTaskScheduleItemView(EditTaskScheduleItemMixin, UpdateView):
    """
    Django-style view class to edit a task schedule item.
    """

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext
        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.EDIT,
                text=_("Edit details for a task schedule item"),
            )
        }

    def get_schedule_id(self) -> int:
        item = cast(TaskScheduleItem, self.object)

        return item.schedule_id

    def get_form_values(self) -> Dict:
        schedule = self.get_schedule()

        form_values = super().get_form_values()
        form_values[ViewParam.SCHEDULE_ID] = schedule.id

        item = cast(TaskScheduleItem, self.object)
        due_within = item.due_by - form_values[ViewParam.DUE_FROM]
        form_values[ViewParam.DUE_WITHIN] = due_within

        return form_values


class DeleteTaskScheduleItemView(TaskScheduleItemMixin, DeleteView):
    """
    Django-style view class to delete a task schedule item.
    """

    form_class = DeleteTaskScheduleItemForm

    def get_extra_context(self) -> Dict[str, Any]:
        _ = self.request.gettext
        return {
            MAKO_VAR_TITLE: self.request.icon_text(
                icon=Icons.DELETE, text=_("Delete a task schedule item")
            )
        }

    def get_schedule_id(self) -> int:
        item = cast(TaskScheduleItem, self.object)

        return item.schedule_id


@view_config(
    route_name=Routes.ADD_TASK_SCHEDULE_ITEM, permission=Permission.GROUPADMIN
)
def add_task_schedule_item(req: "CamcopsRequest") -> Response:
    """
    View to add a task schedule item.
    """
    return AddTaskScheduleItemView(req).dispatch()


@view_config(
    route_name=Routes.EDIT_TASK_SCHEDULE_ITEM, permission=Permission.GROUPADMIN
)
def edit_task_schedule_item(req: "CamcopsRequest") -> Response:
    """
    View to edit a task schedule item.
    """
    return EditTaskScheduleItemView(req).dispatch()


@view_config(
    route_name=Routes.DELETE_TASK_SCHEDULE_ITEM,
    permission=Permission.GROUPADMIN,
)
def delete_task_schedule_item(req: "CamcopsRequest") -> Response:
    """
    View to delete a task schedule item.
    """
    return DeleteTaskScheduleItemView(req).dispatch()


@view_config(
    route_name=Routes.CLIENT_API,
    request_method=HttpMethod.GET,
    permission=NO_PERMISSION_REQUIRED,
    renderer="client_api_signposting.mako",
)
@view_config(
    route_name=Routes.CLIENT_API_ALIAS,
    request_method=HttpMethod.GET,
    permission=NO_PERMISSION_REQUIRED,
    renderer="client_api_signposting.mako",
)
def client_api_signposting(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Patients are likely to enter the ``/api`` address into a web browser,
    especially if it appears as a hyperlink in an email. If so, that will
    arrive as a ``GET`` request. This page will direct them to download the
    app.
    """
    return {
        "github_link": req.icon_text(
            icon=Icons.GITHUB, url=GITHUB_RELEASES_URL, text="GitHub"
        ),
        "server_url": req.route_url(Routes.CLIENT_API),
    }


class SendPatientEmailBaseView(FormView):
    """
    Send an e-mail to a patient (such as: "please download the app and register
    with this URL/code").
    """

    form_class = SendEmailForm
    template_name = "send_patient_email.mako"

    def __init__(self, *args, **kwargs) -> None:
        self._pts = None

        super().__init__(*args, **kwargs)

    def dispatch(self) -> Response:
        if not self.request.user.authorized_to_email_patients:
            _ = self.request.gettext
            raise HTTPBadRequest(_("Not authorized to email patients"))

        return super().dispatch()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs["pts"] = self._get_patient_task_schedule()

        return super().get_context_data(**kwargs)

    def form_valid(self, form: "Form", appstruct: Dict[str, Any]) -> Response:
        config = self.request.config

        patient_email = appstruct.get(ViewParam.EMAIL)

        kwargs = dict(
            from_addr=appstruct.get(ViewParam.EMAIL_FROM),
            to=patient_email,
            subject=appstruct.get(ViewParam.EMAIL_SUBJECT),
            body=appstruct.get(ViewParam.EMAIL_BODY),
            content_type=MimeType.HTML,
        )

        cc = appstruct.get(ViewParam.EMAIL_CC)
        if cc:
            kwargs["cc"] = cc

        bcc = appstruct.get(ViewParam.EMAIL_BCC)
        if bcc:
            kwargs["bcc"] = bcc

        email = Email(**kwargs)
        ok = email.send(
            host=config.email_host,
            username=config.email_host_username,
            password=config.email_host_password,
            port=config.email_port,
            use_tls=config.email_use_tls,
        )
        if ok:
            self._display_success_message(patient_email)
        else:
            self._display_failure_message(patient_email)

        self.request.dbsession.add(email)
        self.request.dbsession.flush()
        pts_id = self.request.get_int_param(ViewParam.PATIENT_TASK_SCHEDULE_ID)
        if pts_id is None:
            _ = self.request.gettext
            raise HTTPBadRequest(_("Patient task schedule does not exist"))

        pts_email = PatientTaskScheduleEmail()
        pts_email.patient_task_schedule_id = pts_id
        pts_email.email_id = email.id
        self.request.dbsession.add(pts_email)
        self.request.dbsession.commit()

        return super().form_valid(form, appstruct)

    def _display_success_message(self, patient_email: str) -> None:
        _ = self.request.gettext
        message = _("Email sent to {patient_email}").format(
            patient_email=patient_email
        )

        self.request.session.flash(message, queue=FlashQueue.SUCCESS)

    def _display_failure_message(self, patient_email: str) -> None:
        _ = self.request.gettext
        message = _("Failed to send email to {patient_email}").format(
            patient_email=patient_email
        )

        self.request.session.flash(message, queue=FlashQueue.DANGER)

    def get_form_values(self) -> Dict:
        pts = self._get_patient_task_schedule()

        if pts is None:
            _ = self.request.gettext
            raise HTTPBadRequest(_("Patient task schedule does not exist"))

        return {
            ViewParam.EMAIL: pts.patient.email,
            ViewParam.EMAIL_CC: pts.task_schedule.email_cc,
            ViewParam.EMAIL_BCC: pts.task_schedule.email_bcc,
            ViewParam.EMAIL_FROM: pts.task_schedule.email_from,
            ViewParam.EMAIL_SUBJECT: pts.task_schedule.email_subject,
            ViewParam.EMAIL_BODY: pts.email_body(self.request),
        }

    def _get_patient_task_schedule(self) -> Optional[PatientTaskSchedule]:
        if self._pts is not None:
            return self._pts

        pts_id = self.request.get_int_param(ViewParam.PATIENT_TASK_SCHEDULE_ID)

        self._pts = (
            self.request.dbsession.query(PatientTaskSchedule)
            .filter(PatientTaskSchedule.id == pts_id)
            .one_or_none()
        )

        return self._pts


class SendEmailFromPatientListView(SendPatientEmailBaseView):
    """
    Send an e-mail to a patient and return to the patient task schedule list
    view.
    """

    def get_success_url(self) -> str:
        return self.request.route_url(Routes.VIEW_PATIENT_TASK_SCHEDULES)


class SendEmailFromPatientTaskScheduleView(SendPatientEmailBaseView):
    """
    Send an e-mail to a patient and return to the task schedule view for that
    specific patient.
    """

    def get_success_url(self) -> str:
        pts_id = self.request.get_int_param(ViewParam.PATIENT_TASK_SCHEDULE_ID)

        return self.request.route_url(
            Routes.VIEW_PATIENT_TASK_SCHEDULE,
            _query={ViewParam.PATIENT_TASK_SCHEDULE_ID: pts_id},
        )


@view_config(
    route_name=Routes.SEND_EMAIL_FROM_PATIENT_TASK_SCHEDULE,
    http_cache=NEVER_CACHE,
)
def send_email_from_patient_task_schedule(req: "CamcopsRequest") -> Response:
    """
    View to send an email to a patient from their task schedule page.
    """
    return SendEmailFromPatientTaskScheduleView(req).dispatch()


@view_config(
    route_name=Routes.SEND_EMAIL_FROM_PATIENT_LIST, http_cache=NEVER_CACHE
)
def send_email_from_patient_list(req: "CamcopsRequest") -> Response:
    """
    View to send an email to a patient from the list of patients.
    """
    return SendEmailFromPatientListView(req).dispatch()


# =============================================================================
# FHIR identifier "system" information
# =============================================================================


@view_config(
    route_name=Routes.FHIR_PATIENT_ID_SYSTEM,
    request_method=HttpMethod.GET,
    renderer="fhir_patient_id_system.mako",
    http_cache=NEVER_CACHE,
)
def view_fhir_patient_id_system(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Placeholder view for FHIR patient identifier "system" types (from the ID
    that we may have provided to a FHIR server).

    Within each system, the "value" is the actual patient's ID number (not
    part of what we show here).
    """
    which_idnum = int(req.matchdict[ViewParam.WHICH_IDNUM])
    if which_idnum not in req.valid_which_idnums:
        _ = req.gettext
        raise HTTPBadRequest(
            f"{_('Unknown patient ID type:')} " f"{which_idnum!r}"
        )
    return dict(which_idnum=which_idnum)


# noinspection PyUnusedLocal
@view_config(
    route_name=Routes.FHIR_QUESTIONNAIRE_SYSTEM,
    request_method=HttpMethod.GET,
    renderer="all_tasks.mako",
    http_cache=NEVER_CACHE,
)
@view_config(
    route_name=Routes.TASK_LIST,
    request_method=HttpMethod.GET,
    renderer="all_tasks.mako",
    http_cache=NEVER_CACHE,
)
def view_task_list(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    Lists all tasks.

    Also the placeholder view for FHIR Questionnaire "system".
    There's only one system -- the "value" is the task type.
    """
    return dict(all_task_classes=Task.all_subclasses_by_tablename())


@view_config(
    route_name=Routes.TASK_DETAILS,
    request_method=HttpMethod.GET,
    renderer="task_details.mako",
    http_cache=NEVER_CACHE,
)
def view_task_details(req: "CamcopsRequest") -> Dict[str, Any]:
    """
    View details of a specific task type.

    Used also for for FHIR DocumentReference, Observation,and
    QuestionnaireResponse "system" types. (There's one system per task. Within
    each task, the "value" relates to the specific task PK.)
    """
    table_name = req.matchdict[ViewParam.TABLE_NAME]
    task_class_dict = tablename_to_task_class_dict()
    if table_name not in task_class_dict:
        _ = req.gettext
        raise HTTPBadRequest(f"{_('Unknown task:')} {table_name!r}")
    task_class = task_class_dict[table_name]
    task_instance = task_class()

    fhir_aq_items = task_instance.get_fhir_questionnaire(req)
    # ddl = task_instance.get_ddl()
    # ddl_html, ddl_css = format_sql_as_html(ddl)

    return dict(
        task_class=task_class,
        task_instance=task_instance,
        fhir_aq_items=fhir_aq_items,
        # ddl_html=ddl_html,
        # css=ddl_css,
    )


@view_config(
    route_name=Routes.FHIR_CONDITION,
    request_method=HttpMethod.GET,
    http_cache=NEVER_CACHE,
)
@view_config(
    route_name=Routes.FHIR_DOCUMENT_REFERENCE,
    request_method=HttpMethod.GET,
    http_cache=NEVER_CACHE,
)
@view_config(
    route_name=Routes.FHIR_OBSERVATION,
    request_method=HttpMethod.GET,
    http_cache=NEVER_CACHE,
)
@view_config(
    route_name=Routes.FHIR_PRACTITIONER,
    request_method=HttpMethod.GET,
    http_cache=NEVER_CACHE,
)
@view_config(
    route_name=Routes.FHIR_QUESTIONNAIRE_RESPONSE,
    request_method=HttpMethod.GET,
    http_cache=NEVER_CACHE,
)
def fhir_view_task(req: "CamcopsRequest") -> Response:
    """
    Retrieve parameters from a FHIR URL referring back to this server, and
    serve the relevant task (as HTML).

    The "canonical URL" or "business identifier" of a FHIR resource is the
    reference to the master copy -- in this case, our copy. See
    https://www.hl7.org/fhir/datatypes.html#Identifier;
    https://www.hl7.org/fhir/resource.html#identifiers.

    FHIR identifiers have a "system" (which is a URL) and a "value". I don't
    think that FHIR has a rule for combining the system and value to create a
    full URL. For some (but by no means all) identifiers that we provide to
    FHIR servers, the "system" refers to a CamCOPS task (and the value to some
    attribute of that task, like the answer to a question (value of a field),
    or a fixed string like "patient", and so on.
    """
    table_name = req.matchdict[ViewParam.TABLE_NAME]
    server_pk = req.matchdict[ViewParam.SERVER_PK]
    return HTTPFound(
        req.route_url(
            Routes.TASK,
            _query={
                ViewParam.TABLE_NAME: table_name,
                ViewParam.SERVER_PK: server_pk,
                ViewParam.VIEWTYPE: ViewArg.HTML,
            },
        )
    )


@view_config(
    route_name=Routes.FHIR_TABLENAME_PK_ID,
    request_method=HttpMethod.GET,
    http_cache=NEVER_CACHE,
)
def fhir_view_tablename_pk(req: "CamcopsRequest") -> Response:
    """
    Deal with the slightly silly system that just takes a tablename and PK
    directly. Security is key here!
    """
    table_name = req.matchdict[ViewParam.TABLE_NAME]
    server_pk = req.matchdict[ViewParam.SERVER_PK]
    if table_name == Patient.__tablename__:
        return view_patient(req, server_pk)
    return HTTPFound(
        req.route_url(
            Routes.TASK,
            _query={
                ViewParam.TABLE_NAME: table_name,
                ViewParam.SERVER_PK: server_pk,
                ViewParam.VIEWTYPE: ViewArg.HTML,
            },
        )
    )


# =============================================================================
# Static assets
# =============================================================================
# https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#advanced-static  # noqa


def debug_form_rendering() -> None:
    r"""
    Test code for form rendering.

    From the command line:

    .. code-block:: bash

        # Start in the CamCOPS source root directory.
        # - Needs the "-f" option to follow forks.
        # - "open" doesn't show all files opened. To see what you need, try
        #   strace cat /proc/version
        # - ... which shows that "openat" is most useful.

        strace -f --trace=openat \
            python -c 'from camcops_server.cc_modules.webview import debug_form_rendering; debug_form_rendering()' \
            | grep site-packages \
            | grep -v "\.pyc"

    This tells us that the templates are files like:

    .. code-block:: none

        site-packages/deform/templates/form.pt
        site-packages/deform/templates/select.pt
        site-packages/deform/templates/textinput.pt

    On 2020-06-29 we are interested in why a newer (Docker) installation
    renders buggy HTML like:

    .. code-block:: none

        <select name="which_idnum" id="deformField2" class=" form-control " multiple="False">
            <option value="1">CPFT RiO number</option>
            <option value="2">NHS number</option>
            <option value="1000">MyHospital number</option>
        </select>

    ... the bug being that ``multiple="False"`` is wrong; an HTML boolean
    attribute is false when *absent*, not when set to a certain value (see
    https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes#Boolean_Attributes).
    The ``multiple`` attribute of ``<select>`` is a boolean attribute
    (https://developer.mozilla.org/en-US/docs/Web/HTML/Element/select).

    The ``select.pt`` file indicates that this is controlled by
    ``tal:attributes`` syntax. TAL is Template Attribution Language
    (https://sharptal.readthedocs.io/en/latest/tal.html).

    TAL is either provided by Zope (given ZPT files) or Chameleon or both. The
    tracing suggests Chameleon. So the TAL language reference is
    https://chameleon.readthedocs.io/en/latest/reference.html.

    Chameleon changelog is
    https://github.com/malthe/chameleon/blob/master/CHANGES.rst.

    Multiple sources for ``tal:attributes`` syntax say that a null value
    (presumably: ``None``) is required to omit the attribute, not a false
    value.

    """  # noqa

    import sys

    from camcops_server.cc_modules.cc_debug import makefunc_trace_unique_calls
    from camcops_server.cc_modules.cc_forms import ChooseTrackerForm
    from camcops_server.cc_modules.cc_request import get_core_debugging_request

    req = get_core_debugging_request()
    form = ChooseTrackerForm(req, as_ctv=False)

    sys.settrace(makefunc_trace_unique_calls(file_only=True))
    _ = form.render()
    sys.settrace(None)
