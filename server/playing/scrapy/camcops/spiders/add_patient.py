#!/usr/bin/env python

r"""
playing/scrapy/camcops/spiders/add_patient.py

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

Temporary test script for generating potential race conditions when adding
new patients.

Note hardcoded URLs, admin credentials.
Also assumes there is a task schedule with ID 3 and a patient idnum with
which_idnum = 1

Usage:

.. code-block:: bash

    pip install scrapy
    cd server/playing/scrapy/camcops
    scrapy crawl add-patient-spider

"""

from cardinal_pythonlib.nhs import generate_random_nhs_number
from scrapy import FormRequest, Request, Spider


class AddPatientSpider(Spider):
    name = "add-patient-spider"
    start_urls = ["https://www.localhost:8000/login"]

    def parse(self, response):
        assert response.status == 200

        return FormRequest.from_response(
            response,
            formdata={"username": "admin", "password": "adminadmin"},
            callback=self.go_to_add_patient
        )

    def go_to_add_patient(self, response):
        assert response.status == 200

        url = "https://www.localhost:8000/add_patient"

        return Request(url, callback=self.add_patient)

    def add_patient(self, response):
        assert response.status == 200

        for i in range(1, 10):
            yield FormRequest.from_response(
                response,
                formdata=[
                    ("_charset_", "UTF-8"),
                    ("__formid__", "deform"),
                    ("group_id", "1"),
                    ("forename", "Ronnie"),
                    ("surname", "Firefox"),
                    ("__start__", "dob:mapping"),
                    ("date", "2020-04-07"),
                    ("__end__", "dob:mapping"),
                    ("__start__", "sex:rename"),
                    ("deformField7", "M"),
                    ("__end__", "sex:rename"),
                    ("address", "222 A"),
                    ("gp", ""),
                    ("other", ""),
                    ("__start__", "id_references:sequence"),
                    ("__start__", "idnum_sequence:mapping"),
                    ("which_idnum", "1"),
                    ("idnum_value", str(generate_random_nhs_number())),
                    ("__end__", "idnum_sequence:mapping"),
                    ("__end__", "id_references:sequence"),
                    ("__start__", "task_schedules:sequence"),
                    ("__start__", "task_schedule_sequence:mapping"),
                    ("schedule_id", "3"),
                    ("__end__", "task_schedule_sequence:mapping"),
                    ("__end__", "task_schedules:sequence"),
                    ("submit", "submit"),
                ],
                callback=self.patient_added
            )

    def patient_added(self, response):
        pass
