#!/usr/bin/env python
# camcops_server/cc_modules/forms.py

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

import logging
from pprint import pformat
from typing import Any, Dict, List
import unittest

from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from colander import (
    Boolean,
    DateTime,
    Integer,
    Invalid,
    Length,
    Schema,
    SchemaNode,
    String,
)
from deform.exception import ValidationFailure
from deform.field import Field
from deform.form import Button, Form
from deform.widget import (
    CheckboxWidget,
    CheckedPasswordWidget,
    HiddenWidget,
    PasswordWidget,
)

from .cc_constants import DEFAULT_ROWS_PER_PAGE
from .cc_pyramid import SUBMIT, ViewParam
from .cc_request import CamcopsRequest, command_line_request
from .cc_user import MINIMUM_PASSWORD_LENGTH

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_CSRF_CHECK = False
DEBUG_FORM_VALIDATION = False

if DEBUG_CSRF_CHECK or DEBUG_FORM_VALIDATION:
    log.warning("Debugging options enabled!")


# =============================================================================
# Widget resources
# =============================================================================

def get_head_form_html(req: CamcopsRequest, forms: List[Form]) -> str:
    """
    Returns the extra HTML that needs to be injected into the <head> section
    for a Deform form to work properly.
    """
    # https://docs.pylonsproject.org/projects/deform/en/latest/widget.html#widget-requirements
    js_resources = []  # type: List[str]
    css_resources = []  # type: List[str]
    for form in forms:
        resources = form.get_widget_resources()  # type: Dict[str, List[str]]
        # Add, ignoring duplicates:
        js_resources.extend(x for x in resources['js']
                            if x not in js_resources)
        css_resources.extend(x for x in resources['css']
                             if x not in css_resources)
    js_links = [req.static_url(r) for r in js_resources]
    css_links = [req.static_url(r) for r in css_resources]
    js_tags = ['<script type="text/javascript" src="%s"></script>' % link
               for link in js_links]
    css_tags = ['<link rel="stylesheet" href="%s"/>' % link
                for link in css_links]
    tags = js_tags + css_tags
    head_html = "\n".join(tags)
    return head_html


# =============================================================================
# Debugging form errors (which can be hidden in their depths)
# =============================================================================
# I'm not alone in the problem of errors from a HiddenWidget:
# https://groups.google.com/forum/?fromgroups#!topic/pylons-discuss/LNHDq6KvNLI
# https://groups.google.com/forum/#!topic/pylons-discuss/Lr1d1VpMycU

class DeformErrorInterface(object):
    def __init__(self, msg: str, *children: "DeformErrorInterface") -> None:
        self._msg = msg
        self.children = children

    def __str__(self) -> str:
        return self._msg


class InformativeForm(Form):
    def validate(self, controls, subcontrol=None) -> Any:
        """Returns a Colander appstruct, or raises."""
        try:
            return super().validate(controls, subcontrol)
        except ValidationFailure as e:
            if DEBUG_FORM_VALIDATION:
                log.critical("Validation failure: {!r}; {}",
                             e, self._get_form_errors())
            self._show_hidden_widgets_for_fields_with_errors(self)
            raise

    def _show_hidden_widgets_for_fields_with_errors(self,
                                                    field: Field) -> None:
        if field.error:
            widget = getattr(field, "widget", None)
            # log.warning(repr(widget))
            # log.warning(repr(widget.hidden))
            if widget is not None and widget.hidden:
                # log.critical("Found hidden widget for field with error!")
                widget.hidden = False
        for child_field in field.children:
            self._show_hidden_widgets_for_fields_with_errors(child_field)

    def _collect_error_errors(self,
                              errorlist: List[str],
                              error: DeformErrorInterface) -> None:
        if error is None:
            return
        errorlist.append(str(error))
        for child_error in error.children:  # typically: subfields
            self._collect_error_errors(errorlist, child_error)

    def _collect_form_errors(self,
                             errorlist: List[str],
                             field: Field,
                             hidden_only: bool = False):
        if hidden_only:
            widget = getattr(field, "widget", None)
            if not isinstance(widget, HiddenWidget):
                return
        # log.critical(repr(field))
        self._collect_error_errors(errorlist, field.error)
        for child_field in field.children:
            self._collect_form_errors(errorlist, child_field,
                                      hidden_only=hidden_only)

    def _get_form_errors(self, hidden_only: bool = False) -> str:
        errorlist = []  # type: List[str]
        self._collect_form_errors(errorlist, self, hidden_only=hidden_only)
        return "; ".join(repr(e) for e in errorlist)


