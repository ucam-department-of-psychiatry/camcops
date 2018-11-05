#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_forms.py

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

**Forms for use by the web front end.**

*COLANDER NODES, NULLS, AND VALIDATION*

- Surprisingly tricky.
- Nodes must be validly intialized with NO USER-DEFINED PARAMETERS to __init__;
  the Deform framework clones them.
- A null appstruct is used to initialize nodes as Forms are created.
  Therefore, the "default" value must be acceptable to the underlying type's
  serialize() function. Note in particular that "default = None" is not
  acceptable to Integer. Having no default is fine, though.
- In general, flexible inheritance is very hard to implement.

- Note that this error:

  .. code-block:: none

    AttributeError: 'EditTaskFilterSchema' object has no attribute 'typ'

  means you have failed to call super().__init__() properly from __init__().

- When creating a schema, its members seem to have to be created in the class
  declaration as class properties, not in __init__().

"""

import logging
from pprint import pformat
from typing import (Any, Callable, Dict, List, Optional,
                    Tuple, Type, TYPE_CHECKING)
import unittest

from cardinal_pythonlib.colander_utils import (
    AllowNoneType,
    BooleanNode,
    DateSelectorNode,
    DateTimeSelectorNode,
    EmailValidatorWithLengthConstraint,
    get_values_and_permissible,
    HiddenIntegerNode,
    HiddenStringNode,
    MandatoryStringNode,
    OptionalIntNode,
    OptionalPendulumNode,
    OptionalStringNode,
    ValidateDangerousOperationNode,
)
from cardinal_pythonlib.deform_utils import (
    DynamicDescriptionsForm,
    InformativeForm,
)
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.sqlalchemy.dialect import SqlaDialectName
from cardinal_pythonlib.sqlalchemy.orm_query import CountStarSpecializedQuery
import colander
from colander import (
    Boolean,
    Date,
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
from deform.form import Button
from deform.widget import (
    CheckboxChoiceWidget,
    CheckedPasswordWidget,
    HiddenWidget,
    MappingWidget,
    PasswordWidget,
    RadioChoiceWidget,
    SelectWidget,
    TextAreaWidget,
    Widget,
)

# import as LITTLE AS POSSIBLE; this is used by lots of modules
# We use some delayed imports here (search for "delayed import")
from .cc_constants import (
    DEFAULT_ROWS_PER_PAGE,
    MINIMUM_PASSWORD_LENGTH,
    USER_NAME_FOR_SYSTEM,
)
from .cc_group import Group
from .cc_idnumdef import (
    IdNumDefinition,
    ID_NUM_VALIDATION_METHOD_CHOICES,
)
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_policy import TokenizedPolicy
from .cc_pyramid import FormAction, ViewArg, ViewParam
from .cc_sqla_coltypes import (
    DATABASE_TITLE_MAX_LEN,
    FILTER_TEXT_MAX_LEN,
    FULLNAME_MAX_LEN,
    GROUP_DESCRIPTION_MAX_LEN,
    GROUP_NAME_MAX_LEN,
    HL7_AA_MAX_LEN,
    HL7_ID_TYPE_MAX_LEN,
    ID_DESCRIPTOR_MAX_LEN,
    USERNAME_MAX_LEN,
)
from .cc_unittest import DemoRequestTestCase

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest
    from .cc_user import User

log = BraceStyleAdapter(logging.getLogger(__name__))

ColanderNullType = type(colander.null)
ValidatorType = Callable[[SchemaNode, Any], None]  # called as v(node, value)

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_CSRF_CHECK = False

if DEBUG_CSRF_CHECK:
    log.warning("Debugging options enabled!")

# =============================================================================
# Constants
# =============================================================================

OR_JOIN_DESCRIPTION = (
    "If you specify more than one, they will be joined with OR."
)


class Binding:
    """
    Keys used for binding dictionaries with Colander schemas (schemata).

    Must match ``kwargs`` of calls to ``bind()`` function of each ``Schema``.
    """
    GROUP = "group"
    OPEN_ADMIN = "open_admin"
    OPEN_WHAT = "open_what"
    OPEN_WHEN = "open_when"
    OPEN_WHO = "open_who"
    REQUEST = "request"
    TRACKER_TASKS_ONLY = "tracker_tasks_only"
    USER = "user"


# =============================================================================
# CSRF
# =============================================================================

class CSRFToken(SchemaNode):
    """
    Node to embed a cross-site request forgery (CSRF) prevention token in a
    form.

    As per http://deformdemo.repoze.org/pyramid_csrf_demo/, modified for a more
    recent Colander API.

    NOTE that this makes use of colander.SchemaNode.bind; this CLONES the
    Schema, and resolves any deferred values by means of the keywords passed to
    bind(). Since the Schema is created at module load time, but since we're
    asking the Schema to know about the request's CSRF values, this is the only
    mechanism
    (https://docs.pylonsproject.org/projects/colander/en/latest/api.html#colander.SchemaNode.bind).

    From http://deform2000.readthedocs.io/en/latest/basics.html:

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

    """  # noqa
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

    You can't put the call to ``bind()`` at the end of ``__init__()``, because
    ``bind()`` calls ``clone()`` with no arguments and ``clone()`` ends up
    calling ``__init__()```...
    """
    csrf = CSRFToken()  # name must match ViewParam.CSRF_TOKEN


# =============================================================================
# Specialized Form classes
# =============================================================================

class SimpleSubmitForm(InformativeForm):
    """
    Form with a simple "submit" button.
    """
    def __init__(self,
                 schema_class: Type[Schema],
                 submit_title: str,
                 request: "CamcopsRequest",
                 **kwargs):
        """
        Args:
            schema_class:
                class of the Colander :class:`Schema` to use as this form's
                schema
            submit_title:
                title (text) to be used for the "submit" button
            request:
                :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        schema = schema_class().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT,
                            title=submit_title)],
            **kwargs
        )


class ApplyCancelForm(InformativeForm):
    """
    Form with "apply" and "cancel" buttons.
    """
    def __init__(self,
                 schema_class: Type[Schema],
                 request: "CamcopsRequest",
                 **kwargs):
        schema = schema_class().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Apply"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class AddCancelForm(InformativeForm):
    """
    Form with "add" and "cancel" buttons.
    """
    def __init__(self,
                 schema_class: Type[Schema],
                 request: "CamcopsRequest",
                 **kwargs):
        schema = schema_class().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=FormAction.SUBMIT, title="Add"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class DangerousForm(DynamicDescriptionsForm):
    """
    Form with one "submit" button (with user-specifiable title text and action
    name), in a CSS class indicating that it's a dangerous operation, plus a
    "Cancel" button.
    """
    def __init__(self,
                 schema_class: Type[Schema],
                 submit_action: str,
                 submit_title: str,
                 request: "CamcopsRequest",
                 **kwargs):
        schema = schema_class().bind(request=request)
        super().__init__(
            schema,
            buttons=[
                Button(name=submit_action, title=submit_title,
                       css_class="btn-danger"),
                Button(name=FormAction.CANCEL, title="Cancel"),
            ],
            **kwargs
        )


class DeleteCancelForm(DangerousForm):
    """
    Form with a "delete" button (visually marked as dangerous) and a "cancel"
    button.
    """
    def __init__(self,
                 schema_class: Type[Schema],
                 request: "CamcopsRequest",
                 **kwargs):
        super().__init__(
            schema_class=schema_class,
            submit_action=FormAction.DELETE,
            submit_title="Delete",
            request=request,
            **kwargs
        )


# =============================================================================
# Specialized SchemaNode classes
# =============================================================================

class OptionalSingleTaskSelector(OptionalStringNode):
    """
    Node to pick one task type.
    """
    title = "Task type"

    def __init__(self, *args, tracker_tasks_only: bool = False,
                 **kwargs) -> None:
        """
        Args:
            tracker_tasks_only: restrict the choices to tasks that offer
                trackers.
        """
        self.tracker_tasks_only = tracker_tasks_only
        self.widget = None  # type: Widget
        self.validator = None  # type: ValidatorType
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        if Binding.TRACKER_TASKS_ONLY in kw:
            self.tracker_tasks_only = kw[Binding.TRACKER_TASKS_ONLY]
        values, pv = get_values_and_permissible(self.get_task_choices(),
                                                True, "[Any]")
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    def get_task_choices(self) -> List[Tuple[str, str]]:
        from .cc_task import Task  # delayed import
        choices = []  # type: List[Tuple[str, str]]
        for tc in Task.all_subclasses_by_shortname():
            if self.tracker_tasks_only and not tc.provides_trackers:
                continue
            choices.append((tc.tablename, tc.shortname))
        return choices


class MultiTaskSelector(SchemaNode):
    """
    Node to select multiple task types.
    """
    schema_type = Set
    default = ""
    missing = ""
    title = "Task type(s)"
    description = (
        "If none are selected, all task types will be offered. " +
        OR_JOIN_DESCRIPTION
    )

    def __init__(self, *args, tracker_tasks_only: bool = False,
                 minimum_number: int = 0, **kwargs) -> None:
        self.tracker_tasks_only = tracker_tasks_only
        self.minimum_number = minimum_number
        self.widget = None  # type: Widget
        self.validator = None  # type: object
        super().__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def after_bind(self, node: SchemaNode, kw: Dict[str, Any]) -> None:
        if Binding.TRACKER_TASKS_ONLY in kw:
            self.tracker_tasks_only = kw[Binding.TRACKER_TASKS_ONLY]
        values, pv = get_values_and_permissible(self.get_task_choices())
        self.widget = CheckboxChoiceWidget(values=values)
        self.validator = Length(min=self.minimum_number)

    def get_task_choices(self) -> List[Tuple[str, str]]:
        from .cc_task import Task  # delayed import
        choices = []  # type: List[Tuple[str, str]]
        for tc in Task.all_subclasses_by_shortname():
            if self.tracker_tasks_only and not tc.provides_trackers:
                continue
            choices.append((tc.tablename, tc.shortname))
        return choices


class MandatoryWhichIdNumSelector(SchemaNode):
    """
    Node to enforce the choice of a single ID number type (e.g. "NHS number"
    or "study Blah ID number").
    """
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
        values = []  # type: List[Tuple[Optional[int], str]]
        for iddef in req.idnum_definitions:
            values.append((iddef.which_idnum, iddef.description))
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


class LinkingIdNumSelector(MandatoryWhichIdNumSelector):
    """
    Convenience node: pick a single ID number, with title/description
    indicating that it's the ID number to link on.
    """
    title = "Linking ID number"
    description = "Which ID number to link on?"


class OptionalWhichIdNumSelector(MandatoryWhichIdNumSelector):
    """
    Node to select (optionally) an ID number type.
    """
    default = None
    missing = None

    def __init__(self, *args, **kwargs):
        self.allow_none = True
        super().__init__(*args, **kwargs)

    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(Integer())


class MandatoryIdNumValue(SchemaNode):
    """
    Mandatory node to capture an ID number value.
    """
    schema_type = Integer
    title = "ID# value"
    validator = Range(min=0)


class OptionalIdNumValue(MandatoryIdNumValue):
    """
    Optional node to capture an ID number value.
    """
    default = None
    missing = None

    @staticmethod
    def schema_type() -> SchemaType:
        return AllowNoneType(Integer())


class MandatoryIdNumNode(MappingSchema):
    """
    Mandatory node to capture an ID number type and the associated actual
    ID number (value).
    """
    which_idnum = MandatoryWhichIdNumSelector()  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = MandatoryIdNumValue()  # must match ViewParam.IDNUM_VALUE
    title = "ID number"


class IdNumSequenceAnyCombination(SequenceSchema):
    """
    Sequence to capture multiple ID numbers (as type/value pairs).
    """
    idnum_sequence = MandatoryIdNumNode()
    title = "ID numbers"

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[Dict[str, int]]) -> None:
        assert isinstance(value, list)
        list_of_lists = [(x[ViewParam.WHICH_IDNUM], x[ViewParam.IDNUM_VALUE])
                         for x in value]
        if len(list_of_lists) != len(set(list_of_lists)):
            raise Invalid(node, "You have specified duplicate ID definitions")


class IdNumSequenceUniquePerWhichIdnum(SequenceSchema):
    """
    Sequence to capture multiple ID numbers (as type/value pairs) but with only
    up to one per ID number type.
    """
    idnum_sequence = MandatoryIdNumNode()
    title = "ID numbers"

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[Dict[str, int]]) -> None:
        assert isinstance(value, list)
        which_idnums = [x[ViewParam.WHICH_IDNUM] for x in value]
        if len(which_idnums) != len(set(which_idnums)):
            raise Invalid(
                node,
                "You have specified >1 value for one ID number type")


SEX_CHOICES = [("F", "F"), ("M", "M"), ("X", "X")]


class OptionalSexSelector(OptionalStringNode):
    """
    Optional node to choose sex.
    """
    title = "Sex"

    def __init__(self, *args, **kwargs) -> None:
        values, pv = get_values_and_permissible(SEX_CHOICES, True, "Any")
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


class MandatorySexSelector(MandatoryStringNode):
    """
    Mandatory node to choose sex.
    """
    title = "Sex"

    def __init__(self, *args, **kwargs) -> None:
        values, pv = get_values_and_permissible(SEX_CHOICES)
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


class MandatoryUserIdSelectorUsersAllowedToSee(SchemaNode):
    """
    Mandatory node to choose a user, from the users that the requesting user
    is allowed to see.
    """
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
            my_allowed_group_ids = user.ids_of_groups_user_may_see
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
    """
    Optional node to select a username, from all possible users.
    """
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
    """
    Mandatory node to select a client device ID.
    """
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
    """
    Optional node to request an integer, marked as a server PK.
    """
    title = "Server PK"


class StartPendulumSelector(OptionalPendulumNode):
    """
    Optional node to select a start date/time.
    """
    title = "Start date/time"


class EndPendulumSelector(OptionalPendulumNode):
    """
    Optional node to select an end date/time.
    """
    title = "End date/time"


class StartDateTimeSelector(DateTimeSelectorNode):
    """
    Optional node to select a start date/time (in UTC).
    """
    title = "Start date/time (UTC)"


class EndDateTimeSelector(DateTimeSelectorNode):
    """
    Optional node to select an end date/time (in UTC).
    """
    title = "End date/time (UTC)"


class StartDateSelector(DateSelectorNode):
    """
    Optional node to select a start date (in UTC).
    """
    title = "Start date (UTC)"


class EndDateSelector(DateSelectorNode):
    """
    Optional node to select an end date (in UTC).
    """
    title = "End date (UTC)"


class RowsPerPageSelector(SchemaNode):
    """
    Node to select how many rows per page are shown.
    """
    _choices = ((10, "10"), (25, "25"), (50, "50"), (100, "100"))

    schema_type = Integer
    default = DEFAULT_ROWS_PER_PAGE
    title = "Items to show per page"
    widget = RadioChoiceWidget(values=_choices)
    validator = OneOf(list(x[0] for x in _choices))


class TaskTrackerOutputTypeSelector(SchemaNode):
    """
    Node to select the output format for a tracker.
    """
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
    """
    Node to select the output format for a report.
    """
    _choices = ((ViewArg.HTML, "HTML"),
                (ViewArg.TSV, "TSV (tab-separated values)"))

    schema_type = String
    default = ViewArg.HTML
    missing = ViewArg.HTML
    title = "View as"
    widget = RadioChoiceWidget(values=_choices)
    validator = OneOf(list(x[0] for x in _choices))


class DumpTypeSelector(SchemaNode):
    """
    Node to select the filtering method for a data dump.
    """
    _choices = (
        (ViewArg.EVERYTHING, "Everything"),
        (ViewArg.USE_SESSION_FILTER, "Use the session filter settings"),
        (ViewArg.SPECIFIC_TASKS_GROUPS, "Specify tasks/groups manually "
                                        "(see below)")
    )

    schema_type = String
    default = ViewArg.EVERYTHING
    missing = ViewArg.EVERYTHING
    title = "Dump method"
    widget = RadioChoiceWidget(values=_choices)
    validator = OneOf(list(x[0] for x in _choices))


class UsernameNode(SchemaNode):
    """
    Node to enter a username.
    """
    schema_type = String
    title = "Username"
    _length_validator = Length(1, USERNAME_MAX_LEN)

    def validator(self, node: SchemaNode, value: Any) -> None:
        if value == USER_NAME_FOR_SYSTEM:
            raise Invalid(node, "Cannot use system username {!r}".format(
                USER_NAME_FOR_SYSTEM))
        self._length_validator(node, value)


class MustChangePasswordNode(SchemaNode):
    """
    Boolean node: must the user change their password?
    """
    schema_type = Boolean
    label = "User must change password at next login"
    title = "Must change password at next login?"
    default = True
    missing = True


class NewPasswordNode(SchemaNode):
    """
    Node to enter a new password.
    """
    schema_type = String
    validator = Length(min=MINIMUM_PASSWORD_LENGTH)
    widget = CheckedPasswordWidget()
    title = "New password"
    description = "Type the new password and confirm it"


class MandatoryGroupIdSelectorAllGroups(SchemaNode):
    """
    Offers a picklist of groups from ALL POSSIBLE GROUPS.
    Used by superusers: "add user to any group".
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


class MandatoryGroupIdSelectorAdministeredGroups(SchemaNode):
    """
    Offers a picklist of groups from GROUPS ADMINISTERED BY REQUESTOR.
    Used by groupadmins: "add user to one of my groups".
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
        administered_group_ids = req.user.ids_of_groups_user_is_admin_for
        groups = dbsession.query(Group).order_by(Group.name)
        values = [(g.id, g.name) for g in groups
                  if g.id in administered_group_ids]
        values, pv = get_values_and_permissible(values)
        self.widget = SelectWidget(values=values)
        self.validator = OneOf(pv)

    @staticmethod
    def schema_type() -> SchemaType:
        return Integer()


class MandatoryGroupIdSelectorOtherGroups(SchemaNode):
    """
    Offers a picklist of groups THAT ARE NOT THE SPECIFIED GROUP (as specified
    in ``kw[Binding.GROUP]``).
    Used by superusers: "which other groups can this group see?"
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
    Used for: "which of your groups do you want to upload into?"
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
    Used for "which do you want to upload into?". Optional.
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
    """
    Sequence schema to capture zero or more non-duplicate groups.
    """
    title = "Groups"

    def __init__(self, *args, minimum_number: int = 0, **kwargs) -> None:
        self.minimum_number = minimum_number
        super().__init__(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def validator(self,
                  node: SchemaNode,
                  value: List[int]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate groups")
        if len(value) < self.minimum_number:
            raise Invalid(node, "You must specify at least {} group(s)".format(
                self.minimum_number))


class AllGroupsSequence(GroupsSequenceBase):
    """
    Sequence to offer a choice of all possible groups.

    Typical use: superuser assigns group memberships to a user.
    """
    group_id_sequence = MandatoryGroupIdSelectorAllGroups()


class AdministeredGroupsSequence(GroupsSequenceBase):
    """
    Sequence to offer a choice of the groups administered by the requestor.

    Typical use: (non-superuser) group administrator assigns group memberships
    to a user.
    """
    group_id_sequence = MandatoryGroupIdSelectorAdministeredGroups()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, minimum_number=1, **kwargs)


class AllOtherGroupsSequence(GroupsSequenceBase):
    """
    Sequence to offer a choice of all possible OTHER groups (as determined
    relative to the group specified in ``kw[Binding.GROUP]``).

    Typical use: superuser assigns group permissions to another group.
    """
    group_id_sequence = MandatoryGroupIdSelectorOtherGroups()


class AllowedGroupsSequence(GroupsSequenceBase):
    """
    Sequence to offer a choice of all the groups the user is allowed to see.
    """
    group_id_sequence = MandatoryGroupIdSelectorAllowedGroups()
    description = OR_JOIN_DESCRIPTION


class TextContentsSequence(SequenceSchema):
    """
    Sequence to capture multiple pieces of text (representing text contents
    for a task filter).
    """
    text_sequence = SchemaNode(
        String(),
        title="Text contents criterion",
        validator=Length(0, FILTER_TEXT_MAX_LEN)
    )
    title = "Text contents"
    description = OR_JOIN_DESCRIPTION

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[str]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate text filters")


class UploadingUserSequence(SequenceSchema):
    """
    Sequence to capture multiple users (for task filters: "uploaded by one of
    the following users...").
    """
    user_id_sequence = MandatoryUserIdSelectorUsersAllowedToSee()
    title = "Uploading users"
    description = OR_JOIN_DESCRIPTION

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[int]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate users")


class DevicesSequence(SequenceSchema):
    """
    Sequence to capture multiple client devices (for task filters: "uploaded by
    one of the following devices...").
    """
    device_id_sequence = MandatoryDeviceIdSelector()
    title = "Uploading devices"
    description = OR_JOIN_DESCRIPTION

    # noinspection PyMethodMayBeStatic
    def validator(self, node: SchemaNode, value: List[int]) -> None:
        assert isinstance(value, list)
        if len(value) != len(set(value)):
            raise Invalid(node, "You have specified duplicate devices")


class SortTsvByHeadingsNode(SchemaNode):
    """
    Boolean node: sort TSV files by column name?
    """
    schema_type = Boolean
    label = "Sort TSV files by heading (column) names?"
    title = "Sort columns?"
    default = False
    missing = False


DIALECT_CHOICES = (
    # http://docs.sqlalchemy.org/en/latest/dialects/
    (SqlaDialectName.MYSQL, "MySQL"),
    (SqlaDialectName.MSSQL, "Microsoft SQL Server"),
    (SqlaDialectName.ORACLE, "Oracle [WILL NOT WORK]"),
    # ... Oracle doesn't work; SQLAlchemy enforces the Oracle rule of a 30-
    # character limit for identifiers, only relaxed to 128 characters in
    # Oracle 12.2 (March 2017).
    (SqlaDialectName.FIREBIRD, "Firebird"),
    (SqlaDialectName.POSTGRES, "PostgreSQL"),
    (SqlaDialectName.SQLITE, "SQLite"),
    (SqlaDialectName.SYBASE, "Sybase"),
)


class DatabaseDialectSelector(SchemaNode):
    """
    Node to choice an SQL dialect (for viewing DDL).
    """
    schema_type = String
    default = SqlaDialectName.MYSQL
    missing = SqlaDialectName.MYSQL
    title = "SQL dialect to use (not all may be valid)"

    def __init__(self, *args, **kwargs) -> None:
        values, pv = get_values_and_permissible(DIALECT_CHOICES)
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


SQLITE_CHOICES = (
    # http://docs.sqlalchemy.org/en/latest/dialects/
    (ViewArg.SQLITE, "Binary SQLite database"),
    (ViewArg.SQL, "SQL text to create SQLite database"),
)


class SqliteSelector(SchemaNode):
    """
    Node to select a way of downloading an SQLite database.
    """
    schema_type = String
    default = ViewArg.SQLITE
    missing = ViewArg.SQLITE
    title = "Database download method"

    def __init__(self, *args, **kwargs) -> None:
        values, pv = get_values_and_permissible(SQLITE_CHOICES)
        self.widget = RadioChoiceWidget(values=values)
        self.validator = OneOf(pv)
        super().__init__(*args, **kwargs)


class IncludeBlobsNode(SchemaNode):
    """
    Boolean node: should BLOBs be included (for downloads)?
    """
    schema_type = Boolean
    default = False
    missing = False
    title = "Include BLOBs?"
    label = "Include binary large objects (BLOBs)? WARNING: may be large"


class PolicyNode(MandatoryStringNode):
    """
    Node to capture a CamCOPS ID number policy, and make sure it is
    syntactically valid.
    """
    def validator(self, node: SchemaNode, value: Any) -> None:
        if not isinstance(value, str):
            # unlikely!
            raise Invalid(node, "Not a string")
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        policy = TokenizedPolicy(value)
        if not policy.is_syntactically_valid():
            raise Invalid(node, "Syntactically invalid policy")
        if not policy.is_valid_from_req(req):
            raise Invalid(node, "Invalid policy (have you referred to "
                                "non-existent ID numbers?")


class IdDefinitionDescriptionNode(SchemaNode):
    """
    Node to capture the description of an ID number type.
    """
    schema_type = String
    title = "Full description (e.g. “NHS number”)"
    validator = Length(1, ID_DESCRIPTOR_MAX_LEN)


class IdDefinitionShortDescriptionNode(SchemaNode):
    """
    Node to capture the short description of an ID number type.
    """
    schema_type = String
    title = "Short description (e.g. “NHS#”)"
    description = "Try to keep it very short!"
    validator = Length(1, ID_DESCRIPTOR_MAX_LEN)


class IdValidationMethodNode(OptionalStringNode):
    """
    Node to choose a build-in ID number validation method.
    """
    title = "Validation method"
    description = "Built-in CamCOPS ID number validation method"
    widget = SelectWidget(values=ID_NUM_VALIDATION_METHOD_CHOICES)
    validator = OneOf(list(x[0] for x in ID_NUM_VALIDATION_METHOD_CHOICES))


class Hl7AssigningAuthorityNode(OptionalStringNode):
    """
    Optional node to capture the name of an HL7 Assigning Authority.
    """
    title = "HL7 Assigning Authority"
    description = (
        "For HL7 messaging: "
        "HL7 Assigning Authority for ID number (unique name of the "
        "system/organization/agency/department that creates the data)."
    )
    validator = Length(0, HL7_AA_MAX_LEN)


class Hl7IdTypeNode(OptionalStringNode):
    """
    Optional node to capture the name of an HL7 Identifier Type code.
    """
    title = "HL7 Identifier Type"
    description = (
        "For HL7 messaging: "
        "HL7 Identifier Type code: ‘a code corresponding to the type "
        "of identifier. In some cases, this code may be used as a "
        "qualifier to the “Assigning Authority” component.’"
    )
    validator = Length(0, HL7_ID_TYPE_MAX_LEN)


class HardWorkConfirmationSchema(CSRFSchema):
    """
    Schema to make it hard to do something. We require a pattern of yes/no
    answers before we will proceed.
    """
    confirm_1_t = BooleanNode(title="Really?", default=False)
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


# =============================================================================
# Login
# =============================================================================

class LoginSchema(CSRFSchema):
    """
    Schema to capture login details.
    """
    username = UsernameNode()  # name must match ViewParam.USERNAME
    password = SchemaNode(  # name must match ViewParam.PASSWORD
        String(),
        widget=PasswordWidget(),
        title="Password",
    )
    redirect_url = HiddenStringNode()  # name must match ViewParam.REDIRECT_URL


class LoginForm(InformativeForm):
    """
    Form to capture login details.
    """
    def __init__(self,
                 request: "CamcopsRequest",
                 autocomplete_password: bool = True,
                 **kwargs) -> None:
        """
        Args:
            autocomplete_password:
                suggest to the browser that it's OK to store the password for
                autocompletion? Note that browsers may ignore this.
        """
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
    """
    Schema to capture an old password (for when a password is being changed).
    """
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
    """
    Schema to change one's own password.
    """
    old_password = OldUserPasswordCheck()
    new_password = NewPasswordNode()  # name must match ViewParam.NEW_PASSWORD

    def __init__(self, *args, must_differ: bool = True, **kwargs):
        """
        Args:
            must_differ:
                must the new password be different from the old one?
        """
        self.must_differ = must_differ
        super().__init__(*args, **kwargs)

    def validator(self, node: SchemaNode, value: Any) -> None:
        if self.must_differ and value['new_password'] == value['old_password']:
            raise Invalid(node, "New password must differ from old")


class ChangeOwnPasswordForm(InformativeForm):
    """
    Form to change one's own password.
    """
    def __init__(self, request: "CamcopsRequest",
                 must_differ: bool = True,
                 **kwargs) -> None:
        """
        Args:
            must_differ:
                must the new password be different from the old one?
        """
        schema = ChangeOwnPasswordSchema(must_differ=must_differ).\
            bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT,
                            title=CHANGE_PASSWORD_TITLE)],
            **kwargs
        )


