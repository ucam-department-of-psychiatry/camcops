#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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


def derived_class_implements_method(derived, base, method_name):
    # http://stackoverflow.com/questions/1776994
    derived_method = getattr(derived, method_name)
    base_method = getattr(base, method_name)
    return derived_method.__func__ != base_method.__func__


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
    elif isinstance(s, unicode):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    else:
        return str(s)
