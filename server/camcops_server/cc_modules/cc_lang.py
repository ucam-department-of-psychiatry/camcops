#!/usr/bin/env python
# camcops_server/cc_modules/cc_lang.py

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

# Misc language-oriented functions

from functools import total_ordering
import logging
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar, Union
import unicodedata

log = logging.getLogger(__name__)  # no BraceAdapter here; we may use {}


# =============================================================================
# Mean
# =============================================================================

def mean(values: Sequence[Union[int, float, None]]) -> Optional[float]:
    """Return mean of a list of numbers, or None."""
    total = 0.0  # starting with "0.0" causes automatic conversion to float
    n = 0
    for x in values:
        if x is not None:
            total += x
            n += 1
    return total / n if n > 0 else None


# =============================================================================
# Does a derived class implement a method?
# =============================================================================

"""
http://stackoverflow.com/questions/1776994
https://docs.python.org/3/library/inspect.html
https://github.com/edoburu/django-fluent-contents/issues/43
https://bytes.com/topic/python/answers/843424-python-2-6-3-0-determining-if-method-inherited  # noqa
https://docs.python.org/3/reference/datamodel.html

In Python 2, you can do this:
    return derived_method.__func__ != base_method.__func__
In Python 3.4:
    ...

class Base(object):
    def one():
        print("base one")
    def two():
        print("base two")


class Derived(Base):
    def two():
        print("derived two")


Derived.two.__dir__()  # not all versions of Python


derived_class_implements_method(Derived, Base, 'one')  # should be False
derived_class_implements_method(Derived, Base, 'two')  # should be True
derived_class_implements_method(Derived, Base, 'three')  # should be False

"""

T1 = TypeVar('T1')
T2 = TypeVar('T2')


def derived_class_implements_method(derived: Type[T1],
                                    base: Type[T2],
                                    method_name: str) -> bool:
    derived_method = getattr(derived, method_name, None)
    if derived_method is None:
        return False
    base_method = getattr(base, method_name, None)
    # if six.PY2:
    #     return derived_method.__func__ != base_method.__func__
    # else:
    #     return derived_method is not base_method
    return derived_method is not base_method


# =============================================================================
# Subclasses
# =============================================================================
# https://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-class-given-its-name  # noqa

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


# =============================================================================
# Lists
# =============================================================================

def flatten_list(l) -> List[Any]:
    return [item for sublist in l for item in sublist]
    # http://stackoverflow.com/questions/952914/


# =============================================================================
# bool
# =============================================================================

def is_false(x: Any) -> bool:
    """Positively false? Evaluates: not x and x is not None."""
    # beware: "0 is False" evaluates to False -- AVOID "is False"!
    # ... but "0 == False" evaluates to True
    # http://stackoverflow.com/questions/3647692/
    # ... but comparisons to booleans with "==" fail PEP8:
    # http://legacy.python.org/dev/peps/pep-0008/
    # ... so use e.g. "bool(x)" or "x" or "not x"
    # http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=True/False_evaluations#True/False_evaluations  # noqa
    return not x and x is not None


# =============================================================================
# Strings
# =============================================================================

def mangle_unicode_to_ascii(s: Any) -> str:
    """Mangle unicode to ASCII, losing accents etc. in the process."""
    # http://stackoverflow.com/questions/1207457
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    return (
        unicodedata.normalize('NFKD', s)
                   .encode('ascii', 'ignore')  # gets rid of accents
                   .decode('ascii')  # back to a string
    )


# =============================================================================
# Object debugging
# =============================================================================

def simple_repr(obj: object) -> str:
    return "<{classname}({kvp})>".format(
        classname=type(obj).__name__,
        kvp=", ".join("{}={}".format(k, repr(v))
                      for k, v in obj.__dict__.items())
    )


def debug_thing(obj, log_level = logging.DEBUG) -> None:
    msgs = ["For {o!r}:".format(o=obj)]
    for attrname in dir(obj):
        attribute = getattr(obj, attrname)
        msgs.append("- {an!r}: {at!r}, of type {t!r}".format(
            an=attrname, at=attribute, t=type(attribute)))
    log.log(log_level, "\n".join(msgs))


# =============================================================================
# Range dictionary for comparisons
# =============================================================================

class BetweenDict(dict):
    # Various alternatives:
    # http://joshuakugler.com/archives/30-BetweenDict,-a-Python-dict-for-value-ranges.html  # noqa
    #   ... NB has initialization default argument bug
    # https://pypi.python.org/pypi/rangedict/0.1.5
    # http://stackoverflow.com/questions/30254739/is-there-a-library-implemented-rangedict-in-python  # noqa
    INVALID_MSG_TYPE = "Key must be an iterable with length 2"
    INVALID_MSG_VALUE = "First element of key must be less than second element"

    # noinspection PyMissingConstructor
    def __init__(self, d: Dict = None) -> None:
        d = d or {}
        for k, v in d.items():
            self[k] = v

    def __getitem__(self, key):
        for k, v in self.items():
            if k[0] <= key < k[1]:
                return v
        raise KeyError("Key '{}' is not in any ranges".format(key))

    def __setitem__(self, key, value):
        try:
            if len(key) != 2:
                raise ValueError(self.INVALID_MSG_TYPE)
        except TypeError:
            raise TypeError(self.INVALID_MSG_TYPE)
        if key[0] < key[1]:
            super().__setitem__((key[0], key[1]), value)
        else:
            raise RuntimeError(self.INVALID_MSG_VALUE)

    def __contains__(self, key):
        try:
            # noinspection PyStatementEffect
            self[key]
            return True
        except KeyError:
            return False


# =============================================================================
# Comparisons
# =============================================================================

@total_ordering
class MinType(object):
    # Something that compares as less than anything
    # http://stackoverflow.com/questions/12971631/sorting-list-by-an-attribute-that-can-be-none
    def __le__(self, other):
        return True

    def __eq__(self, other):
        return self is other


Min = MinType()
