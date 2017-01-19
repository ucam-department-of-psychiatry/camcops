#!/usr/bin/env python
# cc_dt.py

"""
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
"""

import datetime
import re
import typing
from typing import Optional, Union

import dateutil
import dateutil.parser
import dateutil.tz
import pytz
# don't use pytz.reference: http://stackoverflow.com/questions/17733139


# =============================================================================
# Processing dates and times
# =============================================================================

def get_datetime_from_string(s: str) -> datetime.datetime:
    """Convert string (e.g. ISO-8601) to datetime, or None."""
    if not s:
        return None  # if you parse() an empty string, you get today's date
    return dateutil.parser.parse(s)  # deals with ISO8601 automatically


def get_date_from_string(s: str) -> datetime.date:
    """Convert string (e.g. ISO-8601) to date, or None."""
    if not s:
        return None  # if you parse() an empty string, you get today's date
    return dateutil.parser.parse(s).date()  # deals with ISO8601 automatically


def format_datetime(d: Union[datetime.datetime, datetime.date],
                    fmt: str,
                    default: str = None) -> Optional[str]:
    """Format a datetime with a format string, or return default if None."""
    if d is None:
        return default
    return d.strftime(fmt)


def format_datetime_string(s: str,
                           fmt: str,
                           default: Optional[str] = "(None)") -> str:
    """Converts a string representation of a date (usually from the database)
    into a specified strftime() format."""
    if s is None:
        return default
    dt = get_datetime_from_string(s)
    if dt is None:
        return default
    return dt.strftime(fmt)


def get_date_regex_string(dt: datetime.datetime) -> str:
    # Reminders: ? zero or one, + one or more, * zero or more
    wb = "\\b"  # word boundary; escape the slash
    ws = "\\s"  # whitespace; includes newlines
    # Day, allowing leading zeroes and e.g. "1st, 2nd"
    day = "0*" + str(dt.day) + "(st|nd|rd|th)?"
    # Month, allowing leading zeroes for numeric and e.g. Feb/February
    month_numeric = "0*" + str(dt.month)
    month_word = dt.strftime("%B")
    month_word = month_word[0:3] + "(" + month_word[3:] + ")?"
    month = "(" + month_numeric + "|" + month_word + ")"
    # Year
    year = str(dt.year)
    if len(year) == 4:
        year = "(" + year[0:2] + ")?" + year[2:4]
        # ... makes e.g. (19)?86, to match 1986 or 86
    # Separator: one or more of: whitespace, /, -, comma
    sep = "[" + ws + "/,-]+"
    # ... note that the hyphen has to be at the start or end, otherwise it
    #     denotes a range.
    # Regexes
    basic_regexes = [
        day + sep + month + sep + year,  # e.g. 13 Sep 2014
        month + sep + day + sep + year,  # e.g. Sep 13, 2014
        year + sep + month + sep + day,  # e.g. 2014/09/13
    ]
    return (
        "(" +
        "|".join([wb + x + wb for x in basic_regexes]) +
        ")"
    )

# Testing:
if False:
    TEST_GET_DATE_REGEX = '''
from __future__ import print_function
import dateutil.parser
import re
testdate = dateutil.parser.parse("7 Jan 2013")
teststring = """
   I was born on 07 Jan 2013, m'lud.
   It was 7 January 13, or 7/1/13, or 1/7/13, or
   Jan 7 2013, or 2013/01/07, or 2013-01-07,
   or 7th January
   13 (split over a line)
   or Jan 7th 13
   or a host of other variations.

   BUT NOT 8 Jan 2013, or 2013/02/07, or 2013
   Jan 17, or just a number like 7, or a month
   like January, or a nonspecific date like
   Jan 2013 or 7 January.
"""
regex_string = get_date_regex_string(testdate)
replacement = "GONE"
r = re.compile(regex_string, re.IGNORECASE)
print(r.sub(replacement, teststring))
'''


def get_date_regex(dt: datetime.datetime) -> typing.re.Pattern:
    """Regex for anonymisation. Date."""
    return re.compile(get_date_regex_string(dt), re.IGNORECASE)


def get_now_localtz() -> datetime.datetime:
    """Get the time now in the local timezone."""
    localtz = dateutil.tz.tzlocal()
    return datetime.datetime.now(localtz)


def get_now_utc() -> datetime.datetime:
    """Get the time now in the UTC timezone."""
    return datetime.datetime.now(pytz.utc)


def get_now_utc_notz() -> datetime.datetime:
    """Get the UTC time now, but with no timezone information."""
    return get_now_utc().replace(tzinfo=None)


def convert_datetime_to_utc(datetime_tz) -> datetime.datetime:
    """Convert date/time with timezone to UTC (with UTC timezone)."""
    return datetime_tz.astimezone(pytz.utc)


def convert_datetime_to_utc_notz(datetime_tz) -> datetime.datetime:
    """Convert date/time with timezone to UTC without timezone."""
    # Incoming: date/time with timezone
    utc_tz = datetime_tz.astimezone(pytz.utc)
    return utc_tz.replace(tzinfo=None)


def convert_datetime_to_local(datetime_tz) -> datetime.datetime:
    """Convert date/time with timezone to local timezone."""
    # Establish the local timezone
    localtz = dateutil.tz.tzlocal()
    # Convert to local timezone
    return datetime_tz.astimezone(localtz)


def convert_utc_datetime_without_tz_to_local(datetime_utc_notz) \
        -> datetime.datetime:
    """Convert UTC date/time without timezone to local timezone."""
    # 1. Make it explicitly in the UTC timezone.
    datetime_utc_tz = datetime_utc_notz.replace(tzinfo=pytz.utc)
    # 2. Establish the local timezone
    localtz = dateutil.tz.tzlocal()
    # 3. Convert to local timezone
    return datetime_utc_tz.astimezone(localtz)


def get_duration_h_m(start_string: str,
                     end_string: str,
                     default: str = "N/A") -> str:
    """Calculate the time between two dates/times expressed as strings.

    Return format: string, as one of:
        hh:mm
        -hh:mm
    or
        default parameter
    """
    if start_string is None or end_string is None:
        return default
    start = get_datetime_from_string(start_string)
    end = get_datetime_from_string(end_string)
    duration = end - start  # timedelta: stores days, seconds, microseconds
    # days can be +/-; the others are always +
    minutes = int(round(duration.days * 24*60 + duration.seconds/60))
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
