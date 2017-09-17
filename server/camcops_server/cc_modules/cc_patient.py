#!/usr/bin/env python
# camcops_server/cc_modules/cc_patient.py

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

import collections
import logging
from typing import Any, Dict, List, Optional, Union

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.orm_query import get_rows_fieldnames_from_query  # noqa
import hl7
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.expression import and_, ClauseElement, select
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import BigInteger, Date, Integer, UnicodeText

from .cc_audit import audit
from .cc_constants import (
    ACTION,
    DateFormat,
    ERA_NOW,
    FP_ID_DESC_DEFUNCT,
    FP_ID_SHORT_DESC_DEFUNCT,
    FP_ID_NUM_DEFUNCT,
    NUMBER_OF_IDNUMS_DEFUNCT,
    PARAM,
    TSV_PATIENT_FIELD_PREFIX,
)
from .cc_db import GenericTabletRecordMixin
from .cc_dt import (
    format_datetime,
    get_age,
    get_now_localtz,
    PotentialDatetimeType,
)
from .cc_hl7core import make_pid_segment
from .cc_html import answer, get_generic_action_url, get_url_field_value_pair
from .cc_simpleobjects import BarePatientInfo, HL7PatientIdentifier
from .cc_patientidnum import PatientIdNum
from .cc_policy import (
    satisfies_finalize_id_policy,
    satisfies_id_policy,
    satisfies_upload_id_policy,
    TOKENIZED_POLICY_TYPE,
)
from .cc_recipdef import RecipientDefinition
from .cc_report import Report, REPORT_RESULT_TYPE
from .cc_request import CamcopsRequest
from .cc_simpleobjects import IdNumDefinition
from .cc_specialnote import SpecialNote
from .cc_sqla_coltypes import (
    CamcopsColumn,
    IdDescriptorColType,
    PatientNameColType,
    SexColType,
)
from .cc_sqlalchemy import Base
from .cc_unittest import unit_test_ignore
from .cc_version import CAMCOPS_SERVER_VERSION_STRING
from .cc_xml import XML_COMMENT_SPECIAL_NOTES, XmlElement

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Patient class
# =============================================================================

