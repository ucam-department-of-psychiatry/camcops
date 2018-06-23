#!/usr/bin/env python
# camcops_server/cc_modules/cc_analytics.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

Abandoned for now.
"""

_unused = '''

import datetime
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Tuple, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import (
    coerce_to_pendulum,
    format_datetime,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.core_query import count_star
from cardinal_pythonlib.sqlalchemy.schema import get_table_names
from cardinal_pythonlib.sqlalchemy.session import get_engine_from_session
from sqlalchemy.orm import Session as SqlASession

from .cc_constants import DateFormat
from .cc_storedvar import ServerStoredVar, ServerStoredVarNames, StoredVarTypes
from .cc_unittest import unit_test_ignore
from .cc_version import CAMCOPS_SERVER_VERSION

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))

ANALYTICS_FREQUENCY_DAYS = 7  # send analytics weekly

ANALYTICS_URL = "https://egret.psychol.cam.ac.uk/camcops_analytics"
# 131.111.177.41 is egret.psychol.cam.ac.uk, which hosts www.camcops.org.
# Using a numerical IP address saves the DNS lookup step, but fails SSL
# validation (which, in some Python settings, raises an exception).

ANALYTICS_TIMEOUT_MS = 5000

ANALYTICS_PERIOD = datetime.timedelta(days=ANALYTICS_FREQUENCY_DAYS)


def send_analytics_if_necessary(req: "CamcopsRequest") -> None:
    """Send analytics to the CamCOPS base server, if required.

    If analytics reporting is enabled, and analytics have not been sent
    recently, collate and send them to the CamCOPS base server in Cambridge,
    UK.
    """
    cfg = req.config
    now = req.now
    if not cfg.SEND_ANALYTICS:
        # User has disabled analytics reporting.
        return
    dbsession = req.dbsession
    last_sent_var = ServerStoredVar.get_or_create(
        dbsession,
        ServerStoredVarNames.LAST_ANALYTICS_SENT_AT,
        StoredVarTypes.TYPE_TEXT,
        None)
    last_sent_val = last_sent_var.get_value()
    if last_sent_val:
        elapsed = now - coerce_to_pendulum(last_sent_val)
        if elapsed < ANALYTICS_PERIOD:
            # We sent analytics recently.
            return

    # Compile analytics
    now_as_utc_iso_string = format_datetime(now, DateFormat.ISO8601)
    dbsession = req.dbsession
    (table_names, record_counts) = get_all_tables_with_record_counts(dbsession)

    # This is what's sent:
    d = {
        "source": "server",
        "now": now_as_utc_iso_string,
        "camcops_version": str(CAMCOPS_SERVER_VERSION),
        "server": req.server_name,
        "table_names": ",".join(table_names),
        "record_counts": ",".join([str(x) for x in record_counts]),
    }
    # The HTTP_HOST variable might provide some extra information, but is
    # per-request rather than per-server, making analytics involving it that
    # bit more intrusive for little extra benefit, so let's not send it.
    # See http://stackoverflow.com/questions/2297403 for details.

    # Send it.
    encoded_dict = urllib.parse.urlencode(d).encode('ascii')
    req = urllib.request.Request(ANALYTICS_URL, encoded_dict)
    try:
        urllib.request.urlopen(req, timeout=ANALYTICS_TIMEOUT_MS)
        # don't care about any response
    except (urllib.error.URLError, urllib.error.HTTPError):
        # something broke; try again next time
        log.warning("Failed to send analytics to {}", ANALYTICS_URL)
        return

    # Store current time as last-sent time
    log.info("Analytics sent.")
    last_sent_var.set_value(now_as_utc_iso_string)


def get_all_tables_with_record_counts(dbsession: SqlASession) \
        -> Tuple[List[str], List[int]]:
    """
    Returns all database table names ad their associated record counts.

    Returns a tuple (table_names, record_counts); the first element is a
    list of table names, and the second is a list of associated record counts.
    """
    engine = get_engine_from_session(dbsession)
    table_names = get_table_names(engine)
    record_counts = []
    for tablename in table_names:
        # Doesn't distinguish current/noncurrent; counts all records
        record_counts.append(count_star(engine, tablename))
    return table_names, record_counts


def ccanalytics_unit_tests(req: "CamcopsRequest") -> None:
    """Unit tests for the cc_analytics module."""
    dbsession = req.dbsession
    unit_test_ignore("", send_analytics_if_necessary, req)
    unit_test_ignore("", get_all_tables_with_record_counts, dbsession)

'''