class ChangeOtherPasswordSchema(CSRFSchema):
    """
    Schema to change another user's password.
    """
    user_id = HiddenIntegerNode()  # name must match ViewParam.USER_ID
    must_change_password = MustChangePasswordNode()  # match ViewParam.MUST_CHANGE_PASSWORD  # noqa
    new_password = NewPasswordNode()  # name must match ViewParam.NEW_PASSWORD


class ChangeOtherPasswordForm(SimpleSubmitForm):
    """
    Form to change another user's password.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=ChangeOtherPasswordSchema,
                         submit_title=CHANGE_PASSWORD_TITLE,
                         request=request, **kwargs)


# =============================================================================
# Offer/agree terms
# =============================================================================

class OfferTermsSchema(CSRFSchema):
    """
    Schema to offer terms and ask the user to accept them.
    """
    pass


class OfferTermsForm(SimpleSubmitForm):
    """
    Form to offer terms and ask the user to accept them.
    """
    def __init__(self,
                 request: "CamcopsRequest",
                 agree_button_text: str,
                 **kwargs) -> None:
        """
        Args:
            agree_button_text:
                text for the "agree" button
        """
        super().__init__(schema_class=OfferTermsSchema,
                         submit_title=agree_button_text,
                         request=request, **kwargs)


# =============================================================================
# View audit trail
# =============================================================================

class AuditTrailSchema(CSRFSchema):
    """
    Schema to filter audit trail entries.
    """
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME
    source = OptionalStringNode(title="Source (e.g. webviewer, tablet, console)")  # must match ViewParam.SOURCE  # noqa
    remote_ip_addr = OptionalStringNode(title="Remote IP address")  # must match ViewParam.REMOTE_IP_ADDR  # noqa
    username = OptionalUserNameSelector()  # must match ViewParam.USERNAME  # noqa
    table_name = OptionalSingleTaskSelector()  # must match ViewParam.TABLENAME  # noqa
    server_pk = ServerPkSelector()  # must match ViewParam.SERVER_PK
    truncate = BooleanNode(  # must match ViewParam.TRUNCATE
        default=True,
        title="Truncate details for easy viewing",
    )


class AuditTrailForm(SimpleSubmitForm):
    """
    Form to filter and then view audit trail entries.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=AuditTrailSchema,
                         submit_title="View audit trail",
                         request=request, **kwargs)


