from typing import Any as _Any, Optional

class _required:
    def __reduce__(self): ...

required: _Any

class _null:
    def __nonzero__(self): ...
    __bool__: _Any = ...
    def __reduce__(self): ...

null: _null

class _drop:
    def __reduce__(self): ...

drop: _Any

def interpolate(msgs: _Any) -> None: ...

class UnboundDeferredError(Exception): ...

class Invalid(Exception):
    pos: _Any = ...
    positional: bool = ...
    node: _Any = ...
    msg: _Any = ...
    value: _Any = ...
    children: _Any = ...
    def __init__(
        self,
        node: _Any,
        msg: Optional[_Any] = ...,
        value: Optional[_Any] = ...,
    ) -> None: ...
    def messages(self): ...
    def add(self, exc: _Any, pos: Optional[_Any] = ...) -> None: ...
    def __setitem__(self, name: _Any, msg: _Any) -> None: ...
    def paths(self): ...
    def asdict(
        self, translate: Optional[_Any] = ..., separator: str = ...
    ): ...

class UnsupportedFields(Invalid):
    fields: _Any = ...
    def __init__(
        self, node: _Any, fields: _Any, msg: Optional[_Any] = ...
    ) -> None: ...

class All:
    validators: _Any = ...
    def __init__(self, *validators: _Any) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

class Any(All):
    def __call__(self, node: _Any, value: _Any): ...

class Function:
    function: _Any = ...
    msg: _Any = ...
    def __init__(
        self,
        function: _Any,
        msg: Optional[_Any] = ...,
        message: Optional[_Any] = ...,
    ) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

class Regex:
    match_object: _Any = ...
    msg: _Any = ...
    def __init__(
        self, regex: _Any, msg: Optional[_Any] = ..., flags: int = ...
    ) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

EMAIL_RE: str

class Email(Regex):
    def __init__(self, msg: Optional[_Any] = ...) -> None: ...

class Range:
    min: _Any = ...
    max: _Any = ...
    min_err: _Any = ...
    max_err: _Any = ...
    def __init__(
        self,
        min: Optional[_Any] = ...,
        max: Optional[_Any] = ...,
        min_err: _Any = ...,
        max_err: _Any = ...,
    ) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

class Length:
    min: _Any = ...
    max: _Any = ...
    min_err: _Any = ...
    max_err: _Any = ...
    def __init__(
        self,
        min: Optional[_Any] = ...,
        max: Optional[_Any] = ...,
        min_err: _Any = ...,
        max_err: _Any = ...,
    ) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

class OneOf:
    choices: _Any = ...
    def __init__(self, choices: _Any) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

class NoneOf:
    forbidden: _Any = ...
    msg_err: _Any = ...
    def __init__(self, choices: _Any, msg_err: _Any = ...) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

class ContainsOnly:
    err_template: _Any = ...
    choices: _Any = ...
    def __init__(self, choices: _Any) -> None: ...
    def __call__(self, node: _Any, value: _Any) -> None: ...

def luhnok(node: _Any, value: _Any) -> None: ...

URL_REGEX: str
url: _Any
URI_REGEX: str
file_uri: _Any
UUID_REGEX: str
uuid: _Any

class SchemaType:
    def flatten(
        self,
        node: _Any,
        appstruct: _Any,
        prefix: str = ...,
        listitem: bool = ...,
    ): ...
    def unflatten(self, node: _Any, paths: _Any, fstruct: _Any): ...
    def set_value(
        self, node: _Any, appstruct: _Any, path: _Any, value: _Any
    ) -> None: ...
    def get_value(self, node: _Any, appstruct: _Any, path: _Any) -> None: ...
    def cstruct_children(self, node: _Any, cstruct: _Any): ...

class Mapping(SchemaType):
    unknown: _Any = ...
    def __init__(self, unknown: str = ...) -> None: ...
    def cstruct_children(self, node: _Any, cstruct: _Any): ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...
    def flatten(
        self,
        node: _Any,
        appstruct: _Any,
        prefix: str = ...,
        listitem: bool = ...,
    ): ...
    def unflatten(self, node: _Any, paths: _Any, fstruct: _Any): ...
    def set_value(
        self, node: _Any, appstruct: _Any, path: _Any, value: _Any
    ): ...
    def get_value(self, node: _Any, appstruct: _Any, path: _Any): ...

class Positional: ...

class Tuple(Positional, SchemaType):
    def cstruct_children(self, node: _Any, cstruct: _Any): ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...
    def flatten(
        self,
        node: _Any,
        appstruct: _Any,
        prefix: str = ...,
        listitem: bool = ...,
    ): ...
    def unflatten(self, node: _Any, paths: _Any, fstruct: _Any): ...
    def set_value(
        self, node: _Any, appstruct: _Any, path: _Any, value: _Any
    ): ...
    def get_value(self, node: _Any, appstruct: _Any, path: _Any): ...

class Set(SchemaType):
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class List(SchemaType):
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class SequenceItems(list): ...

