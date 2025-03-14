# TODO: These are in no way complete and for the time being are enough to stop
# MyPy complaining about ColanderNullType in cc_forms.py

from collections.abc import Generator
from translationstring import TranslationString
from typing import Any as AnyType, Callable, Optional

from _typeshed import Incomplete

_: Callable[[str], TranslationString]

class _required:
    def __reduce__(self) -> str: ...

required: _required

class _null:
    def __nonzero__(self) -> bool: ...
    __bool__ = __nonzero__
    def __reduce__(self) -> str: ...

null: _null

class _drop:
    def __reduce__(self) -> str: ...

drop: _drop

def interpolate(msgs: AnyType) -> Generator[Incomplete]: ...

class UnboundDeferredError(Exception): ...

class Invalid(Exception):
    pos: Optional[int]
    positional: bool
    node: "SchemaNode"
    msg: AnyType
    value: AnyType
    children: list["SchemaNode"]
    def __init__(
        self,
        node: AnyType,
        msg: AnyType | None = None,
        value: AnyType | None = None,
    ) -> None: ...
    def messages(self) -> AnyType: ...
    def add(self, exc: AnyType, pos: int | None = None) -> None: ...
    def __setitem__(self, name: AnyType, msg: AnyType) -> None: ...
    def paths(self) -> AnyType: ...
    def asdict(
        self,
        translate: Callable[[TranslationString], str] | None = None,
        separator: str = "; ",
    ) -> AnyType: ...

class UnsupportedFields(Invalid):
    fields: AnyType
    def __init__(
        self, node: AnyType, fields: AnyType, msg: AnyType | None = None
    ) -> None: ...

class All:
    validators: Incomplete
    def __init__(self, *validators: AnyType) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

class Any(All):
    def __call__(self, node: AnyType, value: AnyType) -> AnyType: ...

class Function:
    function: Callable[[AnyType], AnyType]
    msg: AnyType
    def __init__(
        self,
        function: AnyType,
        msg: AnyType | None = None,
        message: AnyType | None = None,
    ) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

class Regex:
    match_object: AnyType
    msg: AnyType
    def __init__(
        self, regex: AnyType, msg: AnyType | None = None, flags: int = 0
    ) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

EMAIL_RE: str

class Email(Regex):
    def __init__(self, msg: AnyType | None = None) -> None: ...

class Range:
    min: AnyType
    max: AnyType
    min_err: AnyType
    max_err: AnyType
    def __init__(
        self,
        min: AnyType | None = None,
        max: AnyType | None = None,
        min_err: AnyType = ...,
        max_err: AnyType = ...,
    ) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

class Length:
    min: AnyType
    max: AnyType
    min_err: AnyType
    max_err: AnyType
    def __init__(
        self,
        min: AnyType | None = None,
        max: AnyType | None = None,
        min_err: AnyType = ...,
        max_err: AnyType = ...,
    ) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

class OneOf:
    choices: AnyType
    def __init__(self, choices: AnyType) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

class NoneOf:
    forbidden: AnyType
    msg_err: AnyType
    def __init__(self, choices: AnyType, msg_err: AnyType = ...) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

class ContainsOnly:
    err_template: AnyType
    choices: AnyType
    def __init__(self, choices: AnyType) -> None: ...
    def __call__(self, node: AnyType, value: AnyType) -> None: ...

def luhnok(node: AnyType, value: AnyType) -> None: ...

URL_REGEX: str
url: AnyType
URI_REGEX: str
file_uri: AnyType
UUID_REGEX: str
uuid: AnyType

class SchemaType:
    def flatten(
        self,
        node: AnyType,
        appstruct: AnyType,
        prefix: str = "",
        listitem: bool = False,
    ) -> AnyType: ...
    def unflatten(
        self, node: AnyType, paths: AnyType, fstruct: AnyType
    ) -> AnyType: ...
    def set_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType, value: AnyType
    ) -> None: ...
    def get_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType
    ) -> None: ...
    def cstruct_children(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class Mapping(SchemaType):
    unknown: AnyType
    def __init__(self, unknown: str = "ignore") -> None: ...
    def cstruct_children(self, node: AnyType, cstruct: AnyType) -> AnyType: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...
    def flatten(
        self,
        node: AnyType,
        appstruct: AnyType,
        prefix: str = "",
        listitem: bool = False,
    ) -> AnyType: ...
    def unflatten(
        self, node: AnyType, paths: AnyType, fstruct: AnyType
    ) -> AnyType: ...
    def set_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType, value: AnyType
    ) -> AnyType: ...
    def get_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType
    ) -> AnyType: ...

class Positional: ...

class Tuple(Positional, SchemaType):
    def cstruct_children(self, node: AnyType, cstruct: AnyType) -> AnyType: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...
    def flatten(
        self,
        node: AnyType,
        appstruct: AnyType,
        prefix: str = "",
        listitem: bool = False,
    ) -> AnyType: ...
    def unflatten(
        self, node: AnyType, paths: AnyType, fstruct: AnyType
    ) -> AnyType: ...
    def set_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType, value: AnyType
    ) -> AnyType: ...
    def get_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType
    ) -> AnyType: ...

class Set(SchemaType):
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class List(SchemaType):
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class SequenceItems(list): ...