# =============================================================================
# CSRF
# =============================================================================
# As per http://deformdemo.repoze.org/pyramid_csrf_demo/, modified for a more
# recent Colander API.
# NOTE that this makes use of colander.SchemaNode.bind; this CLONES the Schema,
# and resolves any deferred values by means of the keywords passed to bind().
# Since the Schema is created at module load time, but since we're asking the
# Schema to know about the request's CSRF values, this is the only mechanism.
# https://docs.pylonsproject.org/projects/colander/en/latest/api.html#colander.SchemaNode.bind  # noqa


class CSRFToken(SchemaNode):
    """
    From http://deform2000.readthedocs.io/en/latest/basics.html :

    "The default of a schema node indicates the value to be serialized if a
    value for the schema node is not found in the input data during
    serialization. It should be the deserialized representation. If a schema
    node does not have a default, it is considered "serialization required"."

    "The missing of a schema node indicates the value to be deserialized if a
    value for the schema node is not found in the input data during
    deserialization. It should be the deserialized representation. If a schema
    node does not have a missing value, a colander.Invalid exception will be
    raised if the data structure being deserialized does not contain a matching
    value."

    """
    schema_type = String
    default = ""
    missing = ""
    title = "CSRF token"
    widget = HiddenWidget()

    # noinspection PyUnusedLocal
    def after_bind(self, node, kw: Dict[str, Any]) -> None:
        request = kw["request"]  # type: CamcopsRequest
        csrf_token = request.session.get_csrf_token()
        if DEBUG_CSRF_CHECK:
            log.debug("Got CSRF token from session: {!r}", csrf_token)
        self.default = csrf_token

    def validator(self, node: SchemaNode, value: Any) -> None:
        # Deferred validator via method, as per
        # https://docs.pylonsproject.org/projects/colander/en/latest/basics.html  # noqa
        request = self.bindings["request"]  # type: CamcopsRequest
        csrf_token = request.session.get_csrf_token()  # type: str
        matches = value == csrf_token
        if DEBUG_CSRF_CHECK:
            log.debug("Validating CSRF token: form says {!r}, session says "
                      "{!r}, matches = {}", value, csrf_token, matches)
        if not matches:
            log.warning("CSRF token mismatch; remote address {}",
                        request.remote_addr)
            raise Invalid(node, "Bad CSRF token")


class CSRFSchema(Schema):
    """
    Base class for form schemas that use CSRF (XSRF; cross-site request
    forgery) tokens.

    You can't put the call to bind() at the end of __init__(), because bind()
    calls clone() with no arguments and clone() ends up calling __init__()...
    """

    csrf = CSRFToken()


# =============================================================================
# Login
# =============================================================================

LOGIN_TITLE = "Log in"


class LoginSchema(CSRFSchema):
    username = SchemaNode(  # name must match ViewParam.USERNAME
        String(),
        description="Enter the user name",
    )
    password = SchemaNode(  # name must match ViewParam.PASSWORD
        String(),
        widget=PasswordWidget(),
        description="Enter the password",
    )
    redirect_url = SchemaNode(  # name must match ViewParam.REDIRECT_URL
        String(allow_empty=True),
        missing="",
        default="",
        widget=HiddenWidget(),
    )


class LoginForm(InformativeForm):
    def __init__(self,
                 request: CamcopsRequest,
                 autocomplete_password: bool = True) -> None:
        schema = LoginSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title=LOGIN_TITLE)],
            autocomplete=autocomplete_password
        )
        # Suboptimal: autocomplete_password is not applied to the password
        # widget, just to the form; see
        # http://stackoverflow.com/questions/2530
        # Note that e.g. Chrome may ignore this.


# =============================================================================
# Change password
# =============================================================================

