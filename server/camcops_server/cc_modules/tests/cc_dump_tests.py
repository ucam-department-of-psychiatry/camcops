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

from typing import List, TYPE_CHECKING

import pytest
from sqlalchemy import select
from sqlalchemy.sql.expression import table, text
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import String

from camcops_server.cc_modules.cc_constants import EXTRA_TASK_TABLENAME_FIELD
from camcops_server.cc_modules.cc_db import (
    SFN_CAMCOPS_SERVER_VERSION,
    SFN_IS_COMPLETE,
)

from camcops_server.cc_modules.cc_dump import (
    DumpController,
    copy_tasks_and_summaries,
)
from camcops_server.cc_modules.cc_db import FN_PK, FN_ADDITION_PENDING
from camcops_server.cc_modules.cc_patientidnum import extra_id_colname
from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions
from camcops_server.cc_modules.cc_summaryelement import ExtraSummaryTable
from camcops_server.cc_modules.cc_testfactories import (
    NHSPatientIdNumFactory,
    PatientFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.tests.factories import (
    BmiFactory,
    CardinalExpectationDetectionFactory,
    PhotoSequenceFactory,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session


@pytest.mark.usefixtures("setup_temp_session")
class DumpTestCase(DemoRequestTestCase):
    temp_engine: "Engine"
    temp_session: "Session"


class GetDestTableForSrcObjectTests(DumpTestCase):
    def test_copies_column_comments(self) -> None:
        patient = PatientFactory()
        src_table = patient.__table__

        options = TaskExportOptions()
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(patient)

        self.assertEqual(src_table.c.id.comment, dest_table.c.id.comment)

    def test_copies_column_info_for_foreign_key(self) -> None:
        patient = PatientFactory()
        src_table = patient.__table__

        options = TaskExportOptions()
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(patient)

        self.assertFalse(dest_table.c._device_id.nullable)
        # TODO: if we think it is worth it. Currently will result in index
        # exists error if we try to set this on a removed foreign key.
        # self.assertTrue(dest_table.c._device_id.index)
        self.assertEqual(
            src_table.c._device_id.comment, dest_table.c._device_id.comment
        )

    def test_foreign_keys_are_empty_set(self) -> None:
        patient = PatientFactory()
        bmi = BmiFactory(patient=patient)

        options = TaskExportOptions()
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(bmi)

        self.assertEqual(dest_table.c.patient_id.foreign_keys, set())

    def test_tablet_record_includes_summaries(self) -> None:
        patient = PatientFactory()
        bmi = BmiFactory(patient=patient)

        options = TaskExportOptions(db_include_summaries=True)
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(bmi)
        summary_names = [
            SFN_IS_COMPLETE,
            SFN_CAMCOPS_SERVER_VERSION,
        ]  # not exhaustive list

        dest_names = [c.name for c in dest_table.c]
        self.assertLess(set(summary_names), set(dest_names))

    def test_has_extra_id_num_columns(self) -> None:
        patient = PatientFactory()
        idnum = NHSPatientIdNumFactory(patient=patient)

        options = TaskExportOptions(db_patient_id_per_row=True)
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        dest_table = controller.get_dest_table_for_src_object(patient)
        dest_names = [c.name for c in dest_table.c]

        self.assertIn(extra_id_colname(idnum.which_idnum), dest_names)

    def test_task_descendant_has_extra_task_xref_columns(self) -> None:
        patient = PatientFactory()
        photo_sequence = PhotoSequenceFactory(patient=patient, photos=1)

        options = TaskExportOptions(db_patient_id_per_row=True)
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        single_photo = photo_sequence.photos[0]

        dest_table = controller.get_dest_table_for_src_object(single_photo)
        dest_names = [c.name for c in dest_table.c]

        self.assertIn(EXTRA_TASK_TABLENAME_FIELD, dest_names)


class GetDestTableForEstTests(DumpTestCase):
    def test_copies_table_with_subset_of_columns(self) -> None:
        patient = PatientFactory()
        bmi = BmiFactory(patient=patient)

        options = TaskExportOptions()
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        columns = [
            Column("one", String),
            Column("two", String),
            Column("three", String),
        ]

        est = ExtraSummaryTable(
            tablename="test_tablename",
            xmlname="test_xmlname",
            columns=columns,
            rows=[],
            task=bmi,
        )
        dest_table = controller.get_dest_table_for_est(est)

        src_names = [c.name for c in columns]
        dest_names = [c.name for c in dest_table.c]

        self.assertEqual(set(dest_names), set(src_names))

    def test_appends_extra_id_columns(self) -> None:
        patient = PatientFactory()
        idnum = NHSPatientIdNumFactory(patient=patient)
        bmi = BmiFactory(patient=patient)

        options = TaskExportOptions()
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        est = ExtraSummaryTable(
            tablename="test_tablename",
            xmlname="test_xmlname",
            columns=[],
            rows=[],
            task=bmi,
        )
        dest_table = controller.get_dest_table_for_est(
            est, add_extra_id_cols=True
        )

        dest_names = [c.name for c in dest_table.c]

        self.assertIn(extra_id_colname(idnum.which_idnum), dest_names)

    def test_appends_extra_task_xref_columns(self) -> None:
        patient = PatientFactory()
        photo_sequence = PhotoSequenceFactory(patient=patient, photos=1)

        options = TaskExportOptions()
        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        est = ExtraSummaryTable(
            tablename="test_tablename",
            xmlname="test_xmlname",
            columns=[],
            rows=[],
            task=photo_sequence,
        )
        dest_table = controller.get_dest_table_for_est(
            est, add_extra_id_cols=True
        )

        dest_names = [c.name for c in dest_table.c]

        self.assertIn(EXTRA_TASK_TABLENAME_FIELD, dest_names)


class CopyTasksAndSummariesTests(DumpTestCase):
    def test_task_fields_copied(self) -> None:
        export_options = TaskExportOptions(
            include_blobs=False,
            db_patient_id_per_row=False,
            db_include_summaries=False,
        )

        patient = PatientFactory()
        bmi = BmiFactory(patient=patient)

        copy_tasks_and_summaries(
            tasks=[bmi],
            dst_engine=self.temp_engine,
            dst_session=self.temp_session,
            export_options=export_options,
            req=self.req,
        )
        self.temp_session.commit()

        query = select(text("*")).select_from(table("bmi"))
        result = self.temp_session.execute(query)

        row = next(result)

        # Normal columns
        self.assertAlmostEqual(row.height_m, bmi.height_m)
        self.assertAlmostEqual(row.mass_kg, bmi.mass_kg)

        # Should have been nulled
        for colname in [
            "_addition_pending",
            "_forcibly_preserved",
            "_manually_erased",
        ]:  # not exhaustive list
            self.assertIsNone(getattr(row, colname))

        # No summaries
        self.assertFalse(hasattr(row, SFN_IS_COMPLETE))
        self.assertFalse(hasattr(row, SFN_CAMCOPS_SERVER_VERSION))

    def test_summary_fields_copied(self) -> None:
        export_options = TaskExportOptions(
            include_blobs=False,
            db_patient_id_per_row=False,
            db_include_summaries=True,
        )

        patient = PatientFactory()
        bmi = BmiFactory(patient=patient)

        copy_tasks_and_summaries(
            tasks=[bmi],
            dst_engine=self.temp_engine,
            dst_session=self.temp_session,
            export_options=export_options,
            req=self.req,
        )
        self.temp_session.commit()

        query = select(text("*")).select_from(table("bmi"))
        result = self.temp_session.execute(query)

        row = next(result)

        self.assertTrue(hasattr(row, SFN_IS_COMPLETE))
        self.assertTrue(hasattr(row, SFN_CAMCOPS_SERVER_VERSION))

    def test_has_extra_id_num_columns(self) -> None:
        export_options = TaskExportOptions(
            include_blobs=False,
            db_patient_id_per_row=True,
            db_include_summaries=False,
        )

        patient = PatientFactory()
        idnum = NHSPatientIdNumFactory(patient=patient)
        bmi = BmiFactory(patient=patient)

        copy_tasks_and_summaries(
            tasks=[bmi],
            dst_engine=self.temp_engine,
            dst_session=self.temp_session,
            export_options=export_options,
            req=self.req,
        )
        query = select(text("*")).select_from(table("bmi"))
        result = self.temp_session.execute(query)

        row = next(result)

        self.assertEqual(
            getattr(row, extra_id_colname(idnum.which_idnum)),
            idnum.idnum_value,
        )

    def test_has_extra_task_xref_columns(self) -> None:
        export_options = TaskExportOptions(
            include_blobs=False,
            db_patient_id_per_row=True,
            db_include_summaries=False,
        )

        patient = PatientFactory()
        photo_sequence = PhotoSequenceFactory(patient=patient, photos=1)

        copy_tasks_and_summaries(
            tasks=[photo_sequence],
            dst_engine=self.temp_engine,
            dst_session=self.temp_session,
            export_options=export_options,
            req=self.req,
        )
        query = select(text("*")).select_from(table("photosequence_photos"))
        result = self.temp_session.execute(query)

        row = next(result)

        self.assertEqual(
            getattr(row, EXTRA_TASK_TABLENAME_FIELD), "photosequence"
        )

    def test_has_extra_summary_tables(self) -> None:
        export_options = TaskExportOptions(
            include_blobs=False,
            db_patient_id_per_row=True,
            db_include_summaries=False,
        )

        patient = PatientFactory()
        cardinal_expdet = CardinalExpectationDetectionFactory(
            patient=patient, trials=1, groupspecs=1
        )

        copy_tasks_and_summaries(
            tasks=[cardinal_expdet],
            dst_engine=self.temp_engine,
            dst_session=self.temp_session,
            export_options=export_options,
            req=self.req,
        )

        query = select(text("*")).select_from(
            table("cardinal_expdet_blockprobs")
        )
        result = self.temp_session.execute(query)

        row = next(result)

        self.assertEqual(
            getattr(row, EXTRA_TASK_TABLENAME_FIELD), "cardinal_expdet"
        )

        query = select(text("*")).select_from(
            table("cardinal_expdet_halfprobs")
        )
        result = self.temp_session.execute(query)

        row = next(result)

        self.assertEqual(
            getattr(row, EXTRA_TASK_TABLENAME_FIELD), "cardinal_expdet"
        )


class GenAllDestColumnsTests(DumpTestCase):
    def test_omits_irrelevant_columns(self) -> None:
        options = TaskExportOptions(
            include_blobs=False,
            db_patient_id_per_row=False,
            db_make_all_tables_even_empty=True,
            db_include_summaries=False,
        )

        controller = DumpController(
            self.temp_engine, self.temp_session, options, self.req
        )

        table_column_names: dict[str, List[str]] = {}
        columns = controller.gen_all_dest_columns()

        for column in columns:
            table_column_names.setdefault(column.table.name, []).append(
                column.name
            )

        self.assertIn("bmi", table_column_names)
        self.assertNotIn("blobs", table_column_names)
        self.assertIn(FN_PK, table_column_names["bmi"])
        self.assertNotIn(FN_ADDITION_PENDING, table_column_names["bmi"])
