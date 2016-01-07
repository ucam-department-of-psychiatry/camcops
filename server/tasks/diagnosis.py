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

import pythonlib.rnc_web as ws
from cc_modules.cc_hl7core import make_dg1_segment
from cc_modules.cc_html import (
    answer,
    tr,
)
from cc_modules.cc_nlp import guess_name_components
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    STANDARD_ANCILLARY_FIELDSPECS,
    STANDARD_TASK_FIELDSPECS,
    Task,
    Ancillary
)


# =============================================================================
# DiagnosisBase
# =============================================================================

class DiagnosisItemBase(Ancillary):
    MUST_OVERRIDE = "DiagnosisItemBase: must override fn in derived class"

    @classmethod
    def get_tablename(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_fkname(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_ANCILLARY_FIELDSPECS + [
            dict(name=cls.get_fkname(), notnull=True, cctype="INT",
                 comment="FK to parent table"),
            # ... FK
            dict(name="seqnum", notnull=True, cctype="INT",
                 comment="Sequence number"),
            dict(name="code", cctype="TEXT", comment="Diagnostic code"),
            dict(name="description", cctype="TEXT",
                 comment="Description of the diagnostic code"),
        ]

    @classmethod
    def get_sortfield(self):
        return "seqnum"

    def get_html_table_row(self):
        return tr(
            self.seqnum + 1,
            answer(ws.webify(self.code)),
            answer(ws.webify(self.description)),
        )

    def get_code_for_hl7(self):
        # Normal format is to strip out periods, e.g. "F20.0" becomes "F200"
        if not self.code:
            return ""
        return self.code.replace(".", "").upper()

    def get_text_for_hl7(self):
        return self.description or ""


class DiagnosisBase(object):
    MUST_OVERRIDE = "DiagnosisBase: must override fn in derived class"

    @classmethod
    def get_tablename(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_taskshortname(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_tasklongname(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_itemclass(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_hl7_coding_system(cls):
        raise NotImplementedError(cls.MUST_OVERRIDE)

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS

    @classmethod
    def get_dependent_classes(cls):
        return [cls.get_itemclass()]

    def get_num_items(self):
        itemclass = self.get_itemclass()
        return self.get_ancillary_item_count(itemclass)

    def get_items(self):
        itemclass = self.get_itemclass()
        return self.get_ancillary_items(itemclass)

    def is_complete(self):
        return self.get_num_items() > 0

    def get_task_html(self):
        items = self.get_items()
        html = self.get_standard_clinician_block() + """
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

    def get_clinical_text(self):
        fielddictlist = []
        items = self.get_items()
        for item in items:
            fielddictlist.append({
                "content": "<b>{}</b>: {}".format(ws.webify(item.code),
                                                  ws.webify(item.description))
            })
        return fielddictlist

    def get_hl7_extra_data_segments(self, recipient_def):
        segments = []
        items = self.get_items()
        clinician = guess_name_components(self.clinician_name)
        for i in range(len(items)):
            set_id = i + 1  # make it 1-based, not 0-based
            item = items[i]
            segments.append(make_dg1_segment(
                set_id=set_id,
                diagnosis_datetime=self.get_creation_datetime(),
                coding_system=self.get_hl7_coding_system(),
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
    @classmethod
    def get_tablename(cls):
        return "diagnosis_icd10_item"

    @classmethod
    def get_fkname(cls):
        return "diagnosis_icd10_id"


class DiagnosisIcd10(DiagnosisBase, Task):
    # Inheritance order crucial (search is from left to right)
    @classmethod
    def get_tablename(cls):
        return "diagnosis_icd10"

    @classmethod
    def get_taskshortname(cls):
        return "Diagnosis_ICD10"

    @classmethod
    def get_tasklongname(cls):
        return "Diagnostic codes, ICD-10"

    @classmethod
    def get_itemclass(cls):
        return DiagnosisIcd10Item

    @classmethod
    def get_hl7_coding_system(self):
        # Page A-129 of:
        # https://www.hl7.org/special/committees/vocab/V26_Appendix_A.pdf
        return "I10"


# =============================================================================
# DiagnosisIcd9CM
# =============================================================================

class DiagnosisIcd9CMItem(DiagnosisItemBase):
    @classmethod
    def get_tablename(cls):
        return "diagnosis_icd9cm_item"

    @classmethod
    def get_fkname(cls):
        return "diagnosis_icd9cm_id"


class DiagnosisIcd9CM(DiagnosisBase, Task):
    @classmethod
    def get_tablename(cls):
        return "diagnosis_icd9cm"

    @classmethod
    def get_taskshortname(cls):
        return "Diagnosis_ICD9CM"

    @classmethod
    def get_tasklongname(cls):
        return "Diagnostic codes, ICD-9-CM (DSM-IV-TR)"

    @classmethod
    def get_itemclass(cls):
        return DiagnosisIcd9CMItem

    @classmethod
    def get_hl7_coding_system(self):
        # Page A-129 of:
        # https://www.hl7.org/special/committees/vocab/V26_Appendix_A.pdf
        return "I9CM"
