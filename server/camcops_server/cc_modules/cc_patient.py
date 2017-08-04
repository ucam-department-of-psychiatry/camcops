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
import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from arrow import Arrow
import dateutil.relativedelta
import hl7

import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text

from .cc_audit import audit
from .cc_constants import (
    ACTION,
    DATEFORMAT,
    ERA_NOW,
    FP_ID_DESC,
    FP_ID_SHORT_DESC,
    FP_ID_NUM,
    NUMBER_OF_IDNUMS_DEFUNCT,
    PARAM,
    TSV_PATIENT_FIELD_PREFIX,
)
from .cc_db import GenericTabletRecordMixin
from .cc_dt import (
    format_datetime,
    format_datetime_string,
    get_date_from_string,
    get_datetime_from_string,
    get_now_localtz,
)
from .cc_hl7core import make_pid_segment
from .cc_html import answer, get_generic_action_url, get_url_field_value_pair
from .cc_logger import BraceStyleAdapter
from .cc_simpleobjects import BarePatientInfo, HL7PatientIdentifier
from .cc_patientidnum import PatientIdNum
from .cc_policy import (
    satisfies_finalize_id_policy,
    satisfies_id_policy,
    satisfies_upload_id_policy,
    TOKENIZED_POLICY_TYPE,
)
from .cc_report import expand_id_descriptions
from .cc_recipdef import RecipientDefinition
from .cc_report import Report, REPORT_RESULT_TYPE
from .cc_request import CamcopsRequest
from .cc_specialnote import SpecialNote
from .cc_sqla_coltypes import (
    BigIntUnsigned,
    CamcopsColumn,
    DateTimeAsIsoTextColType,
    IdDescriptorColType,
    IntUnsigned,
    PatientNameColType,
    SexColType,
)
from .cc_sqlalchemy import Base, get_rows_fieldnames_from_raw_sql
from .cc_unittest import unit_test_ignore
from .cc_version import CAMCOPS_SERVER_VERSION_STRING
from .cc_xml import (
    make_xml_branches_from_fieldspecs,
    XML_COMMENT_SPECIAL_NOTES,
    XmlDataTypes,
    XmlElement,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Patient class
# =============================================================================

class Patient(GenericTabletRecordMixin, Base):
    """Class representing a patient."""
    __tablename__ = "patient"

    id = Column(
        "id", IntUnsigned,
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
        "dob", DateTimeAsIsoTextColType,  # *** change; Date?
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
        "address", Text,
        identifies_patient=True,
        comment="Address"
    )
    gp = Column(
        "gp", Text,
        comment="General practitioner (GP)"
    )
    other = CamcopsColumn(
        "other", Text,
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
        )
    )

    # THE FOLLOWING ARE DEFUNCT, AND THE SERVER WORKS AROUND OLD TABLETS IN
    # THE UPLOAD API; DELETE ONCE SQLALCHEMY/ALEMBIC RUNNING:
    idnum1 = Column("idnum1", BigIntUnsigned, comment="ID number 1")
    idnum2 = Column("idnum2", BigIntUnsigned, comment="ID number 2")
    idnum3 = Column("idnum3", BigIntUnsigned, comment="ID number 3")
    idnum4 = Column("idnum4", BigIntUnsigned, comment="ID number 4")
    idnum5 = Column("idnum5", BigIntUnsigned, comment="ID number 5")
    idnum6 = Column("idnum6", BigIntUnsigned, comment="ID number 6")
    idnum7 = Column("idnum7", BigIntUnsigned, comment="ID number 7")
    idnum8 = Column("idnum8", BigIntUnsigned, comment="ID number 8")

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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._idnums = None  # type: List[PatientIdNum]
        self._special_notes = None  # type: List[SpecialNote]

    @reconstructor
    def init_on_load(self) -> None:
        # http://docs.sqlalchemy.org/en/latest/orm/constructors.html
        self._idnums = None  # type: List[PatientIdNum]
        self._special_notes = None  # type: List[SpecialNote]

    def get_idnum_objects(self) -> List[PatientIdNum]:
        return self.idnums
        # if self._idnums is None:
        #     dbsession = SqlASession.object_session(self)  # type: SqlASession
        #     q = dbsession.query(PatientIdNum)
        #     q = q.filter(PatientIdNum.patient_id == self.id)
        #     q = q.filter(PatientIdNum._device_id == self._device_id)
        #     q = q.filter(PatientIdNum._era == self._era)
        #     q = q.filter(PatientIdNum._when_added_batch_utc <= self._when_added_batch_utc)  # noqa
        #     q = q.filter(PatientIdNum._when_removed_batch_utc == self._when_removed_batch_utc)  # noqa # *** check logic! Wrong!
        #     self._idnums = q.fetchall()  # type: List[PatientIdNum]
        # return self._idnums

    def get_idnum_which_value_tuples(self) \
            -> List[Tuple[int, int]]:
        return [(x.which_idnum, x.idnum_value)
                for x in self.get_idnum_objects()]

    def get_idnum_raw_values_only(self) -> List[int]:
        return [x.idnum_value for x in self.get_idnum_objects()]

    def get_xml_root(self, request: CamcopsRequest,
                     skip_fields: List[str] = None) -> XmlElement:
        """Get root of XML tree, as an XmlElementTuple."""
        skip_fields = skip_fields or []
        # Exclude old ID fields:
        for n in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
            nstr = str(n)
            skip_fields.append(FP_ID_NUM + nstr)
            skip_fields.append(FP_ID_DESC + nstr)
            skip_fields.append(FP_ID_SHORT_DESC + nstr)
        branches = make_xml_branches_from_fieldspecs(
            self, skip_fields=skip_fields)
        # Now add newer IDs:
        cfg = request.config
        for n in cfg.get_which_idnums():
            branches.append(XmlElement(name=FP_ID_NUM + nstr,
                                       value=self.get_idnum_value(n),
                                       datatype=XmlDataTypes.INTEGER,
                                       comment="ID number " + nstr))
            branches.append(XmlElement(name=FP_ID_DESC + nstr,
                                       value=self.get_iddesc(request, n),
                                       datatype=XmlDataTypes.STRING,
                                       comment="ID description " + nstr))
            branches.append(XmlElement(name=FP_ID_SHORT_DESC + nstr,
                                       value=self.get_idshortdesc(request, n),
                                       datatype=XmlDataTypes.STRING,
                                       comment="ID short description " + nstr))
        # Special notes
        branches.append(XML_COMMENT_SPECIAL_NOTES)
        for sn in self.get_special_notes():
            branches.append(sn.get_xml_root())
        return XmlElement(name=self.TABLENAME, value=branches)

    def get_dict_for_tsv(self, request: CamcopsRequest) -> Dict[str, Any]:
        d = collections.OrderedDict()
        for f in self.FIELDS:
            # Exclude old ID fields:
            if (not f.startswith(FP_ID_NUM) and
                    not f.startswith(FP_ID_DESC) and
                    not f.startswith(FP_ID_SHORT_DESC)):
                d[TSV_PATIENT_FIELD_PREFIX + f] = getattr(self, f)
        # Now the ID fields:
        cfg = request.config
        for n in cfg.get_which_idnums():
            nstr = str(n)
            d[TSV_PATIENT_FIELD_PREFIX + FP_ID_NUM + nstr] = \
                self.get_idnum_value(n)
            d[TSV_PATIENT_FIELD_PREFIX + FP_ID_DESC + nstr] = \
                self.get_iddesc(request, n)
            d[TSV_PATIENT_FIELD_PREFIX + FP_ID_SHORT_DESC + nstr] = \
                self.get_idshortdesc(request, n)
        return d

    def anonymise(self) -> None:
        """Wipes the object's patient-identifiable content.
        Does NOT write to database."""
        # Save temporarily
        sex = self.sex
        dob = self.get_dob()
        # Wipe
        rnc_db.blank_object(self, Patient.FIELDS)
        # Replace selected values
        self.sex = sex
        if dob:
            dob = dob.replace(day=1)  # set DOB to first of the month
            self.dob = format_datetime(dob, DATEFORMAT.ISO8601_DATE_ONLY)

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

    def get_dates_for_anonymisation(self) -> List[Union[datetime.date,
                                                        datetime.datetime]]:
        """Return a list of dates/datetimes that require removing from other
        fields in the anonymisation process."""
        return [
            self.get_dob(),
        ]

    def get_bare_ptinfo(self) -> BarePatientInfo:
        """Get basic identifying information, as a BarePatientInfo."""
        return BarePatientInfo(
            forename=self.forename,
            surname=self.surname,
            dob=self.dob,
            sex=self.sex,
            whichidnum_idnumvalue_tuples=self.get_whichidnum_idnumvalue_tuples()
        )

    def get_whichidnum_idnumvalue_tuples(self) -> List[Tuple[int, int]]:
        """Return list of (which_idnum, idnum_value) tuples."""
        arr = []  # type: List[Tuple[int, int]]
        for idobj in self.get_idnum_objects():
            if idobj.which_idnum is not None and idobj.idnum_value is not None:
                arr.append((idobj.which_idnum, idobj.idnum_value))
        return arr

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
                answer(format_datetime_string(
                    self.dob, DATEFORMAT.LONG_DATE, default=None)))
        return "DOB: {}.".format(format_datetime_string(
            self.dob, DATEFORMAT.SHORT_DATE))

    def get_age(self, request: CamcopsRequest,
                default: str = "") -> Union[int, str]:
        """Age (in whole years) today, or default."""
        now = request.now_arrow
        return self.get_age_at(now, default=default)

    def get_dob(self) -> Optional[datetime.date]:
        """Date of birth, as a a timezone-naive date."""
        if self.dob is None:
            return None
        return get_date_from_string(self.dob)

    def get_dob_str(self) -> Optional[str]:
        dob_dt = self.get_dob()
        if dob_dt is None:
            return None
        return format_datetime(dob_dt, DATEFORMAT.SHORT_DATE)

    def get_age_at(self,
                   when: Union[datetime.datetime, datetime.date, Arrow],
                   default: str = "") -> Union[int, str]:
        """Age (in whole years) at a particular date, or default.

        Args:
            when: date or datetime or Arrow
            default: default
        """
        dob = self.get_dob()  # date; timezone-naive
        if dob is None:
            return default
        # when must be a date, i.e. timezone-naive. So:
        if type(when) is not datetime.date:
            when = when.date()
        # if it wasn't timezone-naive, we could make it timezone-naive: e.g.
        # now = now.replace(tzinfo = None)
        return dateutil.relativedelta.relativedelta(when, dob).years

    def get_age_at_string(self,
                          now_string: str,
                          default: str = "") -> Union[int, str]:
        """Age (in whole years) at a particular date, or default.

        Args:
            now_string: date/time in string format, e.g. ISO-8601
            default: default string to use
        """
        if now_string is None:
            return default
        return self.get_age_at(get_datetime_from_string(now_string))

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
        for idobj in self.get_idnum_objects():
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
        for x in self.get_idnum_objects():
            if x.which_idnum == which_idnum:
                return x
        return None

    def get_idnum_value(self, which_idnum: int) -> Optional[int]:
        """Get value of a specific ID number, if present."""
        idobj = self.get_idnum_object(which_idnum)
        return idobj.idnum_value if idobj else None

    def set_idnum_value(self, request: CamcopsRequest,
                        which_idnum: int, idnum_value: int) -> None:
        dbsession = request.dbsession
        ccsession = request.camcops_session
        idobjs = self.get_idnum_objects()
        for idobj in idobjs:
            if idobj.which_idnum == which_idnum:
                idobj.idnum_value = idnum_value
                return
        # Otherwise, make a new one:
        newid = PatientIdNum()
        newid.patient_id = self.id
        newid._device_id = self._device_id
        newid._era = self._era
        newid._current = True
        newid._when_added_exact = request.now_iso8601_era_format
        newid._when_added_batch_utc = request.now_utc_datetime
        newid._adding_user_id = ccsession.user_id
        newid._camcops_version = CAMCOPS_SERVER_VERSION_STRING
        dbsession.add(newid)
        self.idnums.append(newid)

    def get_iddesc(self, request: CamcopsRequest,
                   which_idnum: int) -> Optional[str]:
        """Get value of a specific ID description, if present."""
        cfg = request.config
        idobj = self.get_idnum_object(which_idnum)
        return idobj.description(cfg) if idobj else None

    def get_idshortdesc(self, request: CamcopsRequest,
                        which_idnum: int) -> Optional[str]:
        """Get value of a specific ID short description, if present."""
        cfg = request.config
        idobj = self.get_idnum_object(which_idnum)
        return idobj.short_description(cfg) if idobj else None

    def get_idnum_html(self,
                       request: CamcopsRequest,
                       which_idnum: int,
                       longform: bool,
                       label_id_numbers: bool = False) -> str:
        """Returns description HTML.

        Args:
            request: Pyramid request
            which_idnum: which ID number? From 1 to NUMBER_OF_IDNUMS inclusive.
            longform: see get_id_generic
            label_id_numbers: whether to use prefix
        """
        cfg = request.config
        idobj = self.get_idnum_object(which_idnum)
        if not idobj:
            return ""
        nstr = str(which_idnum)  # which ID number?
        return self._get_id_generic(
            longform,
            idobj.idnum_value,
            idobj.description(cfg),
            idobj.short_description(cfg),
            FP_ID_NUM + nstr,
            label_id_numbers
        )

    def get_idother_html(self, longform: bool) -> str:
        """Get HTML for 'other' information."""
        if not self.other:
            return ""
        if longform:
            return "<br>Other details: <b>{}</b>".format(ws.webify(self.other))
        return ws.webify(self.other)

    def get_gp_html(self, longform: bool) -> str:
        """Get HTML for general practitioner details."""
        if not self.gp:
            return ""
        if longform:
            return "<br>GP: <b>{}</b>".format(ws.webify(self.gp))
        return ws.webify(self.gp)

    def get_address_html(self, longform: bool) -> str:
        """Get HTML for address details."""
        if not self.address:
            return ""
        if longform:
            return "<br>Address: <b>{}</b>".format(ws.webify(self.address))
        return ws.webify(self.address)

    def get_html_for_page_header(self, request: CamcopsRequest) -> str:
        """Get HTML used for PDF page header."""
        longform = False
        cfg = request.config
        h = "<b>{}</b> ({}). {}".format(
            self.get_surname_forename_upper(),
            self.get_sex_verbose(),
            self.get_dob_html(longform=longform),
        )
        for idobj in self.get_idnum_objects():
            h += " " + idobj.get_html(cfg=cfg, longform=longform)
        h += " " + self.get_idother_html(longform=longform)
        return h

    def get_html_for_task_header(self, request: CamcopsRequest,
                                 label_id_numbers: bool = False) -> str:
        """Get HTML used for patient details in tasks."""
        longform = True
        cfg = request.config
        h = """
            <div class="patient">
                <b>{name}</b> ({sex})
                {dob}
        """.format(
            name=self.get_surname_forename_upper(),
            sex=self.get_sex_verbose(),
            dob=self.get_dob_html(longform=longform),
        )
        for idobj in self.get_idnum_objects():
            h += """
                {} <!-- ID{} -->
            """.format(
                idobj.get_html(cfg=cfg,
                               longform=longform,
                               label_id_numbers=label_id_numbers),
                idobj.which_idnum
            )
        h += """
                {} <!-- ID_other -->
                {} <!-- address -->
                {} <!-- GP -->
            </div>
        """.format(
            self.get_idother_html(longform=longform),
            self.get_address_html(longform=longform),
            self.get_gp_html(longform=longform),
        )
        h += self.get_special_notes_html()
        return h

    def get_html_for_webview_patient_column(
            self, request: CamcopsRequest) -> str:
        """Get HTML for patient details in task summary view."""
        return """
            <b>{}</b> ({}, {}, aged {})
        """.format(
            self.get_surname_forename_upper(),
            self.get_sex_verbose(),
            format_datetime_string(self.dob, DATEFORMAT.SHORT_DATE,
                                   default="?"),
            self.get_age(request=request, default="?"),
        )

    def get_html_for_id_col(self, request: CamcopsRequest) -> str:
        """Returns HTML used for patient ID column in task summary view."""
        hlist = []
        longform = False
        cfg = request.config
        for idobj in self.get_idnum_objects():
            hlist.append(idobj.get_html(cfg=cfg, longform=longform))
        hlist.append(self.get_idother_html(longform=longform))
        return " ".join(hlist)

    def get_url_edit_patient(self, request: CamcopsRequest) -> str:
        url = get_generic_action_url(request, ACTION.EDIT_PATIENT)
        url += get_url_field_value_pair(PARAM.SERVERPK, self._pk)
        return url

    def is_preserved(self) -> bool:
        """Is the patient record preserved and erased from the tablet?"""
        return self._pk is not None and self._era != ERA_NOW

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(self, details: str, from_console: bool = False) -> None:
        """Audits actions to this patient."""
        audit(details,
              patient_server_pk=self._pk,
              table=Patient.TABLENAME,
              server_pk=self._pk,
              from_console=from_console)

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def get_special_notes(self) -> List[SpecialNote]:
        if self._special_notes is None:
            dbsession = SqlASession.object_session(self)  # type: SqlASession
            patient_id = self.id  # type: int
            self._special_notes = SpecialNote.get_all_instances(
                dbsession=dbsession,
                basetable=self.__tablename__,
                task_or_patient_id=patient_id,
                device_id=self._device_id,
                era=self._era
            )  # type: List[SpecialNote]
        # noinspection PyTypeChecker
        return self._special_notes

    def apply_special_note(
            self,
            request: CamcopsRequest,
            note: str,
            audit_msg: str = "Special note applied manually") -> None:
        """
        Manually applies a special note to a patient.
        WRITES TO DATABASE.
        """
        sn = SpecialNote()
        sn.basetable = self.__tablename__
        sn.task_or_patient_id = self.id
        sn.device_id = self._device_id
        sn.era = self._era
        sn.note_at = request.now_iso8601_era_format
        sn.user_id = request.camcops_session.user_id
        sn.note = note
        request.dbsession.add(sn)
        self.audit(audit_msg)
        # HL7 deletion of corresponding tasks is done in camcops.py
        self._special_notes = None   # will be reloaded if needed
        # *** alter this to an SQLAlchemy relationship?

    def get_special_notes_html(self) -> str:
        special_notes = self.get_special_notes()
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
    report_id = "patient_distinct"
    report_title = ("(Server) Patients, distinct by name, sex, DOB, all ID "
                    "numbers")
    param_spec_list = []

    def get_rows_descriptions(self, request: CamcopsRequest,
                              **kwargs) -> REPORT_RESULT_TYPE:
        # Not easy to get UTF-8 fields out of a query in the column headings!
        # So don't do SELECT idnum8 AS 'idnum8 (Addenbrooke's number)';
        # change it post hoc using cc_report.expand_id_descriptions()
        patienttable = Patient.__tablename__
        select_fields = [
            "p.surname AS surname",
            "p.forename AS forename",
            "p.dob AS dob",
            "p.sex AS sex"
        ]
        from_tables = ["{} AS p".format(patienttable)]
        for n in request.config.get_which_idnums():
            nstr = str(n)
            fieldalias = FP_ID_NUM + nstr  # idnum7
            idtablealias = "i" + nstr  # e.g. i7
            select_fields.append("{}.idnum_value AS {}".format(idtablealias,
                                                               fieldalias))
            from_tables.append(
                """
                    LEFT JOIN {idtable} AS {idtablealias} ON (
                        {idtablealias}.patient_id = p.id
                        AND {idtablealias}._device_id = p._device_id
                        AND {idtablealias}._era = p._era
                        AND {idtablealias}._current
                        AND {idtablealias}.which_idnum = {which_idnum}
                    )
                """.format(
                    idtable=PatientIdNum.tablename,
                    idtablealias=idtablealias,
                    which_idnum=nstr,
                    # ... ugly! No parameters. Still, we know what we've got.
                )
            )
        sql = """
            SELECT DISTINCT {select_fields}
            FROM {from_tables}
            WHERE 
                p._current
            ORDER BY 
                p.surname,
                p.forename,
                p.dob,
                p.sex
        """.format(
            select_fields=", ".join(select_fields),
            from_tables=" ".join(from_tables),
        )
        dbsession = request.dbsession
        rows, fieldnames = get_rows_fieldnames_from_raw_sql(dbsession, sql)
        fieldnames = expand_id_descriptions(fieldnames)
        return rows, fieldnames


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_patient(p: Patient, request: CamcopsRequest) -> None:
    """Unit tests for Patient class."""
    # skip make_tables
    unit_test_ignore("", p.get_xml_root)
    unit_test_ignore("", p.get_literals_for_anonymisation)
    unit_test_ignore("", p.get_dates_for_anonymisation)
    unit_test_ignore("", p.get_bare_ptinfo)
    unit_test_ignore("", p.get_idnum_which_value_tuples)
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
    unit_test_ignore("", p.get_age_at_string, "2000-01-01")
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
    unit_test_ignore("", p.get_url_edit_patient, request)
    unit_test_ignore("", p.get_special_notes_html)

    # Lastly:
    unit_test_ignore("", p.anonymise)


def ccpatient_unit_tests(request: CamcopsRequest) -> None:
    """Unit tests for cc_patient module."""
    dbsession = request.dbsession
    q = dbsession.query(Patient)
    # noinspection PyProtectedMember
    q = q.filter(Patient._current == True)  # noqa
    patient = q.first()
    if patient is None:
        patient = Patient()
        dbsession.add(patient)
    unit_tests_patient(patient, request)

    # Patient_Report_Distinct: tested via cc_report
