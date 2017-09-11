#!/usr/bin/env python
# camcops_server/cc_modules/cc_forms.py

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
from typing import (Any, Dict, Iterable, List, Optional, Tuple, Type,
                    TYPE_CHECKING, Union)
import unittest

from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
import colander
from colander import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Invalid,
    Length,
    OneOf,
    Range,
    Schema,
    SchemaNode,
    SchemaType,
    Set,
    String,
)
from deform.exception import ValidationFailure
from deform.field import Field
from deform.form import Button, Form
from deform.widget import (
    CheckboxChoiceWidget,
    CheckboxWidget,
    CheckedPasswordWidget,
    DateTimeInputWidget,
    HiddenWidget,
    PasswordWidget,
    RadioChoiceWidget,
    SelectWidget,
    Widget,
)
from pendulum import Pendulum
from pendulum.parsing.exceptions import ParserError

# import as LITTLE AS POSSIBLE; this is used by lots of modules
# We use some delayed imports here (search for "delayed import")
from .cc_constants import DEFAULT_ROWS_PER_PAGE, MINIMUM_PASSWORD_LENGTH
from .cc_dt import coerce_to_pendulum, POTENTIAL_DATETIME_TYPES
from .cc_pyramid import Dialect, FormAction, ViewArg, ViewParam

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))

COLANDER_NULL_TYPE = type(colander.null)

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

