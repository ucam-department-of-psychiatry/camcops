#!/usr/bin/env python

r"""
playing/fhir_test.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

Test fhirclient with HAPI FHIR server installed from Docker
https://github.com/hapifhir/hapi-fhir-jpaserver-starter/

"""

from fhirclient import client
from fhirclient.models.questionnaire import Questionnaire

settings = {"app_id": "camcops", "api_base": "http://localhost:8080/fhir"}
smart = client.FHIRClient(settings=settings)

items = []

jsondict = {"status": "active", "item": items}

q = Questionnaire(jsondict=jsondict)
q.create(smart.server)
