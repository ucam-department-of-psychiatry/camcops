#!/usr/bin/env python
# camcops_server/tasks/diagnosis.py

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

from typing import Any, List

import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.core_query import get_rows_fieldnames_from_raw_sql  # noqa
import hl7
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer, Text

from ..cc_modules.cc_ctvinfo import CtvInfo
from ..cc_modules.cc_db import ancillary_relationship, GenericTabletRecordMixin
from ..cc_modules.cc_hl7core import make_dg1_segment
from ..cc_modules.cc_html import answer, tr
from ..cc_modules.cc_nlp import guess_name_components
from ..cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from ..cc_modules.cc_recipdef import RecipientDefinition
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_report import (
    expand_id_descriptions,
    Report,
    REPORT_RESULT_TYPE,
)
from ..cc_modules.cc_sqlalchemy import Base


# =============================================================================
# Helpers
# =============================================================================

FK_COMMENT = "FK to parent table"


# =============================================================================
# DiagnosisBase
# =============================================================================

class DiagnosisItemBase(GenericTabletRecordMixin):
    seqnum = Column(
        "seqnum", Integer,
        nullable=False,
        comment="Sequence number"
    )
    code = Column(
        "code", Text,
        comment="Diagnostic code"
    )
    description = Column(
        "description", Text,
        comment="Description of the diagnostic code"
    )
    comment = Column(  # new in v2.0.0
        "comment", Text,
        comment="Clinician's comment"
    )

    def get_html_table_row(self) -> str:
        return tr(
            self.seqnum + 1,
            answer(ws.webify(self.code)),
            answer(ws.webify(self.description)),
            answer(ws.webify(self.comment)),
        )

    def get_code_for_hl7(self) -> str:
        # Normal format is to strip out periods, e.g. "F20.0" becomes "F200"
        if not self.code:
            return ""
        return self.code.replace(".", "").upper()

    def get_text_for_hl7(self) -> str:
        return self.description or ""


class DiagnosisBase(TaskHasClinicianMixin, TaskHasPatientMixin, Task):
    relates_to_date = Column(  # new in v2.0.0
        "relates_to_date", DateTime,
        comment="Date that diagnoses relate to"
    )

    items = None  # type: List[DiagnosisItemBase]  # must be overridden by a relationship  # noqa

    MUST_OVERRIDE = "DiagnosisBase: must override fn in derived class"
    hl7_coding_system = "?"

    def get_num_items(self) -> int:
        return len(self.items)

    def is_complete(self) -> bool:
        return self.get_num_items() > 0

    def get_task_html(self, req: CamcopsRequest) -> str:
        html = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="10%">Diagnosis #</th>
                    <th width="10%">Code</th>
                    <th width="40%">Description</th>
                    <th width="40%">Comment</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        for item in self.items:
            html += item.get_html_table_row()
        html += """
            </table>
        """
        return html

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        infolist = []
        for item in self.items:
            infolist.append(CtvInfo(
                content="<b>{}</b>: {}".format(ws.webify(item.code),
                                               ws.webify(item.description))
            ))
        return infolist

    # noinspection PyUnusedLocal
    def get_hl7_extra_data_segments(self, recipient_def: RecipientDefinition) \
            -> List[hl7.Segment]:
        segments = []
        clinician = guess_name_components(self.clinician_name)
        for i in range(len(self.items)):
            set_id = i + 1  # make it 1-based, not 0-based
            item = self.items[i]
            segments.append(make_dg1_segment(
                set_id=set_id,
                diagnosis_datetime=self.get_creation_datetime(),
                coding_system=self.hl7_coding_system,
                diagnosis_identifier=item.get_code_for_hl7(),
                diagnosis_text=item.get_text_for_hl7(),
                clinician_surname=clinician.get("surname") or "",
                clinician_forename=clinician.get("forename") or "",
                clinician_prefix=clinician.get("prefix") or "",
                attestation_datetime=self.get_creation_datetime(),
            ))
        return segments


# =============================================================================
# DiagnosisIcd10
# =============================================================================

class DiagnosisIcd10Item(DiagnosisItemBase, Base):
    __tablename__ = "diagnosis_icd10_item"

    diagnosis_icd10_id = Column(
        "diagnosis_icd10_id", Integer,
        nullable=False,
        comment=FK_COMMENT,
    )


class DiagnosisIcd10(DiagnosisBase, Base):
    # Inheritance order crucial (search is from left to right)
    __tablename__ = "diagnosis_icd10"

    items = ancillary_relationship(
        parent_class_name="DiagnosisIcd10",
        ancillary_class_name="DiagnosisIcd10Item",
        ancillary_fk_to_parent_attr_name="diagnosis_icd10_id",
        ancillary_order_by_attr_name="seqnum"
    )

    shortname = "Diagnosis_ICD10"
    longname = "Diagnostic codes, ICD-10"
    dependent_classes = [DiagnosisIcd10Item]
    hl7_coding_system = "I10"
    # Page A-129 of https://www.hl7.org/special/committees/vocab/V26_Appendix_A.pdf  # noqa


# =============================================================================
# DiagnosisIcd9CM
# =============================================================================

