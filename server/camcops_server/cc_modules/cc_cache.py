#!/usr/bin/env python
# camcops_server/cc_modules/cc_cache.py

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

1. The basic cache objects.

2. FIX FOR DOGPILE.CACHE FOR DECORATED FUNCTIONS, 2017-07-28 (PLUS SOME OTHER
   IMPROVEMENTS). SEE 
   
   https://bitbucket.org/zzzeek/dogpile.cache/issues/96/error-in-python-35-with-use-of-deprecated

Crash using type-hinted functions under Python 3.5 with dogpile.cache==0.6.4:

Traceback (most recent call last):
  File "/usr/lib/python3.5/runpy.py", line 184, in _run_module_as_main
    "__main__", mod_spec)
  File "/usr/lib/python3.5/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/home/rudolf/Documents/code/camcops/server/camcops_server/cc_modules/cc_cache.py", line 64, in <module>
    unit_test_cache()
  File "/home/rudolf/Documents/code/camcops/server/camcops_server/cc_modules/cc_cache.py", line 50, in unit_test_cache
    def testfunc() -> str:
  File "/home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/dogpile/cache/region.py", line 1215, in decorator
    key_generator = function_key_generator(namespace, fn)
  File "/home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/dogpile/cache/util.py", line 31, in function_key_generator
    args = inspect.getargspec(fn)
  File "/usr/lib/python3.5/inspect.py", line 1045, in getargspec
    raise ValueError("Function has keyword-only arguments or annotations"
ValueError: Function has keyword-only arguments or annotations, use getfullargspec() API which can support them

"""  # noqa


# =============================================================================
# Imports; logging
# =============================================================================

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional

from dogpile.cache import make_region
# from dogpile.util import compat  # repr used as the default instead of compat.to_str  # noqa

VERBOSE = True
USE_CAMCOPS_PRETTY_LOGS = True  # False to make this standalone
if USE_CAMCOPS_PRETTY_LOGS:
    from .cc_logger import main_only_quicksetup_rootlogger

log = logging.getLogger(__name__)  # don't use BraceStyleAdapter; {} used


# =============================================================================
# The main cache: static for the lifetime of this process.
# =============================================================================

cache_region_static = make_region()

# Can now use:
# @cache_region_static.cache_on_arguments()


# =============================================================================
# Configure cache(s)
# =============================================================================

cache_region_static.configure(
    backend='dogpile.cache.memory'
    # Consider later: memcached via dogpile.cache.pylibmc
)


# =============================================================================
# Helper functions
# =============================================================================

def repr_parameter(param: inspect.Parameter) -> str:
    return (
        "Parameter(name={name}, annotation={annotation}, kind={kind}, "
        "default={default}".format(
            name=param.name, annotation=param.annotation, kind=param.kind,
            default=param.default)
    )


def get_namespace(fn: Callable, namespace: str) -> str:
    # See hidden attributes with dir(fn)
    # noinspection PyUnresolvedReferences
    return "{module}:{name}{extra}".format(
        module=fn.__module__,
        name=fn.__qualname__,  # __qualname__ includes class name, if present
        extra="|{}".format(namespace) if namespace is not None else "",
    )


# =============================================================================
# New function key generators
# =============================================================================

def fkg_allowing_type_hints(
        namespace: Optional[str],
        fn: Callable,
        to_str: Callable[[Any], str] = repr) \
        -> Callable[[Callable], str]:
    """
    Replacement for dogpile.cache.util.function_key_generator that handles
    type-hinted functions like

            def testfunc(param: str) -> str:
                return param + "hello"

        ... at which inspect.getargspec() balks
        ... plus inspect.getargspec() is deprecated in Python 3

    Return a function that generates a string key, based on a given function as
    well as arguments to the returned function itself.

    """

    namespace = get_namespace(fn, namespace)

    sig = inspect.signature(fn)
    argnames = [p.name for p in sig.parameters.values()
                if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
    has_self = bool(argnames and argnames[0] in ('self', 'cls'))

    def generate_key(*args: Any, **kw: Any) -> str:
        if kw:
            raise ValueError("This dogpile.cache key function generator, "
                             "fkg_allowing_type_hints, "
                             "does not accept keyword arguments.")
        if has_self:
            args = args[1:]
        key = namespace + "|" + " ".join(map(to_str, args))
        # log.debug("Returning key: " + key)
        return key

    return generate_key


def multikey_fkg_allowing_type_hints(
        namespace: Optional[str],
        fn: Callable,
        to_str: Callable[[Any], str] = repr) \
        -> Callable[[Callable], List[str]]:
    """
    Equivalent of dogpile.cache function_multi_key_generator, but using
    inspect.signature() instead.
    """

    namespace = get_namespace(fn, namespace)

    sig = inspect.signature(fn)
    argnames = [p.name for p in sig.parameters.values()
                if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
    has_self = bool(argnames and argnames[0] in ('self', 'cls'))

    def generate_keys(*args: Any, **kw: Any) -> List[str]:
        if kw:
            raise ValueError("This dogpile.cache key function generator, "
                             "multikey_fkg_allowing_type_hints, "
                             "does not accept keyword arguments.")
        if has_self:
            args = args[1:]
        keys = [namespace + "|" + key for key in map(to_str, args)]
        # log.debug("Returning keys: " + repr(keys))
        return keys

    return generate_keys


def kw_fkg_allowing_type_hints(
        namespace: Optional[str],
        fn: Callable,
        to_str: Callable[[Any], str] = repr) \
        -> Callable[[Callable], str]:
    """
    As for fkg_allowing_type_hints, but allowing keyword arguments.

    For kwargs passed in, we will build a dict of all argname (key) argvalue
    (values) including default args from the argspec and then alphabetize the
    list before generating the key.

    NOTE ALSO that once we have keyword arguments, we should be using repr(),
    because we need to distinguish

        kwargs = {'p': 'another', 'q': 'thing'}
        ... which compat.string_type will make into
                p=another q=thing
        ... from
        kwargs = {'p': 'another q=thing'}

    """

    namespace = get_namespace(fn, namespace)

    sig = inspect.signature(fn)
    parameters = list(sig.parameters.values())  # convert from odict_values
    argnames = [p.name for p in parameters
                if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
    has_self = bool(argnames and argnames[0] in ('self', 'cls'))
    if has_self:
        arg_index_start = 1
    else:
        arg_index_start = 0
    # log.debug(
    #     "At start of kw_fkg_allowing_type_hints: namespace={namespace},"
    #     "parameters=[{parameters}], argnames={argnames}, "
    #     "has_self={has_self}, "
    #     "arg_index_start={arg_index_start}; fn={fn}".format(
    #         namespace=namespace,
    #         parameters=", ".join(repr_parameter(p) for p in parameters),
    #         argnames=repr(argnames),
    #         has_self=has_self,
    #         arg_index_start=arg_index_start,
    #         fn=repr(fn),
    #     ))

    def generate_key(*args, **kwargs):
        as_kwargs = {}  # type: Dict[str, Any]
        loose_args = []  # type: List[Any]  # those captured by *args
        # 1. args: get the name as well.
        for idx, arg in enumerate(args[arg_index_start:], arg_index_start):
            if idx >= len(argnames):
                # positional argument to be scooped up with *args
                loose_args.append(arg)
            else:
                # normal plain positional argument
                as_kwargs[argnames[idx]] = arg
        # 1b. args with no name
        if loose_args:
            as_kwargs['*args'] = loose_args
            # '*args' is guaranteed not to be a parameter name in its own right
        # 2. kwargs
        as_kwargs.update(kwargs)
        # 3. default values
        for param in parameters[arg_index_start:]:
            if param.default != inspect.Parameter.empty:
                if param.name not in as_kwargs:
                    as_kwargs[param.name] = param.default
        # 4. sorted by name
        #    ... but also incorporating the name of the argument, because once
        #    we allow the arbitrary **kwargs format, order is no longer
        #    sufficient to discriminate
        #       fn(p="another", q="thing")
        #    from
        #       fn(r="another", s="thing")
        argument_values = ["{k}={v}".format(k=key, v=to_str(as_kwargs[key]))
                           for key in sorted(as_kwargs.keys())]
        key = namespace + '|' + " ".join(argument_values)
        # log.debug("Returning key: " + key)
        return key

    return generate_key


# =============================================================================
# Default function key generator with a short name
# =============================================================================

fkg = kw_fkg_allowing_type_hints

# Can now do:
# from .cc_cache import cache_region_static, fkg
# @cache_region_static.cache_on_arguments(function_key_generator=fkg)
# def myfunc():
#     pass


# =============================================================================
# Unit tests
# =============================================================================

def unit_test_cache() -> None:
    plain_fkg = fkg_allowing_type_hints
    kw_fkg = kw_fkg_allowing_type_hints
    # I'm not sure what dogpile.cache.utils.function_multi_key_generator is
    # used for, so haven't fully tested multikey_fkg_allowing_type_hints, but
    # it works internally in the same way as fkg_allowing_type_hints.
    
    fn_was_called = False
    
    def test(result: str, should_call_fn: bool, reset: bool = True) -> None:
        nonlocal fn_was_called
        log.info(result)
        assert fn_was_called == should_call_fn, (
            "fn_was_called={}, should_call_fn={}".format(
                fn_was_called, should_call_fn))
        if reset:
            fn_was_called = False
        
    def fn_called(text: str) -> None:
        log.info(text)
        nonlocal fn_was_called
        fn_was_called = True

    @cache_region_static.cache_on_arguments(function_key_generator=None)
    def no_params_dogpile_default_fkg():  # no type hints!
        fn_called("CACHED FUNCTION no_params_dogpile_default_fkg() CALLED")
        return "no_params_dogpile_default_fkg: hello"

    @cache_region_static.cache_on_arguments(function_key_generator=plain_fkg)
    def noparams() -> str:
        fn_called("CACHED FUNCTION noparams() CALLED")
        return "noparams: hello"

    @cache_region_static.cache_on_arguments(function_key_generator=plain_fkg)
    def oneparam(a: str) -> str:
        fn_called("CACHED FUNCTION oneparam() CALLED")
        return "oneparam: hello, " + a

    @cache_region_static.cache_on_arguments(function_key_generator=plain_fkg)
    def twoparam_with_default_wrong_dec(a: str, b: str = "Zelda") -> str:
        fn_called("CACHED FUNCTION twoparam_with_default_wrong_dec() CALLED")
        return ("twoparam_with_default_wrong_dec: hello, " + a +
                "; this is " + b)

    @cache_region_static.cache_on_arguments(function_key_generator=kw_fkg)
    def twoparam_with_default_right_dec(a: str, b: str = "Zelda") -> str:
        fn_called("CACHED FUNCTION twoparam_with_default_right_dec() CALLED")
        return ("twoparam_with_default_right_dec: hello, " + a +
                "; this is " + b)

    @cache_region_static.cache_on_arguments(function_key_generator=kw_fkg)
    def twoparam_all_defaults_no_typehints(a="David", b="Zelda"):
        fn_called("CACHED FUNCTION twoparam_all_defaults_no_typehints() "
                  "CALLED")
        return ("twoparam_all_defaults_no_typehints: hello, " + a +
                "; this is " + b)

    @cache_region_static.cache_on_arguments(function_key_generator=kw_fkg)
    def fn_args_kwargs(*args, **kwargs):
        fn_called("CACHED FUNCTION fn_args_kwargs() CALLED")
        return ("fn_args_kwargs: args={}, kwargs={}".format(repr(args),
                                                            repr(kwargs)))

    @cache_region_static.cache_on_arguments(function_key_generator=kw_fkg)
    def fn_all_possible(a, b, *args, d="David", **kwargs):
        fn_called("CACHED FUNCTION fn_all_possible() CALLED")
        return "fn_all_possible: a={}, b={}, args={}, d={}, kwargs={}".format(
            repr(a), repr(b), repr(args), repr(d), repr(kwargs))

    class TestClass(object):
        c = 999

        def __init__(self) -> None:
            self.a = 200

        @cache_region_static.cache_on_arguments(function_key_generator=None)
        def no_params_dogpile_default_fkg(self):  # no type hints!
            fn_called("CACHED FUNCTION TestClass."
                      "no_params_dogpile_default_fkg() CALLED")
            return "TestClass.no_params_dogpile_default_fkg: hello"

        @cache_region_static.cache_on_arguments(function_key_generator=None)
        def dogpile_default_test_2(self):  # no type hints!
            fn_called("CACHED FUNCTION TestClass."
                      "dogpile_default_test_2() CALLED")
            return "TestClass.dogpile_default_test_2: hello"

        @cache_region_static.cache_on_arguments(
            function_key_generator=plain_fkg)
        def noparams(self) -> str:
            fn_called("CACHED FUNCTION TestClass.noparams() CALLED")
            return "Testclass.noparams: hello; a={}".format(self.a)

        # Decorator order is critical here:
        # https://stackoverflow.com/questions/1987919/why-can-decorator-not-decorate-a-staticmethod-or-a-classmethod  # noqa
        @classmethod
        @cache_region_static.cache_on_arguments(
            function_key_generator=plain_fkg)
        def classy(cls) -> str:
            fn_called("CACHED FUNCTION TestClass.classy() CALLED")
            return "TestClass.classy: hello; c={}".format(cls.c)

        @staticmethod
        @cache_region_static.cache_on_arguments(
            function_key_generator=plain_fkg)
        def static() -> str:
            fn_called("CACHED FUNCTION TestClass.static() CALLED")
            return "TestClass.static: hello"

        @cache_region_static.cache_on_arguments(
            function_key_generator=plain_fkg)
        def oneparam(self, q: str) -> str:
            fn_called("CACHED FUNCTION TestClass.oneparam() CALLED")
            return "TestClass.oneparam: hello, " + q

        @cache_region_static.cache_on_arguments(function_key_generator=kw_fkg)
        def fn_all_possible(self, a, b, *args, d="David", **kwargs):
            fn_called("CACHED FUNCTION TestClass.fn_all_possible() CALLED")
            return ("TestClass.fn_all_possible: a={}, b={}, args={}, d={}, "
                    "kwargs={}".format(repr(a), repr(b), repr(args), repr(d),
                                       repr(kwargs)))

    class SecondTestClass:
        def __init__(self) -> None:
            self.d = 5

        @cache_region_static.cache_on_arguments(function_key_generator=None)
        def dogpile_default_test_2(self):  # no type hints!
            fn_called("CACHED FUNCTION SecondTestClass."
                      "dogpile_default_test_2() CALLED")
            return "SecondTestClass.dogpile_default_test_2: hello"

    log.warning("Fetching cached information #1 (should call noparams())...")
    test(noparams(), True)
    log.warning("Fetching cached information #2 (should not call noparams())...")  # noqa
    test(noparams(), False)

    log.warning("Testing functions with other signatures...")
    test(oneparam("Arthur"), True)
    test(oneparam("Arthur"), False)
    test(oneparam("Bob"), True)
    test(oneparam("Bob"), False)
    test(twoparam_with_default_wrong_dec("Celia"), True)
    test(twoparam_with_default_wrong_dec("Celia"), False)
    test(twoparam_with_default_wrong_dec("Celia", "Yorick"), True)
    test(twoparam_with_default_wrong_dec("Celia", "Yorick"), False)

    log.warning("Trying with keyword arguments and wrong key generator")
    try:
        log.info(twoparam_with_default_wrong_dec(a="Celia", b="Yorick"))
        raise AssertionError("Inappropriate success with keyword arguments!")
    except ValueError:
        log.info("Correct rejection of keyword arguments")

    log.warning("Trying with keyword arguments and right key generator")
    test(twoparam_with_default_right_dec(a="Celia"), True)
    test(twoparam_with_default_right_dec(a="Celia", b="Yorick"), True)
    test(twoparam_with_default_right_dec(b="Yorick", a="Celia"), False)
    test(twoparam_with_default_right_dec("Celia", b="Yorick"), False)

    test(twoparam_all_defaults_no_typehints(), True)
    test(twoparam_all_defaults_no_typehints(a="Edith"), True)
    test(twoparam_all_defaults_no_typehints(a="Edith"), False)
    test(twoparam_all_defaults_no_typehints(b="Romeo"), True)
    test(twoparam_all_defaults_no_typehints(b="Romeo"), False)
    test(twoparam_all_defaults_no_typehints("Greta", b="Romeo"), True)
    test(twoparam_all_defaults_no_typehints("Greta", b="Romeo"), False)
    test(twoparam_all_defaults_no_typehints(a="Felicity", b="Sigurd"), True)
    test(twoparam_all_defaults_no_typehints(a="Felicity", b="Sigurd"), False)
    test(twoparam_all_defaults_no_typehints("Felicity", "Sigurd"), False)
    test(twoparam_all_defaults_no_typehints("Felicity", "Sigurd"), False)
    test(twoparam_all_defaults_no_typehints(b="Sigurd", a="Felicity"), False)
    test(twoparam_all_defaults_no_typehints(b="Sigurd", a="Felicity"), False)

    test(fn_args_kwargs(1, 2, 3, d="David", f="Edgar"), True)
    test(fn_args_kwargs(1, 2, 3, d="David", f="Edgar"), False)

    test(fn_args_kwargs(p="another", q="thing"), True)
    test(fn_args_kwargs(p="another", q="thing"), False)
    log.warning("The next call MUST NOT go via the cache, i.e. func should be CALLED")  # noqa
    test(fn_args_kwargs(p="another q=thing"), True)
    test(fn_args_kwargs(p="another q=thing"), False)

    test(fn_all_possible(10, 11, 12, "Horace", "Iris"), True)
    test(fn_all_possible(10, 11, 12, "Horace", "Iris"), False)
    test(fn_all_possible(10, 11, 12, d="Horace"), True)
    test(fn_all_possible(10, 11, 12, d="Horace"), False)
    test(fn_all_possible(98, 99, d="Horace"), True)
    test(fn_all_possible(98, 99, d="Horace"), False)
    test(fn_all_possible(98, 99, d="Horace", p="another", q="thing"), True)
    test(fn_all_possible(98, 99, d="Horace", p="another", q="thing"), False)
    test(fn_all_possible(98, 99, d="Horace", r="another", s="thing"), True)
    test(fn_all_possible(98, 99, d="Horace", r="another", s="thing"), False)

    log.warning("Testing class member functions")
    t = TestClass()
    test(t.noparams(), True)
    test(t.noparams(), False)
    test(t.classy(), True)
    test(t.classy(), False)
    test(t.static(), True)
    test(t.static(), False)
    test(t.oneparam("Arthur"), True)
    test(t.oneparam("Arthur"), False)
    test(t.oneparam("Bob"), True)
    test(t.oneparam("Bob"), False)
    test(t.fn_all_possible(10, 11, 12, "Horace", "Iris"), True)
    test(t.fn_all_possible(10, 11, 12, "Horace", "Iris"), False)
    test(t.fn_all_possible(10, 11, 12, d="Horace"), True)
    test(t.fn_all_possible(10, 11, 12, d="Horace"), False)
    test(t.fn_all_possible(98, 99, d="Horace"), True)
    test(t.fn_all_possible(98, 99, d="Horace"), False)
    test(t.fn_all_possible(98, 99, d="Horace", p="another", q="thing"), True)
    test(t.fn_all_possible(98, 99, d="Horace", p="another", q="thing"), False)
    test(t.fn_all_possible(98, 99, d="Horace", r="another", s="thing"), True)
    test(t.fn_all_possible(98, 99, d="Horace", r="another", s="thing"), False)

    test(no_params_dogpile_default_fkg(), True)
    test(no_params_dogpile_default_fkg(), False)
    try:
        test(t.no_params_dogpile_default_fkg(), True)
        log.info("dogpile.cache default FKG correctly distinguishing between "
                 "plain and class-member function in same module")
    except AssertionError:
        log.warning("Known dogpile.cache default FKG problem - conflates "
                    "plain/class member function of same name (unless "
                    "namespace is manually given)")
    test(t.no_params_dogpile_default_fkg(), False)

    t2 = SecondTestClass()
    test(t.dogpile_default_test_2(), True)
    test(t.dogpile_default_test_2(), False)
    try:
        test(t2.dogpile_default_test_2(), True)
        log.info("dogpile.cache default FKG correctly distinguishing between "
                 "member functions of two different classes with same name")
    except AssertionError:
        log.warning("Known dogpile.cache default FKG problem - conflates "
                    "member functions of two different classes where "
                    "functions have same name (unless namespace is manually "
                    "given)")
    test(t2.dogpile_default_test_2(), False)

    log.info("Success!")


# TEST THIS WITH:
# python -m camcops_server.cc_modules.cc_cache
if __name__ == '__main__':
    level = logging.DEBUG if VERBOSE else logging.INFO
    if USE_CAMCOPS_PRETTY_LOGS:
        main_only_quicksetup_rootlogger(level=level)
    else:
        logging.basicConfig(level=level)
    unit_test_cache()