class Sequence(Positional, SchemaType):
    accept_scalar: _Any = ...
    def __init__(self, accept_scalar: bool = ...) -> None: ...
    def cstruct_children(self, node: _Any, cstruct: _Any): ...
    def serialize(
        self, node: _Any, appstruct: _Any, accept_scalar: Optional[_Any] = ...
    ): ...
    def deserialize(
        self, node: _Any, cstruct: _Any, accept_scalar: Optional[_Any] = ...
    ): ...
    def flatten(
        self,
        node: _Any,
        appstruct: _Any,
        prefix: str = ...,
        listitem: bool = ...,
    ): ...
    def unflatten(self, node: _Any, paths: _Any, fstruct: _Any): ...
    def set_value(
        self, node: _Any, appstruct: _Any, path: _Any, value: _Any
    ): ...
    def get_value(self, node: _Any, appstruct: _Any, path: _Any): ...

Seq = Sequence

class String(SchemaType):
    encoding: _Any = ...
    allow_empty: _Any = ...
    def __init__(
        self, encoding: Optional[_Any] = ..., allow_empty: bool = ...
    ) -> None: ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

Str = String

class Number(SchemaType):
    num: _Any = ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class Integer(Number):
    num: _Any = ...
    def __init__(self, strict: bool = ...): ...

Int = Integer

class Float(Number):
    num: _Any = ...

class Decimal(Number):
    quant: _Any = ...
    rounding: _Any = ...
    normalize: _Any = ...
    def __init__(
        self,
        quant: Optional[_Any] = ...,
        rounding: Optional[_Any] = ...,
        normalize: bool = ...,
    ) -> None: ...
    def num(self, val: _Any): ...

class Money(Decimal):
    def __init__(self) -> None: ...

class Boolean(SchemaType):
    false_choices: _Any = ...
    true_choices: _Any = ...
    false_val: _Any = ...
    true_val: _Any = ...
    true_reprs: _Any = ...
    false_reprs: _Any = ...
    def __init__(
        self,
        false_choices: _Any = ...,
        true_choices: _Any = ...,
        false_val: str = ...,
        true_val: str = ...,
    ) -> None: ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

Bool = Boolean

class GlobalObject(SchemaType):
    package: _Any = ...
    def __init__(self, package: _Any) -> None: ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class DateTime(SchemaType):
    err_template: _Any = ...
    default_tzinfo: _Any = ...
    format: _Any = ...
    def __init__(
        self, default_tzinfo: _Any = ..., format: Optional[_Any] = ...
    ) -> None: ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class Date(SchemaType):
    err_template: _Any = ...
    format: _Any = ...
    def __init__(self, format: Optional[_Any] = ...) -> None: ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class Time(SchemaType):
    err_template: _Any = ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class Enum(SchemaType):
    enum_cls: _Any = ...
    attr: _Any = ...
    typ: _Any = ...
    values: _Any = ...
    def __init__(
        self,
        enum_cls: _Any,
        attr: Optional[_Any] = ...,
        typ: Optional[_Any] = ...,
    ) -> None: ...
    def serialize(self, node: _Any, appstruct: _Any): ...
    def deserialize(self, node: _Any, cstruct: _Any): ...

class _SchemaNode:
    preparer: _Any = ...
    validator: _Any = ...
    default: _Any = ...
    missing: _Any = ...
    missing_msg: _Any = ...
    name: str = ...
    raw_title: _Any = ...
    title: _Any = ...
    description: str = ...
    widget: _Any = ...
    after_bind: _Any = ...
    bindings: _Any = ...
    def __new__(cls, *args: _Any, **kw: _Any): ...
    typ: _Any = ...
    def __init__(self, *arg: _Any, **kw: _Any) -> None: ...
    @staticmethod
    def schema_type() -> None: ...
    @property
    def required(self): ...
    def serialize(self, appstruct: _Any = ...): ...
    def flatten(self, appstruct: _Any): ...
    def unflatten(self, fstruct: _Any): ...
    def set_value(
        self, appstruct: _Any, dotted_name: _Any, value: _Any
    ) -> None: ...
    def get_value(self, appstruct: _Any, dotted_name: _Any): ...
    def deserialize(self, cstruct: _Any = ...): ...
    def add(self, node: _Any) -> None: ...
    def insert(self, index: _Any, node: _Any) -> None: ...
    def add_before(self, name: _Any, node: _Any) -> None: ...
    def get(self, name: _Any, default: Optional[_Any] = ...): ...
    def clone(self): ...
    def bind(self, **kw: _Any): ...
    def cstruct_children(self, cstruct: _Any): ...
    def __delitem__(self, name: _Any): ...
    def __getitem__(self, name: _Any): ...
    def __setitem__(self, name: _Any, newnode: _Any): ...
    def __iter__(self) -> _Any: ...
    def __contains__(self, name: _Any): ...
    def raise_invalid(self, msg: _Any, node: Optional[_Any] = ...) -> None: ...

class _SchemaMeta(type):
    def __init__(cls, name: _Any, bases: _Any, clsattrs: _Any): ...

SchemaNode: _Any

class Schema(SchemaNode):
    schema_type: _Any = ...

MappingSchema = Schema

class TupleSchema(SchemaNode):
    schema_type: _Any = ...

class SequenceSchema(SchemaNode):
    schema_type: _Any = ...
    def __init__(self, *args: _Any, **kw: _Any) -> None: ...
    def clone(self): ...

class deferred:
    __doc__: _Any = ...
    wrapped: _Any = ...
    def __init__(self, wrapped: _Any) -> None: ...
    def __call__(self, node: _Any, kw: _Any): ...

class instantiate:
    def __init__(self, *args: _Any, **kw: _Any) -> None: ...
    def __call__(self, class_: _Any): ...
