"""
camcops_server/cc_modules/cc_patient.py

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

**Patients.**

"""

import datetime
import logging
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING,
    Union,
)
import uuid as python_uuid

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.datetimefunc import (
    coerce_to_pendulum_date,
    format_datetime,
    get_age,
    PotentialDatetimeType,
)
from cardinal_pythonlib.json.typing_helpers import JsonObjectType
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from fhirclient.models.address import Address
from fhirclient.models.contactpoint import ContactPoint
from fhirclient.models.humanname import HumanName
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.identifier import Identifier
from fhirclient.models.patient import Patient as FhirPatient
import hl7
import pendulum
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.expression import and_, ClauseElement, select
from sqlalchemy.sql.selectable import SelectBase
from sqlalchemy.sql.sqltypes import UnicodeText

from camcops_server.cc_modules.cc_audit import audit
from camcops_server.cc_modules.cc_constants import (
    DateFormat,
    ERA_NOW,
    FHIRConst as Fc,
    FP_ID_DESC,
    FP_ID_SHORT_DESC,
    FP_ID_NUM,
    SEX_FEMALE,
    SEX_MALE,
    SEX_OTHER_UNSPECIFIED,
    SPREADSHEET_PATIENT_FIELD_PREFIX,
)
from camcops_server.cc_modules.cc_dataclasses import SummarySchemaInfo
from camcops_server.cc_modules.cc_db import GenericTabletRecordMixin
from camcops_server.cc_modules.cc_fhir import (
    fhir_pk_identifier,
    make_fhir_bundle_entry,
)
from camcops_server.cc_modules.cc_hl7 import make_pid_segment
from camcops_server.cc_modules.cc_html import answer
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_simpleobjects import (
    BarePatientInfo,
    HL7PatientIdentifier,
)
from camcops_server.cc_modules.cc_patientidnum import (
    extra_id_colname,
    PatientIdNum,
)
from camcops_server.cc_modules.cc_proquint import proquint_from_uuid
from camcops_server.cc_modules.cc_report import Report
from camcops_server.cc_modules.cc_simpleobjects import (
    IdNumReference,
    TaskExportOptions,
)
from camcops_server.cc_modules.cc_specialnote import SpecialNote
from camcops_server.cc_modules.cc_sqla_coltypes import (
    EmailAddressColType,
    mapped_camcops_column,
    PatientNameColType,
    SexColType,
    UuidColType,
)
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_spreadsheet import SpreadsheetPage
from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION_STRING
from camcops_server.cc_modules.cc_xml import (
    XML_COMMENT_SPECIAL_NOTES,
    XmlElement,
)

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

    from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
    from camcops_server.cc_modules.cc_group import Group
    from camcops_server.cc_modules.cc_policy import TokenizedPolicy
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_taskschedule import PatientTaskSchedule
    from camcops_server.cc_modules.cc_user import User

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Patient class
# =============================================================================


