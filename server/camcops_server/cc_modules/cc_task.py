#!/usr/bin/env python
# camcops_server/cc_modules/cc_task.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

Core task export methods:

------  -----------------------------------------------------------------------
Format  Comment
------  -----------------------------------------------------------------------
HTML    The task in a user-friendly format
PDF     Essentially the HTML output
XML     Centres on the task with its subdata integrated
TSV     Tab-separated value format
SQL     As part of an SQL or SQLite download
------  -----------------------------------------------------------------------
"""

import copy
import logging
import statistics
from typing import (Any, Dict, Iterable, Generator, List, Optional,
                    Tuple, Type, Union)

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.datetimefunc import (
    convert_datetime_to_utc,
    format_datetime,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.orm_query import get_rows_fieldnames_from_query  # noqa
from cardinal_pythonlib.sqlalchemy.orm_inspect import (
    gen_columns,
    gen_orm_classes_from_base,
)
from cardinal_pythonlib.sqlalchemy.schema import is_sqlatype_string
from cardinal_pythonlib.sqlalchemy.sqlfunc import extract_month, extract_year
from cardinal_pythonlib.stringfunc import mangle_unicode_to_ascii
import hl7
from pendulum import Date, DateTime as Pendulum
from pyramid.renderers import render
from semantic_version import Version
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.expression import (and_, desc, func, literal, not_,
                                       select, update)
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Float, Integer, Text

from .cc_anon import get_cris_dd_rows_from_fieldspecs
from .cc_audit import audit
from .cc_blob import Blob, get_blob_img_html
from .cc_cache import cache_region_static, fkg
from .cc_constants import (
    CRIS_CLUSTER_KEY_FIELDSPEC,
    CRIS_PATIENT_COMMENT_PREFIX,
    CRIS_SUMMARY_COMMENT_PREFIX,
    CRIS_TABLENAME_PREFIX,
    CssClass,
    CSS_PAGED_MEDIA,
    DateFormat,
    ERA_NOW,
    INVALID_VALUE,
    TSV_PATIENT_FIELD_PREFIX,
)
from .cc_ctvinfo import CtvInfo
from .cc_db import GenericTabletRecordMixin
from .cc_filename import get_export_filename
from .cc_hl7core import make_obr_segment, make_obx_segment
from .cc_html import (
    get_present_absent_none,
    get_true_false_none,
    get_yes_no,
    get_yes_no_none,
    tr,
    tr_qa,
)
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_pdf import pdf_from_html
from .cc_pyramid import ViewArg
from .cc_recipdef import RecipientDefinition
from .cc_report import Report, PlainReportType
from .cc_request import CamcopsRequest
from .cc_specialnote import SpecialNote
from .cc_sqla_coltypes import (
    CamcopsColumn,
    PendulumDateTimeAsIsoTextColType,
    gen_ancillary_relationships,
    get_column_attr_names,
    get_camcops_blob_column_attr_names,
    permitted_value_failure_msgs,
    permitted_values_ok,
)
from .cc_sqlalchemy import Base
from .cc_summaryelement import ExtraSummaryTable, SummaryElement
from .cc_trackerhelpers import TrackerInfo
from .cc_tsv import TsvPage
from .cc_version import MINIMUM_TABLET_VERSION
from .cc_unittest import DemoDatabaseTestCase
from .cc_xml import (
    get_xml_document,
    XML_COMMENT_ANCILLARY,
    XML_COMMENT_ANONYMOUS,
    XML_COMMENT_BLOBS,
    XML_COMMENT_CALCULATED,
    XML_COMMENT_PATIENT,
    XML_COMMENT_SPECIAL_NOTES,
    XmlElement,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

ANCILLARY_FWD_REF = "Ancillary"
TASK_FWD_REF = "Task"


# =============================================================================
# Patient mixin
# =============================================================================

class TaskHasPatientMixin(object):
    # http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html#using-advanced-relationship-arguments-e-g-primaryjoin-etc  # noqa

    # noinspection PyMethodParameters
    @declared_attr
    def patient_id(cls) -> Column:
        return Column(
            "patient_id", Integer,
            nullable=False, index=True,
            comment="(TASK) Foreign key to patient.id (for this device/era)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def patient(cls) -> RelationshipProperty:
        return relationship(
            "Patient",
            primaryjoin=(
                "and_("
                " remote(Patient.id) == foreign({task}.patient_id), "
                " remote(Patient._device_id) == foreign({task}._device_id), "
                " remote(Patient._era) == foreign({task}._era), "
                " remote(Patient._current) == True "
                ")".format(
                    task=cls.__name__,
                )
            ),
            uselist=False,
            viewonly=True,
            # EMPIRICALLY: SLOWER OVERALL WITH THIS # lazy="joined"
        )
        # NOTE: this retrieves the most recent (i.e. the current) information
        # on that patient. Consequently, task version history doesn't show the
        # history of patient edits. This is consistent with our relationship
        # strategy throughout for the web front-end viewer.

    # noinspection PyMethodParameters
    @classproperty
    def has_patient(cls) -> bool:
        return True


# =============================================================================
# Clinician mixin
# =============================================================================

class TaskHasClinicianMixin(object):
    """
    Mixin to add clinician columns and override clinician-related methods.
    Must be to the LEFT of Task in the class's base class list.
    """
    # noinspection PyMethodParameters
    @declared_attr
    def clinician_specialty(cls) -> Column:
        return CamcopsColumn(
            "clinician_specialty", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's specialty "
                    "(e.g. Liaison Psychiatry)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_name(cls) -> Column:
        return CamcopsColumn(
            "clinician_name", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's name (e.g. Dr X)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_professional_registration(cls) -> Column:
        return Column(
            "clinician_professional_registration", Text,
            comment="(CLINICIAN) Clinician's professional registration (e.g. "
                    "GMC# 12345)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_post(cls) -> Column:
        return CamcopsColumn(
            "clinician_post", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's post (e.g. Consultant)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_service(cls) -> Column:
        return CamcopsColumn(
            "clinician_service", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's service (e.g. Liaison Psychiatry "
                    "Service)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_contact_details(cls) -> Column:
        return CamcopsColumn(
            "clinician_contact_details", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's contact details (e.g. bleep, "
                    "extension)"
        )

    # For field order, see also:
    # https://stackoverflow.com/questions/3923910/sqlalchemy-move-mixin-columns-to-end  # noqa

    # noinspection PyMethodParameters
    @classproperty
    def has_clinician(cls) -> bool:
        return True

    def get_clinician_name(self) -> str:
        return self.clinician_name or ""


# =============================================================================
# Respondent mixin
# =============================================================================

class TaskHasRespondentMixin(object):
    """
    Mixin to add respondent columns and override respondent-related methods.
    Must be to the LEFT of Task in the class's base class list.

    If you don't use declared_attr, the "comment" property doesn't work.
    """

    # noinspection PyMethodParameters
    @declared_attr
    def respondent_name(cls) -> Column:
        return CamcopsColumn(
            "respondent_name", Text,
            identifies_patient=True,
            comment="(RESPONDENT) Respondent's name"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def respondent_relationship(cls) -> Column:
        return Column(
            "respondent_relationship", Text,
            comment="(RESPONDENT) Respondent's relationship to patient"
        )

    # noinspection PyMethodParameters
    @classproperty
    def has_respondent(cls) -> bool:
        return True

    def is_respondent_complete(self) -> bool:
        return all([self.respondent_name, self.respondent_relationship])


# =============================================================================
# Task base class
# =============================================================================

class Task(GenericTabletRecordMixin, Base):
    """
    Abstract base class for all tasks.

    - Column definitions:

        Use CamcopsColumn, not Column, if you have fields that need to define
        permitted values, mark them as BLOB-referencing fields, or do other
        CamCOPS-specific things.
    """
    __abstract__ = True

    # noinspection PyMethodParameters
    @declared_attr
    def __mapper_args__(cls):
        return {
            'polymorphic_identity': cls.__name__,
            'concrete': True,
        }

    # =========================================================================
    # PART 0: COLUMNS COMMON TO ALL TASKS
    # =========================================================================

    # Columns

    # noinspection PyMethodParameters
    @declared_attr
    def when_created(cls) -> Column:
        return Column(
            "when_created", PendulumDateTimeAsIsoTextColType,
            nullable=False,
            comment="(TASK) Date/time this task instance was created (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def when_firstexit(cls) -> Column:
        return Column(
            "when_firstexit", PendulumDateTimeAsIsoTextColType,
            comment="(TASK) Date/time of the first exit from this task "
                    "(ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def firstexit_is_finish(cls) -> Column:
        return Column(
            "firstexit_is_finish", Boolean,
            comment="(TASK) Was the first exit from the task because it was "
                    "finished (1)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def firstexit_is_abort(cls) -> Column:
        return Column(
            "firstexit_is_abort", Boolean,
            comment="(TASK) Was the first exit from this task because it was "
                    "aborted (1)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def editing_time_s(cls) -> Column:
        return Column(
            "editing_time_s", Float,
            comment="(TASK) Time spent editing (s)"
        )

    # Relationships

    # noinspection PyMethodParameters
    @declared_attr
    def special_notes(cls) -> RelationshipProperty:
        return relationship(
            SpecialNote,
            primaryjoin=(
                "and_("
                " remote(SpecialNote.basetable) == literal({repr_task_tablename}), "  # noqa
                " remote(SpecialNote.task_id) == foreign({task}.id), "
                " remote(SpecialNote.device_id) == foreign({task}._device_id), "  # noqa
                " remote(SpecialNote.era) == foreign({task}._era) "
                ")".format(
                    task=cls.__name__,
                    repr_task_tablename=repr(cls.__tablename__),
                )
            ),
            uselist=True,
            order_by="SpecialNote.note_at",
            viewonly=True,  # for now!
        )

    # =========================================================================
    # PART 1: THINGS THAT DERIVED CLASSES MAY CARE ABOUT
    # =========================================================================

    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------
    __tablename__ = None  # type: str  # also the SQLAlchemy table name
    shortname = None  # type: str
    longname = None  # type: str

    # -------------------------------------------------------------------------
    # Attributes that can be overridden
    # -------------------------------------------------------------------------
    extrastring_taskname = None  # type: str  # if None, tablename is used instead  # noqa
    provides_trackers = False
    use_landscape_for_pdf = False
    dependent_classes = []

    # -------------------------------------------------------------------------
    # Methods always overridden by the actual task
    # -------------------------------------------------------------------------

    def is_complete(self) -> bool:
        """
        Is the task instance complete?
        Must be overridden.
        """
        raise NotImplementedError("Task.is_complete must be overridden")

    def get_task_html(self, req: CamcopsRequest) -> str:
        """
        HTML for the main task content.
        Overridden by derived classes.
        """
        raise NotImplementedError(
            "No get_task_html() HTML generator for this task class!")

    # -------------------------------------------------------------------------
    # Implement if you provide trackers
    # -------------------------------------------------------------------------

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        """
        Tasks that provide quantitative information for tracking over time
        should override this and return a list of TrackerInfo, one per tracker.

        The information is read by get_all_plots_for_one_task_html() in
        cc_tracker.py -- q.v.

        Time information will be retrieved using the get_creation_datetime()
        function.
        """
        return []

    # -------------------------------------------------------------------------
    # Override to provide clinical text
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_clinical_text(self, req: CamcopsRequest) -> Optional[List[CtvInfo]]:
        """Tasks that provide clinical text information should override this
        to provide a list of dictionaries.

        Return None (default) for a task that doesn't provide clinical text,
        or [] for one with no information, or a list of CtvInfo objects.
        """
        return None

    # -------------------------------------------------------------------------
    # Override some of these if you provide summaries
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_extra_summary_tables(
            self, req: CamcopsRequest) -> List[ExtraSummaryTable]:
        """
        Override if you wish to create extra summary tables, not just add
        summary columns to task/ancillary tables.
        """
        return []

    # =========================================================================
    # PART 2: INTERNALS
    # =========================================================================

    # -------------------------------------------------------------------------
    # Way to fetch all task types
    # -------------------------------------------------------------------------

    @classmethod
    def gen_all_subclasses(cls) -> Generator[Type[TASK_FWD_REF], None, None]:
        """
        We require that actual tasks are subclasses of both Task and Base

        ... so we can (a) inherit from Task to make a base class for actual
        tasks, as with PCL, HADS, HoNOS, etc.; and (b) not have those
        intermediate classes appear in the task list. Since all actual classes
        must be SQLAlchemy ORM objects inheriting from Base, that common
        inheritance is an excellent way to define them.

        ... CHANGED: things now inherit from Base/Task without necessarily
        being actual tasks; we discriminate using __abstract__ and/or
        __tablename__.
        """
        return gen_orm_classes_from_base(cls)

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_tablename(cls) -> List[Type[TASK_FWD_REF]]:
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.tablename)
        return classes

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_shortname(cls) -> List[Type[TASK_FWD_REF]]:
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.shortname)
        return classes

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_longname(cls) -> List[Type[TASK_FWD_REF]]:
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.longname)
        return classes

    # -------------------------------------------------------------------------
    # Methods that may be overridden by mixins
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def has_patient(cls) -> bool:
        """
        May be overridden by TaskHasPatientMixin.
        """
        return False

    # noinspection PyMethodParameters
    @classproperty
    def is_anonymous(cls) -> bool:
        """
        Antonym for has_patient.
        """
        return not cls.has_patient

    # noinspection PyMethodParameters
    @classproperty
    def has_clinician(cls) -> bool:
        """
        May be overridden by TaskHasClinicianMixin.
        """
        return False

    # noinspection PyMethodParameters
    @classproperty
    def has_respondent(cls) -> bool:
        """
        May be overridden by TaskHasRespondentMixin.
        """
        return False

    # -------------------------------------------------------------------------
    # Other classmethods
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def tablename(cls) -> str:
        return cls.__tablename__

    # noinspection PyMethodParameters
    @classproperty
    def minimum_client_version(cls) -> Version:
        return MINIMUM_TABLET_VERSION

    # noinspection PyMethodParameters
    @classmethod
    def all_tables_with_min_client_version(cls) -> Dict[str, Version]:
        v = cls.minimum_client_version
        d = {cls.__tablename__: v}  # type: Dict[str, Version]
        for _, _, rel_cls in gen_ancillary_relationships(cls):
            d[rel_cls.__tablename__] = v
        return d

    # -------------------------------------------------------------------------
    # More on fields
    # -------------------------------------------------------------------------

    @classmethod
    def get_fieldnames(cls) -> List[str]:
        return get_column_attr_names(cls)

    def field_contents_valid(self) -> bool:
        """
        Checks field contents validity against fieldspecs.
        This is a high-speed function that doesn't bother with explanations,
        since we use it for lots of task is_complete() calculations.
        """
        return permitted_values_ok(self)

    def field_contents_invalid_because(self) -> List[str]:
        """Explains why contents are invalid."""
        return permitted_value_failure_msgs(self)

    def get_blob_fields(self) -> List[str]:
        return get_camcops_blob_column_attr_names(self)

    # -------------------------------------------------------------------------
    # Server field calculations
    # -------------------------------------------------------------------------

    def get_pk(self) -> Optional[int]:
        return self._pk

    def is_preserved(self) -> bool:
        """Is the task preserved and erased from the tablet?"""
        return self._pk is not None and self._era != ERA_NOW

    def was_forcibly_preserved(self) -> bool:
        """Was it forcibly preserved?"""
        return self._forcibly_preserved and self.is_preserved()

    def get_creation_datetime(self) -> Optional[Pendulum]:
        """Creation datetime, or None."""
        return self.when_created

    def get_creation_datetime_utc(self) -> Optional[Pendulum]:
        """Creation datetime in UTC, or None."""
        localtime = self.get_creation_datetime()
        if localtime is None:
            return None
        return convert_datetime_to_utc(localtime)

    def get_seconds_from_creation_to_first_finish(self) -> Optional[float]:
        """Time in seconds from creation time to first finish (i.e. first exit
        if the first exit was a finish rather than an abort), or None."""
        if not self.firstexit_is_finish:
            return None
        start = self.get_creation_datetime()
        end = self.when_firstexit
        if not start or not end:
            return None
        diff = end - start
        return diff.total_seconds()

    def get_adding_user_id(self) -> int:
        return self._adding_user_id

    def get_adding_user_username(self) -> str:
        return self._adding_user.username if self._adding_user else ""

    def get_removing_user_username(self) -> str:
        return self._removing_user.username if self._removing_user else ""

    def get_preserving_user_username(self) -> str:
        return self._preserving_user.username if self._preserving_user else ""

    def get_manually_erasing_user_username(self) -> str:
        return self._manually_erasing_user.username if self._manually_erasing_user else ""  # noqa

    # -------------------------------------------------------------------------
    # Summary tables
    # -------------------------------------------------------------------------

    def standard_task_summary_fields(self) -> List[SummaryElement]:
        return [
            SummaryElement(
                name="is_complete",
                coltype=Boolean(),
                value=self.is_complete(),
                comment="(GENERIC) Task complete?"
            ),
            SummaryElement(
                name="seconds_from_creation_to_first_finish",
                coltype=Float(),
                value=self.get_seconds_from_creation_to_first_finish(),
                comment="(GENERIC) Time (in seconds) from record creation to "
                        "first exit, if that was a finish not an abort",
            ),
        ]

    # -------------------------------------------------------------------------
    # Testing
    # -------------------------------------------------------------------------

    def dump(self) -> None:
        """Dump to log."""
        line_equals = "=" * 79
        lines = ["", line_equals]
        for f in self.get_fieldnames():
            lines.append("{f}: {v!r}".format(f=f, v=getattr(self, f)))
        lines.append(line_equals)
        log.info("\n".join(lines))

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def apply_special_note(self,
                           req: CamcopsRequest,
                           note: str,
                           from_console: bool = False) -> None:
        """
        Manually applies a special note to a task.

        Applies it to all predecessor/successor versions as well.
        WRITES TO DATABASE.
        """
        sn = SpecialNote()
        sn.basetable = self.tablename
        sn.task_id = self.id
        sn.device_id = self._device_id
        sn.era = self._era
        sn.note_at = req.now
        sn.user_id = req.user_id
        sn.note = note
        dbsession = req.dbsession
        dbsession.add(sn)
        self.audit(req, "Special note applied manually", from_console)
        self.delete_from_hl7_message_log(req, from_console)

    # -------------------------------------------------------------------------
    # Clinician
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_clinician_name(self) -> str:
        """
        Get the clinician's name.
        May be overridden by TaskHasClinicianMixin.
        """
        return ""

    # -------------------------------------------------------------------------
    # Respondent
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def is_respondent_complete(self) -> bool:
        """
        May be overridden by TaskHasRespondentMixin.
        """
        return False

    # -------------------------------------------------------------------------
    # About the associated patient
    # -------------------------------------------------------------------------

    @property
    def patient(self) -> Optional[Patient]:
        """
        Overridden by TaskHasPatientMixin.
        """
        return None

    def is_female(self) -> bool:
        """Is the patient female?"""
        return self.patient.is_female() if self.patient else False

    def is_male(self) -> bool:
        """Is the patient male?"""
        return self.patient.is_male() if self.patient else False

    def get_patient_server_pk(self) -> Optional[int]:
        """Get the server PK of the patient, or None."""
        return self.patient.get_pk() if self.patient else None

    def get_patient_forename(self) -> str:
        """Get the patient's forename, in upper case, or ""."""
        return self.patient.get_forename() if self.patient else ""

    def get_patient_surname(self) -> str:
        """Get the patient's surname, in upper case, or ""."""
        return self.patient.get_surname() if self.patient else ""

    def get_patient_dob(self) -> Optional[Date]:
        """Get the patient's DOB, or None."""
        return self.patient.get_dob() if self.patient else None

    def get_patient_dob_first11chars(self) -> Optional[str]:
        """For example: '29 Dec 1999'."""
        if not self.patient:
            return None
        dob_str = self.patient.get_dob_str()
        if not dob_str:
            return None
        return dob_str[:11]

    def get_patient_sex(self) -> str:
        """Get the patient's sex, or ""."""
        return self.patient.get_sex() if self.patient else ""

    def get_patient_address(self) -> str:
        """Get the patient's address, or ""."""
        return self.patient.get_address() if self.patient else ""

    def get_patient_idnum_objects(self) -> List[PatientIdNum]:
        return self.patient.get_idnum_objects() if self.patient else []

    def get_patient_idnum_object(self,
                                 which_idnum: int) -> Optional[PatientIdNum]:
        """
        Get the patient's ID number, or None.
        """
        return (self.patient.get_idnum_object(which_idnum) if self.patient
                else None)

    def get_patient_idnum_value(self, which_idnum: int) -> Optional[int]:
        idobj = self.get_patient_idnum_object(which_idnum=which_idnum)
        return idobj.idnum_value if idobj else None

    def get_patient_hl7_pid_segment(self,
                                    req: CamcopsRequest,
                                    recipient_def: RecipientDefinition) \
            -> Union[hl7.Segment, str]:
        """Get patient HL7 PID segment, or ""."""
        return (self.patient.get_hl7_pid_segment(req, recipient_def)
                if self.patient else "")

    # -------------------------------------------------------------------------
    # HL7
    # -------------------------------------------------------------------------

    def get_hl7_data_segments(self, req: CamcopsRequest,
                              recipient_def: RecipientDefinition) \
            -> List[hl7.Segment]:
        """Returns a list of HL7 data segments.

        These will be:
            OBR segment
            OBX segment
            any extra ones offered by the task
        """
        obr_segment = make_obr_segment(self)
        obx_segment = make_obx_segment(
            req,
            self,
            task_format=recipient_def.task_format,
            observation_identifier=self.tablename + "_" + str(self._pk),
            observation_datetime=self.get_creation_datetime(),
            responsible_observer=self.get_clinician_name(),
            xml_field_comments=recipient_def.xml_field_comments
        )
        return [
            obr_segment,
            obx_segment
        ] + self.get_hl7_extra_data_segments(recipient_def)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_hl7_extra_data_segments(self, recipient_def: RecipientDefinition) \
            -> List[hl7.Segment]:
        """Return a list of any extra HL7 data segments.

        May be overridden.
        """
        return []

    def delete_from_hl7_message_log(self, req: CamcopsRequest,
                                    from_console: bool = False) -> None:
        """
        Erases the object from the HL7 message log (so it will be resent).
        """
        if self._pk is None:
            return
        from .cc_hl7 import HL7Message  # delayed import
        statement = update(HL7Message.__table__)\
            .where(HL7Message.basetable == self.tablename)\
            .where(HL7Message.serverpk == self._pk)\
            .where(not_(HL7Message.cancelled) |
                   HL7Message.cancelled.is_(None))\
            .values(cancelled=1,
                    cancelled_at_utc=req.now_utc)
        # ... this bit: ... AND (NOT cancelled OR cancelled IS NULL) ...:
        # https://stackoverflow.com/questions/37445041/sqlalchemy-how-to-filter-column-which-contains-both-null-and-integer-values  # noqa
        req.dbsession.execute(statement)
        self.audit(
            req,
            "Task cancelled in outbound HL7 message log (may trigger "
            "resending)",
            from_console
        )

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(self, req: CamcopsRequest, details: str,
              from_console: bool = False) -> None:
        """Audits actions to this task."""
        audit(req,
              details,
              patient_server_pk=self.get_patient_server_pk(),
              table=self.tablename,
              server_pk=self._pk,
              from_console=from_console)

    # -------------------------------------------------------------------------
    # Erasure (wiping, leaving record as placeholder)
    # -------------------------------------------------------------------------

    def manually_erase(self, req: CamcopsRequest) -> None:
        """
        Manually erases a task (including sub-tables).
        Also erases linked non-current records.
        This WIPES THE CONTENTS but LEAVES THE RECORD AS A PLACEHOLDER.

        Audits the erasure. Propagates erase through to the HL7 log, so those
        records will be re-sent. WRITES TO DATABASE.
        """
        # Erase ourself and any other in our "family"
        for task in self.get_lineage():
            task.manually_erase_with_dependants(req)
        # Audit and clear HL7 message log
        self.audit(req, "Task details erased manually")
        self.delete_from_hl7_message_log(req)

    def is_erased(self) -> bool:
        return self._manually_erased

    # -------------------------------------------------------------------------
    # Complete deletion
    # -------------------------------------------------------------------------

    def delete_entirely(self, req: CamcopsRequest) -> None:
        """
        Completely delete this task, its lineage, and its dependents.
        """
        for task in self.get_lineage():
            task.delete_with_dependants(req)
        self.audit(req, "Task deleted")

    # -------------------------------------------------------------------------
    # Viewing the task in the list of tasks
    # -------------------------------------------------------------------------

    def is_live_on_tablet(self) -> bool:
        """Is the instance live on a tablet?"""
        return self._era == ERA_NOW

    # -------------------------------------------------------------------------
    # Filtering tasks for the task list
    # -------------------------------------------------------------------------

    @classmethod
    def gen_text_filter_columns(cls) -> Generator[Tuple[str, Column], None,
                                                  None]:
        """
        Yields tuples of (attr_name, Column), for columns that are suitable
        for text filtering.
        """
        for attrname, column in gen_columns(cls):
            if attrname.startswith("_"):  # system field
                continue
            if not is_sqlatype_string(column.type):
                continue
            yield attrname, column

    # -------------------------------------------------------------------------
    # TSV export for basic research dump
    # -------------------------------------------------------------------------

    def get_tsv_pages(self, req: CamcopsRequest) -> List[TsvPage]:
        """
        Returns information used for the basic research dump in TSV format.
        """
        # 1. Our core fields, plus summary information
        main_page = self._get_core_tsv_page(req)
        # 2. Patient details.
        if self.patient:
            main_page.add_or_set_columns_from_page(
                self.patient.get_tsv_page(req))
        tsv_pages = [main_page]
        # 3. +/- Ancillary objects
        for ancillary in self.gen_ancillary_instances():  # type: GenericTabletRecordMixin  # noqa
            page = ancillary._get_core_tsv_page(req)
            tsv_pages.append(page)
        # 4. +/- Extra summary tables
        for est in self.get_extra_summary_tables(req):
            tsv_pages.append(est.get_tsv_page())
        return tsv_pages

    # -------------------------------------------------------------------------
    # Data structure for CRIS data dictionary
    # -------------------------------------------------------------------------

    @classmethod
    def get_cris_dd_rows(cls, req: CamcopsRequest) -> List[Dict]:
        """
        .. todo:: fix get_cris_dd_rows
        """
        if cls.is_anonymous:
            return []
        taskname = cls.shortname
        tablename = CRIS_TABLENAME_PREFIX + cls.tablename
        instance = cls()  # blank PK
        common = instance.get_cris_common_fieldspecs_values()
        taskfieldspecs = instance.get_cris_fieldspecs_values(req, common)
        rows = get_cris_dd_rows_from_fieldspecs(taskname, tablename,
                                                taskfieldspecs)
        for depclass in cls.dependent_classes:
            depinstance = depclass(None)  # blank PK
            deptable = CRIS_TABLENAME_PREFIX + depinstance.tablename
            depfieldspecs = depinstance.get_cris_fieldspecs_values(req, common)
            rows += get_cris_dd_rows_from_fieldspecs(taskname, deptable,
                                                     depfieldspecs)
        return rows

    # -------------------------------------------------------------------------
    # Data export for CRIS and other anonymisation systems
    # -------------------------------------------------------------------------

    @classmethod
    def make_cris_tables(cls, req: CamcopsRequest,
                         db: "DatabaseSupporter") -> None:
        """
        .. todo:: fix make_cris_tables
        """
        # DO NOT CONFUSE pls.db and db. HERE WE ONLY USE db.
        log.info("Generating CRIS staging tables for: {}", cls.shortname)
        cc_db.set_db_to_utf8(db)
        task_table = CRIS_TABLENAME_PREFIX + cls.tablename
        created_tables = []
        for task in cls.gen_all_current_tasks():
            common_fsv = task.get_cris_common_fieldspecs_values()
            task_fsv = task.get_cris_fieldspecs_values(req, common_fsv)
            cc_db.add_sqltype_to_fieldspeclist_in_place(task_fsv)
            if task_table not in created_tables:
                db.drop_table(task_table)
                db.make_table(task_table, task_fsv, dynamic=True)
                created_tables.append(task_table)
            db.insert_record_by_fieldspecs_with_values(task_table, task_fsv)
            # Same for associated ancillary items
            for depclass in cls.dependent_classes:
                items = task.get_ancillary_items(depclass)
                for it in items:
                    item_table = CRIS_TABLENAME_PREFIX + it.tablename
                    item_fsv = it.get_cris_fieldspecs_values(common_fsv)
                    cc_db.add_sqltype_to_fieldspeclist_in_place(item_fsv)
                    if item_table not in created_tables:
                        db.drop_table(item_table)
                        db.make_table(item_table, item_fsv, dynamic=True)
                        created_tables.append(item_table)
                    db.insert_record_by_fieldspecs_with_values(item_table,
                                                               item_fsv)

    def get_cris_common_fieldspecs_values(self) -> "FIELDSPECLIST_TYPE":
        # Store the task's PK in its own but all linked records
        clusterpk_fs = copy.deepcopy(CRIS_CLUSTER_KEY_FIELDSPEC)
        clusterpk_fs["value"] = self._pk
        fieldspecs = [clusterpk_fs]
        # Store a subset of patient info in all linked records
        patientfs = copy.deepcopy(Patient.FIELDSPECS)
        for fs in patientfs:
            if fs.get("cris_include", False):
                fs["value"] = getattr(self.patient, fs["name"])
                fs["name"] = TSV_PATIENT_FIELD_PREFIX + fs["name"]
                fs["comment"] = CRIS_PATIENT_COMMENT_PREFIX + fs.get("comment",
                                                                     "")
                fieldspecs.append(fs)
        return fieldspecs

    def get_cris_fieldspecs_values(
            self,
            req: CamcopsRequest,
            common_fsv: "FIELDSPECLIST_TYPE") -> "FIELDSPECLIST_TYPE":
        fieldspecs = copy.deepcopy(self.get_full_fieldspecs())
        for fs in fieldspecs:
            fs["value"] = getattr(self, fs["name"])
        summaries = self.get_summaries(req)  # summaries include values
        for fs in summaries:
            fs["comment"] = CRIS_SUMMARY_COMMENT_PREFIX + fs.get("comment", "")
        return (
            common_fsv +
            fieldspecs +
            summaries
        )

    # -------------------------------------------------------------------------
    # XML view
    # -------------------------------------------------------------------------

    def get_xml(self,
                req: CamcopsRequest,
                include_calculated: bool = True,
                include_blobs: bool = True,
                include_patient: bool = True,
                indent_spaces: int = 4,
                eol: str = '\n',
                skip_fields: List[str] = None,
                include_comments: bool = False) -> str:
        """Returns XML UTF-8 document representing task."""
        skip_fields = skip_fields or []
        tree = self.get_xml_root(req=req,
                                 include_calculated=include_calculated,
                                 include_blobs=include_blobs,
                                 include_patient=include_patient,
                                 skip_fields=skip_fields)
        return get_xml_document(
            tree,
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    def get_xml_root(self,
                     req: CamcopsRequest,
                     include_calculated: bool = True,
                     include_blobs: bool = True,
                     include_patient: bool = True,
                     include_ancillary: bool = True,
                     skip_fields: List[str] = None) -> XmlElement:
        """
        Returns XML tree. Return value is the root XmlElement.

        Override to include other tables, or to deal with BLOBs, if the default
        methods are insufficient.
        """
        skip_fields = skip_fields or []

        # Core (inc. core BLOBs)
        branches = self.get_xml_core_branches(
            req=req,
            include_calculated=include_calculated,
            include_blobs=include_blobs,
            include_patient=include_patient,
            include_ancillary=include_ancillary,
            skip_fields=skip_fields)
        tree = XmlElement(name=self.tablename, value=branches)
        return tree

    def get_xml_core_branches(
            self,
            req: CamcopsRequest,
            include_calculated: bool = True,
            include_blobs: bool = True,
            include_patient: bool = True,
            include_ancillary: bool = True,
            skip_fields: List[str] = None) -> List[XmlElement]:
        """
        Returns a list of XmlElementTuple elements representing stored,
        calculated, patient, and/or BLOB fields, depending on the options.
        """
        skip_fields = skip_fields or []

        # Stored values +/- calculated values
        branches = self._get_xml_branches(
            req=req,
            skip_attrs=skip_fields,
            include_plain_columns=True,
            include_blobs=False,
            include_calculated=include_calculated
        )

        # Special notes
        branches.append(XML_COMMENT_SPECIAL_NOTES)
        for sn in self.special_notes:
            branches.append(sn.get_xml_root())

        # Patient details
        if self.is_anonymous:
            branches.append(XML_COMMENT_ANONYMOUS)
        elif include_patient:
            branches.append(XML_COMMENT_PATIENT)
            if self.patient:
                branches.append(self.patient.get_xml_root(req))

        # BLOBs
        if include_blobs:
            branches.append(XML_COMMENT_BLOBS)
            branches += self._get_xml_branches(req=req,
                                               skip_attrs=skip_fields,
                                               include_plain_columns=False,
                                               include_blobs=True,
                                               include_calculated=False,
                                               sort_by_attr=True)

        # Ancillary objects
        if include_ancillary:
            item_collections = []  # type: List[XmlElement]
            found_ancillary = False
            # We use a slightly more manual iteration process here so that
            # we iterate through individual ancillaries but clustered by their
            # name (e.g. if we have 50 trials and 5 groups, we do them in
            # collections).
            for attrname, rel_prop, rel_cls in gen_ancillary_relationships(self):  # noqa
                if not found_ancillary:
                    branches.append(XML_COMMENT_ANCILLARY)
                    found_ancillary = True
                itembranches = []  # type: List[XmlElement]
                if rel_prop.uselist:
                    ancillaries = getattr(self, attrname)  # type: List[GenericTabletRecordMixin]  # noqa
                else:
                    ancillaries = [getattr(self, attrname)]  # type: List[GenericTabletRecordMixin]  # noqa
                for ancillary in ancillaries:
                    itembranches.append(
                        ancillary._get_xml_root(
                            req=req,
                            skip_attrs=skip_fields,
                            include_plain_columns=True,
                            include_blobs=True,
                            include_calculated=include_calculated,
                            sort_by_attr=True
                        )
                    )
                itemcollection = XmlElement(name=attrname, value=itembranches)
                item_collections.append(itemcollection)
            item_collections.sort(key=lambda el: el.name)
            branches += item_collections

        # Completely separate additional summary tables
        if include_calculated:
            item_collections = []  # type: List[XmlElement]
            found_est = False
            for est in self.get_extra_summary_tables(req):
                if not found_est and est.rows:
                    branches.append(XML_COMMENT_CALCULATED)
                    found_est = True
                item_collections.append(est.get_xml_element())
            item_collections.sort(key=lambda el: el.name)
            branches += item_collections

        return branches

    # -------------------------------------------------------------------------
    # HTML view
    # -------------------------------------------------------------------------

    def get_html(self, req: CamcopsRequest, anonymise: bool = False) -> str:
        """Returns HTML representing task."""
        req.prepare_for_html_figures()
        return render("task.mako",
                      dict(task=self,
                           anonymise=anonymise,
                           signature=False,
                           viewtype=ViewArg.HTML),
                      request=req)

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf(self, req: CamcopsRequest, anonymise: bool = False) -> bytes:
        """Returns PDF representing task."""
        html = self.get_pdf_html(req, anonymise=anonymise)  # main content
        if CSS_PAGED_MEDIA:
            return pdf_from_html(req, html=html)
        else:
            return pdf_from_html(
                req,
                html=html,
                header_html=render(
                    "wkhtmltopdf_header.mako",
                    dict(inner_text=render("task_page_header.mako",
                                           dict(task=self, anonymise=anonymise),
                                           request=req)),
                    request=req
                ),
                footer_html=render(
                    "wkhtmltopdf_footer.mako",
                    dict(inner_text=render("task_page_footer.mako",
                                           dict(task=self),
                                           request=req)),
                    request=req
                ),
                extra_wkhtmltopdf_options={
                    "orientation": ("Landscape" if self.use_landscape_for_pdf
                                    else "Portrait")
                }
            )

    def get_pdf_html(self, req: CamcopsRequest,
                     anonymise: bool = False) -> str:
        """Gets HTML used to make PDF (slightly different from plain HTML)."""
        req.prepare_for_pdf_figures()
        return render("task.mako",
                      dict(task=self,
                           anonymise=anonymise,
                           pdf_landscape=self.use_landscape_for_pdf,
                           signature=self.has_clinician,
                           viewtype=ViewArg.PDF),
                      request=req)

    def suggested_pdf_filename(self, req: CamcopsRequest) -> str:
        """Suggested filename for PDF."""
        cfg = req.config
        return get_export_filename(
            req=req,
            patient_spec_if_anonymous=cfg.patient_spec_if_anonymous,
            patient_spec=cfg.patient_spec,
            filename_spec=cfg.task_filename_spec,
            task_format=ViewArg.PDF,
            is_anonymous=self.is_anonymous,
            surname=self.patient.get_surname() if self.patient else "",
            forename=self.patient.get_forename() if self.patient else "",
            dob=self.patient.get_dob() if self.patient else None,
            sex=self.patient.get_sex() if self.patient else None,
            idnum_objects=self.patient.get_idnum_objects() if self.patient else None,  # noqa
            creation_datetime=self.get_creation_datetime(),
            basetable=self.tablename,
            serverpk=self._pk
        )

    def write_pdf_to_disk(self, req: CamcopsRequest, filename: str) -> None:
        """Writes PDF to disk, using filename."""
        pdffile = open(filename, "wb")
        pdffile.write(self.get_pdf(req))

    # -------------------------------------------------------------------------
    # Metadata for e.g. RiO
    # -------------------------------------------------------------------------

    def get_rio_metadata(self,
                         which_idnum: int,
                         uploading_user_id: str,
                         document_type: str) -> str:
        """
        Called by cc_hl7.send_to_filestore().

        From Servelec (Lee Meredith) to Rudolf Cardinal, 2014-12-04:

        .. code-block:: none

            Batch Document Upload

            The RiO batch document upload function can be used to upload
            documents in bulk automatically.  RiO includes a Batch Upload
            windows service which monitors a designated folder for new files.
            Each file which is scanned must be placed in the designated folder
            along with a meta-data file which describes the document.  So
            essentially if a document had been scanned in and was called
            ‘ThisIsANewReferralLetterForAPatient.pdf’ then there would also
            need to be a meta file in the same folder called
            ‘ThisIsANewReferralLetterForAPatient.metadata’.  The contents of
            the meta file would need to include the following:

                Field Order; Field Name; Description; Data Mandatory (Y/N);
                Format

                1; ClientID; RiO Client ID which identifies the patient in RiO
                against which the document will be uploaded.; Y; 15
                Alphanumeric Characters

                2; UserID; User ID of the uploaded document, this is any user
                defined within the RiO system and can be a single system user
                called ‘AutomaticDocumentUploadUser’ for example.; Y; 10
                Alphanumeric Characters

                    [NB example longer than that!]

                3; DocumentType; The RiO defined document type eg: APT; Y; 80
                Alphanumeric Characters

                4; Title; The title of the document; N; 40 Alphanumeric
                Characters

                5; Description; The document description.; N; 500 Alphanumeric
                Characters

                6; Author; The author of the document; N; 80 Alphanumeric
                Characters

                7; DocumentDate; The date of the document; N; dd/MM/yyyy HH:mm

                8; FinalRevision; The revision values are 0 Draft or 1 Final,
                this is defaulted to 1 which is Final revision.; N; 0 or 1

            As an example, this is what would be needed in a meta file:

                “1000001”,”TRUST1”,”APT”,”A title”, “A description of the
                    document”, “An author”,”01/12/2012 09:45”,”1”

            (on one line)

        Clarification, from Lee Meredith to Rudolf Cardinal, 2015-02-18:

        - metadata files must be plain ASCII, not UTF-8

            - ... here and cc_hl7.send_to_filestore()

        - line terminator is <CR>

            - ... cc_hl7.send_to_filestore()

        - user name limit is 10 characters, despite incorrect example

            - ... RecipientDefinition.check_valid()

        - DocumentType is a code that maps to a human-readable document
          type; for example, "APT" might map to "Appointment Letter". These
          mappings are specific to the local system. (We will probably want
          one that maps to "Clinical Correspondence" in the absence of
          anything more specific.)

        - RiO will delete the files after it's processed them.

        - Filenames should avoid spaces, but otherwise any other standard
          ASCII code is fine within filenames.

            - ... cc_hl7.send_to_filestore()

        """

        try:
            client_id = self.patient.get_idnum_value(which_idnum)
        except AttributeError:
            client_id = ""
        title = "CamCOPS_" + self.shortname
        description = self.longname
        author = self.get_clinician_name()  # may be blank
        document_date = format_datetime(self.when_created,
                                        DateFormat.RIO_EXPORT_UK)
        # This STRIPS the timezone information; i.e. it is in the local
        # timezone but doesn't tell you which timezone that is. (That's fine;
        # it should be local or users would be confused.)
        final_revision = (0 if self.is_live_on_tablet() else 1)

        item_list = [
            client_id,
            uploading_user_id,
            document_type,
            title,
            description,
            author,
            document_date,
            final_revision
        ]
        # UTF-8 is NOT supported by RiO for metadata. So:
        csv_line = ",".join([
            '"{}"'.format(mangle_unicode_to_ascii(x))
            for x in item_list
        ])
        return csv_line + "\n"

    # -------------------------------------------------------------------------
    # HTML elements used by tasks
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_standard_clinician_comments_block(self,
                                              req: CamcopsRequest,
                                              comments: str) -> str:
        """HTML DIV for clinician's comments."""
        return render("clinician_comments.mako",
                      dict(comment=comments),
                      request=req)

    def get_is_complete_td_pair(self, req: CamcopsRequest) -> str:
        """HTML to indicate whether task is complete or not, and to make it
        very obvious visually when it isn't."""
        c = self.is_complete()
        return """<td>Completed?</td>{}<b>{}</b></td>""".format(
            "<td>" if c else """<td class="{}">""".format(CssClass.INCOMPLETE),
            get_yes_no(req, c)
        )

    def get_is_complete_tr(self, req: CamcopsRequest) -> str:
        """HTML table row to indicate whether task is complete or not, and to
        make it very obvious visually when it isn't."""
        return "<tr>" + self.get_is_complete_td_pair(req) + "</tr>"

    def get_twocol_val_row(self,
                           fieldname: str,
                           default: str = None,
                           label: str = None) -> str:
        """HTML table row, two columns, without web-safing of value."""
        val = getattr(self, fieldname)
        if val is None:
            val = default
        if label is None:
            label = fieldname
        return tr_qa(label, val)

    def get_twocol_string_row(self,
                              fieldname: str,
                              label: str = None) -> str:
        """HTML table row, two columns, with web-safing of value."""
        if label is None:
            label = fieldname
        return tr_qa(label, getattr(self, fieldname))

    def get_twocol_bool_row(self,
                            req: CamcopsRequest,
                            fieldname: str,
                            label: str = None) -> str:
        """HTML table row, two columns, with Boolean Y/N formatter."""
        if label is None:
            label = fieldname
        return tr_qa(label, get_yes_no_none(req, getattr(self, fieldname)))

    def get_twocol_bool_row_true_false(self,
                                       req: CamcopsRequest,
                                       fieldname: str,
                                       label: str = None) -> str:
        """HTML table row, two columns, with Boolean T/F formatter."""
        if label is None:
            label = fieldname
        return tr_qa(label, get_true_false_none(req, getattr(self, fieldname)))

    def get_twocol_bool_row_present_absent(self,
                                           req: CamcopsRequest,
                                           fieldname: str,
                                           label: str = None) -> str:
        """HTML table row, two columns, with Boolean P/A formatter."""
        if label is None:
            label = fieldname
        return tr_qa(label, get_present_absent_none(req,
                                                    getattr(self, fieldname)))

    @staticmethod
    def get_twocol_picture_row(blob: Optional[Blob], label: str) -> str:
        """HTML table row, two columns, with PNG on right."""
        return tr(label, get_blob_img_html(blob))

    # -------------------------------------------------------------------------
    # Field helper functions for subclasses
    # -------------------------------------------------------------------------

    def get_values(self, fields: List[str]) -> List:
        """Get list of object's values from list of field names."""
        return [getattr(self, f) for f in fields]

    def is_field_complete(self, field: str) -> bool:
        """Is the field not None?"""
        return getattr(self, field) is not None

    def are_all_fields_complete(self, fields: List[str]) -> bool:
        """Are all fields not None?"""
        for f in fields:
            if getattr(self, f) is None:
                return False
        return True

    def n_complete(self, fields: List[str]) -> int:
        """How many of the fields are not None?"""
        total = 0
        for f in fields:
            if getattr(self, f) is not None:
                total += 1
        return total

    def n_incomplete(self, fields: List[str]) -> int:
        """How many of the fields are None?"""
        total = 0
        for f in fields:
            if getattr(self, f) is None:
                total += 1
        return total

    def count_booleans(self, fields: List[str]) -> int:
        """How many fields evaluate to True?"""
        total = 0
        for f in fields:
            value = getattr(self, f)
            if value:
                total += 1
        return total

    def all_true(self, fields: List[str]) -> bool:
        """Do all fields evaluate to True?"""
        for f in fields:
            value = getattr(self, f)
            if not value:
                return False
        return True

    def count_where(self,
                    fields: List[str],
                    wherevalues: List[Any]) -> int:
        """Count how many field values are in wherevalues."""
        return sum(1 for x in self.get_values(fields) if x in wherevalues)

    def count_wherenot(self,
                       fields: List[str],
                       notvalues: List[Any]) -> int:
        """Count how many field values are NOT in notvalues."""
        return sum(1 for x in self.get_values(fields) if x not in notvalues)

    def sum_fields(self,
                   fields: List[str],
                   ignorevalue: Any = None) -> Union[int, float]:
        """Sum values stored in all fields (skipping any whose value is
        ignorevalue; treating fields containing None as zero)."""
        total = 0
        for f in fields:
            value = getattr(self, f)
            if value == ignorevalue:
                continue
            total += value if value is not None else 0
        return total

    def mean_fields(self,
                    fields: List[str],
                    ignorevalue: Any = None) -> Union[int, float, None]:
        """
        Mean of values stored in all fields (skipping any whose value is
        ignorevalue).
        """
        values = []
        for f in fields:
            value = getattr(self, f)
            if value != ignorevalue:
                values.append(value)
        try:
            return statistics.mean(values)
        except (TypeError, statistics.StatisticsError):
            return None

    @staticmethod
    def fieldnames_from_prefix(prefix: str, start: int, end: int) -> List[str]:
        return [prefix + str(x) for x in range(start, end + 1)]

    @staticmethod
    def fieldnames_from_list(prefix: str,
                             suffixes: Iterable[Any]) -> List[str]:
        return [prefix + str(x) for x in suffixes]

    # -------------------------------------------------------------------------
    # Extra strings
    # -------------------------------------------------------------------------

    def get_extrastring_taskname(self) -> str:
        return self.extrastring_taskname or self.tablename

    def extrastrings_exist(self, req: CamcopsRequest) -> bool:
        return req.task_extrastrings_exist(self.get_extrastring_taskname())

    def wxstring(self,
                 req: CamcopsRequest,
                 name: str,
                 defaultvalue: str = None,
                 provide_default_if_none: bool = True) -> str:
        if defaultvalue is None and provide_default_if_none:
            defaultvalue = "[{}: {}]".format(self.get_extrastring_taskname(),
                                             name)
        return req.wxstring(
            self.get_extrastring_taskname(),
            name,
            defaultvalue,
            provide_default_if_none=provide_default_if_none)

    def xstring(self,
                req: CamcopsRequest,
                name: str,
                defaultvalue: str = None,
                provide_default_if_none: bool = True) -> str:
        if defaultvalue is None and provide_default_if_none:
            defaultvalue = "[{}: {}]".format(self.get_extrastring_taskname(),
                                             name)
        return req.xstring(
            self.get_extrastring_taskname(),
            name,
            defaultvalue,
            provide_default_if_none=provide_default_if_none)


# =============================================================================
# Fieldnames to auto-exempt from text filtering
# =============================================================================

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def text_filter_exempt_fields(task: Type[Task]) -> List[str]:
    exempt = []  # type: List[str]
    for attrname, column in gen_columns(task):
        if attrname.startswith("_") or not is_sqlatype_string(column.type):
            exempt.append(attrname)
    return exempt


def all_task_tables_with_min_client_version() -> Dict[str, Version]:
    d = {}  # type: Dict[str, Version]
    classes = list(Task.gen_all_subclasses())
    for cls in classes:
        d.update(cls.all_tables_with_min_client_version())
    return d


# =============================================================================
# Support functions
# =============================================================================

def get_from_dict(d: Dict, key: str, default: Any = INVALID_VALUE) -> Any:
    """Returns a value from a dictionary."""
    return d.get(key, default)


# =============================================================================
# Reports
# =============================================================================

class TaskCountReport(Report):
    """Report to count task instances."""

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "taskcount"

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        return "(Server) Count current task instances, by creation date"

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    def get_rows_colnames(self, req: CamcopsRequest) -> PlainReportType:
        final_rows = []
        colnames = []
        dbsession = req.dbsession
        group_ids = req.user.ids_of_groups_user_may_report_on
        superuser = req.user.superuser
        classes = Task.all_subclasses_by_tablename()
        for cls in classes:
            # noinspection PyProtectedMember
            select_fields = [
                literal(cls.__tablename__).label("task"),
                # func.year() is specific to some DBs, e.g. MySQL
                # so is func.extract(); http://modern-sql.com/feature/extract
                extract_year(cls._when_added_batch_utc).label("year"),
                extract_month(cls._when_added_batch_utc).label("month"),
                func.count().label("num_tasks_added"),
            ]
            select_from = cls.__table__
            # noinspection PyProtectedMember
            wheres = [cls._current == True]  # nopep8
            if not superuser:
                # Restrict to accessible groups
                # noinspection PyProtectedMember
                wheres.append(cls._group_id.in_(group_ids))
            group_by = ["year", "month"]
            order_by = [desc("year"), desc("month")]
            # ... http://docs.sqlalchemy.org/en/latest/core/tutorial.html#ordering-or-grouping-by-a-label  # noqa
            query = select(select_fields) \
                .select_from(select_from) \
                .where(and_(*wheres)) \
                .group_by(*group_by) \
                .order_by(*order_by)
            # log.critical(str(query))
            rows, colnames = get_rows_fieldnames_from_query(dbsession, query)
            final_rows.extend(rows)
        return PlainReportType(rows=final_rows, columns=colnames)


# =============================================================================
# Unit testing
# =============================================================================

class TaskTests(DemoDatabaseTestCase):
    def test_query_phq9(self) -> None:
        self.announce("test_query_phq9")
        from camcops_server.tasks import Phq9
        phq9_query = self.dbsession.query(Phq9)
        results = phq9_query.all()
        log.info("{}", results)

    def test_all_tasks(self) -> None:
        self.announce("test_all_tasks")
        from datetime import date
        import hl7
        from sqlalchemy.sql.schema import Column
        from camcops_server.cc_modules.cc_ctvinfo import CtvInfo
        from camcops_server.cc_modules.cc_simpleobjects import IdNumReference
        from camcops_server.cc_modules.cc_summaryelement import SummaryElement
        from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo
        from camcops_server.cc_modules.cc_tsv import TsvPage
        from camcops_server.cc_modules.cc_xml import XmlElement

        subclasses = Task.all_subclasses_by_tablename()
        tables = [cls.tablename for cls in subclasses]
        log.info("Actual task table names: {!r} (n={})", tables, len(tables))
        req = self.req
        recipdef = self.recipdef
        for cls in subclasses:
            log.info("Testing {}", cls)
            q = self.dbsession.query(cls)
            t = q.first()  # type: Task

            self.assertIsNotNone(t, "Missing task!")

            self.assertIsInstance(t.is_complete(), bool)
            self.assertIsInstance(t.get_task_html(req), str)
            for trackerinfo in t.get_trackers(req):
                self.assertIsInstance(trackerinfo, TrackerInfo)
            ctvlist = t.get_clinical_text(req)
            if ctvlist is not None:
                for ctvinfo in ctvlist:
                    self.assertIsInstance(ctvinfo, CtvInfo)
            for est in t.get_extra_summary_tables(req):
                self.assertIsInstance(est.get_tsv_page(), TsvPage)
                self.assertIsInstance(est.get_xml_element(), XmlElement)

            self.assertIsInstance(t.has_patient, bool)
            self.assertIsInstance(t.is_anonymous, bool)
            self.assertIsInstance(t.has_clinician, bool)
            self.assertIsInstance(t.has_respondent, bool)
            self.assertIsInstance(t.tablename, str)
            for fn in t.get_fieldnames():
                self.assertIsInstance(fn, str)
            self.assertIsInstance(t.field_contents_valid(), bool)
            for msg in t.field_contents_invalid_because():
                self.assertIsInstance(msg, str)
            for fn in t.get_blob_fields():
                self.assertIsInstance(fn, str)

            self.assertIsInstance(t.get_pk(), int)  # all our examples do have PKs  # noqa
            self.assertIsInstance(t.is_preserved(), bool)
            self.assertIsInstance(t.was_forcibly_preserved(), bool)
            self.assertIsInstanceOrNone(t.get_creation_datetime(), Pendulum)
            self.assertIsInstanceOrNone(
                t.get_creation_datetime_utc(), Pendulum)
            self.assertIsInstanceOrNone(
                t.get_seconds_from_creation_to_first_finish(), float)

            self.assertIsInstance(t.get_adding_user_id(), int)
            self.assertIsInstance(t.get_adding_user_username(), str)
            self.assertIsInstance(t.get_removing_user_username(), str)
            self.assertIsInstance(t.get_preserving_user_username(), str)
            self.assertIsInstance(t.get_manually_erasing_user_username(), str)

            for se in t.standard_task_summary_fields():
                self.assertIsInstance(se, SummaryElement)

            self.assertIsInstance(t.get_clinician_name(), str)
            self.assertIsInstance(t.is_respondent_complete(), bool)
            self.assertIsInstanceOrNone(t.patient, Patient)
            self.assertIsInstance(t.is_female(), bool)
            self.assertIsInstance(t.is_male(), bool)
            self.assertIsInstanceOrNone(t.get_patient_server_pk(), int)
            self.assertIsInstance(t.get_patient_forename(), str)
            self.assertIsInstance(t.get_patient_surname(), str)
            dob = t.get_patient_dob()
            assert (
                dob is None or
                isinstance(dob, date) or
                isinstance(dob, Date)
            )
            self.assertIsInstanceOrNone(t.get_patient_dob_first11chars(), str)
            self.assertIsInstance(t.get_patient_sex(), str)
            self.assertIsInstance(t.get_patient_address(), str)
            for idnum in t.get_patient_idnum_objects():
                self.assertIsInstance(idnum.get_idnum_reference(),
                                      IdNumReference)
                self.assertIsInstance(idnum.is_valid(), bool)
                self.assertIsInstance(idnum.description(req), str)
                self.assertIsInstance(idnum.short_description(req), str)
                self.assertIsInstance(idnum.get_filename_component(req), str)
            pidseg = t.get_patient_hl7_pid_segment(req, recipdef)
            assert isinstance(pidseg, str) or isinstance(pidseg, hl7.Segment)
            for dataseg in t.get_hl7_data_segments(req, recipdef):
                self.assertIsInstance(dataseg, hl7.Segment)
            for dataseg in t.get_hl7_extra_data_segments(recipdef):
                self.assertIsInstance(dataseg, hl7.Segment)
            self.assertIsInstance(t.is_erased(), bool)
            self.assertIsInstance(t.is_live_on_tablet(), bool)
            for attrname, col in t.gen_text_filter_columns():
                self.assertIsInstance(attrname, str)
                self.assertIsInstance(col, Column)
            for page in t.get_tsv_pages(req):
                self.assertIsInstance(page.get_tsv(), str)
            # *** replace test when anonymous export redone: get_cris_dd_rows
            self.assertIsInstance(t.get_xml(req), str)
            self.assertIsInstance(t.get_html(req), str)
            self.assertIsInstance(t.get_pdf(req), bytes)
            self.assertIsInstance(t.get_pdf_html(req), str)
            self.assertIsInstance(t.suggested_pdf_filename(req), str)
            self.assertIsInstance(
                t.get_rio_metadata(which_idnum=1,
                                   uploading_user_id=self.user.id,
                                   document_type="some_doc_type"),
                str
            )