# =============================================================================
# View HL7 message log
# =============================================================================

class HL7MessageLogSchema(CSRFSchema):
    """
    Schema to filter HL7 message logs.
    """
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE
    table_name = OptionalSingleTaskSelector()  # must match ViewParam.TABLENAME  # noqa
    server_pk = ServerPkSelector()  # must match ViewParam.SERVER_PK
    hl7_run_id = OptionalIntNode(title="Run ID")  # must match ViewParam.HL7_RUN_ID  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME


class HL7MessageLogForm(SimpleSubmitForm):
    """
    Form to filter and then view HL7 message logs.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=HL7MessageLogSchema,
                         submit_title="View HL7 message log",
                         request=request, **kwargs)


# =============================================================================
# View HL7 run log
# =============================================================================

class HL7RunLogSchema(CSRFSchema):
    """
    Schema to filter HL7 run logs.
    """
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE
    hl7_run_id = OptionalIntNode(title="Run ID")  # must match ViewParam.HL7_RUN_ID  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME


class HL7RunLogForm(SimpleSubmitForm):
    """
    Form to filter and then view HL7 run logs.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=HL7RunLogSchema,
                         submit_title="View HL7 run log",
                         request=request, **kwargs)


# =============================================================================
# Task filters
# =============================================================================

