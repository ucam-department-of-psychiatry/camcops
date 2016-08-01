#!/usr/bin/env python3
# diagnosis.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from typing import List

import cardinal_pythonlib.rnc_web as ws
import hl7

from ..cc_modules.cc_constants import NUMBER_OF_IDNUMS
from ..cc_modules.cc_hl7core import make_dg1_segment
from ..cc_modules.cc_html import answer, tr
from ..cc_modules.cc_nlp import guess_name_components
from ..cc_modules.cc_task import Ancillary, CtvInfo, Task
from ..cc_modules.cc_pls import pls
from ..cc_modules.cc_recipdef import RecipientDefinition
from ..cc_modules.cc_report import (
    expand_id_descriptions,
    Report,
    REPORT_RESULT_TYPE,
)


# =============================================================================
# Helpers
# =============================================================================

def make_diagnosis_item_base_fieldspecs(fkname: str):
    return [
        dict(name=fkname, notnull=True, cctype="INT",
             comment="FK to parent table"),
        # ... FK
        dict(name="seqnum", notnull=True, cctype="INT",
             comment="Sequence number"),
        dict(name="code", cctype="TEXT", comment="Diagnostic code"),
        dict(name="description", cctype="TEXT",
             comment="Description of the diagnostic code"),
    ]


# =============================================================================
# DiagnosisBase
# =============================================================================

class DiagnosisItemBase(Ancillary):
    sortfield = "seqnum"

    @classmethod
    def get_fkname(cls) -> str:
        return cls.fkname

    def get_html_table_row(self) -> str:
        return tr(
            self.seqnum + 1,
            answer(ws.webify(self.code)),
            answer(ws.webify(self.description)),
        )

    def get_code_for_hl7(self) -> str:
        # Normal format is to strip out periods, e.g. "F20.0" becomes "F200"
        if not self.code:
            return ""
        return self.code.replace(".", "").upper()

    def get_text_for_hl7(self) -> str:
        return self.description or ""


class DiagnosisBase(object):
    MUST_OVERRIDE = "DiagnosisBase: must override fn in derived class"
    fieldspecs = []
    has_clinician = True
    hl7_coding_system = "?"

    def get_num_items(self) -> int:
        itemclass = self.dependent_classes[0]
        return self.get_ancillary_item_count(itemclass)

    def get_items(self) -> List[DiagnosisItemBase]:
        itemclass = self.dependent_classes[0]
        return self.get_ancillary_items(itemclass)

    def is_complete(self) -> bool:
        return self.get_num_items() > 0

    def get_task_html(self) -> str:
        items = self.get_items()
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
                    <th width="80%">Description</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        for item in items:
            html += item.get_html_table_row()
        html += """
            </table>
        """
        return html

    def get_clinical_text(self) -> List[CtvInfo]:
        infolist = []
        items = self.get_items()
        for item in items:
            infolist.append(CtvInfo(
                content="<b>{}</b>: {}".format(ws.webify(item.code),
                                               ws.webify(item.description))
            ))
        return infolist

    # noinspection PyUnusedLocal
    def get_hl7_extra_data_segments(self, recipient_def: RecipientDefinition) \
            -> List[hl7.Segment]:
        segments = []
        items = self.get_items()
        clinician = guess_name_components(self.clinician_name)
        for i in range(len(items)):
            set_id = i + 1  # make it 1-based, not 0-based
            item = items[i]
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

class DiagnosisIcd10Item(DiagnosisItemBase):
    tablename = "diagnosis_icd10_item"
    fkname = "diagnosis_icd10_id"
    fieldspecs = make_diagnosis_item_base_fieldspecs(fkname)


class DiagnosisIcd10(DiagnosisBase, Task):
    # Inheritance order crucial (search is from left to right)
    tablename = "diagnosis_icd10"
    shortname = "Diagnosis_ICD10"
    longname = "Diagnostic codes, ICD-10"
    dependent_classes = [DiagnosisIcd10Item]
    hl7_coding_system = "I10"
    # Page A-129 of https://www.hl7.org/special/committees/vocab/V26_Appendix_A.pdf  # noqa


# =============================================================================
# DiagnosisIcd9CM
# =============================================================================

class DiagnosisIcd9CMItem(DiagnosisItemBase):
    tablename = "diagnosis_icd9cm_item"
    fkname = "diagnosis_icd9cm_id"
    fieldspecs = make_diagnosis_item_base_fieldspecs(fkname)


class DiagnosisIcd9CM(DiagnosisBase, Task):
    tablename = "diagnosis_icd9cm"
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
    select_idnums = ["p.idnum{n} AS idnum{n}".format(n=n)
                     for n in range(1, NUMBER_OF_IDNUMS + 1)]
    sql = """
        SELECT
            p.surname AS surname,
            p.forename AS forename,
            p.dob AS dob,
            p.sex AS sex,
            {select_idnums},
            d.when_created,
            '{system}' AS system,
            i.code AS code,
            i.description AS description
        FROM patient p
        INNER JOIN {diagnosis_table} d
            ON d.patient_id = p.id
            AND d._device = p._device
            AND d._era = p._era
        INNER JOIN {item_table} i
            ON i.{item_fk_fieldname} = d.id
            AND i._device = d._device
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
        select_idnums=", ".join(select_idnums),
        system=system,
        diagnosis_table=diagnosis_table,
        item_table=item_table,
        item_fk_fieldname=item_fk_fieldname,
    )
    return sql


def get_diagnosis_report(diagnosis_table: str,
                         item_table: str,
                         item_fk_fieldname: str,
                         system: str) -> REPORT_RESULT_TYPE:
    sql = get_diagnosis_report_sql(diagnosis_table, item_table,
                                   item_fk_fieldname, system)
    (rows, fieldnames) = pls.db.fetchall_with_fieldnames(sql)
    fieldnames = expand_id_descriptions(fieldnames)
    return rows, fieldnames


class DiagnosisICD9CMReport(Report):
    """Report to show ICD-9-CM (DSM-IV-TR) diagnoses."""
    report_id = "diagnoses_icd9cm"
    report_title = ("Diagnosis – ICD-9-CM (DSM-IV-TR) diagnoses for all "
                    "patients")
    param_spec_list = []

    @staticmethod
    def get_rows_descriptions() -> REPORT_RESULT_TYPE:
        return get_diagnosis_report(
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
    def get_rows_descriptions() -> REPORT_RESULT_TYPE:
        return get_diagnosis_report(
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
    def get_rows_descriptions() -> REPORT_RESULT_TYPE:
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
        (rows, fieldnames) = pls.db.fetchall_with_fieldnames(sql)
        fieldnames = expand_id_descriptions(fieldnames)
        return rows, fieldnames
