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

COLANDER NODES, NULLS, AND VALIDATION
- Surprisingly tricky.
- Nodes must be validly intialized with NO USER-DEFINED PARAMETERS to __init__;
  the Deform framework clones them.
- A null appstruct is used to initialize nodes as Forms are created.
  Therefore, the "default" value must be acceptable to the underlying type's
  serialize() function. Note in particular that "default = None" is not
  acceptable to Integer. Having no default is fine, though.
- In general, flexible inheritance is very hard to implement.

- Note that this error:
    AttributeError: 'EditTaskFilterSchema' object has no attribute 'typ'
  means you have failed to call super().__init__() properly from __init__().

- When creating a schema, its members seem to have to be created in the class
  declaration as class properties, not in __init__().
"""

import logging
from pprint import pformat
from typing import (Any, Callable, Dict, Iterable, List, Optional, Tuple, Type,
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
    Email,
    Integer,
    Invalid,
    Length,
    MappingSchema,
    OneOf,
    Range,
    Schema,
    SchemaNode,
    SchemaType,
    SequenceSchema,
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
    MappingWidget,
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
from .cc_dt import coerce_to_pendulum, PotentialDatetimeType
from .cc_group import Group
from .cc_pyramid import Dialect, FormAction, ViewArg, ViewParam

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest
    from .cc_user import User

log = BraceStyleAdapter(logging.getLogger(__name__))

ColanderNullType = type(colander.null)
ValidatorType = Callable[[SchemaNode, Any], None]  # called as v(node, value)

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_COLANDER = False
DEBUG_CSRF_CHECK = False
DEBUG_FORM_VALIDATION = False

if DEBUG_COLANDER or DEBUG_CSRF_CHECK or DEBUG_FORM_VALIDATION:
    log.warning("Debugging options enabled!")

# =============================================================================
# Constants
# =============================================================================

OR_JOIN = "If you specify more than one, they will be joined with OR."
SERIALIZED_NONE = ""


class Binding:
    # Must match kwargs of calls to bind() function of each Schema
    GROUP = "group"
    OPEN_ADMIN = "open_admin"
    OPEN_WHAT = "open_what"
    OPEN_WHEN = "open_when"
    OPEN_WHO = "open_who"
    REQUEST = "request"
    USER = "user"


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
                log.warning("Validation failure: {!r}; {}",
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


def debug_validator(validator: ValidatorType) -> ValidatorType:
    """
    Use as a wrapper around a validator, e.g.
        self.validator = debug_validator(OneOf(["some", "values"]))
    """
    def _validate(node: SchemaNode, value: Any) -> None:
        log.debug("Validating: {!r}", value)
        try:
            validator(node, value)
            log.debug("... accepted")
        except Invalid:
            log.debug("... rejected")
            raise

    return _validate


# =============================================================================
# New generic SchemaType classes
# =============================================================================

class PendulumType(SchemaType):
    def __init__(self, use_local_tz: bool = True):
        self.use_local_tz = use_local_tz
        super().__init__()  # not necessary; SchemaType has no __init__

    def serialize(self,
                  node: SchemaNode,
                  appstruct: Union[PotentialDatetimeType,
                                   ColanderNullType]) \
            -> Union[str, ColanderNullType]:
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
                    cstruct: Union[str, ColanderNullType]) \
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


class AllowNoneType(SchemaType):
    """
    Serializes None to '', and deserializes '' to None; otherwise defers
    to the parent type.
    A type which accept serialize None to '' and deserialize '' to None.
    When the value is not equal to None/'', it will use (de)serialization of
    the given type. This can be used to make nodes optional.
    Example:
        date = colander.SchemaNode(
            colander.NoneType(colander.DateTime()),
            default=None,
            missing=None,
        )
    """
    def __init__(self, type_: SchemaType) -> None:
        self.type_ = type_

    def serialize(self, node: SchemaNode,
                  value: Any) -> Union[str, ColanderNullType]:
        if value is None:
            retval = ''
        else:
            # noinspection PyUnresolvedReferences
            retval = self.type_.serialize(node, value)
        if DEBUG_COLANDER:
            log.debug("AllowNoneType.serialize: {!r} -> {!r}", value, retval)
        return retval

    def deserialize(self, node: SchemaNode,
                    value: Union[str, ColanderNullType]) -> Any:
        if value is None or value == '':
            retval = None
        else:
            # noinspection PyUnresolvedReferences
            retval = self.type_.deserialize(node, value)
        if DEBUG_COLANDER:
            log.debug("AllowNoneType.deserialize: {!r} -> {!r}", value, retval)
        return retval


# NOTE ALSO that Colander nodes explicitly never validate a missing value; see
# colander/__init__.py, in _SchemaNode.deserialize().
# We want them to do so, essentially so we can pass in None to a form but
# have the form refuse to validate if it's still None at submission.


# =============================================================================
# Node helper functions
# =============================================================================

def get_values_and_permissible(values: Iterable[Tuple[Any, str]],
                               add_none: bool = False,
                               none_description: str = "[None]") \
        -> Tuple[List[Tuple[Any, str]], List[Any]]:
    permissible_values = list(x[0] for x in values)
    # ... does not include the None value; those do not go to the validator
    if add_none:
        none_tuple = (SERIALIZED_NONE, none_description)
        values = [none_tuple] + list(values)
    return values, permissible_values


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
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        csrf_token = req.session.get_csrf_token()
        if DEBUG_CSRF_CHECK:
            log.debug("Got CSRF token from session: {!r}", csrf_token)
        self.default = csrf_token

    def validator(self, node: SchemaNode, value: Any) -> None:
        # Deferred validator via method, as per
        # https://docs.pylonsproject.org/projects/colander/en/latest/basics.html  # noqa
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
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
# Other new generic SchemaNode classes
# =============================================================================
# Note that we must pass both *args and **kwargs upwards, because SchemaNode
# does some odd stuff with clone().

class OptionalIntNode(SchemaNode):
    # YOU CANNOT USE ARGUMENTS THAT INFLUENCE THE STRUCTURE, because these Node
    # objects get default-copied by Deform.
    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(Integer())

    default = None
    missing = None


class OptionalStringNode(SchemaNode):
    """
    Coerces None to "" when serializing; otherwise it is coerced to "None",
    which is much more wrong.
    """
    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(String(allow_empty=True))

    default = ""
    missing = ""


class HiddenIntegerNode(OptionalIntNode):
    widget = HiddenWidget()


class HiddenStringNode(OptionalStringNode):
    widget = HiddenWidget()


class DateTimeSelectorNode(SchemaNode):
    schema_type = DateTime
    missing = None


class DateSelectorNode(SchemaNode):
    schema_type = Date
    missing = None


class OptionalPendulumNode(SchemaNode):
    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(PendulumType())

    default = None
    missing = None
    widget = DateTimeInputWidget()


class BooleanNode(SchemaNode):
    schema_type = Boolean
    widget = CheckboxWidget()

    def __init__(self, *args, title: str = "?", default: bool = False,
                 **kwargs) -> None:
        self.title = title  # above the checkbox
        self.label = title  # to the right of the checkbox
        self.default = default
        self.missing = default
        super().__init__(*args, **kwargs)


# =============================================================================
# Specialized SchemaNode classes
# =============================================================================

class OptionalSingleTaskSelector(OptionalStringNode):
    title = "Task type"

    def __init__(self, *args, **kwargs) -> None:
        self.widget = None  # type: Widget
        self.validator = None  # type: ValidatorType
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        values, pv = get_values_and_permissible(self.get_task_choices(),
                                                True, "[Any]")
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
    description = (
        "If none are selected, all task types will be offered. " + OR_JOIN
    )

    def __init__(self, *args, minimum_length: int = 1, **kwargs) -> None:
        self.minimum_length = minimum_length
        self.widget = None  # type: Widget
        self.validator = None  # type: object
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        values, pv = get_values_and_permissible(self.get_task_choices())
        self.widget = CheckboxChoiceWidget(values=values)
        self.validator = Length(min=self.minimum_length)

    @staticmethod
    def get_task_choices() -> List[Tuple[str, str]]:
        raise NotImplementedError()


class AllTasksOptionalSingleTaskSelector(OptionalSingleTaskSelector):
    @staticmethod
    def get_task_choices() -> List[Tuple[str, str]]:
        from .cc_task import Task  # delayed import
        choices = []  # type: List[Tuple[str, str]]
        for tc in Task.all_subclasses_by_shortname():
            choices.append((tc.tablename, tc.shortname))
        return choices


class AllTasksMultiTaskSelector(MultiTaskSelector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, minimum_length=0, **kwargs)

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


class MandatoryWhichIdNumSelector(SchemaNode):
    title = "Identifier"
    widget = SelectWidget()

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "allow_none"):
            # ... allows parameter-free (!) inheritance by OptionalWhichIdNumSelector  # noqa
            self.allow_none = False
        self.validator = None
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        cfg = req.config
        values = []  # type: List[Tuple[Optional[int], str]]
        for which_idnum in cfg.get_which_idnums():
            values.append((which_idnum, cfg.get_id_desc(which_idnum)))
        values, pv = get_values_and_permissible(values, self.allow_none,
                                                "[ignore]")
        # ... can't use None, because SelectWidget() will convert that to
        # "None"; can't use colander.null, because that converts to
        # "<colander.null>"; use "", which is the default null_value of
        # SelectWidget.
        self.widget.values = values
        self.validator = OneOf(pv)

    @staticmethod
    def schema_type() -> SchemaType:
        return Integer()


class OptionalWhichIdNumSelector(MandatoryWhichIdNumSelector):
    default = None
    missing = None

    def __init__(self, *args, **kwargs):
        self.allow_none = True
        super().__init__(*args, **kwargs)

    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(Integer())


class MandatoryIdNumValue(SchemaNode):
    schema_type = Integer
    title = "ID# value"
    validator = Range(min=0)


class OptionalIdNumValue(MandatoryIdNumValue):
    default = None
    missing = None

    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(Integer())


class MandatoryIdNumDefinitionNode(MappingSchema):
    which_idnum = MandatoryWhichIdNumSelector()  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = MandatoryIdNumValue()  # must match ViewParam.IDNUM_VALUE
    title = "ID number"


class IdNumDefinitionSequence(SequenceSchema):
    idnum_def_sequence = MandatoryIdNumDefinitionNode()
    title = "ID numbers"
    description = OR_JOIN

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[Dict[str, int]]) -> None:
        # log.critical("IdNumDefinitionSequence.validator: {!r}", value)
        assert isinstance(value, list)
        list_of_lists = [(x[ViewParam.WHICH_IDNUM], x[ViewParam.IDNUM_VALUE])
                         for x in value]
        if len(list_of_lists) != len(set(list_of_lists)):
            raise Invalid(node, "You have specified duplicate ID definitions")


class SexSelector(OptionalStringNode):
    _sex_choices = [("F", "F"), ("M", "M"), ("X", "X")]
    title = "Sex"

    def __init__(self, *args, **kwargs) -> None:
        values, pv = get_values_and_permissible(self._sex_choices, True, "Any")
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


class MandatoryUserIdSelectorUsersAllowedToSee(SchemaNode):
    schema_type = Integer
    title = "User"

    def __init__(self, *args, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        from .cc_user import User  # delayed import
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        dbsession = req.dbsession
        user = req.user
        if user.superuser:
            users = dbsession.query(User).order_by(User.username)
        else:
            # Users in my groups, or groups I'm allowed to see
            my_allowed_group_ids = user.ids_of_groups_user_may_see()
            users = dbsession.query(User)\
                .join(Group)\
                .filter(Group.id.in_(my_allowed_group_ids))\
                .order_by(User.username)
        values = []  # type: List[Tuple[Optional[int], str]]
        for user in users:
            values.append((user.id, user.username))
        values, pv = get_values_and_permissible(values, False)
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)


class OptionalUserNameSelector(OptionalStringNode):
    title = "User"

    def __init__(self, *args, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        from .cc_user import User  # delayed import
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        dbsession = req.dbsession
        values = []  # type: List[Tuple[str, str]]
        users = dbsession.query(User).order_by(User.username)
        for user in users:
            values.append((user.username, user.username))
        values, pv = get_values_and_permissible(values, True, "[ignore]")
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)


class MandatoryDeviceIdSelector(SchemaNode):
    schema_type = Integer
    title = "Device"

    def __init__(self, *args, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        from .cc_device import Device  # delayed import
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        dbsession = req.dbsession
        devices = dbsession.query(Device).order_by(Device.friendly_name)
        values = []  # type: List[Tuple[Optional[int], str]]
        for device in devices:
            values.append((device.id, device.friendly_name))
        values, pv = get_values_and_permissible(values, False)
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)


class ServerPkSelector(OptionalIntNode):
    title = "Server PK"


class StartPendulumSelector(OptionalPendulumNode):
    title = "Start date/time"


class EndPendulumSelector(OptionalPendulumNode):
    title = "End date/time"


class StartDateTimeSelector(DateTimeSelectorNode):
    title = "Start date/time (UTC)"


class EndDateTimeSelector(DateTimeSelectorNode):
    title = "End date/time (UTC)"


class StartDateSelector(DateSelectorNode):
    title = "Start date (UTC)"


class EndDateSelector(DateSelectorNode):
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


class UsernameNode(SchemaNode):
    schema_type = String
    title = "Username"


class MustChangePasswordNode(SchemaNode):
    schema_type = Boolean
    label = "User must change password at next login"
    title = "Must change password at next login?"
    default = True
    missing = True


class NewPasswordNode(SchemaNode):
    schema_type = String
    validator = Length(min=MINIMUM_PASSWORD_LENGTH)
    widget = CheckedPasswordWidget()
    title = "New password"
    description = "Type the new password and confirm it"


class MandatoryGroupIdSelectorAllGroups(SchemaNode):
    """
    Offers a picklist of groups from ALL POSSIBLE GROUPS.
    Used by superusers (e.g. add user to group).
    """
    title = "Group"

    def __init__(self, *args, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        dbsession = req.dbsession
        groups = dbsession.query(Group).order_by(Group.name)
        values = [(g.id, g.name) for g in groups]
        values, pv = get_values_and_permissible(values)
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    @staticmethod
    def schema_type() -> SchemaType:
        return Integer()


class MandatoryGroupIdSelectorOtherGroups(SchemaNode):
    """
    Offers a picklist of groups THAT ARE NOT THE SPECIFIED GROUP.
    Used by superusers, typically: "which other groups can this group see?"
    """
    title = "Other group"

    def __init__(self, *args, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        group = kw[Binding.GROUP]  # type: Group  # ATYPICAL BINDING
        dbsession = req.dbsession
        groups = dbsession.query(Group).order_by(Group.name)
        values = [(g.id, g.name) for g in groups if g.id != group.id]
        values, pv = get_values_and_permissible(values)
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    @staticmethod
    def schema_type() -> SchemaType:
        return Integer()


class MandatoryGroupIdSelectorUserGroups(SchemaNode):
    """
    Offers a picklist of groups from THOSE THE USER IS A MEMBER OF.
    """
    title = "Group"

    def __init__(self, *args, **kwargs) -> None:
        if not hasattr(self, "allow_none"):
            # ... allows parameter-free (!) inheritance by OptionalGroupIdSelectorUserGroups  # noqa
            self.allow_none = False
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        user = kw[Binding.USER]  # type: User  # ATYPICAL BINDING
        groups = sorted(list(user.groups), key=lambda g: g.name)
        values = [(g.id, g.name) for g in groups]
        values, pv = get_values_and_permissible(values, self.allow_none,
                                                "[None]")
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    @staticmethod
    def schema_type() -> SchemaType:
        return Integer()


class OptionalGroupIdSelectorUserGroups(MandatoryGroupIdSelectorUserGroups):
    """
    Offers a picklist of groups from THOSE THE USER IS A MEMBER OF.
    Used for "which do you want to upload into?".
    """
    default = None
    missing = None

    def __init__(self, *args, **kwargs) -> None:
        self.allow_none = True
        super().__init__(*args, **kwargs)

    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(Integer())


class MandatoryGroupIdSelectorAllowedGroups(SchemaNode):
    """
    Offers a picklist of groups from THOSE THE USER IS ALLOWED TO SEE.
    Used for task filters.
    """
    title = "Group"

    def __init__(self, *args, **kwargs) -> None:
        self.validator = None  # type: object
        self.widget = None  # type: Widget
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        req = kw[Binding.REQUEST]  # type: CamcopsRequest
        dbsession = req.dbsession
        user = req.user
        if user.superuser:
            groups = dbsession.query(Group).order_by(Group.name)
        else:
            groups = sorted(list(user.groups), key=lambda g: g.name)
        values = [(g.id, g.name) for g in groups]
        values, pv = get_values_and_permissible(values)
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    @staticmethod
    def schema_type() -> SchemaType:
        return Integer()


class GroupsSequenceBase(SequenceSchema):
    title = "Groups"

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[int]) -> None:
        # log.critical("GroupsSequenceBase.validator: {!r}", value)
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate groups")


class AllGroupsSequence(GroupsSequenceBase):
    """
    Typical use: superuser assigns group memberships to a user.
    Offer all possible groups.
    """
    group_id_sequence = MandatoryGroupIdSelectorAllGroups()


class AllOtherGroupsSequence(GroupsSequenceBase):
    """
    Typical use: superuser assigns group permissions to another group.
    Offer all possible OTHER groups.
    """
    group_id_sequence = MandatoryGroupIdSelectorOtherGroups()


class AllowedGroupsSequence(GroupsSequenceBase):
    group_id_sequence = MandatoryGroupIdSelectorAllowedGroups()
    description = OR_JOIN


class TextContentsSequence(SequenceSchema):
    text_sequence = SchemaNode(
        String(),
        title="Text contents criterion"
    )
    title = "Text contents"
    description = OR_JOIN

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[str]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate text filters")


class UploadingUserSequence(SequenceSchema):
    user_id_sequence = MandatoryUserIdSelectorUsersAllowedToSee()
    title = "Uploading users"
    description = OR_JOIN

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[int]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate users")


class DevicesSequence(SequenceSchema):
    device_id_sequence = MandatoryDeviceIdSelector()
    title = "Uploading devices"
    description = OR_JOIN

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[int]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate devices")


# =============================================================================
# Login
# =============================================================================

class LoginSchema(CSRFSchema):
    username = UsernameNode()  # name must match ViewParam.USERNAME
    password = SchemaNode(  # name must match ViewParam.PASSWORD
        String(),
        widget=PasswordWidget(),
        title="Password",
    )
    redirect_url = HiddenStringNode()  # name must match ViewParam.REDIRECT_URL


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
    widget = PasswordWidget()

    def validator(self, node: SchemaNode, value: Any) -> None:
        request = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        user = request.user
        assert user is not None
        if not user.is_password_valid(value):
            raise Invalid(node, "Old password incorrect")


class ChangeOwnPasswordSchema(CSRFSchema):
    old_password = OldUserPasswordCheck()
    new_password = NewPasswordNode()  # name must match ViewParam.NEW_PASSWORD

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
    user_id = HiddenIntegerNode()  # name must match ViewParam.USER_ID
    must_change_password = MustChangePasswordNode()  # match ViewParam.MUST_CHANGE_PASSWORD  # noqa
    new_password = NewPasswordNode()  # name must match ViewParam.NEW_PASSWORD


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
    source = OptionalStringNode(title="Source (e.g. webviewer, tablet, console)")  # must match ViewParam.SOURCE  # noqa
    remote_ip_addr = OptionalStringNode(title="Remote IP address")  # must match ViewParam.REMOTE_IP_ADDR  # noqa
    username = OptionalUserNameSelector()  # must match ViewParam.USERNAME  # noqa
    table_name = AllTasksOptionalSingleTaskSelector()  # must match ViewParam.TABLENAME  # noqa
    server_pk = ServerPkSelector()  # must match ViewParam.SERVER_PK
    truncate = BooleanNode(  # must match ViewParam.TRUNCATE
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
    table_name = AllTasksOptionalSingleTaskSelector()  # must match ViewParam.TABLENAME  # noqa
    server_pk = ServerPkSelector()  # must match ViewParam.SERVER_PK
    hl7_run_id = OptionalIntNode(title="Run ID")  # must match ViewParam.HL7_RUN_ID  # noqa
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
    hl7_run_id = OptionalIntNode(title="Run ID")  # must match ViewParam.HL7_RUN_ID  # noqa
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

class EditTaskFilterWhoSchema(Schema):
    surname = OptionalStringNode(title="Surname")  # must match ViewParam.SURNAME  # noqa
    forename = OptionalStringNode(title="Forename")  # must match ViewParam.FORENAME  # noqa
    dob = SchemaNode(  # must match ViewParam.DOB
        Date(),
        missing=None,
        title="Date of birth",
    )
    sex = SexSelector()  # must match ViewParam.SEX
    id_definitions = IdNumDefinitionSequence()  # must match ViewParam.ID_DEFINITIONS  # noqa


class EditTaskFilterWhenSchema(Schema):
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME


class EditTaskFilterWhatSchema(Schema):
    text_contents = TextContentsSequence()  # must match ViewParam.TEXT_CONTENTS  # noqa
    tasks = AllTasksMultiTaskSelector()  # must match ViewParam.TASKS
    complete_only = BooleanNode(  # must match ViewParam.COMPLETE_ONLY
        default=False,
        title="Only completed tasks?",
    )


class EditTaskFilterAdminSchema(Schema):
    device_ids = DevicesSequence()  # must match ViewParam.DEVICE_IDS
    user_ids = UploadingUserSequence()  # must match ViewParam.USER_IDS
    group_ids = AllowedGroupsSequence()  # must match ViewParam.GROUP_IDS


class EditTaskFilterSchema(CSRFSchema):
    who = EditTaskFilterWhoSchema(  # must match ViewParam.WHO
        title="Who",
        widget=MappingWidget(template="mapping_accordion", open=False)
    )
    what = EditTaskFilterWhatSchema(  # must match ViewParam.WHAT
        title="What",
        widget=MappingWidget(template="mapping_accordion", open=False)
    )
    when = EditTaskFilterWhenSchema(  # must match ViewParam.WHEN
        title="When",
        widget=MappingWidget(template="mapping_accordion", open=False)
    )
    admin = EditTaskFilterAdminSchema(  # must match ViewParam.ADMIN
        title="Administrative criteria",
        widget=MappingWidget(template="mapping_accordion", open=False)
    )

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        # log.critical("EditTaskFilterSchema.after_bind")
        # log.critical("{!r}", self.__dict__)
        # This is pretty nasty. By the time we get here, the Form class has
        # made Field objects, and, I think, called a clone() function on us.
        # Objects like "who" are not in our __dict__ any more. Our __dict__
        # looks like:
        #   {
        #       'typ': <colander.Mapping object at 0x7fd7989b18d0>,
        #       'bindings': {
        #           'open_who': True,
        #           'open_when': True,
        #           'request': ...,
        #       },
        #       '_order': 118,
        #       'children': [
        #           <...CSRFToken object at ... (named csrf)>,
        #           <...EditTaskFilterWhoSchema object at ... (named who)>,
        #           ...
        #       ],
        #       'title': ''
        #   }
        who = next(x for x in self.children if x.name == 'who')
        what = next(x for x in self.children if x.name == 'what')
        when = next(x for x in self.children if x.name == 'when')
        admin = next(x for x in self.children if x.name == 'admin')
        # log.critical("who = {!r}", who)
        # log.critical("who.__dict__ = {!r}", who.__dict__)
        who.widget.open = kw[Binding.OPEN_WHO]
        what.widget.open = kw[Binding.OPEN_WHAT]
        when.widget.open = kw[Binding.OPEN_WHEN]
        admin.widget.open = kw[Binding.OPEN_ADMIN]


class EditTaskFilterForm(InformativeForm):
    def __init__(self, 
                 request: "CamcopsRequest",
                 open_who: bool = False,
                 open_what: bool = False,
                 open_when: bool = False,
                 open_admin: bool = False,
                 **kwargs) -> None:
        schema = EditTaskFilterSchema().bind(request=request,
                                             open_admin=open_admin,
                                             open_what=open_what,
                                             open_when=open_when,
                                             open_who=open_who)
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
    which_idnum = MandatoryWhichIdNumSelector()  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = MandatoryIdNumValue()  # must match ViewParam.IDNUM_VALUE  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME
    all_tasks = BooleanNode(  # match ViewParam.ALL_TASKS
        default=True,
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
    report_id = HiddenStringNode()  # must match ViewParams.REPORT_ID
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

    def __init__(self, *args, **kwargs) -> None:
        values, pv = get_values_and_permissible(DIALECT_CHOICES)
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
# Add/edit/delete users
# =============================================================================

class EditUserSchema(CSRFSchema):
    username = UsernameNode()  # name must match ViewParam.USERNAME and User attribute  # noqa
    fullname = OptionalStringNode(  # name must match ViewParam.FULLNAME and User attribute  # noqa
        title="Full name",
    )
    email = OptionalStringNode(  # name must match ViewParam.EMAIL and User attribute  # noqa
        validator=Email(),
        title="E-mail address",
    )
    may_upload = BooleanNode(  # match ViewParam.MAY_UPLOAD and User attribute
        default=True,
        title="Permitted to upload from a tablet/device",
    )
    may_register_devices = BooleanNode(  # match ViewParam.MAY_REGISTER_DEVICES and User attribute  # noqa
        default=True,
        title="Permitted to register tablet/client devices",
    )
    may_use_webviewer = BooleanNode(  # match ViewParam.MAY_USE_WEBVIEWER and User attribute  # noqa
        default=True,
        title="May log in to web front end",
    )
    view_all_patients_when_unfiltered = BooleanNode(  # match ViewParam.VIEW_ALL_PATIENTS_WHEN_UNFILTERED and User attribute  # noqa
        default=False,
        title="May log in to web front end",
    )
    superuser = BooleanNode(  # match ViewParam.SUPERUSER and User attribute  # noqa
        default=False,
        title="Superuser (CAUTION!)",
    )
    may_dump_data = BooleanNode(  # match ViewParam.MAY_DUMP_DATA and User attribute  # noqa
        default=False,
        title="May perform bulk data dumps",
    )
    may_run_reports = BooleanNode(  # match ViewParam.MAY_RUN_REPORTS and User attribute  # noqa
        default=False,
        title="May run reports (OVERRIDES OTHER VIEW RESTRICTIONS)",
    )
    may_add_notes = BooleanNode(  # match ViewParam.MAY_ADD_NOTES and User attribute  # noqa
        default=False,
        title="May add special notes to tasks",
    )
    must_change_password = MustChangePasswordNode()  # match ViewParam.MUST_CHANGE_PASSWORD and User attribute  # noqa
    group_ids = AllGroupsSequence()  # must match ViewParam.GROUP_IDS


class EditUserForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = EditUserSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Apply"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class AddUserSchema(CSRFSchema):
    username = UsernameNode()  # name must match ViewParam.USERNAME and User attribute  # noqa
    new_password = NewPasswordNode()  # name must match ViewParam.NEW_PASSWORD
    must_change_password = MustChangePasswordNode()  # match ViewParam.MUST_CHANGE_PASSWORD and User attribute  # noqa


class AddUserForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = AddUserSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Add"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class SetUserUploadGroupSchema(CSRFSchema):
    upload_group_id = OptionalGroupIdSelectorUserGroups(  # must match ViewParam.UPLOAD_GROUP_ID  # noqa
        title="Group into which to upload data",
    )


class SetUserUploadGroupForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", user: "User",
                 **kwargs) -> None:
        schema = SetUserUploadGroupSchema().bind(request=request,
                                                 user=user)  # UNUSUAL
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Set"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class DeleteUserSchema(CSRFSchema):
    user_id = HiddenIntegerNode()  # name must match ViewParam.USER_ID
    confirm_1_t = BooleanNode(title="Really delete user?", default=False)
    confirm_2_f = BooleanNode(title="Please untick to confirm", default=True)
    confirm_3_t = BooleanNode(title="Leave ticked to confirm", default=True)
    confirm_4_t = BooleanNode(title="Be really sure; tick here also to "
                                    "confirm", default=False)

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: Any) -> None:
        if ((not value['confirm_1_t']) or
                value['confirm_2_f'] or
                (not value['confirm_3_t']) or
                (not value['confirm_4_t'])):
            raise Invalid(node, "Not fully confirmed")


class DeleteUserForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = DeleteUserSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.DELETE, title="Delete",
                       css_class="btn-danger"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


# =============================================================================
# Add/edit/delete groups
# =============================================================================

class EditGroupSchema(CSRFSchema):
    name = SchemaNode(  # must match ViewParam.NAME
        String(),
        title="Group name",
    )
    description = OptionalStringNode()  # must match ViewParam.DESCRIPTION
    group_ids = AllOtherGroupsSequence()  # must match ViewParam.GROUP_IDS


class EditGroupForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", group: Group,
                 **kwargs) -> None:
        schema = EditGroupSchema().bind(request=request,
                                        group=group)  # UNUSUAL BINDING
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Apply"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class AddGroupSchema(CSRFSchema):
    name = SchemaNode(  # name must match ViewParam.NAME
        String(),
        title="Group name"
    )


class AddGroupForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = AddGroupSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Add"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class DeleteGroupSchema(CSRFSchema):
    group_id = HiddenIntegerNode()  # name must match ViewParam.GROUP_ID
    confirm_1_t = BooleanNode(title="Really delete group?", default=False)
    confirm_2_t = BooleanNode(title="Leave ticked to confirm", default=True)
    confirm_3_f = BooleanNode(title="Please untick to confirm", default=True)
    confirm_4_t = BooleanNode(title="Be really sure; tick here also to "
                                    "confirm", default=False)

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: Any) -> None:
        if ((not value['confirm_1_t']) or
                (not value['confirm_2_t']) or
                value['confirm_3_f'] or
                (not value['confirm_4_t'])):
            raise Invalid(node, "Not fully confirmed")


class DeleteGroupForm(InformativeForm):
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = DeleteGroupSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.DELETE, title="Delete",
                       css_class="btn-danger"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
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