class EditTaskFilterWhoSchema(Schema):
    """
    Schema to edit the "who" parts of a task filter.
    """
    surname = OptionalStringNode(title="Surname")  # must match ViewParam.SURNAME  # noqa
    forename = OptionalStringNode(title="Forename")  # must match ViewParam.FORENAME  # noqa
    dob = SchemaNode(  # must match ViewParam.DOB
        Date(),
        missing=None,
        title="Date of birth",
    )
    sex = OptionalSexSelector()  # must match ViewParam.SEX
    id_references = IdNumSequenceAnyCombination(
        description=OR_JOIN_DESCRIPTION)  # must match ViewParam.ID_REFERENCES  # noqa


class EditTaskFilterWhenSchema(Schema):
    """
    Schema to edit the "when" parts of a task filter.
    """
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME


class EditTaskFilterWhatSchema(Schema):
    """
    Schema to edit the "what" parts of a task filter.
    """
    text_contents = TextContentsSequence()  # must match ViewParam.TEXT_CONTENTS  # noqa
    complete_only = BooleanNode(  # must match ViewParam.COMPLETE_ONLY
        default=False,
        title="Only completed tasks?",
    )
    tasks = MultiTaskSelector()  # must match ViewParam.TASKS


class EditTaskFilterAdminSchema(Schema):
    """
    Schema to edit the "admin" parts of a task filter.
    """
    device_ids = DevicesSequence()  # must match ViewParam.DEVICE_IDS
    user_ids = UploadingUserSequence()  # must match ViewParam.USER_IDS
    group_ids = AllowedGroupsSequence()  # must match ViewParam.GROUP_IDS