def get_head_form_html(req: "CamcopsRequest", forms: List[Form]) -> str:
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

    RNC: Serialized values are always STRINGS.

    """
    schema_type = String
    default = ""
    missing = ""
    title = "CSRF token"
    widget = HiddenWidget()

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        req = kw["request"]  # type: CamcopsRequest
        csrf_token = req.session.get_csrf_token()
        if DEBUG_CSRF_CHECK:
            log.debug("Got CSRF token from session: {!r}", csrf_token)
        self.default = csrf_token

    def validator(self, node: SchemaNode, value: Any) -> None:
        # Deferred validator via method, as per
        # https://docs.pylonsproject.org/projects/colander/en/latest/basics.html  # noqa
        req = self.bindings["request"]  # type: CamcopsRequest
        csrf_token = req.session.get_csrf_token()  # type: str
        matches = value == csrf_token
        if DEBUG_CSRF_CHECK:
            log.debug("Validating CSRF token: form says {!r}, session says "
                      "{!r}, matches = {}", value, csrf_token, matches)
        if not matches:
            log.warning("CSRF token mismatch; remote address {}",
                        req.remote_addr)
            raise Invalid(node, "Bad CSRF token")


class CSRFSchema(Schema):
    """
    Base class for form schemas that use CSRF (XSRF; cross-site request
    forgery) tokens.

    You can't put the call to bind() at the end of __init__(), because bind()
    calls clone() with no arguments and clone() ends up calling __init__()...
    """

    csrf = CSRFToken()  # name must match ViewParam.CSRF_TOKEN


# =============================================================================
# New generic SchemaType classes
# =============================================================================

class PendulumType(SchemaType):
    def __init__(self, use_local_tz: bool = True):
        self.use_local_tz = use_local_tz
        super().__init__()  # not necessary; SchemaType has no __init__

    def serialize(self,
                  node: SchemaNode,
                  appstruct: Union[POTENTIAL_DATETIME_TYPES,
                                   COLANDER_NULL_TYPE]) \
            -> Union[str, COLANDER_NULL_TYPE]:
        if not appstruct:
            return colander.null
        try:
            appstruct = coerce_to_pendulum(appstruct,
                                           assume_local=self.use_local_tz)
        except (ValueError, ParserError) as e:
            raise Invalid(node, "{!r} is not a Pendulum object; error was "
                                "{!r}".format(appstruct, e))
        return appstruct.isoformat()

    def deserialize(self,
                    node: SchemaNode,
                    cstruct: Union[str, COLANDER_NULL_TYPE]) \
            -> Optional[Pendulum]:
        if not cstruct:
            return colander.null
        try:
            result = coerce_to_pendulum(cstruct,
                                        assume_local=self.use_local_tz)
        except (ValueError, ParserError) as e:
            raise Invalid(node, "Invalid date/time: value={!r}, error="
                                "{!r}".format(cstruct, e))
        return result


# =============================================================================
# Other new generic SchemaNode classes
# =============================================================================
# Note that we must pass both *args and **kwargs upwards, because SchemaNode
# does some odd stuff with clone().

class NoneAcceptantNode(SchemaNode):
    """
    Accepts None values for schema nodes.
    See
        https://stackoverflow.com/questions/18774976/colander-how-do-i-allow-none-values  # noqa
    but modified because that doesn't work properly.
    Most applicable for e.g. integer types.
    Note that Colander serializes everything to strings, but treats
    colander.null in a special way.
    """
    def __init__(self, *args, allow_none: bool = True, **kwargs) -> None:
        self.allow_none = allow_none
        super().__init__(*args, **kwargs)

    def deserialize(self, value: str) -> Any:
        if self.allow_none and value == colander.null:
            retval = None
        else:
            retval = super().deserialize(value)
        # log.critical("deserialize: {!r} -> {!r}", value, retval)
        return retval

    def serialize(self, value: Any) -> str:
        if self.allow_none and value is None or value is colander.null:
            retval = colander.null
        else:
            retval = super().serialize(value)
        # log.critical("serialize: {!r} -> {!r}", value, retval)
        return retval


def get_values_and_permissible(values: Iterable[Tuple[Any, str]],
                               add_none: bool = False,
                               none_tuple: Tuple[Any, str] = None) \
        -> Tuple[List[Tuple[Any, str]], List[Any]]:
    if add_none:
        assert none_tuple is not None and len(none_tuple) == 2
        values = [none_tuple] + list(values)
    permissible_values = list(x[0] for x in values)
    return values, permissible_values


class OptionalInt(NoneAcceptantNode):
    schema_type = Integer
    default = None
    missing = None

    def __init__(self, *args, title: str = "?", **kwargs) -> None:
        self.title = title
        super().__init__(*args, **kwargs)


class OptionalString(SchemaNode):
    schema_type = String
    default = ""
    missing = ""

    def __init__(self, *args, title: str = "?", **kwargs) -> None:
        self.title = title
        super().__init__(*args, **kwargs)


class HiddenInteger(SchemaNode):
    schema_type = Integer
    widget = HiddenWidget()


class HiddenString(SchemaNode):
    schema_type = String
    widget = HiddenWidget()


class DateTimeSelector(SchemaNode):
    schema_type = DateTime
    missing = None


class DateSelector(SchemaNode):
    schema_type = Date
    missing = None


class PendulumSelector(NoneAcceptantNode):
    schema_type = PendulumType
    default = None
    missing = None
    widget = DateTimeInputWidget()


# =============================================================================
# Specialized SchemaNode classes
# =============================================================================

class SingleTaskSelector(SchemaNode):
    schema_type = String
    default = ""
    missing = ""
    title = "Task type"

    def __init__(self, *args, allow_none: bool = True, **kwargs) -> None:
        self.allow_none = allow_none
        self.widget = None  # type: Widget
        self.validator = None  # type: object
        super().__init__(*args, **kwargs)

    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        values, pv = get_values_and_permissible(self.get_task_choices(),
                                                self.allow_none, ("", "[Any]"))
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    @staticmethod
    def get_task_choices() -> List[Tuple[str, str]]:
        raise NotImplementedError


class MultiTaskSelector(SchemaNode):
    schema_type = Set
    default = ""
    missing = ""
    title = "Task type(s)"

    def __init__(self, *args, minimum_length: int = 1, **kwargs) -> None:
        self.minimum_length = minimum_length
        self.widget = None  # type: Widget
        self.validator = None  # type: object
        super().__init__(*args, **kwargs)

    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        values, pv = get_values_and_permissible(self.get_task_choices(),
                                                add_none=False)
        self.widget = CheckboxChoiceWidget(values=values)
        self.validator = Length(min=self.minimum_length)

    @staticmethod
    def get_task_choices() -> List[Tuple[str, str]]:
        raise NotImplementedError()


class AllTasksSingleTaskSelector(SingleTaskSelector):
    @staticmethod
    def get_task_choices() -> List[Tuple[str, str]]:
        from .cc_task import Task  # delayed import
        choices = []  # type: List[Tuple[str, str]]
        for tc in Task.all_subclasses_by_shortname():
            choices.append((tc.tablename, tc.shortname))
        return choices


class TrackerTaskSelector(MultiTaskSelector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, minimum_length=0, **kwargs)

    @staticmethod
    def get_task_choices() -> List[Tuple[str, str]]:
        from .cc_task import Task  # delayed import
        choices = []  # type: List[Tuple[str, str]]
        for tc in Task.all_subclasses_by_shortname():
            if tc.provides_trackers:
                choices.append((tc.tablename, tc.shortname))
        return choices


class WhichIdNumSelector(NoneAcceptantNode):
    schema_type = Integer
    default = None
    missing = None
    title = "Identifier"
    widget = SelectWidget()
    validator = None

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        req = kw["request"]  # type: CamcopsRequest
        cfg = req.config
        values = []  # type: List[Tuple[Optional[int], str]]
        for which_idnum in cfg.get_which_idnums():
            values.append((which_idnum, cfg.get_id_desc(which_idnum)))
        values, pv = get_values_and_permissible(values, self.allow_none,
                                                ("", "[ignore]"))
        # ... can't use None, because SelectWidget() will convert that to
        # "None"; can't use colander.null, because that converts to
        # "<colander.null>"; use "", which is the default null_value of
        # SelectWidget.
        self.widget.values = values
        self.validator = OneOf(pv)


class IdNumValue(NoneAcceptantNode):
    schema_type = Integer
    default = None
    missing = None
    title = "ID# value"
    validator = Range(min=0)


class SexSelector(SchemaNode):
    _sex_choices = [("F", "F"), ("M", "M"), ("X", "X")]

    schema_type = String
    default = ""
    missing = ""
    title = "Sex"

    def __init__(self, *args, allow_none: bool = True, **kwargs) -> None:
        values, pv = get_values_and_permissible(self._sex_choices, allow_none,
                                                ("", "Any"))
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


class UserIdSelector(NoneAcceptantNode):
    schema_type = Integer
    default = None
    missing = None
    title = "User"

    def __init__(self, *args, allow_none: bool = True, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, allow_none=allow_none, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        from .cc_user import User  # delayed import
        req = kw["request"]  # type: CamcopsRequest
        dbsession = req.dbsession
        values = []  # type: List[Tuple[Optional[int], str]]
        users = dbsession.query(User).order_by(User.username)
        for user in users:
            values.append((user.id, user.username))
        values, pv = get_values_and_permissible(values, self.allow_none,
                                                ("", "[Any]"))
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)


class UserNameSelector(SchemaNode):
    schema_type = String
    default = ""
    missing = ""
    title = "User"

    def __init__(self, *args, allow_none: bool, **kwargs) -> None:
        self.allow_none = allow_none
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        from .cc_user import User  # delayed import
        req = kw["request"]  # type: CamcopsRequest
        dbsession = req.dbsession
        values = []  # type: List[Tuple[Optional[int], str]]
        users = dbsession.query(User).order_by(User.username)
        for user in users:
            values.append((user.username, user.username))
        values, pv = get_values_and_permissible(values, self.allow_none,
                                                (None, "[ignore]"))
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)


class ServerPkSelector(SchemaNode):
    schema_type = Integer
    missing = None
    title = "Server PK"


class StartPendulumSelector(PendulumSelector):
    title = "Start date/time"


class EndPendulumSelector(PendulumSelector):
    title = "End date/time"


class StartDateTimeSelector(DateTimeSelector):
    title = "Start date/time (UTC)"


class EndDateTimeSelector(DateTimeSelector):
    title = "End date/time (UTC)"


class StartDateSelector(DateSelector):
    title = "Start date (UTC)"


class EndDateSelector(DateSelector):
    title = "End date (UTC)"


class RowsPerPageSelector(SchemaNode):
    _choices = ((10, "10"), (25, "25"), (50, "50"), (100, "100"))

    schema_type = Integer
    default = DEFAULT_ROWS_PER_PAGE
    title = "Items to show per page"
    widget = RadioChoiceWidget(values=_choices)
    validator = OneOf(list(x[0] for x in _choices))


class TaskTrackerOutputTypeSelector(SchemaNode):
    _choices = ((ViewArg.HTML, "HTML"),
                (ViewArg.PDF, "PDF"),
                (ViewArg.XML, "XML"))

    schema_type = String
    default = ViewArg.HTML
    missing = ViewArg.HTML
    title = "View as"
    widget = RadioChoiceWidget(values=_choices)
    validator = OneOf(list(x[0] for x in _choices))


class ReportOutputTypeSelector(SchemaNode):
    _choices = ((ViewArg.HTML, "HTML"),
                (ViewArg.TSV, "TSV (tab-separated values)"))

    schema_type = String
    default = ViewArg.HTML
    missing = ViewArg.HTML
    title = "View as"
    widget = RadioChoiceWidget(values=_choices)
    validator = OneOf(list(x[0] for x in _choices))


# =============================================================================
# Login
# =============================================================================

class LoginSchema(CSRFSchema):
    username = SchemaNode(  # name must match ViewParam.USERNAME
        String(),
        description="Username",
    )
    password = SchemaNode(  # name must match ViewParam.PASSWORD
        String(),
        widget=PasswordWidget(),
        description="Password",
    )
    redirect_url = SchemaNode(  # name must match ViewParam.REDIRECT_URL
        String(allow_empty=True),
        missing="",
        default="",
        widget=HiddenWidget(),
    )


class LoginForm(InformativeForm):
    def __init__(self,
                 request: "CamcopsRequest",
                 autocomplete_password: bool = True,
                 **kwargs) -> None:
        schema = LoginSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT, title="Log in")],
            autocomplete=autocomplete_password,
            **kwargs
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
    def __init__(self, request: "CamcopsRequest",
                 must_differ: bool = True,
                 **kwargs) -> None:
        schema = ChangeOwnPasswordSchema(must_differ=must_differ).\
            bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT,
                            title=CHANGE_PASSWORD_TITLE)],
            **kwargs
        )


class ChangeOtherPasswordSchema(CSRFSchema):
    user_id = HiddenInteger()  # name must match ViewParam.USER_ID
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
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = ChangeOtherPasswordSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT,
                            title=CHANGE_PASSWORD_TITLE)],
            **kwargs
        )


# =============================================================================
# Offer/agree terms
# =============================================================================

class OfferTermsSchema(CSRFSchema):
    pass


class OfferTermsForm(InformativeForm):
    def __init__(self,
                 request: "CamcopsRequest",
                 agree_button_text: str,
                 **kwargs) -> None:
        schema = OfferTermsSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT, title=agree_button_text)],
            **kwargs
        )


# =============================================================================
# View audit trail
# =============================================================================

class AuditTrailSchema(CSRFSchema):
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME
    source = OptionalString(title="Source (e.g. webviewer, tablet, console)")  # must match ViewParam.SOURCE  # noqa
    remote_ip_addr = OptionalString(title="Remote IP address")  # must match ViewParam.REMOTE_IP_ADDR  # noqa
    username = UserNameSelector(allow_none=True)  # must match ViewParam.USERNAME  # noqa
    table_name = AllTasksSingleTaskSelector(allow_none=True)  # must match ViewParam.TABLENAME  # noqa
    server_pk = ServerPkSelector()  # must match ViewParam.SERVER_PK
    truncate = SchemaNode(  # must match ViewParam.TRUNCATE
        Boolean(),
        default=True,
        title="Truncate details for easy viewing",
    )


class AuditTrailForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = AuditTrailSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT, title="View audit trail")],
            **kwargs
        )


# =============================================================================
# View HL7 message log
# =============================================================================

class HL7MessageLogSchema(CSRFSchema):
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE
    table_name = AllTasksSingleTaskSelector(allow_none=True)  # must match ViewParam.TABLENAME  # noqa
    server_pk = ServerPkSelector()  # must match ViewParam.SERVER_PK
    hl7_run_id = OptionalInt(title="Run ID")  # must match ViewParam.HL7_RUN_ID  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME


class HL7MessageLogForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = HL7MessageLogSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT,
                            title="View HL7 message log")],
            **kwargs
        )


# =============================================================================
# View HL7 run log
# =============================================================================

class HL7RunLogSchema(CSRFSchema):
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE
    hl7_run_id = OptionalInt(title="Run ID")  # must match ViewParam.HL7_RUN_ID  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME


class HL7RunLogForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = HL7RunLogSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT, title="View HL7 run log")],
            **kwargs
        )


# =============================================================================
# Task filters
# =============================================================================

class TaskFiltersSchema(CSRFSchema):
    surname = OptionalString(title="Surname")  # must match ViewParam.SURNAME
    forename = OptionalString(title="Forename")  # must match ViewParam.FORENAME
    dob = SchemaNode(  # must match ViewParam.DOB
        Date(),
        missing=None,
        title="Date of birth",
    )
    sex = SexSelector(allow_none=True)  # must match ViewParam.SEX
    which_idnum = WhichIdNumSelector(allow_none=True)  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = IdNumValue(allow_none=True)  # must match ViewParam.IDNUM_VALUE  # noqa
    table_name = AllTasksSingleTaskSelector(allow_none=True)  # must match ViewParam.TABLENAME  # noqa
    only_complete = SchemaNode(  # must match ViewParam.ONLY_COMPLETE
        Boolean(),
        widget=CheckboxWidget(),
        default=False,
        missing=False,
        title="Only completed tasks?",
    )
    user_id = UserIdSelector(allow_none=True)  # must match ViewParam.USER_ID
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME
    text_contents = OptionalString(title="Text contents")  # must match ViewParam.TEXT_CONTENTS  # noqa


class TaskFiltersForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = TaskFiltersSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SET_FILTERS, title="Set filters"),
                     Button(name=FormAction.CLEAR_FILTERS, title="Clear")],
            **kwargs
        )


class TasksPerPageSchema(CSRFSchema):
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE


class TasksPerPageForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = TasksPerPageSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT_TASKS_PER_PAGE,
                            title="Set n/page")],
            **kwargs
        )


class RefreshTasksSchema(CSRFSchema):
    pass


class RefreshTasksForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = RefreshTasksSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.REFRESH_TASKS, title="Refresh")],
            **kwargs
        )


# =============================================================================
# Trackers
# =============================================================================

class ChooseTrackerSchema(CSRFSchema):
    which_idnum = WhichIdNumSelector(allow_none=False)  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = IdNumValue(allow_none=False)  # must match ViewParam.IDNUM_VALUE  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME
    all_tasks = SchemaNode(  # match ViewParam.ALL_TASKS
        Boolean(),
        default=True,
        missing=True,
        title="Use all eligible task types?",
    )
    tasks = TrackerTaskSelector()  # must match ViewParam.TASKS
    viewtype = TaskTrackerOutputTypeSelector()  # must match ViewParams.VIEWTYPE


class ChooseTrackerForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest",
                 as_ctv: bool, **kwargs) -> None:
        schema = ChooseTrackerSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT,
                            title=("View CTV" if as_ctv else "View tracker"))],
            **kwargs
        )


# =============================================================================
# Reports, which use dynamically created forms
# =============================================================================

class ReportParamSchema(CSRFSchema):
    report_id = HiddenString()  # must match ViewParams.REPORT_ID
    viewtype = ReportOutputTypeSelector()  # must match ViewParams.VIEWTYPE
    # Specific forms may inherit from this.


class ReportParamForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest",
                 schema_class: Type[ReportParamSchema], **kwargs) -> None:
        schema = schema_class().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT, title="View report")],
            **kwargs
        )


# =============================================================================
# View DDL
# =============================================================================

DIALECT_CHOICES = (
    # http://docs.sqlalchemy.org/en/latest/dialects/
    (Dialect.MYSQL, "MySQL"),
    (Dialect.MSSQL, "Microsoft SQL Server"),
    (Dialect.ORACLE, "Oracle"),
    (Dialect.FIREBIRD, "Firebird"),
    (Dialect.POSTGRES, "PostgreSQL"),
    (Dialect.SQLITE, "SQLite"),
    (Dialect.SYBASE, "Sybase"),
)


class DatabaseDialectSelector(SchemaNode):

    schema_type = String
    default = ""
    missing = ""
    title = "SQL dialect to view DDL in"

    def __init__(self, *args, allow_none: bool = False, **kwargs) -> None:
        values, pv = get_values_and_permissible(
            DIALECT_CHOICES, allow_none, ("", "Any"))
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


class ViewDdlSchema(CSRFSchema):
    dialect = DatabaseDialectSelector()  # must match ViewParam.DIALECT


class ViewDdlForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = ViewDdlSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT, title="View DDL")],
            **kwargs
        )


# =============================================================================
# Unit tests
# =============================================================================

class SchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        from .cc_request import command_line_request
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