class Patient(GenericTabletRecordMixin, Base):
    """
    Class representing a patient.
    """
    __tablename__ = "patient"

    id = Column(
        "id", Integer,
        nullable=False,
        comment="Primary key (patient ID) on the source tablet device"
        # client PK
    )
    forename = CamcopsColumn(
        "forename", PatientNameColType,
        index=True,
        identifies_patient=True, cris_include=True,
        comment="Forename"
    )
    surname = CamcopsColumn(
        "surname", PatientNameColType,
        index=True,
        identifies_patient=True, cris_include=True,
        comment="Surname"
    )
    dob = CamcopsColumn(
        "dob", Date,  # verified: merge_db handles this correctly
        index=True,
        identifies_patient=True, cris_include=True,
        comment="Date of birth"
        # ... e.g. "2013-02-04"
    )
    sex = CamcopsColumn(
        "sex", SexColType,
        index=True,
        cris_include=True,
        comment="Sex (M, F, X)"
    )
    address = CamcopsColumn(
        "address", UnicodeText,
        identifies_patient=True,
        comment="Address"
    )
    gp = Column(
        "gp", UnicodeText,
        comment="General practitioner (GP)"
    )
    other = CamcopsColumn(
        "other", UnicodeText,
        identifies_patient=True,
        comment="Other details"
    )
    idnums = relationship(
        # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#relationship-custom-foreign
        # http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship  # noqa
        # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#relationship-primaryjoin  # noqa
        "PatientIdNum",
        primaryjoin=(
            "and_("
            " remote(PatientIdNum.patient_id) == foreign(Patient.id), "
            " remote(PatientIdNum._device_id) == foreign(Patient._device_id), "
            " remote(PatientIdNum._era) == foreign(Patient._era), "
            " remote(PatientIdNum._current) == True "
            # " remote(PatientIdNum._when_added_batch_utc) <= foreign(Patient._when_added_batch_utc), "  # noqa
            # " remote(PatientIdNum._when_removed_batch_utc) == foreign(Patient._when_removed_batch_utc), "  # noqa # *** check logic! Wrong!
            ")"
        ),
        uselist=True,
        viewonly=True,
        # Not profiled - any benefit unclear # lazy="joined"
    )

    # THE FOLLOWING ARE DEFUNCT, AND THE SERVER WORKS AROUND OLD TABLETS IN
    # THE UPLOAD API; DELETE ONCE SQLALCHEMY/ALEMBIC RUNNING:
    idnum1 = Column("idnum1", BigInteger, comment="ID number 1")
    idnum2 = Column("idnum2", BigInteger, comment="ID number 2")
    idnum3 = Column("idnum3", BigInteger, comment="ID number 3")
    idnum4 = Column("idnum4", BigInteger, comment="ID number 4")
    idnum5 = Column("idnum5", BigInteger, comment="ID number 5")
    idnum6 = Column("idnum6", BigInteger, comment="ID number 6")
    idnum7 = Column("idnum7", BigInteger, comment="ID number 7")
    idnum8 = Column("idnum8", BigInteger, comment="ID number 8")

    iddesc1 = Column("iddesc1", IdDescriptorColType, comment="ID description 1")  # noqa
    iddesc2 = Column("iddesc2", IdDescriptorColType, comment="ID description 2")  # noqa
    iddesc3 = Column("iddesc3", IdDescriptorColType, comment="ID description 3")  # noqa
    iddesc4 = Column("iddesc4", IdDescriptorColType, comment="ID description 4")  # noqa
    iddesc5 = Column("iddesc5", IdDescriptorColType, comment="ID description 5")  # noqa
    iddesc6 = Column("iddesc6", IdDescriptorColType, comment="ID description 6")  # noqa
    iddesc7 = Column("iddesc7", IdDescriptorColType, comment="ID description 7")  # noqa
    iddesc8 = Column("iddesc8", IdDescriptorColType, comment="ID description 8")  # noqa

    idshortdesc1 = Column("idshortdesc1", IdDescriptorColType, comment="ID short description 1")  # noqa
    idshortdesc2 = Column("idshortdesc2", IdDescriptorColType, comment="ID short description 2")  # noqa
    idshortdesc3 = Column("idshortdesc3", IdDescriptorColType, comment="ID short description 3")  # noqa
    idshortdesc4 = Column("idshortdesc4", IdDescriptorColType, comment="ID short description 4")  # noqa
    idshortdesc5 = Column("idshortdesc5", IdDescriptorColType, comment="ID short description 5")  # noqa
    idshortdesc6 = Column("idshortdesc6", IdDescriptorColType, comment="ID short description 6")  # noqa
    idshortdesc7 = Column("idshortdesc7", IdDescriptorColType, comment="ID short description 7")  # noqa
    idshortdesc8 = Column("idshortdesc8", IdDescriptorColType, comment="ID short description 8")  # noqa

    # Relationships

    # noinspection PyMethodParameters
    @declared_attr
    def special_notes(cls) -> RelationshipProperty:
        # The SpecialNote also allows a link to patients, not just tasks,
        # like this:
        return relationship(
            SpecialNote,
            primaryjoin=(
                "and_("
                " remote(SpecialNote.basetable) == literal({repr_patient_tablename}), "  # noqa
                " remote(SpecialNote.task_id) == foreign(Patient.id), "
                " remote(SpecialNote.device_id) == foreign(Patient._device_id), "  # noqa
                " remote(SpecialNote.era) == foreign(Patient._era) "
                ")".format(
                    repr_patient_tablename=repr(cls.__tablename__),
                )
            ),
            uselist=True,
            order_by="SpecialNote.note_at",
            viewonly=True,  # *** for now!
        )

    @classmethod
    def get_patients_by_idnum(cls,
                              dbsession: SqlASession,
                              which_idnum: int,
                              idnum_value: int) -> List['Patient']:
        if not which_idnum or which_idnum < 1:
            return []
        if idnum_value is None:
            return []
        q = dbsession.query(cls).join(PatientIdNum)  # the join pre-restricts to current ID numbers  # noqa
        q = q.filter(PatientIdNum.which_idnum == which_idnum)
        q = q.filter(PatientIdNum.idnum_value == idnum_value)
        q = q.filter(cls._current == True)  # noqa
        patients = q.all()  # type: List[Patient]
        return patients

    def get_idnum_objects(self) -> List[PatientIdNum]:
        return self.idnums  # type: List[PatientIdNum]

    def get_idnum_definitions(self) -> List[IdNumDefinition]:
        idnums = self.idnums  # type: List[PatientIdNum]
        return [x.get_idnum_definition() for x in idnums if x.is_valid()]

    def get_idnum_raw_values_only(self) -> List[int]:
        idnums = self.idnums  # type: List[PatientIdNum]
        return [x.idnum_value for x in idnums if x.is_valid()]

    def get_xml_root(self, req: CamcopsRequest,
                     skip_fields: List[str] = None) -> XmlElement:
        """Get root of XML tree, as an XmlElementTuple."""
        skip_fields = skip_fields or []
        # Exclude old ID fields:
        for n in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
            nstr = str(n)
            skip_fields.append(FP_ID_NUM_DEFUNCT + nstr)
            skip_fields.append(FP_ID_DESC_DEFUNCT + nstr)
            skip_fields.append(FP_ID_SHORT_DESC_DEFUNCT + nstr)
        branches = self._get_xml_branches(skip_attrs=skip_fields)
        # Now add newer IDs:
        pidnum_branches = []  # type: List[XmlElement]
        for pidnum in self.idnums:  # type: PatientIdNum
            pidnum_branches.append(pidnum._get_xml_root())
        branches.append(XmlElement(
            name="idnums",
            value=pidnum_branches
        ))
        # Special notes
        branches.append(XML_COMMENT_SPECIAL_NOTES)
        special_notes = self.special_notes  # type: List[SpecialNote]
        for sn in special_notes:
            branches.append(sn.get_xml_root())
        return XmlElement(name=self.__tablename__, value=branches)

    def get_dict_for_tsv(self, req: CamcopsRequest) -> Dict[str, Any]:
        d = collections.OrderedDict()
        for f in self.FIELDS:
            # Exclude old ID fields:
            if (not f.startswith(FP_ID_NUM_DEFUNCT) and
                    not f.startswith(FP_ID_DESC_DEFUNCT) and
                    not f.startswith(FP_ID_SHORT_DESC_DEFUNCT)):
                d[TSV_PATIENT_FIELD_PREFIX + f] = getattr(self, f)
        # Now the ID fields:
        cfg = req.config
        for n in cfg.get_which_idnums():
            nstr = str(n)
            d[TSV_PATIENT_FIELD_PREFIX + FP_ID_NUM_DEFUNCT + nstr] = \
                self.get_idnum_value(n)
            d[TSV_PATIENT_FIELD_PREFIX + FP_ID_DESC_DEFUNCT + nstr] = \
                self.get_iddesc(req, n)
            d[TSV_PATIENT_FIELD_PREFIX + FP_ID_SHORT_DESC_DEFUNCT + nstr] = \
                self.get_idshortdesc(req, n)
        return d

    def get_literals_for_anonymisation(self) -> List[str]:
        """Return a list of strings that require removing from other fields in
        the anonymisation process."""
        literals = []  # type: List[str]
        if self.forename:
            forename = self.forename  # type: str # for type checker
            literals.append(forename)
        if self.surname:
            surname = self.surname  # type: str # for type checker
            literals.append(surname)
        if self.address is not None:
            literals.extend([x for x in self.address.split(",") if x])
        if self.other is not None:
            literals.extend([x for x in self.other.split(",") if x])
        literals.extend(str(x) for x in self.get_idnum_raw_values_only()
                        if x is not None)
        return literals

    def get_bare_ptinfo(self) -> BarePatientInfo:
        """Get basic identifying information, as a BarePatientInfo."""
        return BarePatientInfo(
            forename=self.forename,
            surname=self.surname,
            dob=self.dob,
            sex=self.sex,
            idnum_definitions=self.get_idnum_definitions()
        )

    def satisfies_upload_id_policy(self) -> bool:
        """Does the patient satisfy the uploading ID policy?"""
        return satisfies_upload_id_policy(self.get_bare_ptinfo())

    def satisfies_finalize_id_policy(self) -> bool:
        """Does the patient satisfy the finalizing ID policy?"""
        return satisfies_finalize_id_policy(self.get_bare_ptinfo())

    def satisfies_id_policy(self,
                            policy: TOKENIZED_POLICY_TYPE) -> bool:
        """Does the patient satisfy a particular ID policy?"""
        return satisfies_id_policy(policy, self.get_bare_ptinfo())

    def dump(self) -> None:
        """Dump object to database's log."""
        rnc_db.dump_database_object(self, Patient.FIELDS)

    def get_pk(self) -> Optional[int]:
        return self._pk

    def get_era(self) -> Optional[str]:
        return self._era

    def get_device_id(self) -> Optional[int]:
        return self._device_id

    def get_surname(self) -> str:
        """Get surname (in upper case) or ""."""
        return self.surname.upper() if self.surname else ""

    def get_forename(self) -> str:
        """Get forename (in upper case) or ""."""
        return self.forename.upper() if self.forename else ""

    def get_surname_forename_upper(self) -> str:
        """Get "SURNAME, FORENAME" in HTML-safe format, using "UNKNOWN" for
        missing details."""
        s = self.surname.upper() if self.surname else "(UNKNOWN)"
        f = self.forename.upper() if self.surname else "(UNKNOWN)"
        return ws.webify(s + ", " + f)

    def get_dob_html(self, longform: bool) -> str:
        """HTML fragment for date of birth."""
        if longform:
            return "<br>Date of birth: {}".format(
                answer(format_datetime(
                    self.dob, DateFormat.LONG_DATE, default=None)))
        return "DOB: {}.".format(format_datetime(
            self.dob, DateFormat.SHORT_DATE))

    def get_age(self, req: CamcopsRequest,
                default: str = "") -> Union[int, str]:
        """Age (in whole years) today, or default."""
        now = req.now
        return self.get_age_at(now, default=default)

    def get_dob(self) -> Optional[Date]:
        """Date of birth, as a a timezone-naive date."""
        return self.dob

    def get_dob_str(self) -> Optional[str]:
        dob_dt = self.get_dob()
        if dob_dt is None:
            return None
        return format_datetime(dob_dt, DateFormat.SHORT_DATE)

    def get_age_at(self,
                   when: PotentialDatetimeType,
                   default: str = "") -> Union[int, str]:
        """
        Age (in whole years) at a particular date, or default.
        """
        return get_age(self.dob, when, default=default)

    def is_female(self) -> bool:
        """Is sex 'F'?"""
        return self.sex == "F"

    def is_male(self) -> bool:
        """Is sex 'M'?"""
        return self.sex == "M"

    def get_sex(self) -> str:
        """Return sex or ""."""
        return "" if not self.sex else self.sex

    def get_sex_verbose(self, default: str = "sex unknown") -> str:
        """Returns HTML-safe version of sex, or default."""
        return default if not self.sex else ws.webify(self.sex)

    def get_address(self) -> Optional[str]:
        """Returns address (NOT necessarily web-safe)."""
        address = self.address  # type: Optional[str]
        return address

    def get_hl7_pid_segment(self,
                            recipient_def: RecipientDefinition) -> hl7.Segment:
        """Get HL7 patient identifier (PID) segment."""
        # Put the primary one first:
        patient_id_tuple_list = [
            HL7PatientIdentifier(
                id=str(self.get_idnum_value(recipient_def.primary_idnum)),
                id_type=recipient_def.get_id_type(
                    recipient_def.primary_idnum),
                assigning_authority=recipient_def.get_id_aa(
                    recipient_def.primary_idnum)
            )
        ]
        # Then the rest:
        for idobj in self.idnums:
            which_idnum = idobj.which_idnum
            if which_idnum == recipient_def.primary_idnum:
                continue
            idnum_value = idobj.idnum_value
            if idnum_value is None:
                continue
            patient_id_tuple_list.append(
                HL7PatientIdentifier(
                    id=str(idnum_value),
                    id_type=recipient_def.get_id_type(which_idnum),
                    assigning_authority=recipient_def.get_id_aa(which_idnum)
                )
            )
        return make_pid_segment(
            forename=self.get_surname(),
            surname=self.get_forename(),
            dob=self.get_dob(),
            sex=self.get_sex(),
            address=self.get_address(),
            patient_id_list=patient_id_tuple_list,
        )

    def get_idnum_object(self, which_idnum: int) -> Optional[PatientIdNum]:
        """
        Gets the PatientIdNum object for a specified which_idnum, or None.
        """
        idnums = self.idnums  # type: List[PatientIdNum]
        for x in idnums:
            if x.which_idnum == which_idnum:
                return x
        return None

    def get_idnum_value(self, which_idnum: int) -> Optional[int]:
        """Get value of a specific ID number, if present."""
        idobj = self.get_idnum_object(which_idnum)
        return idobj.idnum_value if idobj else None

    def set_idnum_value(self, req: CamcopsRequest,
                        which_idnum: int, idnum_value: int) -> None:
        dbsession = req.dbsession
        ccsession = req.camcops_session
        idnums = self.idnums  # type: List[PatientIdNum]
        for idobj in idnums:
            if idobj.which_idnum == which_idnum:
                idobj.idnum_value = idnum_value
                return
        # Otherwise, make a new one:
        newid = PatientIdNum()
        newid.patient_id = self.id
        newid._device_id = self._device_id
        newid._era = self._era
        newid._current = True
        newid._when_added_exact = req.now_iso8601_era_format
        newid._when_added_batch_utc = req.now_utc
        newid._adding_user_id = ccsession.user_id
        newid._camcops_version = CAMCOPS_SERVER_VERSION_STRING
        dbsession.add(newid)
        self.idnums.append(newid)

    def get_iddesc(self, req: CamcopsRequest,
                   which_idnum: int) -> Optional[str]:
        """Get value of a specific ID description, if present."""
        idobj = self.get_idnum_object(which_idnum)
        return idobj.description(req) if idobj else None

    def get_idshortdesc(self, req: CamcopsRequest,
                        which_idnum: int) -> Optional[str]:
        """Get value of a specific ID short description, if present."""
        idobj = self.get_idnum_object(which_idnum)
        return idobj.short_description(req) if idobj else None

    def get_idnum_html(self,
                       req: CamcopsRequest,
                       which_idnum: int,
                       longform: bool,
                       label_id_numbers: bool = False) -> str:
        """Returns description HTML.

        Args:
            req: Pyramid request
            which_idnum: which ID number? From 1 to NUMBER_OF_IDNUMS inclusive.
            longform: see get_id_generic
            label_id_numbers: whether to use prefix
        """
        idobj = self.get_idnum_object(which_idnum)
        if not idobj:
            return ""
        nstr = str(which_idnum)  # which ID number?
        return self._get_id_generic(
            longform,
            idobj.idnum_value,
            idobj.description(req),
            idobj.short_description(req),
            FP_ID_NUM_DEFUNCT + nstr,
            label_id_numbers
        )

    def get_url_edit_patient(self, req: CamcopsRequest) -> str:
        url = get_generic_action_url(req, ACTION.EDIT_PATIENT)
        url += get_url_field_value_pair(PARAM.SERVERPK, self._pk)
        return url

    def is_preserved(self) -> bool:
        """Is the patient record preserved and erased from the tablet?"""
        return self._pk is not None and self._era != ERA_NOW

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(self, req: CamcopsRequest,
              details: str, from_console: bool = False) -> None:
        """Audits actions to this patient."""
        audit(req,
              details,
              patient_server_pk=self._pk,
              table=Patient.__tablename__,
              server_pk=self._pk,
              from_console=from_console)

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def apply_special_note(
            self,
            req: CamcopsRequest,
            note: str,
            audit_msg: str = "Special note applied manually") -> None:
        """
        Manually applies a special note to a patient.
        WRITES TO DATABASE.
        """
        sn = SpecialNote()
        sn.basetable = self.__tablename__
        sn.task_id = self.id
        sn.device_id = self._device_id
        sn.era = self._era
        sn.note_at = req.now_iso8601_era_format
        sn.user_id = req.camcops_session.user_id
        sn.note = note
        req.dbsession.add(sn)
        self.special_notes.append(sn)
        self.audit(audit_msg)
        # HL7 deletion of corresponding tasks is done in camcops.py

    def get_special_notes_html(self) -> str:
        special_notes = self.special_notes  # type: List[SpecialNote]
        if not special_notes:
            return ""
        note_html = "<br>".join([x.get_note_as_html() for x in special_notes])
        return """
            <div class="specialnote">
                <b>PATIENT SPECIAL NOTES:</b><br>
                {}
            </div>
        """.format(
            note_html
        )