class EditTaskFilterSchema(CSRFSchema):
    """
    Schema to edit a task filter.
    """
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
        # log.debug("EditTaskFilterSchema.after_bind")
        # log.debug("{!r}", self.__dict__)
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
        # log.debug("who = {!r}", who)
        # log.debug("who.__dict__ = {!r}", who.__dict__)
        who.widget.open = kw[Binding.OPEN_WHO]
        what.widget.open = kw[Binding.OPEN_WHAT]
        when.widget.open = kw[Binding.OPEN_WHEN]
        admin.widget.open = kw[Binding.OPEN_ADMIN]


class EditTaskFilterForm(InformativeForm):
    """
    Form to edit a task filter.
    """
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
    """
    Schema to edit the number of rows per page, for the task view.
    """
    rows_per_page = RowsPerPageSelector()  # must match ViewParam.ROWS_PER_PAGE


class TasksPerPageForm(InformativeForm):
    """
    Form to edit the number of tasks per page, for the task view.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        schema = TasksPerPageSchema().bind(request=request)
        super().__init__(
            schema,
            buttons=[Button(name=FormAction.SUBMIT_TASKS_PER_PAGE,
                            title="Set n/page")],
            **kwargs
        )


class RefreshTasksSchema(CSRFSchema):
    """
    Schema for a "refresh tasks" button.
    """
    pass


class RefreshTasksForm(InformativeForm):
    """
    Form for a "refresh tasks" button.
    """
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
    """
    Schema to select a tracker or CTV.
    """
    which_idnum = MandatoryWhichIdNumSelector()  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = MandatoryIdNumValue()  # must match ViewParam.IDNUM_VALUE  # noqa
    start_datetime = StartPendulumSelector()  # must match ViewParam.START_DATETIME  # noqa
    end_datetime = EndPendulumSelector()  # must match ViewParam.END_DATETIME
    all_tasks = BooleanNode(  # match ViewParam.ALL_TASKS
        default=True,
        title="Use all eligible task types?",
    )
    tasks = MultiTaskSelector()  # must match ViewParam.TASKS
    # tracker_tasks_only will be set via the binding
    viewtype = TaskTrackerOutputTypeSelector()  # must match ViewParams.VIEWTYPE  # noqa


class ChooseTrackerForm(InformativeForm):
    """
    Form to select a tracker or CTV.
    """
    def __init__(self, request: "CamcopsRequest",
                 as_ctv: bool, **kwargs) -> None:
        """
        Args:
            as_ctv: CTV, not tracker?
        """
        schema = ChooseTrackerSchema().bind(request=request,
                                            tracker_tasks_only=not as_ctv)
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
    """
    Schema to embed a report type (ID) and output format (view type).
    """
    viewtype = ReportOutputTypeSelector()  # must match ViewParam.VIEWTYPE
    report_id = HiddenStringNode()  # must match ViewParam.REPORT_ID
    # Specific forms may inherit from this.


class ReportParamForm(SimpleSubmitForm):
    """
    Form to view a specific report. Often derived from, to configure the report
    in more detail.
    """
    def __init__(self, request: "CamcopsRequest",
                 schema_class: Type[ReportParamSchema], **kwargs) -> None:
        super().__init__(schema_class=schema_class,
                         submit_title="View report",
                         request=request, **kwargs)


# =============================================================================
# View DDL
# =============================================================================

class ViewDdlSchema(CSRFSchema):
    """
    Schema to choose how to view DDL.
    """
    dialect = DatabaseDialectSelector()  # must match ViewParam.DIALECT


class ViewDdlForm(SimpleSubmitForm):
    """
    Form to choose how to view DDL (and then view it).
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=ViewDdlSchema,
                         submit_title="View DDL",
                         request=request, **kwargs)


