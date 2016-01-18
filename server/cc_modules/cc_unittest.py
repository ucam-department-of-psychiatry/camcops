#!/usr/bin/env python3
# cc_unittest.py

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

import sys


# =============================================================================
# Unit testing
# =============================================================================

FAILEDMSG = "Unit test failed"


def unit_test(message, function, *args, **kwargs):
    """Print message; return function(*args, **kwargs)."""
    message = message or "Testing " + function.__name__
    print(message + "... ", end="")
    sys.stdout.flush()
    return function(*args, **kwargs)


def unit_test_ignore(message, function, *args, **kwargs):
    """Print message; call/ignore function(*args, **kwargs); print "OK"."""
    unit_test(message, function, *args, **kwargs)
    print("OK")


def unit_test_show(message, function, *args, **kwargs):
    """Print message; call function(*args, **kwargs); print "OK: <result>"."""
    x = unit_test(message, function, *args, **kwargs)
    print("OK: " + str(x))


def unit_test_verify(message, function, intended_result, *args, **kwargs):
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the result was not intended_result."""
    x = unit_test(message, function, *args, **kwargs)
    if x != intended_result:
        raise AssertionError(FAILEDMSG)
    print("OK")


def unit_test_verify_not(message, function, must_not_return, *args, **kwargs):
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the result was must_not_return."""
    x = unit_test(message, function, *args, **kwargs)
    if x == must_not_return:
        raise AssertionError(FAILEDMSG)
    print("OK")


def unit_test_ignore_except(message, function, allowed_asserts, *args,
                            **kwargs):
    """Print message; call function(*args, **kwargs); allow any exceptions
    passed in the tuple allowed_asserts."""
    try:
        unit_test(message, function, *args, **kwargs)
    except allowed_asserts:
        pass
    print("OK")


def unit_test_verify_except(message, function, intended_result,
                            allowed_asserts, *args, **kwargs):
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the result was not intended_result; allow any exceptions passed in
    the tuple allowed_asserts."""
    try:
        x = unit_test(message, function, *args, **kwargs)
        if x != intended_result:
            raise AssertionError(FAILEDMSG)
    except allowed_asserts:
        pass
    print("OK")


def unit_test_must_raise(message, function, required_asserts, *args, **kwargs):
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the function does not raise an exception within the tuple
    required_asserts."""
    try:
        unit_test(message, function, *args, **kwargs)
        raise AssertionError(FAILEDMSG)
    except required_asserts:
        print("OK")


def get_object_name(obj):
    if hasattr(obj, '__name__'):
        # a class
        return obj.__name__
    else:
        # an instance
        return type(obj).__name__


def unit_test_require_truthy_attribute(obj, attrname):
    if not getattr(obj, attrname):
        raise AssertionError("Object {}: missing attribute {}".format(
            get_object_name(obj), attrname))
