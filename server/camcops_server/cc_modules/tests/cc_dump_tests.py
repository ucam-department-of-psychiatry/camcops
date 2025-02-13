"""
camcops_server/cc_modules/tests/cc_dump_tests.py

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

"""

from camcops_server.cc_modules.cc_db import (
    SFN_CAMCOPS_SERVER_VERSION,
    SFN_IS_COMPLETE,
)

from camcops_server.cc_modules.cc_dump import DumpController
from camcops_server.cc_modules.cc_patientidnum import extra_id_colname
from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions
from camcops_server.cc_modules.cc_testfactories import (
    NHSPatientIdNumFactory,
    PatientFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.tests.factories import BmiFactory


class GetDestTableForSrcObjectTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        patient = PatientFactory()
        self.idnum = NHSPatientIdNumFactory(patient=patient)
        self.obj = BmiFactory(patient=patient)
        self.src_table = self.obj.__table__

    def test_copies_table_with_subset_of_columns(self) -> None:
        options = TaskExportOptions()

        controller = DumpController(
            self.engine, self.dbsession, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(self.obj)

        src_names = [c.name for c in self.src_table.c]
        dest_names = [c.name for c in dest_table.c]

        self.assertLess(set(dest_names), set(src_names))

    def test_copies_column_comments(self) -> None:
        options = TaskExportOptions()

        controller = DumpController(
            self.engine, self.dbsession, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(self.obj)

        self.assertEqual(self.src_table.c.id.comment, dest_table.c.id.comment)

    def test_skips_irrelevant_columns(self) -> None:
        options = TaskExportOptions()

        controller = DumpController(
            self.engine, self.dbsession, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(self.obj)

        src_names = [c.name for c in self.src_table.c]
        dest_names = [c.name for c in dest_table.c]

        for c in [
            "_addition_pending",
            "_forcibly_preserved",
            "_manually_erased",
        ]:  # not exhaustive list
            self.assertIn(c, src_names)
            self.assertNotIn(c, dest_names)

    def test_foreign_keys_are_empty_set(self) -> None:
        options = TaskExportOptions()

        controller = DumpController(
            self.engine, self.dbsession, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(self.obj)

        self.assertEqual(dest_table.c.patient_id.foreign_keys, set())

    def test_tablet_record_includes_summaries(self) -> None:
        options = TaskExportOptions(db_include_summaries=True)

        controller = DumpController(
            self.engine, self.dbsession, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(self.obj)
        summary_names = [
            SFN_IS_COMPLETE,
            SFN_CAMCOPS_SERVER_VERSION,
        ]  # not exhaustive list

        dest_names = [c.name for c in dest_table.c]
        self.assertLess(set(summary_names), set(dest_names))

    def test_has_extra_id_columns(self) -> None:
        options = TaskExportOptions(db_patient_id_per_row=True)

        controller = DumpController(
            self.engine, self.dbsession, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(self.obj)
        dest_names = [c.name for c in dest_table.c]

        self.assertIn(extra_id_colname(self.idnum.which_idnum), dest_names)