# =============================================================================
# Add/edit/delete users
# =============================================================================

class UserGroupPermissionsGroupAdminSchema(CSRFSchema):
    """
    Edit group-specific permissions for a user. For group administrators.
    """
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
        title="May view (browse) records from all patients when no patient "
              "filter set",
    )
    may_dump_data = BooleanNode(  # match ViewParam.MAY_DUMP_DATA and User attribute  # noqa
        default=False,
        title="May perform bulk data dumps",
    )
    may_run_reports = BooleanNode(  # match ViewParam.MAY_RUN_REPORTS and User attribute  # noqa
        default=False,
        title="May run reports",
    )
    may_add_notes = BooleanNode(  # match ViewParam.MAY_ADD_NOTES and User attribute  # noqa
        default=False,
        title="May add special notes to tasks",
    )


class UserGroupPermissionsFullSchema(UserGroupPermissionsGroupAdminSchema):
    """
    Edit group-specific permissions for a user. For superusers; includes the
    option to make the user a groupadmin.
    """
    groupadmin = BooleanNode(  # match ViewParam.GROUPADMIN and User attribute  # noqa
        default=True,
        title="User is a privileged group administrator for this group",
    )


class EditUserGroupAdminSchema(CSRFSchema):
    """
    Schema to edit a user. Version for group administrators.
    """
    username = UsernameNode()  # name must match ViewParam.USERNAME and User attribute  # noqa
    fullname = OptionalStringNode(  # name must match ViewParam.FULLNAME and User attribute  # noqa
        title="Full name",
        validator=Length(0, FULLNAME_MAX_LEN)
    )
    email = OptionalStringNode(  # name must match ViewParam.EMAIL and User attribute  # noqa
        validator=EmailValidatorWithLengthConstraint(),
        title="E-mail address",
    )
    must_change_password = MustChangePasswordNode()  # match ViewParam.MUST_CHANGE_PASSWORD and User attribute  # noqa
    group_ids = AdministeredGroupsSequence()  # must match ViewParam.GROUP_IDS


class EditUserFullSchema(EditUserGroupAdminSchema):
    """
    Schema to edit a user. Version for superusers; can also make the user a
    superuser.
    """
    superuser = BooleanNode(  # match ViewParam.SUPERUSER and User attribute  # noqa
        default=False,
        title="Superuser (CAUTION!)",
    )
    group_ids = AllGroupsSequence()  # must match ViewParam.GROUP_IDS


class EditUserFullForm(ApplyCancelForm):
    """
    Form to edit a user. Full version for superusers.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=EditUserFullSchema,
                         request=request, **kwargs)


class EditUserGroupAdminForm(ApplyCancelForm):
    """
    Form to edit a user. Version for group administrators.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=EditUserGroupAdminSchema,
                         request=request, **kwargs)


class EditUserGroupPermissionsFullForm(ApplyCancelForm):
    """
    Form to edit a user's permissions within a group. Version for superusers.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=UserGroupPermissionsFullSchema,
                         request=request, **kwargs)


class EditUserGroupMembershipGroupAdminForm(ApplyCancelForm):
    """
    Form to edit a user's permissions within a group. Version for group
    administrators.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=UserGroupPermissionsGroupAdminSchema,
                         request=request, **kwargs)


class AddUserSuperuserSchema(CSRFSchema):
    """
    Schema to add a user. Version for superusers.
    """
    username = UsernameNode()  # name must match ViewParam.USERNAME and User attribute  # noqa
    new_password = NewPasswordNode()  # name must match ViewParam.NEW_PASSWORD
    must_change_password = MustChangePasswordNode()  # match ViewParam.MUST_CHANGE_PASSWORD and User attribute  # noqa
    group_ids = AllGroupsSequence()  # must match ViewParam.GROUP_IDS


class AddUserGroupadminSchema(AddUserSuperuserSchema):
    """
    Schema to add a user. Version for group administrators.
    """
    group_ids = AdministeredGroupsSequence()  # must match ViewParam.GROUP_IDS


class AddUserSuperuserForm(AddCancelForm):
    """
    Form to add a user. Version for superusers.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=AddUserSuperuserSchema,
                         request=request, **kwargs)


class AddUserGroupadminForm(AddCancelForm):
    """
    Form to add a user. Version for group administrators.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=AddUserGroupadminSchema,
                         request=request, **kwargs)


class SetUserUploadGroupSchema(CSRFSchema):
    """
    Schema to choose the group into which a user uploads.
    """
    upload_group_id = OptionalGroupIdSelectorUserGroups(  # must match ViewParam.UPLOAD_GROUP_ID  # noqa
        title="Group into which to upload data",
        description="Pick a group from those to which the user belongs"
    )


class SetUserUploadGroupForm(InformativeForm):
    """
    Form to choose the group into which a user uploads.
    """
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


class DeleteUserSchema(HardWorkConfirmationSchema):
    """
    Schema to delete a user.
    """
    user_id = HiddenIntegerNode()  # name must match ViewParam.USER_ID
    danger = ValidateDangerousOperationNode()


class DeleteUserForm(DeleteCancelForm):
    """
    Form to delete a user.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=DeleteUserSchema,
                         request=request, **kwargs)


# =============================================================================
# Add/edit/delete groups
# =============================================================================

class EditGroupSchema(CSRFSchema):
    """
    Schema to edit a group.
    """
    group_id = HiddenIntegerNode()  # must match ViewParam.GROUP_ID
    name = SchemaNode(  # must match ViewParam.NAME
        String(),
        title="Group name",
        validator=Length(1, GROUP_NAME_MAX_LEN),
    )
    description = MandatoryStringNode(  # must match ViewParam.DESCRIPTION
        validator=Length(1, GROUP_DESCRIPTION_MAX_LEN),
    )
    group_ids = AllOtherGroupsSequence(  # must match ViewParam.GROUP_IDS
        title="Other groups this group may see"
    )
    upload_policy = PolicyNode(  # must match ViewParam.UPLOAD_POLICY
        title="Upload policy",
        description="Minimum required patient information to copy data to "
                    "server"
    )
    finalize_policy = PolicyNode(  # must match ViewParam.FINALIZE_POLICY
        title="Finalize policy",
        description="Minimum required patient information to clear data off "
                    "source device"
    )

    def validator(self, node: SchemaNode, value: Any) -> None:
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        q = CountStarSpecializedQuery(Group, session=req.dbsession)\
            .filter(Group.id != value[ViewParam.GROUP_ID])\
            .filter(Group.name == value[ViewParam.NAME])
        if q.count_star() > 0:
            raise Invalid(node, "Name is used by another group!")


class EditGroupForm(InformativeForm):
    """
    Form to edit a group.
    """
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
    """
    Schema to add a group.
    """
    name = SchemaNode(  # name must match ViewParam.NAME
        String(),
        title="Group name"
    )

    def validator(self, node: SchemaNode, value: Any) -> None:
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        q = CountStarSpecializedQuery(Group, session=req.dbsession)\
            .filter(Group.name == value[ViewParam.NAME])
        if q.count_star() > 0:
            raise Invalid(node, "Name is used by another group!")


class AddGroupForm(AddCancelForm):
    """
    Form to add a group.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=AddGroupSchema,
                         request=request, **kwargs)


