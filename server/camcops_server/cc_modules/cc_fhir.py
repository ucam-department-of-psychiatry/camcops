#!/usr/bin/env python

"""camcops_server/cc_modules/cc_fhir.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

**Implements communication with a FHIR server.**
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskFhir
    from camcops_server.cc_modules.cc_request import CamcopsRequest


class FhirExportException(Exception):
    pass


class FhirTaskExporter(object):
    def export_task(self,
                    req: "CamcopsRequest",
                    exported_task_fhir: "ExportedTaskFhir") -> None:
        pass
