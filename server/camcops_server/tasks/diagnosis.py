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

import logging
from typing import List, Type

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
import hl7
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.expression import and_, literal, select, SelectBase, union
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Date, Integer, UnicodeText

from camcops_server.cc_modules.cc_ctvinfo import CtvInfo
from camcops_server.cc_modules.cc_db import (
    ancillary_relationship,
    GenericTabletRecordMixin,
)
from camcops_server.cc_modules.cc_hl7core import make_dg1_segment
from camcops_server.cc_modules.cc_html import answer, tr
from camcops_server.cc_modules.cc_nlp import guess_name_components
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_recipdef import RecipientDefinition
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_report import Report
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import DiagnosticCodeColType

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Helpers
# =============================================================================

FK_COMMENT = "FK to parent table"


# =============================================================================
# DiagnosisBase
# =============================================================================

class DiagnosisItemBase(GenericTabletRecordMixin, Base):
    __abstract__ = True

    # noinspection PyMethodParameters
    @declared_attr
    def seqnum(cls) -> Column:
        return Column(
            "seqnum", Integer,
            nullable=False,
            comment="Sequence number"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def code(cls) -> Column:
        return Column(
            "code", DiagnosticCodeColType,
            comment="Diagnostic code"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def description(cls) -> Column:
        return Column(
            "description", UnicodeText,
            comment="Description of the diagnostic code"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def comment(cls) -> Column:
        return Column(  # new in v2.0.0
            "comment", UnicodeText,
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
    __abstract__ = True

    # noinspection PyMethodParameters
    @declared_attr
    def relates_to_date(cls) -> Column:
        return Column(  # new in v2.0.0
            "relates_to_date", Date,
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
            self.get_is_complete_tr(req),
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

class DiagnosisIcd10Item(DiagnosisItemBase):
    __tablename__ = "diagnosis_icd10_item"

    diagnosis_icd10_id = Column(
        "diagnosis_icd10_id", Integer,
        nullable=False,
        comment=FK_COMMENT,
    )


class DiagnosisIcd10(DiagnosisBase):
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

class DiagnosisIcd9CMItem(DiagnosisItemBase):
    __tablename__ = "diagnosis_icd9cm_item"

    diagnosis_icd9cm_id = Column(
        "diagnosis_icd9cm_id", Integer,
        nullable=False,
        comment=FK_COMMENT,
    )


class DiagnosisIcd9CM(DiagnosisBase):
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

ORDER_BY = ["surname", "forename", "dob", "sex",
            "when_created", "system", "code"]


# noinspection PyProtectedMember
def get_diagnosis_report_query(req: CamcopsRequest,
                               diagnosis_class: Type[DiagnosisBase],
                               item_class: Type[DiagnosisItemBase],
                               item_fk_fieldname: str,
                               system: str) -> SelectBase:
    select_fields = [
        Patient.surname.label("surname"),
        Patient.forename.label("forename"),
        Patient.dob.label("dob"),
        Patient.sex.label("sex"),
    ]
    select_from = Patient.__table__
    select_from = select_from.join(diagnosis_class.__table__, and_(
        diagnosis_class.patient_id == Patient.id,
        diagnosis_class._device_id == Patient._device_id,
        diagnosis_class._era == Patient._era
    ))  # nopep8
    select_from = select_from.join(item_class.__table__, and_(
        getattr(item_class, item_fk_fieldname) == diagnosis_class.id,
        item_class._device_id == diagnosis_class._device_id,
        item_class._era == diagnosis_class._era
    ))  # nopep8
    for iddef in req.idnum_definitions:
        n = iddef.which_idnum
        desc = iddef.short_description
        aliased_table = PatientIdNum.__table__.alias("i{}".format(n))
        select_fields.append(aliased_table.c.idnum_value.label(desc))
        select_from = select_from.outerjoin(aliased_table, and_(
            aliased_table.c.patient_id == Patient.id,
            aliased_table.c._device_id == Patient._device_id,
            aliased_table.c._era == Patient._era,
            # Note: the following are part of the JOIN, not the WHERE:
            # (or failure to match a row will wipe out the Patient from the
            # OUTER JOIN):
            aliased_table.c._current == True,
            aliased_table.c.which_idnum == n,
        ))  # nopep8
    select_fields += [
        diagnosis_class.when_created.label("when_created"),
        literal(system).label("system"),
        item_class.code.label("code"),
        item_class.description.label("description"),
    ]
    wheres = [
        Patient._current == True,
        diagnosis_class._current == True,
        item_class._current == True,
    ]  # nopep8
    if not req.user.superuser:
        # Restrict to accessible groups
        group_ids = req.user.ids_of_groups_user_may_report_on
        wheres.append(diagnosis_class._group_id.in_(group_ids))
        # Helpfully, SQLAlchemy will render this as "... AND 1 != 1" if we
        # pass an empty list to in_().
    query = select(select_fields).select_from(select_from).where(and_(*wheres))
    return query


def get_diagnosis_report(req: CamcopsRequest,
                         diagnosis_class: Type[DiagnosisBase],
                         item_class: Type[DiagnosisItemBase],
                         item_fk_fieldname: str,
                         system: str) -> SelectBase:
    query = get_diagnosis_report_query(req, diagnosis_class, item_class,
                                       item_fk_fieldname, system)
    query = query.order_by(*ORDER_BY)
    return query


class DiagnosisICD9CMReport(Report):
    """Report to show ICD-9-CM (DSM-IV-TR) diagnoses."""

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "diagnoses_icd9cm"

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        return ("Diagnosis – ICD-9-CM (DSM-IV-TR) diagnoses for all "
                "patients")

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    def get_query(self, req: CamcopsRequest) -> SelectBase:
        return get_diagnosis_report(
            req,
            diagnosis_class=DiagnosisIcd9CM,
            item_class=DiagnosisIcd9CMItem,
            item_fk_fieldname='diagnosis_icd9cm_id',
            system='ICD-9-CM'
        )


class DiagnosisICD10Report(Report):
    """Report to show ICD-10 diagnoses."""

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "diagnoses_icd10"

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        return "Diagnosis – ICD-10 diagnoses for all patients"

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    def get_query(self, req: CamcopsRequest) -> SelectBase:
        return get_diagnosis_report(
            req,
            diagnosis_class=DiagnosisIcd10,
            item_class=DiagnosisIcd10Item,
            item_fk_fieldname='diagnosis_icd10_id',
            system='ICD-10'
        )


class DiagnosisAllReport(Report):
    """Report to show all diagnoses."""

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "diagnoses_all"

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        return "Diagnosis – All diagnoses for all patients"

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    def get_query(self, req: CamcopsRequest) -> SelectBase:
        sql_icd9cm = get_diagnosis_report_query(
            req,
            diagnosis_class=DiagnosisIcd9CM,
            item_class=DiagnosisIcd9CMItem,
            item_fk_fieldname='diagnosis_icd9cm_id',
            system='ICD-9-CM'
        )
        sql_icd10 = get_diagnosis_report_query(
            req,
            diagnosis_class=DiagnosisIcd10,
            item_class=DiagnosisIcd10Item,
            item_fk_fieldname='diagnosis_icd10_id',
            system='ICD-10'
        )
        query = union(sql_icd9cm, sql_icd10)
        query = query.order_by(*ORDER_BY)
        return query
