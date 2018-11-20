#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_client_api_helpers.py

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

**Additional helper functions used by the client (tablet device) API and the
webview for special features.**

"""

from typing import Tuple

from sqlalchemy.sql.schema import Table

from camcops_server.cc_modules.cc_all_models import NONTASK_CLIENT_TABLENAMES
from camcops_server.cc_modules.cc_blob import Blob
from camcops_server.cc_modules.cc_patient import Patient, PatientIdNum


# =============================================================================
# Table sort order
# =============================================================================

def upload_commit_order_sorter(x: Table) -> Tuple:
    """
    Function to sort tables for the commit phase of the upload.

    Ensure we do the "patient" and "patient_idnum" tables first; task
    indexing depends on referring to those correctly, and so does ID number
    indexing.

    BLOBs also need to come early, as ancillary and task tables may both
    refer to them.

    Ancillary tables need to come before main task tables, or the
    :meth:`camcops_server.cc_modules.cc_task.Task.is_complete` function may go
    wrong.

    Task tables come last.

    Args:
        x: an SQLAlchemy :class:`Table`

    Returns:
        a tuple suitable for use as the key to a ``sort()`` or ``sorted()``
        operation

    Note that ``False`` sorts before ``True``, and see
    https://stackoverflow.com/questions/23090664/sorting-a-list-of-string-in-python-such-that-a-specific-string-if-present-appea.
    """  # noqa
    return (x.name != Patient.__tablename__,
            x.name != PatientIdNum.__tablename__,
            x.name != Blob.__tablename__,
            x.name not in NONTASK_CLIENT_TABLENAMES,
            x.name)


