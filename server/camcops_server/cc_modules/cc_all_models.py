#!/usr/bin/env python
# camcops_server/cc_modules/cc_all_models.py

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

The point of this is to import everything that's an SQLAlchemy model, so
they're registered (and also Task knows about all its subclasses).

"""

# How to suppress "Unused import statement"?
# https://stackoverflow.com/questions/21139329/false-unused-import-statement-in-pycharm  # noqa
# http://codeoptimism.com/blog/pycharm-suppress-inspections-list/

# =============================================================================
# Non-task model imports
# =============================================================================

# noinspection PyUnresolvedReferences
from .cc_audit import AuditEntry
# noinspection PyUnresolvedReferences
from .cc_blob import Blob
# noinspection PyUnresolvedReferences
from .cc_hl7 import HL7Run
# noinspection PyUnresolvedReferences
from .cc_patient import Patient, PatientIdNum
# noinspection PyUnresolvedReferences
from .cc_session import CamcopsSession
# noinspection PyUnresolvedReferences
from .cc_specialnote import SpecialNote
# noinspection PyUnresolvedReferences
from .cc_storedvar import DeviceStoredVar, ServerStoredVar
# noinspection PyUnresolvedReferences
from .cc_user import SecurityAccountLockout, SecurityLoginFailure, User


# =============================================================================
# Task imports
# =============================================================================

# import_submodules("..tasks", __package__)
#
# ... NO LONGER SUFFICIENT as we are using SQLAlchemy relationship clauses that
# are EVALUATED and so require the class names to be in the relevant namespace
# at the time. So doing something equivalent to "import tasks.phq9" -- which is
# what we get from 'import_submodules("..tasks", __package__)' -- isn't enough.
# We need something equivalent to "from tasks.phq9 import Phq9".

# noinspection PyUnresolvedReferences
from ..tasks import *