CHANGE_PASSWORD_TITLE = "Change password"


class OldUserPasswordCheck(SchemaNode):
    schema_type = String
    title = "Old password"
    description = "Type the old password"
    widget = PasswordWidget()

    def validator(self, node: SchemaNode, value: Any) -> None:
        request = self.bindings["request"]  # type: CamcopsRequest
        user = request.user
        assert user is not None
        if not user.is_password_valid(value):
            raise Invalid(node, "Old password incorrect")


class ChangeOwnPasswordSchema(CSRFSchema):
    old_password = OldUserPasswordCheck()
    new_password = SchemaNode(  # name must match ViewParam.NEW_PASSWORD
        String(),
        validator=Length(min=MINIMUM_PASSWORD_LENGTH),
        widget=CheckedPasswordWidget(),
        title="New password",
        description="Type the new password and confirm it",
    )

    def __init__(self, *args, must_differ: bool = True, **kwargs):
        self.must_differ = must_differ
        super().__init__(*args, **kwargs)

    def validator(self, node: SchemaNode, value: Any) -> None:
        if self.must_differ and value['new_password'] == value['old_password']:
            raise Invalid(node, "New password must differ from old")


class ChangeOwnPasswordForm(InformativeForm):
    def __init__(self, request: CamcopsRequest,
                 must_differ: bool = True) -> None:
        schema = ChangeOwnPasswordSchema(must_differ=must_differ).\
            bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title=CHANGE_PASSWORD_TITLE)]
        )


class ChangeOtherPasswordSchema(CSRFSchema):
    user_id = SchemaNode(  # name must match ViewParam.USER_ID
        Integer(),
        widget=HiddenWidget(),
    )
    must_change_password = SchemaNode(  # match ViewParam.MUST_CHANGE_PASSWORD
        Boolean(),
        default=True,
        description="",
        label="User must change password at next login",
        title="Must change password at next login?",
    )
    new_password = SchemaNode(  # name must match ViewParam.NEW_PASSWORD
        String(),
        validator=Length(min=MINIMUM_PASSWORD_LENGTH),
        widget=CheckedPasswordWidget(),
        description="Type the new password and confirm it",
    )


class ChangeOtherPasswordForm(InformativeForm):
    def __init__(self, request: CamcopsRequest) -> None:
        schema = ChangeOtherPasswordSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title=CHANGE_PASSWORD_TITLE)]
        )


# =============================================================================
# Offer/agree terms
# =============================================================================

class OfferTermsSchema(CSRFSchema):
    pass


class OfferTermsForm(InformativeForm):
    def __init__(self,
                 request: CamcopsRequest,
                 agree_button_text: str) -> None:
        schema = OfferTermsSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title=agree_button_text)]
        )


# =============================================================================
# View audit trail
# =============================================================================

class AuditTrailSchema(CSRFSchema):
    rows_per_page = SchemaNode(  # must match ViewParam.ROWS_PER_PAGE
        Integer(),
        default=DEFAULT_ROWS_PER_PAGE,
        title="Number of entries to show per page",
    )
    start_datetime = SchemaNode(  # must match ViewParam.START_DATETIME
        DateTime(),
        missing=None,
        title="Start date/time (UTC)",
    )
    end_datetime = SchemaNode(  # must match ViewParam.END_DATETIME
        DateTime(),
        missing=None,
        title="End date/time (UTC)",
    )
    source = SchemaNode(  # must match ViewParam.SOURCE
        String(),
        default="",
        missing="",
        title="Source (e.g. webviewer, tablet, console)",
    )
    remote_ip_addr = SchemaNode(  # must match ViewParam.REMOTE_IP_ADDR
        String(),
        default="",
        missing="",
        title="Remote IP address",
    )
    username = SchemaNode(  # must match ViewParam.USERNAME
        String(),
        default="",
        missing="",
        title="User name",
    )
    table_name = SchemaNode(  # must match ViewParam.TABLENAME
        String(),
        default="",
        missing="",
        title="Database table name",
    )
    server_pk = SchemaNode(  # must match ViewParam.SERVER_PK
        Integer(),
        missing=None,
        title="Server PK",
    )
    truncate = SchemaNode(  # must match ViewParam.TRUNCATE
        Boolean(),
        default=True,
        title="Truncate details for easy viewing",
    )