class DeleteGroupSchema(HardWorkConfirmationSchema):
    """
    Schema to delete a group.
    """
    group_id = HiddenIntegerNode()  # name must match ViewParam.GROUP_ID
    danger = ValidateDangerousOperationNode()


class DeleteGroupForm(DeleteCancelForm):
    """
    Form to delete a group.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=DeleteGroupSchema,
                         request=request, **kwargs)


# =============================================================================
# Offer research dumps
# =============================================================================

class OfferDumpManualSchema(Schema):
    """
    Schema to offer the "manual" settings for a data dump (groups, task types).
    """
    group_ids = AllowedGroupsSequence()  # must match ViewParam.GROUP_IDS
    tasks = MultiTaskSelector()  # must match ViewParam.TASKS

    title = "Manual settings"
    widget = MappingWidget(template="mapping_accordion", open=False)


class OfferBasicDumpSchema(CSRFSchema):
    """
    Schema to choose the settings for a basic (TSV/ZIP) data dump.
    """
    dump_method = DumpTypeSelector()  # must match ViewParam.DUMP_METHOD
    sort = SortTsvByHeadingsNode()  # must match ViewParam.SORT
    manual = OfferDumpManualSchema()  # must match ViewParam.MANUAL


class OfferBasicDumpForm(SimpleSubmitForm):
    """
    Form to offer a basic (TSV/ZIP) data dump.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=OfferBasicDumpSchema,
                         submit_title="Dump",
                         request=request, **kwargs)


class OfferSqlDumpSchema(CSRFSchema):
    """
    Schema to choose the settings for an SQL data dump.
    """
    dump_method = DumpTypeSelector()  # must match ViewParam.DUMP_METHOD
    sqlite_method = SqliteSelector()  # must match ViewParam.SQLITE_METHOD
    include_blobs = IncludeBlobsNode()  # must match ViewParam.INCLUDE_BLOBS
    manual = OfferDumpManualSchema()  # must match ViewParam.MANUAL


class OfferSqlDumpForm(SimpleSubmitForm):
    """
    Form to choose the settings for an SQL data dump.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=OfferSqlDumpSchema,
                         submit_title="Dump",
                         request=request, **kwargs)


# =============================================================================
# Edit server settings
# =============================================================================

class EditServerSettingsSchema(CSRFSchema):
    """
    Schema to edit the global settings for the server.
    """
    database_title = SchemaNode(  # must match ViewParam.DATABASE_TITLE
        String(),
        title="Database friendly title",
        validator=Length(1, DATABASE_TITLE_MAX_LEN),
    )


class EditServerSettingsForm(ApplyCancelForm):
    """
    Form to edit the global settings for the server.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=EditServerSettingsSchema,
                         request=request, **kwargs)


class EditIdDefinitionSchema(CSRFSchema):
    """
    Schema to edit an ID number definition.
    """
    which_idnum = HiddenIntegerNode()  # must match ViewParam.WHICH_IDNUM
    description = IdDefinitionDescriptionNode()  # must match ViewParam.DESCRIPTION  # noqa
    short_description = IdDefinitionShortDescriptionNode()  # must match ViewParam.SHORT_DESCRIPTION  # noqa
    validation_method = IdValidationMethodNode()  # must match ViewParam.VALIDATION_METHOD
    hl7_id_type = Hl7IdTypeNode()  # must match ViewParam.HL7_ID_TYPE
    hl7_assigning_authority = Hl7AssigningAuthorityNode()  # must match ViewParam.HL7_ASSIGNING_AUTHORITY  # noqa

    def validator(self, node: SchemaNode, value: Any) -> None:
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        qd = CountStarSpecializedQuery(IdNumDefinition, session=req.dbsession)\
            .filter(IdNumDefinition.which_idnum !=
                    value[ViewParam.WHICH_IDNUM])\
            .filter(IdNumDefinition.description ==
                    value[ViewParam.DESCRIPTION])
        if qd.count_star() > 0:
            raise Invalid(node, "Description is used by another ID number!")
        qs = CountStarSpecializedQuery(IdNumDefinition, session=req.dbsession)\
            .filter(IdNumDefinition.which_idnum !=
                    value[ViewParam.WHICH_IDNUM])\
            .filter(IdNumDefinition.short_description ==
                    value[ViewParam.SHORT_DESCRIPTION])
        if qs.count_star() > 0:
            raise Invalid(node, "Short description is used by another ID "
                                "number!")


class EditIdDefinitionForm(ApplyCancelForm):
    """
    Form to edit an ID number definition.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=EditIdDefinitionSchema,
                         request=request, **kwargs)


class AddIdDefinitionSchema(CSRFSchema):
    """
    Schema to add an ID number definition.
    """
    which_idnum = SchemaNode(  # must match ViewParam.WHICH_IDNUM
        Integer(),
        title="Which ID number?",
        description="Specify the integer to represent the type of this ID "
                    "number class (e.g. consecutive numbering from 1)",
        validator=Range(min=1)
    )
    description = IdDefinitionDescriptionNode()  # must match ViewParam.DESCRIPTION  # noqa
    short_description = IdDefinitionShortDescriptionNode()  # must match ViewParam.SHORT_DESCRIPTION  # noqa

    def validator(self, node: SchemaNode, value: Any) -> None:
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        qw = CountStarSpecializedQuery(IdNumDefinition, session=req.dbsession)\
            .filter(IdNumDefinition.which_idnum ==
                    value[ViewParam.WHICH_IDNUM])
        if qw.count_star() > 0:
            raise Invalid(node, "ID# clashes with another ID number!")
        qd = CountStarSpecializedQuery(IdNumDefinition, session=req.dbsession)\
            .filter(IdNumDefinition.description ==
                    value[ViewParam.DESCRIPTION])
        if qd.count_star() > 0:
            raise Invalid(node, "Description is used by another ID number!")
        qs = CountStarSpecializedQuery(IdNumDefinition, session=req.dbsession)\
            .filter(IdNumDefinition.short_description ==
                    value[ViewParam.SHORT_DESCRIPTION])
        if qs.count_star() > 0:
            raise Invalid(node, "Short description is used by another ID "
                                "number!")


class AddIdDefinitionForm(AddCancelForm):
    """
    Form to add an ID number definition.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=AddIdDefinitionSchema,
                         request=request, **kwargs)


class DeleteIdDefinitionSchema(HardWorkConfirmationSchema):
    """
    Schema to delete an ID number definition.
    """
    which_idnum = HiddenIntegerNode()  # name must match ViewParam.WHICH_IDNUM
    danger = ValidateDangerousOperationNode()