class Sequence(Positional, SchemaType):
    accept_scalar: AnyType
    def __init__(self, accept_scalar: bool = False) -> None: ...
    def cstruct_children(self, node: AnyType, cstruct: AnyType) -> AnyType: ...
    def serialize(
        self,
        node: AnyType,
        appstruct: AnyType,
        accept_scalar: AnyType | None = None,
    ) -> AnyType: ...
    def deserialize(
        self,
        node: AnyType,
        cstruct: AnyType,
        accept_scalar: AnyType | None = None,
    ) -> AnyType: ...
    def flatten(
        self,
        node: AnyType,
        appstruct: AnyType,
        prefix: str = "",
        listitem: bool = False,
    ) -> AnyType: ...
    def unflatten(
        self, node: AnyType, paths: AnyType, fstruct: AnyType
    ) -> AnyType: ...
    def set_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType, value: AnyType
    ) -> AnyType: ...
    def get_value(
        self, node: AnyType, appstruct: AnyType, path: AnyType
    ) -> AnyType: ...

Seq = Sequence

class String(SchemaType):
    encoding: AnyType
    allow_empty: AnyType
    def __init__(
        self, encoding: AnyType | None = None, allow_empty: bool = False
    ) -> None: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

Str = String

class Number(SchemaType):
    num: AnyType
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class Integer(Number):
    num = int
    def __init__(self, strict: bool = False) -> None: ...

Int = Integer

class Float(Number):
    num = float

class Decimal(Number):
    quant: AnyType
    rounding: AnyType
    normalize: AnyType
    def __init__(
        self,
        quant: AnyType | None = None,
        rounding: AnyType | None = None,
        normalize: bool = False,
    ) -> None: ...
    def num(self, val: AnyType) -> AnyType: ...

class Money(Decimal):
    def __init__(self) -> None: ...

class Boolean(SchemaType):
    false_choices: AnyType
    true_choices: AnyType
    false_val: AnyType
    true_val: AnyType
    true_reprs: AnyType
    false_reprs: AnyType
    def __init__(
        self,
        false_choices: AnyType = ("false", "0"),
        true_choices: AnyType = (),
        false_val: str = "false",
        true_val: str = "true",
    ) -> None: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

Bool = Boolean

class GlobalObject(SchemaType):
    package: AnyType
    def __init__(self, package: AnyType) -> None: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class DateTime(SchemaType):
    err_template: AnyType
    default_tzinfo: AnyType
    format: AnyType
    def __init__(
        self, default_tzinfo: AnyType = ..., format: AnyType | None = None
    ) -> None: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class Date(SchemaType):
    err_template: AnyType
    format: AnyType
    def __init__(self, format: AnyType | None = None) -> None: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class Time(SchemaType):
    err_template: AnyType
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class Enum(SchemaType):
    enum_cls: AnyType
    attr: AnyType
    typ: AnyType
    values: AnyType
    def __init__(
        self,
        enum_cls: AnyType,
        attr: AnyType | None = None,
        typ: AnyType | None = None,
    ) -> None: ...
    def serialize(self, node: AnyType, appstruct: AnyType) -> AnyType: ...
    def deserialize(self, node: AnyType, cstruct: AnyType) -> AnyType: ...

class _SchemaNode:
    preparer: AnyType
    validator: AnyType
    default = null
    missing = required
    missing_msg: AnyType
    name: str
    raw_title: AnyType
    title: AnyType
    description: str
    widget: AnyType
    after_bind: AnyType
    bindings: AnyType
    def __new__(cls, *args: AnyType, **kw: AnyType) -> AnyType: ...
    typ: AnyType
    def __init__(self, *arg: AnyType, **kw: AnyType) -> None: ...
    @staticmethod
    def schema_type() -> None: ...
    @property
    def required(self) -> AnyType: ...
    def serialize(self, appstruct: AnyType = ...) -> AnyType: ...
    def flatten(self, appstruct: AnyType) -> AnyType: ...
    def unflatten(self, fstruct: AnyType) -> AnyType: ...
    def set_value(
        self, appstruct: AnyType, dotted_name: AnyType, value: AnyType
    ) -> None: ...
    def get_value(
        self, appstruct: AnyType, dotted_name: AnyType
    ) -> AnyType: ...
    def deserialize(self, cstruct: AnyType = ...) -> AnyType: ...
    def add(self, node: AnyType) -> None: ...
    def insert(self, index: AnyType, node: AnyType) -> None: ...
    def add_before(self, name: AnyType, node: AnyType) -> None: ...
    def get(
        self, name: AnyType, default: AnyType | None = None
    ) -> AnyType: ...
    def clone(self) -> AnyType: ...
    def bind(self, **kw: AnyType) -> AnyType: ...
    def cstruct_children(self, cstruct: AnyType) -> AnyType: ...
    def __delitem__(self, name: AnyType) -> None: ...
    def __getitem__(self, name: AnyType) -> AnyType: ...
    def __setitem__(self, name: AnyType, newnode: AnyType) -> None: ...
    def __iter__(self) -> AnyType: ...
    def __contains__(self, name: AnyType) -> bool: ...
    def raise_invalid(
        self, msg: AnyType, node: AnyType | None = None
    ) -> None: ...

class _SchemaMeta(type):
    def __init__(
        cls, name: AnyType, bases: AnyType, clsattrs: AnyType
    ) -> None: ...

SchemaNode: AnyType

class Schema(SchemaNode):
    schema_type = Mapping

MappingSchema = Schema

class TupleSchema(SchemaNode):
    schema_type = Tuple

class SequenceSchema(SchemaNode):
    schema_type = Sequence
    def __init__(self, *args: AnyType, **kw: AnyType) -> None: ...
    def clone(self) -> AnyType: ...

class deferred:
    __doc__: AnyType
    wrapped: AnyType
    def __init__(self, wrapped: AnyType) -> None: ...
    def __call__(self, node: AnyType, kw: AnyType) -> AnyType: ...

class instantiate:
    def __init__(self, *args: AnyType, **kw: AnyType) -> None: ...
    def __call__(self, class_: AnyType) -> AnyType: ...
