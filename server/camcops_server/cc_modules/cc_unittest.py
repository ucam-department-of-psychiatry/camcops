#!/usr/bin/env python3
# cc_unittest.py

"""
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
"""

import sys
from typing import Any, Tuple, Union


# =============================================================================
# Unit testing
# =============================================================================

FAILEDMSG = "Unit test failed"


def unit_test(message: str, function, *args, **kwargs) -> Any:
    """Print message; return function(*args, **kwargs)."""
    message = message or "Testing " + function.__name__
    print(message + "... ", end="")
    sys.stdout.flush()
    return function(*args, **kwargs)


def unit_test_ignore(message: str, function, *args, **kwargs) -> None:
    """Print message; call/ignore function(*args, **kwargs); print "OK"."""
    unit_test(message, function, *args, **kwargs)
    print("OK")


def unit_test_show(message: str, function, *args, **kwargs) -> None:
    """Print message; call function(*args, **kwargs); print "OK: <result>"."""
    x = unit_test(message, function, *args, **kwargs)
    print("OK: " + str(x))


def unit_test_verify(message: str, function, intended_result: Any,
                     *args, **kwargs) -> None:
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the result was not intended_result."""
    x = unit_test(message, function, *args, **kwargs)
    if x != intended_result:
        raise AssertionError(FAILEDMSG)
    print("OK")


def unit_test_verify_not(message: str, function,
                         must_not_return: Any, *args, **kwargs) -> None:
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the result was must_not_return."""
    x = unit_test(message, function, *args, **kwargs)
    if x == must_not_return:
        raise AssertionError(FAILEDMSG)
    print("OK")


def unit_test_ignore_except(message: str,
                            function,
                            allowed_asserts: Union[Exception,
                                                   Tuple[Exception]],
                            *args, **kwargs) -> None:
    """Print message; call function(*args, **kwargs); allow any exceptions
    passed in the tuple allowed_asserts."""
    try:
        unit_test(message, function, *args, **kwargs)
    except allowed_asserts:
        pass
    print("OK")


def unit_test_verify_except(message: str,
                            function,
                            intended_result: any,
                            allowed_asserts: Union[Exception,
                                                   Tuple[Exception]],
                            *args, **kwargs) -> None:
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


def unit_test_must_raise(message: str,
                         function,
                         required_asserts: Union[Exception,
                                                 Tuple[Exception]],
                         *args, **kwargs) -> None:
    """Print message; call function(*args, **kwargs); raise an AssertionError
    if the function does not raise an exception within the tuple
    required_asserts."""
    try:
        unit_test(message, function, *args, **kwargs)
        raise AssertionError(FAILEDMSG)
    except required_asserts:
        print("OK")


def get_object_name(obj) -> str:
    if hasattr(obj, '__name__'):
        # a class
        return obj.__name__
    else:
        # an instance
        return type(obj).__name__


def unit_test_require_truthy_attribute(obj, attrname: str) -> None:
    if not getattr(obj, attrname):
        raise AssertionError("Object {}: missing attribute {}".format(
            get_object_name(obj), attrname))