# =============================================================================
# Reports
# =============================================================================

class DistinctPatientReport(Report):
    """Report to show distinct patients."""

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "patient_distinct"

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        return ("(Server) Patients, distinct by name, sex, DOB, all ID "
                "numbers")

    # noinspection PyProtectedMember
    def get_rows_descriptions(self, req: CamcopsRequest) -> REPORT_RESULT_TYPE:
        # Not easy to get UTF-8 fields out of a query in the column headings!
        # So don't do SELECT idnum8 AS 'idnum8 (Addenbrooke's number)';
        # change it post hoc using cc_report.expand_id_descriptions()
        dbsession = req.dbsession
        select_fields = [
            Patient.surname.label("surname"),
            Patient.forename.label("forename"),
            Patient.dob.label("dob"),
            Patient.sex.label("sex"),
        ]
        select_from = Patient.__table__
        # noinspection PyPep8
        wheres = [Patient._current == True]  # type: List[ClauseElement]
        for n in req.config.get_which_idnums():
            desc = req.config.get_id_shortdesc(n)
            aliased_table = PatientIdNum.__table__.alias("i{}".format(n))
            select_fields.append(aliased_table.c.idnum_value.label(desc))
            # noinspection PyPep8
            select_from = select_from.outerjoin(aliased_table, and_(
                aliased_table.c.patient_id == Patient.id,
                aliased_table.c._device_id == Patient._device_id,
                aliased_table.c._era == Patient._era,
                # Note: the following are part of the JOIN, not the WHERE:
                # (or failure to match a row will wipe out the Patient from the
                # OUTER JOIN):
                aliased_table.c._current == True,
                aliased_table.c.which_idnum == n,
            ))
        order_by = [
            Patient.surname,
            Patient.forename,
            Patient.dob,
            Patient.sex,
        ]
        query = select(select_fields)\
            .select_from(select_from)\
            .where(and_(*wheres))\
            .order_by(*order_by)\
            .distinct()
        # log.critical(str(query))
        rows, fieldnames = get_rows_fieldnames_from_query(dbsession, query)
        return rows, fieldnames


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_patient(p: Patient, req: CamcopsRequest) -> None:
    """Unit tests for Patient class."""
    # skip make_tables
    unit_test_ignore("", p.get_xml_root)
    unit_test_ignore("", p.get_literals_for_anonymisation)
    unit_test_ignore("", p.get_dates_for_anonymisation)
    unit_test_ignore("", p.get_bare_ptinfo)
    unit_test_ignore("", p.get_idnum_definitions)
    unit_test_ignore("", p.satisfies_upload_id_policy)
    unit_test_ignore("", p.satisfies_finalize_id_policy)
    # implicitly tested: satisfies_id_policy
    unit_test_ignore("", p.dump)
    unit_test_ignore("", p.get_surname)
    unit_test_ignore("", p.get_forename)
    unit_test_ignore("", p.get_surname_forename_upper)
    unit_test_ignore("", p.get_dob_html, True)
    unit_test_ignore("", p.get_dob_html, False)
    unit_test_ignore("", p.get_age)
    unit_test_ignore("", p.get_dob)
    unit_test_ignore("", p.get_age_at, get_now_localtz())
    unit_test_ignore("", p.is_female)
    unit_test_ignore("", p.is_male)
    unit_test_ignore("", p.get_sex)
    unit_test_ignore("", p.get_sex_verbose)
    # get_hl7_pid_segment: skipped as no default RecipientDefinition yet
    for i in range(-1, 10):  # deliberate, includes duff values
        unit_test_ignore("", p.get_idnum_value, i)
        unit_test_ignore("", p.get_iddesc, i)
        unit_test_ignore("", p.get_idshortdesc, i)
    unit_test_ignore("", p.get_idother_html, True)
    unit_test_ignore("", p.get_idother_html, False)
    unit_test_ignore("", p.get_gp_html, True)
    unit_test_ignore("", p.get_gp_html, False)
    unit_test_ignore("", p.get_address_html, True)
    unit_test_ignore("", p.get_address_html, False)
    unit_test_ignore("", p.get_html_for_page_header)
    unit_test_ignore("", p.get_html_for_task_header, True)
    unit_test_ignore("", p.get_html_for_task_header, False)
    unit_test_ignore("", p.get_html_for_webview_patient_column)
    unit_test_ignore("", p.get_url_edit_patient, req)
    unit_test_ignore("", p.get_special_notes_html)

    # Lastly:
    unit_test_ignore("", p.anonymise)


def ccpatient_unit_tests(req: CamcopsRequest) -> None:
    """Unit tests for cc_patient module."""
    dbsession = req.dbsession
    q = dbsession.query(Patient)
    # noinspection PyProtectedMember
    q = q.filter(Patient._current == True)  # noqa
    patient = q.first()
    if patient is None:
        patient = Patient()
        dbsession.add(patient)
    unit_tests_patient(patient, req)

    # Patient_Report_Distinct: tested via cc_report
