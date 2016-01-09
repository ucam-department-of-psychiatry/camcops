#!/usr/bin/env python3
# cc_lang.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import unicodedata
import six


# =============================================================================
# Misc language-oriented functions
# =============================================================================

def mean(values):
    """Return mean of a list of numbers, or None."""
    total = 0.0  # starting with "0.0" causes automatic conversion to float
    n = 0
    for x in values:
        if x is not None:
            total += x
            n += 1
    return total / n if n > 0 else None


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
def derived_class_implements_method(derived, base, method_name):
    derived_method = getattr(derived, method_name, None)
    if derived_method is None:
        return False
    base_method = getattr(base, method_name, None)
    if six.PY2:
        return derived_method.__func__ != base_method.__func__
    else:
        return derived_method is not base_method


def flatten_list(l):
    return [item for sublist in l for item in sublist]
    # http://stackoverflow.com/questions/952914/


def is_false(x):
    """Positively false? Evaluates: not x and x is not None."""
    # beware: "0 is False" evaluates to False -- AVOID "is False"!
    # ... but "0 == False" evaluates to True
    # http://stackoverflow.com/questions/3647692/
    # ... but comparisons to booleans with "==" fail PEP8:
    # http://legacy.python.org/dev/peps/pep-0008/
    # ... so use e.g. "bool(x)" or "x" or "not x"
    # http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=True/False_evaluations#True/False_evaluations  # noqa
    return (not x and x is not None)


def mangle_unicode_to_str(s):
    """Mangle unicode to str, losing accents etc. in the process."""
    # http://stackoverflow.com/questions/1207457
    if s is None:
        return ""
    elif isinstance(s, str):
        return (
            unicodedata.normalize('NFKD', s)
                       .encode('ascii', 'ignore')  # gets rid of accents
                       .decode('ascii')  # back to a string
        )
    else:
        return str(s)