class Patient(GenericTabletRecordMixin, Base):
    """
    Class representing a patient.
    """

    __tablename__ = "patient"

    id: Mapped[int] = mapped_column(
        comment="Primary key (patient ID) on the source tablet device",
        # client PK
    )
    uuid: Mapped[Optional[python_uuid.UUID]] = mapped_camcops_column(
        UuidColType,
        comment="UUID",
        default=python_uuid.uuid4,  # generates a random UUID
    )
    forename: Mapped[Optional[str]] = mapped_camcops_column(
        PatientNameColType,
        index=True,
        identifies_patient=True,
        include_in_anon_staging_db=True,
        comment="Forename",
    )
    surname: Mapped[Optional[str]] = mapped_camcops_column(
        PatientNameColType,
        index=True,
        identifies_patient=True,
        include_in_anon_staging_db=True,
        comment="Surname",
    )
    dob: Mapped[Optional[datetime.date]] = mapped_camcops_column(
        index=True,
        identifies_patient=True,
        include_in_anon_staging_db=True,
        comment="Date of birth",
        # ... e.g. "2013-02-04"
    )
    sex: Mapped[Optional[str]] = mapped_camcops_column(
        SexColType,
        index=True,
        include_in_anon_staging_db=True,
        comment="Sex (M, F, X)",
    )
    address: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, identifies_patient=True, comment="Address"
    )
    email: Mapped[Optional[str]] = mapped_camcops_column(
        EmailAddressColType,
        identifies_patient=True,
        comment="Patient's e-mail address",
    )
    gp: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText,
        identifies_patient=True,
        comment="General practitioner (GP)",
    )
    other: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, identifies_patient=True, comment="Other details"
    )
    idnums: Mapped[list["PatientIdNum"]] = relationship(
        # https://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#relationship-custom-foreign
        # https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship  # noqa
        # https://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#relationship-primaryjoin  # noqa
        primaryjoin=(
            "and_("
            " remote(PatientIdNum.patient_id) == foreign(Patient.id), "
            " remote(PatientIdNum._device_id) == foreign(Patient._device_id), "
            " remote(PatientIdNum._era) == foreign(Patient._era), "
            " remote(PatientIdNum._current) == True "
            ")"
        ),
        uselist=True,
        viewonly=True,
        # Profiling results 2019-10-14 exporting 4185 phq9 records with
        # unique patients to xlsx (task-patient relationship "selectin")
        # lazy="select"  : 35.3s
        # lazy="joined"  : 27.3s
        # lazy="subquery": 15.2s (31.0s when task-patient also subquery)
        # lazy="selectin": 26.4s
        # See also patient relationship on Task class (cc_task.py)
        lazy="subquery",
    )

    task_schedules: Mapped[list["PatientTaskSchedule"]] = relationship(
        back_populates="patient",
        cascade="all, delete",
        cascade_backrefs=False,
    )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # THE FOLLOWING ARE DEFUNCT, AND THE SERVER WORKS AROUND OLD TABLETS IN
    # THE UPLOAD API.
    #
    # idnum1 = Column("idnum1", BigInteger, comment="ID number 1")
    # idnum2 = Column("idnum2", BigInteger, comment="ID number 2")
    # idnum3 = Column("idnum3", BigInteger, comment="ID number 3")
    # idnum4 = Column("idnum4", BigInteger, comment="ID number 4")
    # idnum5 = Column("idnum5", BigInteger, comment="ID number 5")
    # idnum6 = Column("idnum6", BigInteger, comment="ID number 6")
    # idnum7 = Column("idnum7", BigInteger, comment="ID number 7")
    # idnum8 = Column("idnum8", BigInteger, comment="ID number 8")
    #
    # iddesc1 = Column("iddesc1", IdDescriptorColType, comment="ID description 1")  # noqa
    # iddesc2 = Column("iddesc2", IdDescriptorColType, comment="ID description 2")  # noqa
    # iddesc3 = Column("iddesc3", IdDescriptorColType, comment="ID description 3")  # noqa
    # iddesc4 = Column("iddesc4", IdDescriptorColType, comment="ID description 4")  # noqa
    # iddesc5 = Column("iddesc5", IdDescriptorColType, comment="ID description 5")  # noqa
    # iddesc6 = Column("iddesc6", IdDescriptorColType, comment="ID description 6")  # noqa
    # iddesc7 = Column("iddesc7", IdDescriptorColType, comment="ID description 7")  # noqa
    # iddesc8 = Column("iddesc8", IdDescriptorColType, comment="ID description 8")  # noqa
    #
    # idshortdesc1 = Column("idshortdesc1", IdDescriptorColType, comment="ID short description 1")  # noqa
    # idshortdesc2 = Column("idshortdesc2", IdDescriptorColType, comment="ID short description 2")  # noqa
    # idshortdesc3 = Column("idshortdesc3", IdDescriptorColType, comment="ID short description 3")  # noqa
    # idshortdesc4 = Column("idshortdesc4", IdDescriptorColType, comment="ID short description 4")  # noqa
    # idshortdesc5 = Column("idshortdesc5", IdDescriptorColType, comment="ID short description 5")  # noqa
    # idshortdesc6 = Column("idshortdesc6", IdDescriptorColType, comment="ID short description 6")  # noqa
    # idshortdesc7 = Column("idshortdesc7", IdDescriptorColType, comment="ID short description 7")  # noqa
    # idshortdesc8 = Column("idshortdesc8", IdDescriptorColType, comment="ID short description 8")  # noqa
    #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @declared_attr  # type: ignore[arg-type]
    def special_notes(cls) -> RelationshipProperty:
        """
        Relationship to all :class:`SpecialNote` objects associated with this
        patient.
        """
        # The SpecialNote also allows a link to patients, not just tasks,
        # like this:
        return relationship(
            SpecialNote,
            primaryjoin=(
                "and_("
                " remote(SpecialNote.basetable) == literal({repr_patient_tablename}), "  # noqa
                " remote(SpecialNote.task_id) == foreign(Patient.id), "
                " remote(SpecialNote.device_id) == foreign(Patient._device_id), "  # noqa
                " remote(SpecialNote.era) == foreign(Patient._era), "
                " not_(SpecialNote.hidden)"
                ")".format(repr_patient_tablename=repr(cls.__tablename__))
            ),
            uselist=True,
            order_by="SpecialNote.note_at",
            viewonly=True,  # for now!
        )

    # -------------------------------------------------------------------------
    # Patient-fetching classmethods
    # -------------------------------------------------------------------------

    @classmethod
    def get_patients_by_idnum(
        cls,
        dbsession: SqlASession,
        which_idnum: int,
        idnum_value: int,
        group_id: int = None,
        current_only: bool = True,
    ) -> List["Patient"]:
        """
        Get all patients matching the specified ID number.

        Args:
            dbsession: a :class:`sqlalchemy.orm.session.Session`
            which_idnum: which ID number type?
            idnum_value: actual value of the ID number
            group_id: optional group ID to restrict to
            current_only: restrict to ``_current`` patients?

        Returns:
            list of all matching patients

        """
        if not which_idnum or which_idnum < 1:
            return []
        if idnum_value is None:
            return []
        q = dbsession.query(cls).join(cls.idnums)  # type: ignore[arg-type]
        # ... the join pre-restricts to current ID numbers
        # https://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#using-custom-operators-in-join-conditions  # noqa
        q = q.filter(PatientIdNum.which_idnum == which_idnum)
        q = q.filter(PatientIdNum.idnum_value == idnum_value)
        if group_id is not None:
            q = q.filter(Patient._group_id == group_id)
        if current_only:
            q = q.filter(cls._current == True)  # noqa: E712
        patients = q.all()  # type: List[Patient]
        return patients

    @classmethod
    def get_patient_by_pk(
        cls, dbsession: SqlASession, server_pk: int
    ) -> Optional["Patient"]:
        """
        Fetch a patient by the server PK.
        """
        return dbsession.query(cls).filter(cls._pk == server_pk).first()

    @classmethod
    def get_patient_by_id_device_era(
        cls, dbsession: SqlASession, client_id: int, device_id: int, era: str
    ) -> Optional["Patient"]:
        """
        Fetch a patient by the client ID, device ID, and era.
        """
        return (
            dbsession.query(cls)
            .filter(cls.id == client_id)
            .filter(cls._device_id == device_id)
            .filter(cls._era == era)
            .first()
        )

    # -------------------------------------------------------------------------
    # String representations
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        """
        A plain string version, without the need for a request object.

        Example:

        .. code-block:: none

            SMITH, BOB (M, 1 Jan 1950, idnum1=123, idnum2=456)
        """
        return "{sf} ({sex}, {dob}, {ids})".format(
            sf=self.get_surname_forename_upper(),
            sex=self.sex,
            dob=self.get_dob_str(),
            ids=", ".join(str(i) for i in self.get_idnum_objects()),
        )

    def prettystr(self, req: "CamcopsRequest") -> str:
        """
        A prettified string version.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`

        Example:

        .. code-block:: none

            SMITH, BOB (M, 1 Jan 1950, RiO# 123, NHS# 456)
        """
        return "{sf} ({sex}, {dob}, {ids})".format(
            sf=self.get_surname_forename_upper(),
            sex=self.sex,
            dob=self.get_dob_str(),
            ids=", ".join(i.prettystr(req) for i in self.get_idnum_objects()),
        )

    def get_letter_style_identifiers(self, req: "CamcopsRequest") -> str:
        """
        Our best guess at the kind of text you'd put in a clinical letter to
        say "it's about this patient".

        Example:

        .. code-block:: none

            Bob Smith (1 Jan 1950, RiO number 123, NHS number 456)
        """
        return "{fs} ({dob}, {ids})".format(
            fs=self.get_forename_surname(),
            dob=self.get_dob_str(),
            ids=", ".join(
                i.full_prettystr(req) for i in self.get_idnum_objects()
            ),
        )

    # -------------------------------------------------------------------------
    # Equality
    # -------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """
        Is this patient the same as another?

        .. code-block:: python

            from camcops_server.cc_modules.cc_patient import Patient
            p1 = Patient(id=1, _device_id=1, _era="NOW")
            print(p1 == p1)  # True
            p2 = Patient(id=1, _device_id=1, _era="NOW")
            print(p1 == p2)  # True
            p3 = Patient(id=1, _device_id=2, _era="NOW")
            print(p1 == p3)  # False

            s = set([p1, p2, p3])  # contains two patients

        IMPERFECT in that it doesn't use intermediate patients to link
        identity (e.g. P1 has RiO#=3, P2 has RiO#=3, NHS#=5, P3 has NHS#=5;
        they are all the same by inference but P1 and P3 will not compare
        equal).

        """
        # Same object?
        # log.debug("self={}, other={}", self, other)
        if self is other:
            # log.debug("... same object; equal")
            return True

        if not isinstance(other, Patient):
            # Since SQLAlchemy 2.0, when lazy-loading from related objects
            # (e.g. Task.patient) the patient will be compared with
            # non-patient SQLA internal status codes so we need to cater for
            # this. It is probably good practice anyway.

            # MyPy does not recognise try... except AttributeError
            return NotImplemented

        # Same device/era/patient ID (client PK)? Test int before str for speed
        if (
            self.id == other.id
            and self._device_id == other._device_id
            and self._era == other._era
            and self.id is not None
            and self._device_id is not None
            and self._era is not None
        ):
            # log.debug("... same device/era/id; equal")
            return True
        # Shared ID number?
        for sid in self.idnums:
            if sid in other.idnums:
                # log.debug("... share idnum {}; equal", sid)
                return True
        # Otherwise...
        # log.debug("... unequal")
        return False

    def __hash__(self) -> int:
        """
        To put objects into a set, they must be hashable.
        See https://docs.python.org/3/glossary.html#term-hashable.
        If two objects are equal (via :func:`__eq__`) they must provide the
        same hash value (but two objects with the same hash are not necessarily
        equal).
        """
        return 0  # all objects have the same hash; "use __eq__() instead"

    # -------------------------------------------------------------------------
    # ID numbers
    # -------------------------------------------------------------------------

    def get_idnum_objects(self) -> List[PatientIdNum]:
        """
        Returns all :class:`PatientIdNum` objects for the patient.

        These are SQLAlchemy ORM objects.
        """
        return self.idnums

    def get_idnum_references(self) -> List[IdNumReference]:
        """
        Returns all
        :class:`camcops_server.cc_modules.cc_simpleobjects.IdNumReference`
        objects for the patient.

        These are simple which_idnum/idnum_value pairs.
        """
        idnums = self.idnums  # type: List[PatientIdNum]
        return [
            x.get_idnum_reference()
            for x in idnums
            if x.is_superficially_valid()
        ]

    def get_idnum_raw_values_only(self) -> List[int]:
        """
        Get all plain ID number values (ignoring which ID number type they
        represent) for the patient.
        """
        idnums = self.idnums  # type: List[PatientIdNum]
        return [x.idnum_value for x in idnums if x.is_superficially_valid()]

    def get_idnum_object(self, which_idnum: int) -> Optional[PatientIdNum]:
        """
        Gets the PatientIdNum object for a specified which_idnum, or None.
        """
        idnums = self.idnums  # type: List[PatientIdNum]
        for x in idnums:
            if x.which_idnum == which_idnum:
                return x
        return None

    def has_idnum_type(self, which_idnum: int) -> bool:
        """
        Does the patient have an ID number of the specified type?
        """
        return self.get_idnum_object(which_idnum) is not None

    def get_idnum_value(self, which_idnum: int) -> Optional[int]:
        """
        Get value of a specific ID number, if present.
        """
        idobj = self.get_idnum_object(which_idnum)
        return idobj.idnum_value if idobj else None

    def set_idnum_value(
        self, req: "CamcopsRequest", which_idnum: int, idnum_value: int
    ) -> None:
        """
        Sets an ID number value.
        """
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
        newid._when_added_exact = req.now_era_format
        newid._when_added_batch_utc = req.now_utc
        newid._adding_user_id = ccsession.user_id
        newid._camcops_version = CAMCOPS_SERVER_VERSION_STRING
        dbsession.add(newid)
        self.idnums.append(newid)

    def get_iddesc(
        self, req: "CamcopsRequest", which_idnum: int
    ) -> Optional[str]:
        """
        Get value of a specific ID description, if present.
        """
        idobj = self.get_idnum_object(which_idnum)
        return idobj.description(req) if idobj else None

    def get_idshortdesc(
        self, req: "CamcopsRequest", which_idnum: int
    ) -> Optional[str]:
        """
        Get value of a specific ID short description, if present.
        """
        idobj = self.get_idnum_object(which_idnum)
        return idobj.short_description(req) if idobj else None

    def add_extra_idnum_info_to_row(self, row: Dict[str, Any]) -> None:
        """
        For the ``DB_PATIENT_ID_PER_ROW`` export option. Adds additional ID
        number info to a row.

        Args:
            row: future database row, as a dictionary
        """
        for idobj in self.idnums:
            which_idnum = idobj.which_idnum
            fieldname = extra_id_colname(which_idnum)
            row[fieldname] = idobj.idnum_value

    # -------------------------------------------------------------------------
    # Group
    # -------------------------------------------------------------------------

    @property
    def group(self) -> Optional["Group"]:
        """
        Returns the :class:`camcops_server.cc_modules.cc_group.Group` to which
        this patient's record belongs.
        """
        return self._group

    # -------------------------------------------------------------------------
    # Policies
    # -------------------------------------------------------------------------

    def satisfies_upload_id_policy(self) -> bool:
        """
        Does the patient satisfy the uploading ID policy?
        """
        group = self._group  # type: Optional[Group]
        if not group:
            return False
        return self.satisfies_id_policy(group.tokenized_upload_policy())

    def satisfies_finalize_id_policy(self) -> bool:
        """
        Does the patient satisfy the finalizing ID policy?
        """
        group = self._group  # type: Optional[Group]
        if not group:
            return False
        return self.satisfies_id_policy(group.tokenized_finalize_policy())

    def satisfies_id_policy(self, policy: "TokenizedPolicy") -> bool:
        """
        Does the patient satisfy a particular ID policy?
        """
        return policy.satisfies_id_policy(self.get_bare_ptinfo())

    # -------------------------------------------------------------------------
    # Name, DOB/age, sex, address, etc.
    # -------------------------------------------------------------------------

    def get_surname(self) -> str:
        """
        Get surname (in upper case) or "".
        """
        return self.surname.upper() if self.surname else ""

    def get_forename(self) -> str:
        """
        Get forename (in upper case) or "".
        """
        return self.forename.upper() if self.forename else ""

    def get_forename_surname(self) -> str:
        """
        Get "Forename Surname" as a string, using "(UNKNOWN)" for missing
        details.
        """
        f = self.forename or "(UNKNOWN)"
        s = self.surname or "(UNKNOWN)"
        return f"{f} {s}"

    def get_surname_forename_upper(self) -> str:
        """
        Get "SURNAME, FORENAME", using "(UNKNOWN)" for missing details.
        """
        s = self.surname.upper() if self.surname else "(UNKNOWN)"
        f = self.forename.upper() if self.forename else "(UNKNOWN)"
        return f"{s}, {f}"

    def get_dob_html(self, req: "CamcopsRequest", longform: bool) -> str:
        """
        HTML fragment for date of birth.
        """
        _ = req.gettext
        if longform:
            dob = answer(
                format_datetime(self.dob, DateFormat.LONG_DATE, default=None)
            )

            dobtext = _("Date of birth:")
            return f"<br>{dobtext} {dob}"
        else:
            dobtext = _("DOB:")
            dob = format_datetime(self.dob, DateFormat.SHORT_DATE)
            return f"{dobtext} {dob}."

    def get_age(
        self, req: "CamcopsRequest", default: str = ""
    ) -> Union[int, str]:
        """
        Age (in whole years) today, or default.
        """
        now = req.now
        return self.get_age_at(now, default=default)

    def get_dob(self) -> Optional[pendulum.Date]:
        """
        Date of birth, as a a timezone-naive date.
        """
        dob = self.dob
        if not dob:
            return None
        return coerce_to_pendulum_date(dob)

    def get_dob_str(self) -> Optional[str]:
        """
        Date of birth, as a string.
        """
        dob_dt = self.get_dob()
        if dob_dt is None:
            return None
        return format_datetime(dob_dt, DateFormat.SHORT_DATE)

    def get_age_at(
        self, when: PotentialDatetimeType, default: str = ""
    ) -> Union[int, str]:
        """
        Age (in whole years) at a particular date, or default.
        """
        return get_age(self.dob, when, default=default)

    def is_female(self) -> bool:
        """
        Is sex 'F'?
        """
        return self.sex == SEX_FEMALE

    def is_male(self) -> bool:
        """
        Is sex 'M'?
        """
        return self.sex == SEX_MALE

    def get_sex(self) -> str:
        """
        Return sex or "".
        """
        return self.sex or ""

    def get_sex_verbose(self, default: str = "sex unknown") -> str:
        """
        Returns HTML-safe version of sex, or default.
        """
        return default if not self.sex else ws.webify(self.sex)

    def get_address(self) -> Optional[str]:
        """
        Returns address (NOT necessarily web-safe).
        """
        address = self.address  # type: Optional[str]
        return address or ""

    def get_email(self) -> Optional[str]:
        """
        Returns email address
        """
        email = self.email  # type: Optional[str]
        return email or ""

    # -------------------------------------------------------------------------
    # Other representations
    # -------------------------------------------------------------------------

    def get_xml_root(
        self, req: "CamcopsRequest", options: TaskExportOptions = None
    ) -> XmlElement:
        """
        Get root of XML tree, as an
        :class:`camcops_server.cc_modules.cc_xml.XmlElement`.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            options: a :class:`camcops_server.cc_modules.cc_simpleobjects.TaskExportOptions`
        """  # noqa
        # No point in skipping old ID columns (1-8) now; they're gone.
        branches = self._get_xml_branches(req, options=options)
        # Now add new-style IDs:
        pidnum_branches = []  # type: List[XmlElement]
        pidnum_options = TaskExportOptions(
            xml_include_plain_columns=True, xml_with_header_comments=False
        )
        for pidnum in self.idnums:  # type: PatientIdNum
            pidnum_branches.append(
                pidnum._get_xml_root(req, options=pidnum_options)
            )
        branches.append(XmlElement(name="idnums", value=pidnum_branches))
        # Special notes
        branches.append(XML_COMMENT_SPECIAL_NOTES)
        special_notes = self.special_notes  # type: List[SpecialNote]
        for sn in special_notes:
            branches.append(sn.get_xml_root())
        return XmlElement(name=self.__tablename__, value=branches)

    def get_spreadsheet_page(self, req: "CamcopsRequest") -> SpreadsheetPage:
        """
        Get a :class:`camcops_server.cc_modules.cc_spreadsheet.SpreadsheetPage`
        for the patient.
        """
        # 1. Our core fields.
        page = self._get_core_spreadsheet_page(
            req, heading_prefix=SPREADSHEET_PATIENT_FIELD_PREFIX
        )
        # 2. ID number details
        #    We can't just iterate through the ID numbers; we have to iterate
        #    through all possible ID numbers.
        for iddef in req.idnum_definitions:
            n = iddef.which_idnum
            nstr = str(n)
            shortdesc = iddef.short_description
            longdesc = iddef.description
            idnum_value = next(
                (
                    idnum.idnum_value
                    for idnum in self.idnums
                    if idnum.which_idnum == n
                    and idnum.is_superficially_valid()
                ),
                None,
            )
            page.add_or_set_value(
                heading=SPREADSHEET_PATIENT_FIELD_PREFIX + FP_ID_NUM + nstr,
                value=idnum_value,
            )
            page.add_or_set_value(
                heading=SPREADSHEET_PATIENT_FIELD_PREFIX + FP_ID_DESC + nstr,
                value=longdesc,
            )
            page.add_or_set_value(
                heading=(
                    SPREADSHEET_PATIENT_FIELD_PREFIX + FP_ID_SHORT_DESC + nstr
                ),
                value=shortdesc,
            )
        return page

    def get_spreadsheet_schema_elements(
        self, req: "CamcopsRequest", table_name: str = ""
    ) -> Set[SummarySchemaInfo]:
        """
        Follows :func:`get_spreadsheet_page`, but retrieving schema
        information.
        """
        # 1. Core fields
        items = self._get_core_spreadsheet_schema(
            table_name=table_name,
            column_name_prefix=SPREADSHEET_PATIENT_FIELD_PREFIX,
        )
        # 2. ID number details
        table_name = table_name or self.__tablename__
        for iddef in req.idnum_definitions:
            n = iddef.which_idnum
            nstr = str(n)
            comment_suffix = f" [ID#{n}]"
            items.add(
                SummarySchemaInfo(
                    table_name=table_name,
                    source=SummarySchemaInfo.SSV_DB,
                    column_name=(
                        SPREADSHEET_PATIENT_FIELD_PREFIX + FP_ID_NUM + nstr
                    ),
                    data_type=str(PatientIdNum.idnum_value.type),
                    comment=PatientIdNum.idnum_value.comment + comment_suffix,
                )
            )
            items.add(
                SummarySchemaInfo(
                    table_name=table_name,
                    source=SummarySchemaInfo.SSV_DB,
                    column_name=(
                        SPREADSHEET_PATIENT_FIELD_PREFIX + FP_ID_DESC + nstr
                    ),
                    data_type=str(IdNumDefinition.description.type),
                    comment=IdNumDefinition.description.comment
                    + comment_suffix,
                )
            )
            items.add(
                SummarySchemaInfo(
                    table_name=table_name,
                    source=SummarySchemaInfo.SSV_DB,
                    column_name=(
                        SPREADSHEET_PATIENT_FIELD_PREFIX
                        + FP_ID_SHORT_DESC
                        + nstr
                    ),
                    data_type=str(IdNumDefinition.short_description.type),
                    comment=(
                        IdNumDefinition.short_description.comment
                        + comment_suffix
                    ),
                )
            )
        return items

    def get_bare_ptinfo(self) -> BarePatientInfo:
        """
        Get basic identifying information, as a
        :class:`camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
        object.
        """
        return BarePatientInfo(
            forename=self.forename,
            surname=self.surname,
            sex=self.sex,
            dob=self.dob,  # type: ignore[arg-type]
            address=self.address,
            email=self.email,
            gp=self.gp,
            otherdetails=self.other,
            idnum_definitions=self.get_idnum_references(),
        )

    def get_hl7_pid_segment(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> hl7.Segment:
        """
        Get HL7 patient identifier (PID) segment.

        Args:
            req:
                a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            recipient:
                a :class:`camcops_server.cc_modules.cc_exportrecipient.ExportRecipient`

        Returns:
            a :class:`hl7.Segment` object
        """  # noqa
        # Put the primary one first:
        patient_id_tuple_list = [
            HL7PatientIdentifier(
                pid=str(self.get_idnum_value(recipient.primary_idnum)),
                id_type=recipient.get_hl7_id_type(
                    req, recipient.primary_idnum
                ),
                assigning_authority=recipient.get_hl7_id_aa(
                    req, recipient.primary_idnum
                ),
            )
        ]
        # Then the rest:
        for idobj in self.idnums:
            which_idnum = idobj.which_idnum
            if which_idnum == recipient.primary_idnum:
                continue
            idnum_value = idobj.idnum_value
            if idnum_value is None:
                continue
            patient_id_tuple_list.append(
                HL7PatientIdentifier(
                    pid=str(idnum_value),
                    id_type=recipient.get_hl7_id_type(req, which_idnum),
                    assigning_authority=recipient.get_hl7_id_aa(
                        req, which_idnum
                    ),
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

    # -------------------------------------------------------------------------
    # FHIR
    # -------------------------------------------------------------------------

    def get_fhir_bundle_entry(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> Dict[str, Any]:
        """
        Returns a dictionary, suitable for serializing to JSON, that
        encapsulates patient identity information in a FHIR bundle.

        See https://www.hl7.org/fhir/patient.html.
        """
        # The JSON objects we will build up:
        patient_dict = {}  # type: JsonObjectType

        # Name
        if self.forename or self.surname:
            name_dict = {}  # type: JsonObjectType
            if self.forename:
                name_dict[Fc.NAME_GIVEN] = [self.forename]
            if self.surname:
                name_dict[Fc.NAME_FAMILY] = self.surname
            patient_dict[Fc.NAME] = [HumanName(jsondict=name_dict).as_json()]

        # DOB
        if self.dob:
            patient_dict[Fc.BIRTHDATE] = format_datetime(
                self.dob, DateFormat.FILENAME_DATE_ONLY
            )

        # Sex/gender (should always be present, per client minimum ID policy)
        if self.sex:
            gender_lookup = {
                SEX_FEMALE: Fc.GENDER_FEMALE,
                SEX_MALE: Fc.GENDER_MALE,
                SEX_OTHER_UNSPECIFIED: Fc.GENDER_OTHER,
            }
            patient_dict[Fc.GENDER] = gender_lookup.get(
                self.sex, Fc.GENDER_UNKNOWN
            )

        # Address
        if self.address:
            patient_dict[Fc.ADDRESS] = [
                Address(jsondict={Fc.ADDRESS_TEXT: self.address}).as_json()
            ]

        # Email
        if self.email:
            patient_dict[Fc.TELECOM] = [
                ContactPoint(
                    jsondict={
                        Fc.SYSTEM: Fc.TELECOM_SYSTEM_EMAIL,
                        Fc.VALUE: self.email,
                    }
                ).as_json()
            ]

        # General practitioner (GP): via
        # fhirclient.models.fhirreference.FHIRReference; too structured.

        # ID numbers go here:
        return make_fhir_bundle_entry(
            resource_type_url=Fc.RESOURCE_TYPE_PATIENT,
            identifier=self.get_fhir_identifier(req, recipient),
            resource=FhirPatient(jsondict=patient_dict).as_json(),
        )

    def get_fhir_identifier(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> Identifier:
        """
        Returns a FHIR identifier for this patient, as a
        :class:`fhirclient.models.identifier.Identifier` object.

        This pairs a URL to our CamCOPS server indicating the ID number type
        (as the "system") with the actual ID number (as the "value").

        For debugging situations, it falls back to a default identifier (using
        the PK on our CamCOPS server).
        """
        which_idnum = recipient.primary_idnum
        try:
            # For real exports, the fact that the patient does have an ID
            # number of the right type will have been pre-verified.
            if which_idnum is None:
                raise AttributeError
            idnum_object = self.get_idnum_object(which_idnum)
            idnum_value = idnum_object.idnum_value  # may raise AttributeError
            iddef = req.get_idnum_definition(which_idnum)
            idnum_url = iddef.effective_fhir_id_system(req)
            return Identifier(
                jsondict={Fc.SYSTEM: idnum_url, Fc.VALUE: str(idnum_value)}
            )
        except AttributeError:
            # We are probably in a debugging/drafting situation. Fall back to
            # a default identifier.
            return fhir_pk_identifier(
                req,
                self.__tablename__,
                self.pk,
                Fc.CAMCOPS_VALUE_PATIENT_WITHIN_TASK,
            )

    def get_fhir_subject_ref(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> Dict:
        """
        Returns a FHIRReference (in JSON dict format) used to refer to this
        patient as a "subject" of some other entry (like a questionnaire).
        """
        return FHIRReference(
            jsondict={
                Fc.TYPE: Fc.RESOURCE_TYPE_PATIENT,
                Fc.IDENTIFIER: self.get_fhir_identifier(
                    req, recipient
                ).as_json(),
            }
        ).as_json()

    # -------------------------------------------------------------------------
    # Database status
    # -------------------------------------------------------------------------

    def is_preserved(self) -> bool:
        """
        Is the patient record preserved and erased from the tablet?
        """
        return self._pk is not None and self._era != ERA_NOW

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(
        self, req: "CamcopsRequest", details: str, from_console: bool = False
    ) -> None:
        """
        Audits an action to this patient.
        """
        audit(
            req,
            details,
            patient_server_pk=self._pk,
            table=Patient.__tablename__,
            server_pk=self._pk,
            from_console=from_console,
        )

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def apply_special_note(
        self,
        req: "CamcopsRequest",
        note: str,
        audit_msg: str = "Special note applied manually",
    ) -> None:
        """
        Manually applies a special note to a patient.
        WRITES TO DATABASE.
        """
        sn = SpecialNote()
        sn.basetable = self.__tablename__
        sn.task_id = self.id  # patient ID, in this case
        sn.device_id = self._device_id
        sn.era = self._era
        sn.note_at = req.now
        sn.user_id = req.user_id
        sn.note = note
        req.dbsession.add(sn)
        self.special_notes.append(sn)  # type: ignore[attr-defined]
        self.audit(req, audit_msg)
        # HL7 deletion of corresponding tasks is done in camcops_server.py

    # -------------------------------------------------------------------------
    # Deletion
    # -------------------------------------------------------------------------

    def gen_patient_idnums_even_noncurrent(
        self,
    ) -> Generator[PatientIdNum, None, None]:
        """
        Generates all :class:`PatientIdNum` objects, including non-current
        ones.
        """
        for lineage_member in self._gen_unique_lineage_objects(  # type: ignore[assignment]  # noqa: E501
            self.idnums
        ):  # type: PatientIdNum
            yield lineage_member

    def delete_with_dependants(self, req: "CamcopsRequest") -> None:
        """
        Delete the patient with all its dependent objects.
        """
        if self._pk is None:
            return
        for pidnum in self.gen_patient_idnums_even_noncurrent():
            req.dbsession.delete(pidnum)
        super().delete_with_dependants(req)

    # -------------------------------------------------------------------------
    # Permissions
    # -------------------------------------------------------------------------

    def user_may_view(self, user: "User") -> bool:
        """
        May this user inspect patient details directly?
        """
        return self._group_id in user.ids_of_groups_user_may_see

    def user_may_edit(self, req: "CamcopsRequest") -> bool:
        """
        Does the current user have permission to edit this patient?
        """
        if self.created_on_server(req):
            # Anyone in the group with the right permission
            return req.user.may_manage_patients_in_group(self._group_id)

        # Finalized patient: Need to be group administrator
        return req.user.may_administer_group(self._group_id)

    # --------------------------------------------------------------------------
    # UUID
    # --------------------------------------------------------------------------
    @property
    def uuid_as_proquint(self) -> Optional[str]:
        # Convert integer into pronounceable quintuplets (proquint)
        # https://arxiv.org/html/0901.4016
        if self.uuid is None:
            return None

        return proquint_from_uuid(self.uuid)

    @property
    def duplicates(self) -> set["Patient"]:
        """
        Returns a set of patients that have an ID Number that matches this one.
        For a patient to be considered a duplicate, the ID number needs to
        match on:

        * Group
        * Type of ID Number (e.g. NHS Number)
        * Value of ID number
        * Device where patient was created

        and have the "current" flag set to True
        """

        dups = set()

        for idnum in self.idnums:
            for dup in idnum.duplicates:
                dups.add(dup.patient)

        return dups


# =============================================================================
# Validate candidate patient info for upload
# =============================================================================


def is_candidate_patient_valid_for_group(
    ptinfo: BarePatientInfo, group: "Group", finalizing: bool
) -> Tuple[bool, str]:
    """
    Is the specified patient acceptable to upload into this group?

    Checks:

    - group upload or finalize policy

    .. todo:: is_candidate_patient_valid: check against predefined patients, if
       the group wants

    Args:
        ptinfo:
            a
            :class:`camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
            representing the patient info to check
        group:
            the :class:`camcops_server.cc_modules.cc_group.Group` into which
            this patient will be uploaded, if allowed
        finalizing:
            finalizing, rather than uploading?

    Returns:
        tuple: valid, reason

    """
    if not group:
        return False, "Nonexistent group"

    if finalizing:
        if not group.tokenized_finalize_policy().satisfies_id_policy(ptinfo):
            return False, "Fails finalizing ID policy"
    else:
        if not group.tokenized_upload_policy().satisfies_id_policy(ptinfo):
            return False, "Fails upload ID policy"

    # todo: add checks against prevalidated patients here

    return True, ""


def is_candidate_patient_valid_for_restricted_user(
    req: "CamcopsRequest", ptinfo: BarePatientInfo
) -> Tuple[bool, str]:
    """
    Is the specified patient OK to be uploaded by this user? Performs a check
    for restricted (single-patient) users; if true, ensures that the
    identifiers all match the expected patient.

    Args:
        req:
            the :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        ptinfo:
            a
            :class:`camcops_server.cc_modules.cc_simpleobjects.BarePatientInfo`
            representing the patient info to check

    Returns:
        tuple: valid, reason
    """
    user = req.user
    if not user.auto_generated:
        # Not a restricted user; no problem.
        return True, ""

    server_patient = user.single_patient
    if not server_patient:
        return (
            False,
            (
                f"Restricted user {user.username} does not have associated "
                f"patient details"
            ),
        )

    server_ptinfo = server_patient.get_bare_ptinfo()
    if ptinfo != server_ptinfo:
        return False, f"Should be {server_ptinfo}"

    return True, ""


# =============================================================================
# Reports
# =============================================================================


class DistinctPatientReport(Report):
    """
    Report to show distinct patients.
    """

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "patient_distinct"

    @classmethod
    def title(cls, req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _(
            "(Server) Patients, distinct by name, sex, DOB, all ID " "numbers"
        )

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    # noinspection PyProtectedMember
    def get_query(self, req: "CamcopsRequest") -> SelectBase:
        select_fields: list[ColumnElement[Any]] = [
            Patient.surname.label("surname"),
            Patient.forename.label("forename"),
            Patient.dob.label("dob"),
            Patient.sex.label("sex"),
        ]
        # noinspection PyUnresolvedReferences
        select_from = Patient.__table__
        wheres = [
            Patient._current == True  # noqa: E712
        ]  # type: List[ClauseElement]
        if not req.user.superuser:
            # Restrict to accessible groups
            group_ids = req.user.ids_of_groups_user_may_report_on
            wheres.append(Patient._group_id.in_(group_ids))
        for iddef in req.idnum_definitions:
            n = iddef.which_idnum
            desc = iddef.short_description
            # noinspection PyUnresolvedReferences
            aliased_table = PatientIdNum.__table__.alias(f"i{n}")
            select_fields.append(aliased_table.c.idnum_value.label(desc))
            select_from = select_from.outerjoin(
                aliased_table,
                and_(
                    aliased_table.c.patient_id == Patient.id,
                    aliased_table.c._device_id == Patient._device_id,
                    aliased_table.c._era == Patient._era,
                    # Note: the following are part of the JOIN, not the WHERE:
                    # (or failure to match a row will wipe out the Patient from
                    # the OUTER JOIN):
                    aliased_table.c._current == True,  # noqa: E712
                    aliased_table.c.which_idnum == n,
                ),
            )  # nopep8
        order_by = [
            Patient.surname,
            Patient.forename,
            Patient.dob,
            Patient.sex,
        ]
        query = (
            select(*select_fields)
            .select_from(select_from)
            .where(and_(*wheres))  # type: ignore[arg-type]
            .order_by(*order_by)
            .distinct()
        )
        return query