class DeleteIdDefinitionForm(DangerousForm):
    """
    Form to add an ID number definition.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=DeleteIdDefinitionSchema,
                         submit_action=FormAction.DELETE,
                         submit_title="Delete",
                         request=request, **kwargs)


# =============================================================================
# Special notes
# =============================================================================

class AddSpecialNoteSchema(CSRFSchema):
    """
    Schema to add a special note to a task.
    """
    table_name = HiddenStringNode()  # must match ViewParam.TABLENAME
    server_pk = HiddenIntegerNode()  # must match ViewParam.SERVER_PK
    note = MandatoryStringNode(  # must match ViewParam.NOTE
        widget=TextAreaWidget(rows=20, cols=80)
    )
    danger = ValidateDangerousOperationNode()


class AddSpecialNoteForm(DangerousForm):
    """
    Form to add a special note to a task.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=AddSpecialNoteSchema,
                         submit_action=FormAction.SUBMIT,
                         submit_title="Add",
                         request=request, **kwargs)


# =============================================================================
# The unusual data manipulation operations
# =============================================================================

class EraseTaskSchema(HardWorkConfirmationSchema):
    """
    Schema to erase a task.
    """
    table_name = HiddenStringNode()  # must match ViewParam.TABLENAME
    server_pk = HiddenIntegerNode()  # must match ViewParam.SERVER_PK
    danger = ValidateDangerousOperationNode()


class EraseTaskForm(DangerousForm):
    """
    Form to erase a task.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=EraseTaskSchema,
                         submit_action=FormAction.DELETE,
                         submit_title="Erase",
                         request=request, **kwargs)


class DeletePatientChooseSchema(CSRFSchema):
    """
    Schema to delete a patient.
    """
    which_idnum = MandatoryWhichIdNumSelector()  # must match ViewParam.WHICH_IDNUM  # noqa
    idnum_value = MandatoryIdNumValue()  # must match ViewParam.IDNUM_VALUE
    group_id = MandatoryGroupIdSelectorAdministeredGroups()  # must match ViewParam.GROUP_ID  # noqa
    danger = ValidateDangerousOperationNode()


class DeletePatientChooseForm(DangerousForm):
    """
    Form to delete a patient.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=DeletePatientChooseSchema,
                         submit_action=FormAction.SUBMIT,
                         submit_title="Show tasks that will be deleted",
                         request=request, **kwargs)


class DeletePatientConfirmSchema(HardWorkConfirmationSchema):
    """
    Schema to confirm deletion of a patient.
    """
    which_idnum = HiddenIntegerNode()  # must match ViewParam.WHICH_IDNUM
    idnum_value = HiddenIntegerNode()  # must match ViewParam.IDNUM_VALUE
    group_id = HiddenIntegerNode()  # must match ViewParam.GROUP_ID
    danger = ValidateDangerousOperationNode()


class DeletePatientConfirmForm(DangerousForm):
    """
    Form to confirm deletion of a patient.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=DeletePatientConfirmSchema,
                         submit_action=FormAction.DELETE,
                         submit_title="Delete",
                         request=request, **kwargs)


EDIT_PATIENT_SIMPLE_PARAMS = [
    ViewParam.FORENAME,
    ViewParam.SURNAME,
    ViewParam.DOB,
    ViewParam.SEX,
    ViewParam.ADDRESS,
    ViewParam.GP,
    ViewParam.OTHER,
]


class EditPatientSchema(CSRFSchema):
    """
    Schema to edit a patient.
    """
    server_pk = HiddenIntegerNode()  # must match ViewParam.SERVER_PK
    group_id = HiddenIntegerNode()  # must match ViewParam.GROUP_ID
    forename = OptionalStringNode()  # must match ViewParam.FORENAME
    surname = OptionalStringNode()  # must match ViewParam.SURNAME
    dob = DateSelectorNode(title="Date of birth")  # must match ViewParam.DOB
    sex = MandatorySexSelector()  # must match ViewParam.SEX
    address = OptionalStringNode()  # must match ViewParam.ADDRESS
    gp = OptionalStringNode(title="GP")  # must match ViewParam.GP
    other = OptionalStringNode()  # must match ViewParam.OTHER
    id_references = IdNumSequenceUniquePerWhichIdnum()  # must match ViewParam.ID_REFERENCES  # noqa
    danger = ValidateDangerousOperationNode()

    def validator(self, node: SchemaNode, value: Any) -> None:
        req = self.bindings[Binding.REQUEST]  # type: CamcopsRequest
        dbsession = req.dbsession
        group_id = value[ViewParam.GROUP_ID]
        group = Group.get_group_by_id(dbsession, group_id)
        testpatient = Patient()
        for k in EDIT_PATIENT_SIMPLE_PARAMS:
            setattr(testpatient, k, value[k])
        testpatient.idnums = []  # type: List[PatientIdNum]
        for idrefdict in value[ViewParam.ID_REFERENCES]:
            pidnum = PatientIdNum()
            pidnum.which_idnum = idrefdict[ViewParam.WHICH_IDNUM]
            pidnum.idnum_value = idrefdict[ViewParam.IDNUM_VALUE]
            testpatient.idnums.append(pidnum)
        tk_finalize_policy = TokenizedPolicy(group.finalize_policy)
        if not testpatient.satisfies_id_policy(tk_finalize_policy):
            raise Invalid(
                node,
                "Patient would not meet 'finalize' ID policy for group {}! "
                "[That policy is: {!r}]".format(
                    group.name, group.finalize_policy))


class EditPatientForm(DangerousForm):
    """
    Form to edit a patient.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=EditPatientSchema,
                         submit_action=FormAction.SUBMIT,
                         submit_title="Submit",
                         request=request, **kwargs)


class ForciblyFinalizeChooseDeviceSchema(CSRFSchema):
    """
    Schema to force-finalize records from a device.
    """
    device_id = MandatoryDeviceIdSelector()  # must match ViewParam.DEVICE_ID
    danger = ValidateDangerousOperationNode()


class ForciblyFinalizeChooseDeviceForm(SimpleSubmitForm):
    """
    Form to force-finalize records from a device.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=ForciblyFinalizeChooseDeviceSchema,
                         submit_title="View affected tasks",
                         request=request, **kwargs)


class ForciblyFinalizeConfirmSchema(HardWorkConfirmationSchema):
    """
    Schema to confirm force-finalizing of a device.
    """
    device_id = HiddenIntegerNode()  # must match ViewParam.DEVICE_ID
    danger = ValidateDangerousOperationNode()


class ForciblyFinalizeConfirmForm(DangerousForm):
    """
    Form to confirm force-finalizing of a device.
    """
    def __init__(self, request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(schema_class=ForciblyFinalizeConfirmSchema,
                         submit_action=FormAction.FINALIZE,
                         submit_title="Forcibly finalize",
                         request=request, **kwargs)


# =============================================================================
# Unit tests
# =============================================================================

class SchemaTests(DemoRequestTestCase):
    """
    Unit tests.
    """
    @staticmethod
    def _serialize_deserialize(schema: Schema,
                               appstruct: Dict[str, Any]) -> None:
        cstruct = schema.serialize(appstruct)
        final = schema.deserialize(cstruct)
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

    def test_login_schema(self) -> None:
        self.announce("test_login_schema")  # noqa
        appstruct = {
            ViewParam.USERNAME: "testuser",
            ViewParam.PASSWORD: "testpw",
        }
        schema = LoginSchema().bind(request=self.req)
        self._serialize_deserialize(schema, appstruct)


# =============================================================================
# main
# =============================================================================
# run with "python -m camcops_server.cc_modules.forms -v" to be verbose

if __name__ == "__main__":
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    unittest.main()
