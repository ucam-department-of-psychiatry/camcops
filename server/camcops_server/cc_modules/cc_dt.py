#!/usr/bin/env python
# camcops_server/cc_modules/cc_dt.py

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

import datetime
from typing import Optional, Union

import pendulum
from pendulum import Date, Pendulum
import tzlocal

PotentialDatetimeType = Union[None, datetime.datetime, datetime.date,
                              Pendulum, str]


# =============================================================================
# Coerce things to our favourite datetime class
# ... including adding timezone information to timezone-naive objects
# =============================================================================

def coerce_to_pendulum(x: PotentialDatetimeType,
                       assume_local: bool = False) -> Optional[Pendulum]:
    """
    Converts something to a Pendulum, or None.
    May raise:
        pendulum.parsing.exceptions.ParserError
        ValueError
    """
    if not x:  # None and blank string
        return None
    if isinstance(x, Pendulum):
        return x
    tz = get_tz_local() if assume_local else get_tz_utc()
    if isinstance(x, datetime.datetime):
        return pendulum.instance(x, tz=tz)  # (*)
    elif isinstance(x, datetime.date):
        # BEWARE: datetime subclasses date. The order is crucial here.
        # Can also use: type(x) is datetime.date
        midnight = Pendulum.min.time()
        dt = Pendulum.combine(x, midnight)
        return pendulum.instance(dt, tz=tz)  # (*)
    elif isinstance(x, str):
        return pendulum.parse(x, tz=tz)  # (*)  # may raise
    else:
        raise ValueError("Don't know how to convert to Pendulum: "
                         "{!r}".format(x))
    # (*) If x already knew its timezone, it will not
    # be altered; "tz" will only be applied in the absence of other info.


def coerce_to_date(x: PotentialDatetimeType,
                   assume_local: bool = False) -> Optional[Date]:
    p = coerce_to_pendulum(x, assume_local=assume_local)
    if p is None:
        return None
    return p.date()


# =============================================================================
# Format dates/times to strings
# =============================================================================

def format_datetime(d: PotentialDatetimeType,
                    fmt: str,
                    default: str = None) -> Optional[str]:
    """Format a datetime with a format string, or return default if None."""
    d = coerce_to_pendulum(d)
    if d is None:
        return default
    return d.strftime(fmt)


# =============================================================================
# Time zones themselves
# =============================================================================

def get_tz_local() -> datetime.tzinfo:
    return tzlocal.get_localzone()


def get_tz_utc() -> datetime.tzinfo:
    return pendulum.UTC


# =============================================================================
# Now
# =============================================================================

def get_now_localtz() -> Pendulum:
    """Get the time now in the local timezone."""
    tz = get_tz_local()
    return pendulum.now().in_tz(tz)


def get_now_utc() -> Pendulum:
    """Get the time now in the UTC timezone."""
    tz = get_tz_utc()
    return pendulum.utcnow().in_tz(tz)


# =============================================================================
# From one timezone to another
# =============================================================================

def convert_datetime_to_utc(dt: Pendulum) -> Pendulum:
    """Convert date/time with timezone to UTC (with UTC timezone)."""
    tz = get_tz_utc()
    return dt.in_tz(tz)


def convert_datetime_to_local(dt: Pendulum) -> Pendulum:
    """Convert date/time with timezone to local timezone."""
    tz = get_tz_local()
    return dt.in_tz(tz)


# =============================================================================
# Time differences
# =============================================================================

def get_duration_h_m(start: Union[str, Pendulum],
                     end: Union[str, Pendulum],
                     default: str = "N/A") -> str:
    """Calculate the time between two dates/times expressed as strings.

    Return format: string, as one of:
        hh:mm
        -hh:mm
    or
        default parameter
    """
    start = coerce_to_pendulum(start)
    end = coerce_to_pendulum(end)
    if start is None or end is None:
        return default
    duration = end - start
    minutes = duration.in_minutes()
    (hours, minutes) = divmod(minutes, 60)
    if hours < 0:
        # negative... trickier
        # Python's divmod does interesting things with negative numbers:
        # Hours will be negative, and minutes always positive
        hours += 1
        minutes = 60 - minutes
        return "-{}:{}".format(hours, "00" if minutes == 0 else minutes)
    else:
        return "{}:{}".format(hours, "00" if minutes == 0 else minutes)


def get_age(dob: PotentialDatetimeType,
            when: PotentialDatetimeType,
            default: str = "") -> Union[int, str]:
    """
    Age (in whole years) at a particular date, or default.
    """
    dob = coerce_to_pendulum(dob)
    when = coerce_to_pendulum(when)
    if dob is None or when is None:
        return default
    return (when - dob).years