class DiagnosisIcd9CMItem(DiagnosisItemBase, Base):
    __tablename__ = "diagnosis_icd9cm_item"

    diagnosis_icd9cm_id = Column(
        "diagnosis_icd9cm_id", Integer,
        nullable=False,
        comment=FK_COMMENT,
    )


class DiagnosisIcd9CM(DiagnosisBase, Base):
    __tablename__ = "diagnosis_icd9cm"

    items = ancillary_relationship(
        parent_class_name="DiagnosisIcd9CM",
        ancillary_class_name="DiagnosisIcd9CMItem",
        ancillary_fk_to_parent_attr_name="diagnosis_icd9cm_id",
        ancillary_order_by_attr_name="seqnum"
    )

    shortname = "Diagnosis_ICD9CM"
    longname = "Diagnostic codes, ICD-9-CM (DSM-IV-TR)"
    dependent_classes = [DiagnosisIcd9CMItem]
    hl7_coding_system = "I9CM"
    # Page A-129 of https://www.hl7.org/special/committees/vocab/V26_Appendix_A.pdf  # noqa


# =============================================================================
# Reports
# =============================================================================

def get_diagnosis_report_sql(diagnosis_table: str,
                             item_table: str,
                             item_fk_fieldname: str,
                             system: str) -> str:
    sql = """
        SELECT
            p.surname AS surname,
            p.forename AS forename,
            p.dob AS dob,
            p.sex AS sex,
            'IDNUMS_NEED_FIXING' AS idnums,
            d.when_created,
            '{system}' AS system,
            i.code AS code,
            i.description AS description
        FROM patient p
        INNER JOIN {diagnosis_table} d
            ON d.patient_id = p.id
            AND d._device_id = p._device_id
            AND d._era = p._era
        INNER JOIN {item_table} i
            ON i.{item_fk_fieldname} = d.id
            AND i._device_id = d._device_id
            AND i._era = d._era
        WHERE
            p._current
            AND d._current
            AND i._current
        ORDER BY
            p.surname,
            p.forename,
            p.dob,
            p.sex,
            d.when_created,
            i.code
    """.format(
        system=system,
        diagnosis_table=diagnosis_table,
        item_table=item_table,
        item_fk_fieldname=item_fk_fieldname,
    )
    return sql


def get_diagnosis_report(req: CamcopsRequest,
                         diagnosis_table: str,
                         item_table: str,
                         item_fk_fieldname: str,
                         system: str) -> REPORT_RESULT_TYPE:
    sql = get_diagnosis_report_sql(diagnosis_table, item_table,
                                   item_fk_fieldname, system)
    dbsession = req.dbsession
    rows, fieldnames = get_rows_fieldnames_from_raw_sql(dbsession, sql)
    fieldnames = expand_id_descriptions(fieldnames)
    return rows, fieldnames


class DiagnosisICD9CMReport(Report):
    """Report to show ICD-9-CM (DSM-IV-TR) diagnoses."""
    report_id = "diagnoses_icd9cm"
    report_title = ("Diagnosis – ICD-9-CM (DSM-IV-TR) diagnoses for all "
                    "patients")
    param_spec_list = []

    @staticmethod
    def get_rows_descriptions(self, req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        return get_diagnosis_report(
            req,
            diagnosis_table='diagnosis_icd9cm',
            item_table='diagnosis_icd9cm_item',
            item_fk_fieldname='diagnosis_icd9cm_id',
            system='ICD-9-CM'
        )


class DiagnosisICD10Report(Report):
    """Report to show ICD-10 diagnoses."""
    report_id = "diagnoses_icd10"
    report_title = "Diagnosis – ICD-10 diagnoses for all patients"
    param_spec_list = []

    @staticmethod
    def get_rows_descriptions(self, req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        return get_diagnosis_report(
            req,
            diagnosis_table='diagnosis_icd10',
            item_table='diagnosis_icd10_item',
            item_fk_fieldname='diagnosis_icd10_id',
            system='ICD-10'
        )


class DiagnosisAllReport(Report):
    """Report to show all diagnoses."""
    report_id = "diagnoses_all"
    report_title = "Diagnosis – All diagnoses for all patients"
    param_spec_list = []

    @staticmethod
    def get_rows_descriptions(self, req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        sql_icd9cm = get_diagnosis_report_sql(
            diagnosis_table='diagnosis_icd9cm',
            item_table='diagnosis_icd9cm_item',
            item_fk_fieldname='diagnosis_icd9cm_id',
            system='ICD-9-CM'
        )
        sql_icd10 = get_diagnosis_report_sql(
            diagnosis_table='diagnosis_icd10',
            item_table='diagnosis_icd10_item',
            item_fk_fieldname='diagnosis_icd10_id',
            system='ICD-10'
        )
        sql = """
            ({sql_icd9cm})
            UNION
            ({sql_icd10})
            ORDER BY
                surname,
                forename,
                dob,
                sex,
                when_created,
                system,
                code
        """.format(
            sql_icd9cm=sql_icd9cm,
            sql_icd10=sql_icd10,
        )
        dbsession = req.dbsession
        rows, fieldnames = get_rows_fieldnames_from_raw_sql(dbsession, sql)
        fieldnames = expand_id_descriptions(fieldnames)
        return rows, fieldnames