class AuditTrailForm(InformativeForm):
    def __init__(self, request: CamcopsRequest) -> None:
        schema = AuditTrailSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title="View audit trail")]
        )


# =============================================================================
# View HL7 message log
# =============================================================================

class HL7MessageLogSchema(CSRFSchema):
    rows_per_page = SchemaNode(  # must match ViewParam.ROWS_PER_PAGE
        Integer(),
        default=DEFAULT_ROWS_PER_PAGE,
        title="Number of entries to show per page",
    )
    table_name = SchemaNode(  # must match ViewParam.TABLENAME
        String(),
        default="",
        missing="",
        title="Task base table (blank for all tasks)",
    )
    server_pk = SchemaNode(  # must match ViewParam.SERVER_PK
        Integer(),
        missing=None,
        title="Task server PK (blank for all tasks)",
    )
    hl7_run_id = SchemaNode(  # must match ViewParam.HL7_RUN_ID
        Integer(),
        missing=None,
        title="Run ID",
    )
    start_datetime = SchemaNode(  # must match ViewParam.START_DATETIME
        DateTime(),
        missing=None,
        title="Start date/time (UTC)",
    )
    end_datetime = SchemaNode(  # must match ViewParam.END_DATETIME
        DateTime(),
        missing=None,
        title="End date/time (UTC)",
    )


class HL7MessageLogForm(InformativeForm):
    def __init__(self, request: CamcopsRequest) -> None:
        schema = HL7MessageLogSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title="View HL7 message log")]
        )


# =============================================================================
# View HL7 run log
# =============================================================================

class HL7RunLogSchema(CSRFSchema):
    rows_per_page = SchemaNode(  # must match ViewParam.ROWS_PER_PAGE
        Integer(),
        default=DEFAULT_ROWS_PER_PAGE,
        title="Number of entries to show per page",
    )
    hl7_run_id = SchemaNode(  # must match ViewParam.HL7_RUN_ID
        Integer(),
        missing=None,
        title="Run ID",
    )
    start_datetime = SchemaNode(  # must match ViewParam.START_DATETIME
        DateTime(),
        missing=None,
        title="Start date/time (UTC)",
    )
    end_datetime = SchemaNode(  # must match ViewParam.END_DATETIME
        DateTime(),
        missing=None,
        title="End date/time (UTC)",
    )


class HL7RunLogForm(InformativeForm):
    def __init__(self, request: CamcopsRequest) -> None:
        schema = HL7RunLogSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=SUBMIT, title="View HL7 run log")]
        )


# =============================================================================
# Unit tests
# =============================================================================

class SchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.req = command_line_request()

    def tearDown(self) -> None:
        pass

    @staticmethod
    def serialize_deserialize(schema: Schema,
                              appstruct: Dict[str, Any]) -> None:
        cstruct = schema.serialize(appstruct)
        log.info("0. starting appstruct: {!r}", appstruct)
        log.info("1. serialize(appstruct) -> cstruct = {!r}", cstruct)
        final = schema.deserialize(cstruct)
        log.info("2. deserialize(cstruct) -> final = {!r}", final)
        mismatch = False
        for k, v in appstruct.items():
            if final[k] != v:
                mismatch = True
                break
        assert not mismatch, (
            "Elements of final don't match corresponding elements of starting "
            "appstruct:\n"
            "final = {}\n"
            "start = {}".format(
                pformat(final), pformat(appstruct)
            )
        )
        log.info("... all elements of final appstruct match corresponding "
                 "elements of starting appstruct")

    def test_login_schema(self) -> None:
        appstruct = {
            ViewParam.USERNAME: "testuser",
            ViewParam.PASSWORD: "testpw",
        }
        schema = LoginSchema().bind(request=self.req)
        self.serialize_deserialize(schema, appstruct)


# =============================================================================
# main
# =============================================================================
# run with "python -m camcops_server.cc_modules.forms -v" to be verbose

if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    unittest.main()
