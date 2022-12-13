#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_task.py

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

**Represents CamCOPS tasks.**

Core task export methods:

======= =======================================================================
Format  Comment
======= =======================================================================
HTML    The task in a user-friendly format.
PDF     Essentially the HTML output, but with page headers and (for clinician
        tasks) a signature block, and without additional HTML administrative
        hyperlinks.
XML     Centres on the task with its subdata integrated.
TSV     Tab-separated value format.
SQL     As part of an SQL or SQLite download.
======= =======================================================================

"""

from base64 import b64encode
from collections import Counter, OrderedDict
import datetime
import logging
import statistics
from typing import (
    Any,
    Dict,
    Iterable,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TYPE_CHECKING,
    Union,
)

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.datetimefunc import (
    convert_datetime_to_utc,
    format_datetime,
    pendulum_to_utc_datetime_without_tz,
)
from cardinal_pythonlib.httpconst import MimeType
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.dialect import SqlaDialectName
from cardinal_pythonlib.sqlalchemy.orm_inspect import (
    gen_columns,
    gen_orm_classes_from_base,
)
from cardinal_pythonlib.sqlalchemy.schema import (
    is_sqlatype_binary,
    is_sqlatype_string,
)
from cardinal_pythonlib.stringfunc import mangle_unicode_to_ascii
from fhirclient.models.attachment import Attachment
from fhirclient.models.bundle import Bundle
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.contactpoint import ContactPoint
from fhirclient.models.documentreference import (
    DocumentReference,
    DocumentReferenceContent,
)
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.humanname import HumanName
from fhirclient.models.identifier import Identifier
from fhirclient.models.observation import Observation
from fhirclient.models.practitioner import Practitioner
from fhirclient.models.questionnaire import Questionnaire
from fhirclient.models.questionnaireresponse import QuestionnaireResponse
import hl7
from pendulum import Date as PendulumDate, DateTime as Pendulum
from pyramid.renderers import render
from semantic_version import Version
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.expression import not_, update
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import (
    Boolean,
    Date as DateColType,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)

from camcops_server.cc_modules.cc_audit import audit
from camcops_server.cc_modules.cc_baseconstants import DOCUMENTATION_URL
from camcops_server.cc_modules.cc_blob import Blob, get_blob_img_html
from camcops_server.cc_modules.cc_cache import cache_region_static, fkg
from camcops_server.cc_modules.cc_constants import (
    ASCII,
    CssClass,
    CSS_PAGED_MEDIA,
    DateFormat,
    FHIRConst as Fc,
    FileType,
    ERA_NOW,
    INVALID_VALUE,
    UTF8,
)
from camcops_server.cc_modules.cc_dataclasses import SummarySchemaInfo
from camcops_server.cc_modules.cc_db import (
    GenericTabletRecordMixin,
    SFN_CAMCOPS_SERVER_VERSION,
    SFN_IS_COMPLETE,
    SFN_SECONDS_CREATION_TO_FIRST_FINISH,
    TASK_FREQUENT_FIELDS,
    TFN_CLINICIAN_CONTACT_DETAILS,
    TFN_CLINICIAN_NAME,
    TFN_CLINICIAN_POST,
    TFN_CLINICIAN_PROFESSIONAL_REGISTRATION,
    TFN_CLINICIAN_SERVICE,
    TFN_CLINICIAN_SPECIALTY,
    TFN_EDITING_TIME_S,
    TFN_FIRSTEXIT_IS_ABORT,
    TFN_FIRSTEXIT_IS_FINISH,
    TFN_PATIENT_ID,
    TFN_RESPONDENT_NAME,
    TFN_RESPONDENT_RELATIONSHIP,
    TFN_WHEN_CREATED,
    TFN_WHEN_FIRSTEXIT,
)
from camcops_server.cc_modules.cc_exception import FhirExportException
from camcops_server.cc_modules.cc_fhir import (
    fhir_observation_component_from_snomed,
    fhir_system_value,
    fhir_sysval_from_id,
    FHIRAnsweredQuestion,
    FHIRAnswerType,
    FHIRQuestionType,
    make_fhir_bundle_entry,
)
from camcops_server.cc_modules.cc_filename import get_export_filename
from camcops_server.cc_modules.cc_hl7 import make_obr_segment, make_obx_segment
from camcops_server.cc_modules.cc_html import (
    get_present_absent_none,
    get_true_false_none,
    get_yes_no,
    get_yes_no_none,
    tr,
    tr_qa,
)
from camcops_server.cc_modules.cc_pdf import pdf_from_html
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg
from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions
from camcops_server.cc_modules.cc_snomed import SnomedLookup
from camcops_server.cc_modules.cc_specialnote import SpecialNote
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BoolColumn,
    CamcopsColumn,
    COLATTR_PERMITTED_VALUE_CHECKER,
    gen_ancillary_relationships,
    get_camcops_blob_column_attr_names,
    get_column_attr_names,
    PendulumDateTimeAsIsoTextColType,
    permitted_value_failure_msgs,
    permitted_values_ok,
    PermittedValueChecker,
    SemanticVersionColType,
    TableNameColType,
)
from camcops_server.cc_modules.cc_sqlalchemy import Base, get_table_ddl
from camcops_server.cc_modules.cc_summaryelement import (
    ExtraSummaryTable,
    SummaryElement,
)
from camcops_server.cc_modules.cc_version import (
    CAMCOPS_SERVER_VERSION,
    CAMCOPS_SERVER_VERSION_STRING,
    MINIMUM_TABLET_VERSION,
)
from camcops_server.cc_modules.cc_xml import (
    get_xml_document,
    XML_COMMENT_ANCILLARY,
    XML_COMMENT_ANONYMOUS,
    XML_COMMENT_BLOBS,
    XML_COMMENT_CALCULATED,
    XML_COMMENT_PATIENT,
    XML_COMMENT_SNOMED_CT,
    XML_COMMENT_SPECIAL_NOTES,
    XML_NAME_SNOMED_CODES,
    XmlElement,
    XmlLiteral,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_ctvinfo import CtvInfo  # noqa: F401
    from camcops_server.cc_modules.cc_exportrecipient import (  # noqa: F401
        ExportRecipient,
    )
    from camcops_server.cc_modules.cc_patient import Patient  # noqa: F401
    from camcops_server.cc_modules.cc_patientidnum import (  # noqa: F401
        PatientIdNum,
    )
    from camcops_server.cc_modules.cc_request import (  # noqa: F401
        CamcopsRequest,
    )
    from camcops_server.cc_modules.cc_snomed import (  # noqa: F401
        SnomedExpression,
    )
    from camcops_server.cc_modules.cc_trackerhelpers import (  # noqa: F401
        TrackerInfo,
    )
    from camcops_server.cc_modules.cc_spreadsheet import (  # noqa: F401
        SpreadsheetPage,
    )

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_SKIP_FHIR_DOCS = False
DEBUG_SHOW_FHIR_QUESTIONNAIRE = False

if any([DEBUG_SKIP_FHIR_DOCS, DEBUG_SHOW_FHIR_QUESTIONNAIRE]):
    log.warning("Debugging options enabled!")


# =============================================================================
# Constants
# =============================================================================

ANCILLARY_FWD_REF = "Ancillary"
TASK_FWD_REF = "Task"

FHIR_UNKNOWN_TEXT = "[?]"

SNOMED_TABLENAME = "_snomed_ct"
SNOMED_COLNAME_TASKTABLE = "task_tablename"
SNOMED_COLNAME_TASKPK = "task_pk"
SNOMED_COLNAME_WHENCREATED_UTC = "when_created"
SNOMED_COLNAME_EXPRESSION = "snomed_expression"
UNUSED_SNOMED_XML_NAME = "snomed_ct_expressions"


# =============================================================================
# Patient mixin
# =============================================================================


class TaskHasPatientMixin(object):
    """
    Mixin for tasks that have a patient (aren't anonymous).
    """

    # https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html#using-advanced-relationship-arguments-e-g-primaryjoin-etc  # noqa

    # noinspection PyMethodParameters
    @declared_attr
    def patient_id(cls) -> Column:
        """
        SQLAlchemy :class:`Column` that is a foreign key to the patient table.
        """
        return Column(
            TFN_PATIENT_ID,
            Integer,
            nullable=False,
            index=True,
            comment="(TASK) Foreign key to patient.id (for this device/era)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def patient(cls) -> RelationshipProperty:
        """
        SQLAlchemy relationship: "the patient for this task".

        Note that this refers to the CURRENT version of the patient. If there
        is an editing chain, older patient versions are not retrieved.

        Compare :func:`camcops_server.cc_modules.cc_blob.blob_relationship`,
        which uses the same strategy, as do several other similar functions.

        """
        return relationship(
            "Patient",
            primaryjoin=(
                "and_("
                " remote(Patient.id) == foreign({task}.patient_id), "
                " remote(Patient._device_id) == foreign({task}._device_id), "
                " remote(Patient._era) == foreign({task}._era), "
                " remote(Patient._current) == True "
                ")".format(task=cls.__name__)
            ),
            uselist=False,
            viewonly=True,
            # Profiling results 2019-10-14 exporting 4185 phq9 records with
            # unique patients to xlsx
            # lazy="select"  : 59.7s
            # lazy="joined"  : 44.3s
            # lazy="subquery": 36.9s
            # lazy="selectin": 35.3s
            # See also idnums relationship on Patient class (cc_patient.py)
            lazy="selectin",
        )
        # NOTE: this retrieves the most recent (i.e. the current) information
        # on that patient. Consequently, task version history doesn't show the
        # history of patient edits. This is consistent with our relationship
        # strategy throughout for the web front-end viewer.

    # noinspection PyMethodParameters
    @classproperty
    def has_patient(cls) -> bool:
        """
        Does this task have a patient? (Yes.)
        """
        return True


# =============================================================================
# Clinician mixin
# =============================================================================


class TaskHasClinicianMixin(object):
    """
    Mixin to add clinician columns and override clinician-related methods.

    Must be to the LEFT of ``Task`` in the class's base class list, i.e.
    must have higher precedence than ``Task`` in the method resolution order.
    """

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_specialty(cls) -> Column:
        return CamcopsColumn(
            TFN_CLINICIAN_SPECIALTY,
            Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's specialty "
            "(e.g. Liaison Psychiatry)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_name(cls) -> Column:
        return CamcopsColumn(
            TFN_CLINICIAN_NAME,
            Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's name (e.g. Dr X)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_professional_registration(cls) -> Column:
        return CamcopsColumn(
            TFN_CLINICIAN_PROFESSIONAL_REGISTRATION,
            Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's professional registration (e.g. "
            "GMC# 12345)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_post(cls) -> Column:
        return CamcopsColumn(
            TFN_CLINICIAN_POST,
            Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's post (e.g. Consultant)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_service(cls) -> Column:
        return CamcopsColumn(
            TFN_CLINICIAN_SERVICE,
            Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's service (e.g. Liaison Psychiatry "
            "Service)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_contact_details(cls) -> Column:
        return CamcopsColumn(
            TFN_CLINICIAN_CONTACT_DETAILS,
            Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's contact details (e.g. bleep, "
            "extension)",
        )

    # For field order, see also:
    # https://stackoverflow.com/questions/3923910/sqlalchemy-move-mixin-columns-to-end  # noqa

    # noinspection PyMethodParameters
    @classproperty
    def has_clinician(cls) -> bool:
        """
        Does the task have a clinician? (Yes.)
        """
        return True

    def get_clinician_name(self) -> str:
        """
        Returns the clinician's name.
        """
        return self.clinician_name or ""

    def get_clinician_fhir_telecom_other(self, req: "CamcopsRequest") -> str:
        """
        Return a mishmash of information that doesn't fit neatly into a FHIR
        Practitioner object, but people might actually want to know.
        """
        _ = req.gettext
        components = []  # type: List[str]
        # In sequence, e.g.:
        # - Consultant
        if self.clinician_post:
            components.append(f'{_("Post:")} {self.clinician_post}')
        # - Liaison Psychiatry
        if self.clinician_specialty:
            components.append(f'{_("Specialty:")} {self.clinician_specialty}')
        # - GMC# 12345
        if self.clinician_professional_registration:
            components.append(
                f'{_("Professional registration:")} '
                f"{self.clinician_professional_registration}"
            )
        # - Liaison Psychiatry Service
        if self.clinician_service:
            components.append(f'{_("Service:")} {self.clinician_service}')
        # - tel. x12345
        if self.clinician_contact_details:
            components.append(
                f'{_("Contact details:")} ' f"{self.clinician_contact_details}"
            )
        return " | ".join(components)


# =============================================================================
# Respondent mixin
# =============================================================================


class TaskHasRespondentMixin(object):
    """
    Mixin to add respondent columns and override respondent-related methods.

    A respondent is someone who isn't the patient and isn't a clinician, such
    as a family member or carer.

    Must be to the LEFT of ``Task`` in the class's base class list, i.e.
    must have higher precedence than ``Task`` in the method resolution order.

    Notes:

    - If you don't use ``@declared_attr``, the ``comment`` property on columns
      doesn't work.
    """

    # noinspection PyMethodParameters
    @declared_attr
    def respondent_name(cls) -> Column:
        return CamcopsColumn(
            TFN_RESPONDENT_NAME,
            Text,
            identifies_patient=True,
            comment="(RESPONDENT) Respondent's name",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def respondent_relationship(cls) -> Column:
        return Column(
            TFN_RESPONDENT_RELATIONSHIP,
            Text,
            comment="(RESPONDENT) Respondent's relationship to patient",
        )

    # noinspection PyMethodParameters
    @classproperty
    def has_respondent(cls) -> bool:
        """
        Does the class have a respondent? (Yes.)
        """
        return True

    def is_respondent_complete(self) -> bool:
        """
        Do we have sufficient information about the respondent?
        (That means: name, relationship to the patient.)
        """
        return all([self.respondent_name, self.respondent_relationship])


# =============================================================================
# Task base class
# =============================================================================


class Task(GenericTabletRecordMixin, Base):
    """
    Abstract base class for all tasks.

    Note:

    - For column definitions: use
      :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn`, not
      :class:`Column`, if you have fields that need to define permitted values,
      mark them as BLOB-referencing fields, or do other CamCOPS-specific
      things.

    """

    __abstract__ = True

    # noinspection PyMethodParameters
    @declared_attr
    def __mapper_args__(cls):
        return {"polymorphic_identity": cls.__name__, "concrete": True}

    # =========================================================================
    # PART 0: COLUMNS COMMON TO ALL TASKS
    # =========================================================================

    # Columns

    # noinspection PyMethodParameters
    @declared_attr
    def when_created(cls) -> Column:
        """
        Column representing the task's creation time.
        """
        return Column(
            TFN_WHEN_CREATED,
            PendulumDateTimeAsIsoTextColType,
            nullable=False,
            comment="(TASK) Date/time this task instance was created "
            "(ISO 8601)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def when_firstexit(cls) -> Column:
        """
        Column representing when the user first exited the task's editor
        (i.e. first "finish" or first "abort").
        """
        return Column(
            TFN_WHEN_FIRSTEXIT,
            PendulumDateTimeAsIsoTextColType,
            comment="(TASK) Date/time of the first exit from this task "
            "(ISO 8601)",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def firstexit_is_finish(cls) -> Column:
        """
        Was the first exit from the task's editor a successful "finish"?
        """
        return Column(
            TFN_FIRSTEXIT_IS_FINISH,
            Boolean,
            comment="(TASK) Was the first exit from the task because it was "
            "finished (1)?",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def firstexit_is_abort(cls) -> Column:
        """
        Was the first exit from the task's editor an "abort"?
        """
        return Column(
            TFN_FIRSTEXIT_IS_ABORT,
            Boolean,
            comment="(TASK) Was the first exit from this task because it was "
            "aborted (1)?",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def editing_time_s(cls) -> Column:
        """
        How long has the user spent editing the task?
        (Calculated by the CamCOPS client.)
        """
        return Column(
            TFN_EDITING_TIME_S, Float, comment="(TASK) Time spent editing (s)"
        )

    # Relationships

    # noinspection PyMethodParameters
    @declared_attr
    def special_notes(cls) -> RelationshipProperty:
        """
        List-style SQLAlchemy relationship to any :class:`SpecialNote` objects
        attached to this class. Skips hidden (quasi-deleted) notes.
        """
        return relationship(
            SpecialNote,
            primaryjoin=(
                "and_("
                " remote(SpecialNote.basetable) == literal({repr_task_tablename}), "  # noqa
                " remote(SpecialNote.task_id) == foreign({task}.id), "
                " remote(SpecialNote.device_id) == foreign({task}._device_id), "  # noqa
                " remote(SpecialNote.era) == foreign({task}._era), "
                " not_(SpecialNote.hidden)"
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
    #
    # Notes:
    #
    # - for summaries, see GenericTabletRecordMixin.get_summaries

    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------
    __tablename__ = None  # type: str  # also the SQLAlchemy table name
    shortname = None  # type: str

    # -------------------------------------------------------------------------
    # Attributes that can be overridden
    # -------------------------------------------------------------------------
    extrastring_taskname = (
        None
    )  # type: str  # if None, tablename is used instead  # noqa
    info_filename_stem = (
        None
    )  # type: str  # if None, tablename is used instead  # noqa
    provides_trackers = False
    use_landscape_for_pdf = False
    dependent_classes = []

    prohibits_clinical = False
    prohibits_commercial = False
    prohibits_educational = False
    prohibits_research = False

    @classmethod
    def prohibits_anything(cls) -> bool:
        return any(
            [
                cls.prohibits_clinical,
                cls.prohibits_commercial,
                cls.prohibits_educational,
                cls.prohibits_research,
            ]
        )

    # -------------------------------------------------------------------------
    # Methods always overridden by the actual task
    # -------------------------------------------------------------------------

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        """
        Long name (in the relevant language).
        """
        raise NotImplementedError("Task.longname must be overridden")

    def is_complete(self) -> bool:
        """
        Is the task instance complete?

        Must be overridden.
        """
        raise NotImplementedError("Task.is_complete must be overridden")

    def get_task_html(self, req: "CamcopsRequest") -> str:
        """
        HTML for the main task content.

        Must be overridden by derived classes.
        """
        raise NotImplementedError(
            "No get_task_html() HTML generator for this task class!"
        )

    # -------------------------------------------------------------------------
    # Implement if you provide trackers
    # -------------------------------------------------------------------------

    def get_trackers(self, req: "CamcopsRequest") -> List["TrackerInfo"]:
        """
        Tasks that provide quantitative information for tracking over time
        should override this and return a list of
        :class:`camcops_server.cc_modules.cc_trackerhelpers.TrackerInfo`
        objects, one per tracker.

        The information is read by
        :meth:`camcops_server.cc_modules.cc_tracker.Tracker.get_all_plots_for_one_task_html`.

        Time information will be retrieved using :func:`get_creation_datetime`.
        """  # noqa
        return []

    # -------------------------------------------------------------------------
    # Override to provide clinical text
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_clinical_text(
        self, req: "CamcopsRequest"
    ) -> Optional[List["CtvInfo"]]:
        """
        Tasks that provide clinical text information should override this
        to provide a list of
        :class:`camcops_server.cc_modules.cc_ctvinfo.CtvInfo` objects.

        Return ``None`` (default) for a task that doesn't provide clinical
        text, or ``[]`` for one that does in general but has no information for
        this particular instance, or a list of
        :class:`camcops_server.cc_modules.cc_ctvinfo.CtvInfo` objects.
        """
        return None

    # -------------------------------------------------------------------------
    # Override some of these if you provide summaries
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_extra_summary_tables(
        self, req: "CamcopsRequest"
    ) -> List[ExtraSummaryTable]:
        """
        Override if you wish to create extra summary tables, not just add
        summary columns to task/ancillary tables.

        Return a list of
        :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`
        objects.
        """
        return []

    # -------------------------------------------------------------------------
    # Implement if you provide SNOMED-CT codes
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_snomed_codes(
        self, req: "CamcopsRequest"
    ) -> List["SnomedExpression"]:
        """
        Returns all SNOMED-CT codes for this task.

        Args:
            req: the
                :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`

        Returns:
            a list of
            :class:`camcops_server.cc_modules.cc_snomed.SnomedExpression`
            objects

        """
        return []

    # =========================================================================
    # PART 2: INTERNALS
    # =========================================================================

    # -------------------------------------------------------------------------
    # Representations
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        if self.is_anonymous:
            patient_str = ""
        else:
            patient_str = f", patient={self.patient}"
        return "{t} (_pk={pk}, when_created={wc}{patient})".format(
            t=self.tablename,
            pk=self.pk,
            wc=(
                format_datetime(self.when_created, DateFormat.ERA)
                if self.when_created
                else "None"
            ),
            patient=patient_str,
        )

    def __repr__(self) -> str:
        return "<{classname}(_pk={pk}, when_created={wc})>".format(
            classname=self.__class__.__qualname__,
            pk=self.pk,
            wc=(
                format_datetime(self.when_created, DateFormat.ERA)
                if self.when_created
                else "None"
            ),
        )

    # -------------------------------------------------------------------------
    # Way to fetch all task types
    # -------------------------------------------------------------------------

    @classmethod
    def gen_all_subclasses(cls) -> Generator[Type[TASK_FWD_REF], None, None]:
        """
        Generate all non-abstract SQLAlchemy ORM subclasses of :class:`Task` --
        that is, all task classes.

        We require that actual tasks are subclasses of both :class:`Task` and
        :class:`camcops_server.cc_modules.cc_sqlalchemy.Base`.

        OLD WAY (ignore): this means we can (a) inherit from Task to make an
        abstract base class for actual tasks, as with PCL, HADS, HoNOS, etc.;
        and (b) not have those intermediate classes appear in the task list.
        Since all actual classes must be SQLAlchemy ORM objects inheriting from
        Base, that common inheritance is an excellent way to define them.

        NEW WAY: things now inherit from Base/Task without necessarily
        being actual tasks; we discriminate using ``__abstract__`` and/or
        ``__tablename__``. See
        https://docs.sqlalchemy.org/en/latest/orm/inheritance.html#abstract-concrete-classes
        """  # noqa
        # noinspection PyTypeChecker
        return gen_orm_classes_from_base(cls)

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_tablename(cls) -> List[Type[TASK_FWD_REF]]:
        """
        Return all task classes, ordered by table name.
        """
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.tablename)
        return classes

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_shortname(cls) -> List[Type[TASK_FWD_REF]]:
        """
        Return all task classes, ordered by short name.
        """
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.shortname)
        return classes

    @classmethod
    def all_subclasses_by_longname(
        cls, req: "CamcopsRequest"
    ) -> List[Type[TASK_FWD_REF]]:
        """
        Return all task classes, ordered by long name.
        """
        classes = cls.all_subclasses_by_shortname()
        classes.sort(key=lambda c: c.longname(req))
        return classes

    # -------------------------------------------------------------------------
    # Methods that may be overridden by mixins
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def has_patient(cls) -> bool:
        """
        Does the task have a patient? (No.)

        May be overridden by :class:`TaskHasPatientMixin`.
        """
        return False

    # noinspection PyMethodParameters
    @classproperty
    def is_anonymous(cls) -> bool:
        """
        Antonym for :attr:`has_patient`.
        """
        return not cls.has_patient

    # noinspection PyMethodParameters
    @classproperty
    def has_clinician(cls) -> bool:
        """
        Does the task have a clinician? (No.)

        May be overridden by :class:`TaskHasClinicianMixin`.
        """
        return False

    # noinspection PyMethodParameters
    @classproperty
    def has_respondent(cls) -> bool:
        """
        Does the task have a respondent? (No.)

        May be overridden by :class:`TaskHasRespondentMixin`.
        """
        return False

    # -------------------------------------------------------------------------
    # Other classmethods
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def tablename(cls) -> str:
        """
        Returns the database table name for the task's primary table.
        """
        return cls.__tablename__

    # noinspection PyMethodParameters
    @classproperty
    def minimum_client_version(cls) -> Version:
        """
        Returns the minimum client version that provides this task.

        Override this as you add tasks.

        Used by
        :func:`camcops_server.cc_modules.client_api.ensure_valid_table_name`.

        (There are some pre-C++ client versions for which the default is not
        exactly accurate, and the tasks do not override, but this is of no
        consequence and the version numbering system also changed, from
        something legible as a float -- e.g. ``1.2 > 1.14`` -- to something
        interpreted as a semantic version -- e.g. ``1.2 < 1.14``. So we ignore
        that.)
        """
        return MINIMUM_TABLET_VERSION

    # noinspection PyMethodParameters
    @classmethod
    def all_tables_with_min_client_version(cls) -> Dict[str, Version]:
        """
        Returns a dictionary mapping all this task's table names (primary and
        ancillary) to the corresponding minimum client version.
        """
        v = cls.minimum_client_version
        d = {cls.__tablename__: v}  # type: Dict[str, Version]
        for _, _, rel_cls in gen_ancillary_relationships(cls):
            d[rel_cls.__tablename__] = v
        return d

    @classmethod
    def all_tables(cls) -> List[Table]:
        """
        Returns all table classes (primary table plus any ancillary tables).
        """
        # noinspection PyUnresolvedReferences
        return [cls.__table__] + [
            rel_cls.__table__
            for _, _, rel_cls in gen_ancillary_relationships(cls)
        ]

    @classmethod
    def get_ddl(cls, dialect_name: str = SqlaDialectName.MYSQL) -> str:
        """
        Returns DDL for the primary and any ancillary tables.
        """
        return "\n\n".join(
            get_table_ddl(t, dialect_name).strip() for t in cls.all_tables()
        )

    @classmethod
    def help_url(cls) -> str:
        """
        Returns the URL for task-specific online help.

        By default, this is based on the tablename -- e.g. ``phq9``, giving
        ``phq9.html`` in the documentation (from ``phq9.rst`` in the source).
        However, some tasks override this -- which they may do by writing

        .. code-block:: python

            info_filename_stem = "XXX"

        In the C++ code, compare infoFilenameStem() for individual tasks and
        urlconst::taskDocUrl() overall.

        The online help is presently only in English.
        """
        basename = cls.help_url_basename()
        language = "en"
        # DOCUMENTATION_URL has a trailing slash already
        return f"{DOCUMENTATION_URL}{language}/latest/tasks/{basename}.html"

    @classmethod
    def help_url_basename(cls) -> str:
        return cls.info_filename_stem or cls.tablename

    # -------------------------------------------------------------------------
    # More on fields
    # -------------------------------------------------------------------------

    @classmethod
    def get_fieldnames(cls) -> List[str]:
        """
        Returns all field (column) names for this task's primary table.
        """
        return get_column_attr_names(cls)

    def field_contents_valid(self) -> bool:
        """
        Checks field contents validity.

        This is a high-speed function that doesn't bother with explanations,
        since we use it for lots of task :func:`is_complete` calculations.
        """
        return permitted_values_ok(self)

    def field_contents_invalid_because(self) -> List[str]:
        """
        Explains why contents are invalid.
        """
        return permitted_value_failure_msgs(self)

    def get_blob_fields(self) -> List[str]:
        """
        Returns field (column) names for all BLOB fields in this class.
        """
        return get_camcops_blob_column_attr_names(self)

    # -------------------------------------------------------------------------
    # Server field calculations
    # -------------------------------------------------------------------------

    def is_preserved(self) -> bool:
        """
        Is the task preserved and erased from the tablet?
        """
        return self._pk is not None and self._era != ERA_NOW

    def was_forcibly_preserved(self) -> bool:
        """
        Was this task forcibly preserved?
        """
        return self._forcibly_preserved and self.is_preserved()

    def get_creation_datetime(self) -> Optional[Pendulum]:
        """
        Creation datetime, or None.
        """
        return self.when_created

    def get_creation_datetime_utc(self) -> Optional[Pendulum]:
        """
        Creation datetime in UTC, or None.
        """
        localtime = self.get_creation_datetime()
        if localtime is None:
            return None
        return convert_datetime_to_utc(localtime)

    def get_creation_datetime_utc_tz_unaware(
        self,
    ) -> Optional[datetime.datetime]:
        """
        Creation time as a :class:`datetime.datetime` object on UTC with no
        timezone (i.e. an "offset-naive" datetime), or None.
        """
        localtime = self.get_creation_datetime()
        if localtime is None:
            return None
        return pendulum_to_utc_datetime_without_tz(localtime)

    def get_seconds_from_creation_to_first_finish(self) -> Optional[float]:
        """
        Time in seconds from creation time to first finish (i.e. first exit
        if the first exit was a finish rather than an abort), or None.
        """
        if not self.firstexit_is_finish:
            return None
        start = self.get_creation_datetime()
        end = self.when_firstexit
        if not start or not end:
            return None
        diff = end - start
        return diff.total_seconds()

    def get_adding_user_id(self) -> Optional[int]:
        """
        Returns the user ID of the user who uploaded this task.
        """
        # noinspection PyTypeChecker
        return self._adding_user_id

    def get_adding_user_username(self) -> str:
        """
        Returns the username of the user who uploaded this task.
        """
        return self._adding_user.username if self._adding_user else ""

    def get_removing_user_username(self) -> str:
        """
        Returns the username of the user who deleted this task (by removing it
        on the client and re-uploading).
        """
        return self._removing_user.username if self._removing_user else ""

    def get_preserving_user_username(self) -> str:
        """
        Returns the username of the user who "preserved" this task (marking it
        to be saved on the server and then deleting it from the client).
        """
        return self._preserving_user.username if self._preserving_user else ""

    def get_manually_erasing_user_username(self) -> str:
        """
        Returns the username of the user who erased this task manually on the
        server.
        """
        return (
            self._manually_erasing_user.username
            if self._manually_erasing_user
            else ""
        )

    # -------------------------------------------------------------------------
    # Summary tables
    # -------------------------------------------------------------------------

    def standard_task_summary_fields(self) -> List[SummaryElement]:
        """
        Returns summary fields/values provided by all tasks.
        """
        return [
            SummaryElement(
                name=SFN_IS_COMPLETE,
                coltype=Boolean(),
                value=self.is_complete(),
                comment="(GENERIC) Task complete?",
            ),
            SummaryElement(
                name=SFN_SECONDS_CREATION_TO_FIRST_FINISH,
                coltype=Float(),
                value=self.get_seconds_from_creation_to_first_finish(),
                comment="(GENERIC) Time (in seconds) from record creation to "
                "first exit, if that was a finish not an abort",
            ),
            SummaryElement(
                name=SFN_CAMCOPS_SERVER_VERSION,
                coltype=SemanticVersionColType(),
                value=CAMCOPS_SERVER_VERSION,
                comment="(GENERIC) CamCOPS server version that created the "
                "summary information",
            ),
        ]

    def get_all_summary_tables(
        self, req: "CamcopsRequest"
    ) -> List[ExtraSummaryTable]:
        """
        Returns all
        :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`
        objects for this class, including any provided by subclasses, plus
        SNOMED CT codes if enabled.
        """
        tables = self.get_extra_summary_tables(req)
        if req.snomed_supported:
            tables.append(self._get_snomed_extra_summary_table(req))
        return tables

    def _get_snomed_extra_summary_table(
        self, req: "CamcopsRequest"
    ) -> ExtraSummaryTable:
        """
        Returns a
        :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`
        for this task's SNOMED CT codes.
        """
        codes = self.get_snomed_codes(req)
        columns = [
            Column(
                SNOMED_COLNAME_TASKTABLE,
                TableNameColType,
                comment="Task's base table name",
            ),
            Column(
                SNOMED_COLNAME_TASKPK,
                Integer,
                comment="Task's server primary key",
            ),
            Column(
                SNOMED_COLNAME_WHENCREATED_UTC,
                DateTime,
                comment="Task's creation date/time (UTC)",
            ),
            CamcopsColumn(
                SNOMED_COLNAME_EXPRESSION,
                Text,
                exempt_from_anonymisation=True,
                comment="SNOMED CT expression",
            ),
        ]
        rows = []  # type: List[Dict[str, Any]]
        for code in codes:
            d = OrderedDict(
                [
                    (SNOMED_COLNAME_TASKTABLE, self.tablename),
                    (SNOMED_COLNAME_TASKPK, self.pk),
                    (
                        SNOMED_COLNAME_WHENCREATED_UTC,
                        self.get_creation_datetime_utc_tz_unaware(),
                    ),
                    (SNOMED_COLNAME_EXPRESSION, code.as_string()),
                ]
            )
            rows.append(d)
        return ExtraSummaryTable(
            tablename=SNOMED_TABLENAME,
            xmlname=UNUSED_SNOMED_XML_NAME,  # though actual XML doesn't use this route  # noqa
            columns=columns,
            rows=rows,
            task=self,
        )

    # -------------------------------------------------------------------------
    # Testing
    # -------------------------------------------------------------------------

    def dump(self) -> None:
        """
        Dump a description of the task instance to the Python log, for
        debugging.
        """
        line_equals = "=" * 79
        lines = ["", line_equals]
        for f in self.get_fieldnames():
            lines.append(f"{f}: {getattr(self, f)!r}")
        lines.append(line_equals)
        log.info("\n".join(lines))

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def apply_special_note(
        self, req: "CamcopsRequest", note: str, from_console: bool = False
    ) -> None:
        """
        Manually applies a special note to a task.

        Applies it to all predecessor/successor versions as well.
        WRITES TO THE DATABASE.
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
        self.cancel_from_export_log(req, from_console)

    # -------------------------------------------------------------------------
    # Clinician
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_clinician_name(self) -> str:
        """
        May be overridden by :class:`TaskHasClinicianMixin`; q.v.
        """
        return ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_clinician_fhir_telecom_other(self, req: "CamcopsRequest") -> str:
        """
        May be overridden by :class:`TaskHasClinicianMixin`; q.v.
        """
        return ""

    # -------------------------------------------------------------------------
    # Respondent
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def is_respondent_complete(self) -> bool:
        """
        Is the respondent information complete?

        May be overridden by :class:`TaskHasRespondentMixin`.
        """
        return False

    # -------------------------------------------------------------------------
    # About the associated patient
    # -------------------------------------------------------------------------

    @property
    def patient(self) -> Optional["Patient"]:
        """
        Returns the :class:`camcops_server.cc_modules.cc_patient.Patient` for
        this task.

        Overridden by :class:`TaskHasPatientMixin`.
        """
        return None

    def is_female(self) -> bool:
        """
        Is the patient female?
        """
        return self.patient.is_female() if self.patient else False

    def is_male(self) -> bool:
        """
        Is the patient male?
        """
        return self.patient.is_male() if self.patient else False

    def get_patient_server_pk(self) -> Optional[int]:
        """
        Get the server PK of the patient, or None.
        """
        return self.patient.pk if self.patient else None

    def get_patient_forename(self) -> str:
        """
        Get the patient's forename, in upper case, or "".
        """
        return self.patient.get_forename() if self.patient else ""

    def get_patient_surname(self) -> str:
        """
        Get the patient's surname, in upper case, or "".
        """
        return self.patient.get_surname() if self.patient else ""

    def get_patient_dob(self) -> Optional[PendulumDate]:
        """
        Get the patient's DOB, or None.
        """
        return self.patient.get_dob() if self.patient else None

    def get_patient_dob_first11chars(self) -> Optional[str]:
        """
        Gets the patient's date of birth in an 11-character human-readable
        short format. For example: ``29 Dec 1999``.
        """
        if not self.patient:
            return None
        dob_str = self.patient.get_dob_str()
        if not dob_str:
            return None
        return dob_str[:11]

    def get_patient_sex(self) -> str:
        """
        Get the patient's sex, or "".
        """
        return self.patient.get_sex() if self.patient else ""

    def get_patient_address(self) -> str:
        """
        Get the patient's address, or "".
        """
        return self.patient.get_address() if self.patient else ""

    def get_patient_idnum_objects(self) -> List["PatientIdNum"]:
        """
        Gets all
        :class:`camcops_server.cc_modules.cc_patientidnum.PatientIdNum` objects
        for the patient.
        """
        return self.patient.get_idnum_objects() if self.patient else []

    def get_patient_idnum_object(
        self, which_idnum: int
    ) -> Optional["PatientIdNum"]:
        """
        Get the patient's
        :class:`camcops_server.cc_modules.cc_patientidnum.PatientIdNum` for the
        specified ID number type (``which_idnum``), or None.
        """
        return (
            self.patient.get_idnum_object(which_idnum)
            if self.patient
            else None
        )

    def any_patient_idnums_invalid(self, req: "CamcopsRequest") -> bool:
        """
        Do we have a patient who has any invalid ID numbers?

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        idnums = self.get_patient_idnum_objects()
        for idnum in idnums:
            if not idnum.is_fully_valid(req):
                return True
        return False

    def get_patient_idnum_value(self, which_idnum: int) -> Optional[int]:
        """
        Get the patient's ID number value for the specified ID number
        type (``which_idnum``), or None.
        """
        idobj = self.get_patient_idnum_object(which_idnum=which_idnum)
        return idobj.idnum_value if idobj else None

    def get_patient_hl7_pid_segment(
        self, req: "CamcopsRequest", recipient_def: "ExportRecipient"
    ) -> Union[hl7.Segment, str]:
        """
        Get an HL7 PID segment for the patient, or "".
        """
        return (
            self.patient.get_hl7_pid_segment(req, recipient_def)
            if self.patient
            else ""
        )

    # -------------------------------------------------------------------------
    # HL7 v2
    # -------------------------------------------------------------------------

    def get_hl7_data_segments(
        self, req: "CamcopsRequest", recipient_def: "ExportRecipient"
    ) -> List[hl7.Segment]:
        """
        Returns a list of HL7 data segments.

        These will be:

        - observation request (OBR) segment
        - observation result (OBX) segment
        - any extra ones offered by the task
        """
        obr_segment = make_obr_segment(self)
        export_options = recipient_def.get_task_export_options()
        obx_segment = make_obx_segment(
            req,
            self,
            task_format=recipient_def.task_format,
            observation_identifier=self.tablename + "_" + str(self._pk),
            observation_datetime=self.get_creation_datetime(),
            responsible_observer=self.get_clinician_name(),
            export_options=export_options,
        )
        return [obr_segment, obx_segment] + self.get_hl7_extra_data_segments(
            recipient_def
        )

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_hl7_extra_data_segments(
        self, recipient_def: "ExportRecipient"
    ) -> List[hl7.Segment]:
        """
        Return a list of any extra HL7 data segments. (See
        :func:`get_hl7_data_segments`, which calls this function.)

        May be overridden.
        """
        return []

    # -------------------------------------------------------------------------
    # FHIR: framework
    # -------------------------------------------------------------------------

    def get_fhir_bundle(
        self,
        req: "CamcopsRequest",
        recipient: "ExportRecipient",
        skip_docs_if_other_content: bool = DEBUG_SKIP_FHIR_DOCS,
    ) -> Bundle:
        """
        Get a single FHIR Bundle with all entries. See
        :meth:`get_fhir_bundle_entries`.
        """
        # Get the content:
        bundle_entries = self.get_fhir_bundle_entries(
            req,
            recipient,
            skip_docs_if_other_content=skip_docs_if_other_content,
        )
        # ... may raise FhirExportException

        # Sanity checks:
        id_counter = Counter()
        for entry in bundle_entries:
            assert (
                Fc.RESOURCE in entry
            ), f"Bundle entry has no resource: {entry}"  # just wrong
            resource = entry[Fc.RESOURCE]
            assert Fc.IDENTIFIER in resource, (
                f"Bundle entry has no identifier for its resource: "
                f"{resource}"
            )  # might succeed, but would insert an unidentified resource
            identifier = resource[Fc.IDENTIFIER]
            if not isinstance(identifier, list):
                identifier = [identifier]
            for id_ in identifier:
                system = id_[Fc.SYSTEM]
                value = id_[Fc.VALUE]
                id_counter.update([fhir_system_value(system, value)])
            most_common = id_counter.most_common(1)[0]
            assert (
                most_common[1] == 1
            ), f"Resources have duplicate IDs: {most_common[0]}"

        # Bundle up the content into a transaction bundle:
        return Bundle(
            jsondict={Fc.TYPE: Fc.TRANSACTION, Fc.ENTRY: bundle_entries}
        )
        # This is one of the few FHIR objects that we don't return with
        # ".as_json()", because Bundle objects have useful methods for talking
        # to the FHIR server.

    def get_fhir_bundle_entries(
        self,
        req: "CamcopsRequest",
        recipient: "ExportRecipient",
        skip_docs_if_other_content: bool = DEBUG_SKIP_FHIR_DOCS,
    ) -> List[Dict]:
        """
        Get all FHIR bundle entries. This is the "top-level" function to
        provide all FHIR information for the task. That information includes:

        - the Patient, if applicable;
        - the Questionnaire (task) itself;
        - multiple QuestionnaireResponse entries for the specific answers from
          this task instance.

        If the task refuses to support FHIR, raises :exc:`FhirExportException`.

        Args:
            req:
                a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            recipient:
                an
                :class:`camcops_server.cc_modules.cc_exportrecipient.ExportRecipient`
            skip_docs_if_other_content:
                A debugging option: skip the document (e.g. PDF, HTML, XML),
                making the FHIR output smaller and more legible for debugging.
                However, if the task offers no other content, this will raise
                :exc:`FhirExportException`.
        """  # noqa
        bundle_entries = []  # type: List[Dict]

        # Patient (0 or 1)
        if self.has_patient:
            bundle_entries.append(
                self.patient.get_fhir_bundle_entry(req, recipient)
            )

        # Clinician (0 or 1)
        if self.has_clinician:
            bundle_entries.append(self._get_fhir_clinician_bundle_entry(req))

        # Questionnaire, QuestionnaireResponse
        q_bundle_entry, qr_bundle_entry = self._get_fhir_q_qr_bundle_entries(
            req, recipient
        )
        if q_bundle_entry and qr_bundle_entry:
            bundle_entries += [
                # Questionnaire
                q_bundle_entry,
                # Collection of QuestionnaireResponse entries
                qr_bundle_entry,
            ]

        # Observation (0 or more) -- includes Coding
        bundle_entries += self._get_fhir_detail_bundle_entries(req, recipient)

        # DocumentReference (0-1; always 1 in normal use )
        if skip_docs_if_other_content:
            if not bundle_entries:
                # We can't have nothing!
                raise FhirExportException(
                    "Skipping task because DEBUG_SKIP_FHIR_DOCS set and no "
                    "other content"
                )
        else:
            bundle_entries.append(
                self._get_fhir_docref_bundle_entry(req, recipient)
            )

        return bundle_entries

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Generic
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def fhir_when_task_created(self) -> str:
        """
        Time of task creation, in a FHIR-compatible format.
        """
        return self.when_created.isoformat()

    def _get_fhir_detail_bundle_entries(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> List[Dict]:
        """
        Returns a list of bundle entries (0-1 of them) for Observation objects,
        which may each contain several ObservationComponent objects. This
        includes any SNOMED codes offered, and any extras.

        See:

        - https://www.hl7.org/fhir/terminologies-systems.html
        - https://www.hl7.org/fhir/observation.html#code-interop
        - https://www.hl7.org/fhir/observation.html#gr-comp

        In particular, whether information should be grouped into one
        Observation (via ObservationComponent objects) or as separate
        observations depends on whether it is conceptually independent. For
        example, for BMI, height and weight should be separate.
        """
        bundle_entries = []  # type: List[Dict]

        # SNOMED, as one observation with several components:
        if req.snomed_supported:
            snomed_components = []  # type: List[Dict]
            for expr in self.get_snomed_codes(req):
                snomed_components.append(
                    fhir_observation_component_from_snomed(req, expr)
                )
            if snomed_components:
                observable_entity = req.snomed(SnomedLookup.OBSERVABLE_ENTITY)
                snomed_observation = self._get_fhir_observation(
                    req,
                    recipient,
                    obs_dict={
                        # "code" is mandatory even if there are components.
                        Fc.CODE: CodeableConcept(
                            jsondict={
                                Fc.CODING: [
                                    Coding(
                                        jsondict={
                                            Fc.SYSTEM: Fc.CODE_SYSTEM_SNOMED_CT,  # noqa
                                            Fc.CODE: str(
                                                observable_entity.identifier
                                            ),
                                            Fc.DISPLAY: observable_entity.as_string(  # noqa
                                                longform=True
                                            ),
                                            Fc.USER_SELECTED: False,
                                        }
                                    ).as_json()
                                ],
                                Fc.TEXT: observable_entity.term,
                            }
                        ).as_json(),
                        Fc.COMPONENT: snomed_components,
                    },
                )
                bundle_entries.append(
                    make_fhir_bundle_entry(
                        resource_type_url=Fc.RESOURCE_TYPE_OBSERVATION,
                        identifier=self._get_fhir_observation_id(
                            req, name="snomed"
                        ),
                        resource=snomed_observation,
                    )
                )

        # Extra -- these can be very varied:
        bundle_entries += self.get_fhir_extra_bundle_entries(req, recipient)

        # Done
        return bundle_entries

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Identifiers
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Generic:

    def _get_fhir_id_this_task_class(
        self,
        req: "CamcopsRequest",
        route_name: str,
        value_within_task_class: Union[int, str],
    ) -> Identifier:
        """
        For when we want to refer to something within a specific task class, in
        the abstract. The URL refers to the task class, not the task instance.
        """
        return Identifier(
            jsondict={
                Fc.SYSTEM: req.route_url(
                    route_name,
                    table_name=self.tablename,  # to match ViewParam.TABLE_NAME
                ),
                Fc.VALUE: str(value_within_task_class),
            }
        )

    def _get_fhir_id_this_task_instance(
        self,
        req: "CamcopsRequest",
        route_name: str,
        value_within_task_instance: Union[int, str],
    ) -> Identifier:
        """
        A number of FHIR identifiers refer to "this task" and nothing very much
        more specific (because they represent a type of thing of which there
        can only be one per task), but do so through a range of different route
        names that make the FHIR URLs look sensible. This is a convenience
        function for them. The intention is to route to the specific task
        instance concerned.
        """
        return Identifier(
            jsondict={
                Fc.SYSTEM: req.route_url(
                    route_name,
                    table_name=self.tablename,  # to match ViewParam.TABLE_NAME
                    server_pk=str(self._pk),  # to match ViewParam.SERVER_PK
                ),
                Fc.VALUE: str(value_within_task_instance),
            }
        )

    # Specific:

    def _get_fhir_condition_id(
        self, req: "CamcopsRequest", name: Union[int, str]
    ) -> Identifier:
        """
        Returns a FHIR Identifier for an Observation, representing this task
        instance and a named observation within it.
        """
        return self._get_fhir_id_this_task_instance(
            req, Routes.FHIR_CONDITION, name
        )

    def _get_fhir_docref_id(
        self, req: "CamcopsRequest", task_format: str
    ) -> Identifier:
        """
        Returns a FHIR Identifier (e.g. for a DocumentReference collection)
        representing the view of this task.
        """
        return self._get_fhir_id_this_task_instance(
            req, Routes.FHIR_DOCUMENT_REFERENCE, task_format
        )

    def _get_fhir_observation_id(
        self, req: "CamcopsRequest", name: str
    ) -> Identifier:
        """
        Returns a FHIR Identifier for an Observation, representing this task
        instance and a named observation within it.
        """
        return self._get_fhir_id_this_task_instance(
            req, Routes.FHIR_OBSERVATION, name
        )

    def _get_fhir_practitioner_id(self, req: "CamcopsRequest") -> Identifier:
        """
        Returns a FHIR Identifier for the clinician. (Clinicians are not
        sensibly made unique across tasks, but are task-specific.)
        """
        return self._get_fhir_id_this_task_instance(
            req,
            Routes.FHIR_PRACTITIONER,
            Fc.CAMCOPS_VALUE_CLINICIAN_WITHIN_TASK,
        )

    def _get_fhir_questionnaire_id(self, req: "CamcopsRequest") -> Identifier:
        """
        Returns a FHIR Identifier (e.g. for a Questionnaire) representing this
        task, in the abstract.

        Incorporates the CamCOPS version, so that if aspects (even the
        formatting of question text) changes, a new version will be stored
        despite the "ifNoneExist" clause.
        """
        return Identifier(
            jsondict={
                Fc.SYSTEM: req.route_url(Routes.FHIR_QUESTIONNAIRE_SYSTEM),
                Fc.VALUE: f"{self.tablename}/{CAMCOPS_SERVER_VERSION_STRING}",
            }
        )

    def _get_fhir_questionnaire_response_id(
        self, req: "CamcopsRequest"
    ) -> Identifier:
        """
        Returns a FHIR Identifier (e.g. for a QuestionnaireResponse collection)
        representing this task instance. QuestionnaireResponse items are
        specific answers, not abstract descriptions.
        """
        return self._get_fhir_id_this_task_instance(
            req,
            Routes.FHIR_QUESTIONNAIRE_RESPONSE,
            Fc.CAMCOPS_VALUE_QUESTIONNAIRE_RESPONSE_WITHIN_TASK,
        )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # References to identifiers
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_fhir_subject_ref(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> Dict:
        """
        Returns a reference to the patient, for "subject" fields.
        """
        assert (
            self.has_patient
        ), "Don't call Task._get_fhir_subject_ref() for anonymous tasks"
        return self.patient.get_fhir_subject_ref(req, recipient)

    def _get_fhir_practitioner_ref(self, req: "CamcopsRequest") -> Dict:
        """
        Returns a reference to the clinician, for "practitioner" fields.
        """
        assert self.has_clinician, (
            "Don't call Task._get_fhir_clinician_ref() "
            "for tasks without a clinician"
        )
        return FHIRReference(
            jsondict={
                Fc.TYPE: Fc.RESOURCE_TYPE_PRACTITIONER,
                Fc.IDENTIFIER: self._get_fhir_practitioner_id(req).as_json(),
            }
        ).as_json()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # DocumentReference
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_fhir_docref_bundle_entry(
        self,
        req: "CamcopsRequest",
        recipient: "ExportRecipient",
        text_encoding: str = UTF8,
    ) -> Dict:
        """
        Returns bundle entries for an attached document, which is a full
        representation of the task according to the selected task format (e.g.
        PDF).

        This requires a DocumentReference, which can (in theory) either embed
        the data, or refer via a URL to an associated Binary object. We do it
        directly.

        See:

        - https://fhirblog.com/2013/11/06/fhir-and-xds-submitting-a-document-from-a-document-source/
        - https://fhirblog.com/2013/11/12/the-fhir-documentreference-resource/
        - https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-documentreference.html
        - https://build.fhir.org/ig/HL7/US-Core/clinical-notes-guidance.html
        """  # noqa

        # Establish content_type and binary_data
        task_format = recipient.task_format
        if task_format == FileType.PDF:
            binary_data = self.get_pdf(req)
            content_type = MimeType.PDF
        else:
            if task_format == FileType.XML:
                txt = self.get_xml(
                    req,
                    options=TaskExportOptions(
                        include_blobs=False,
                        xml_include_ancillary=True,
                        xml_include_calculated=True,
                        xml_include_comments=True,
                        xml_include_patient=True,
                        xml_include_plain_columns=True,
                        xml_include_snomed=True,
                        xml_with_header_comments=True,
                    ),
                )
                content_type = MimeType.XML
            elif task_format == FileType.HTML:
                txt = self.get_html(req)
                content_type = MimeType.HTML
            else:
                raise ValueError(f"Unknown task format: {task_format!r}")
            binary_data = txt.encode(text_encoding)
        b64_encoded_bytes = b64encode(binary_data)  # type: bytes
        b64_encoded_str = b64_encoded_bytes.decode(ASCII)

        # Build the DocumentReference
        docref_id = self._get_fhir_docref_id(req, task_format)
        dr_dict = {
            # Metadata:
            Fc.DATE: self.fhir_when_task_created,
            Fc.DESCRIPTION: self.longname(req),
            Fc.DOCSTATUS: (
                Fc.DOCSTATUS_FINAL
                if self.is_finalized()
                else Fc.DOCSTATUS_PRELIMINARY
            ),
            Fc.MASTER_IDENTIFIER: docref_id.as_json(),
            Fc.STATUS: Fc.DOCSTATUS_CURRENT,
            # And the content:
            Fc.CONTENT: [
                DocumentReferenceContent(
                    jsondict={
                        Fc.ATTACHMENT: Attachment(
                            jsondict={
                                Fc.CONTENT_TYPE: content_type,
                                Fc.DATA: b64_encoded_str,
                            }
                        ).as_json()
                    }
                ).as_json()
            ],
        }
        # Optional metadata:
        if self.has_clinician:
            dr_dict[Fc.AUTHOR] = [self._get_fhir_practitioner_ref(req)]
        if self.has_patient:
            dr_dict[Fc.SUBJECT] = self._get_fhir_subject_ref(req, recipient)

        # DocumentReference
        return make_fhir_bundle_entry(
            resource_type_url=Fc.RESOURCE_TYPE_DOCUMENT_REFERENCE,
            identifier=docref_id,
            resource=DocumentReference(jsondict=dr_dict).as_json(),
        )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Observation
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_fhir_observation(
        self,
        req: "CamcopsRequest",
        recipient: "ExportRecipient",
        obs_dict: Dict,
    ) -> Dict:
        """
        Given a starting dictionary for an Observation, complete it for this
        task (by adding "when", "who", and status information) and return the
        Observation (as a dict in JSON format).
        """
        obs_dict.update(
            {
                Fc.EFFECTIVE_DATE_TIME: self.fhir_when_task_created,
                Fc.STATUS: (
                    Fc.OBSSTATUS_FINAL
                    if self.is_finalized()
                    else Fc.OBSSTATUS_PRELIMINARY
                ),
            }
        )
        if self.has_patient:
            obs_dict[Fc.SUBJECT] = self._get_fhir_subject_ref(req, recipient)
        return Observation(jsondict=obs_dict).as_json()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Practitioner (clinician)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_fhir_clinician_bundle_entry(self, req: "CamcopsRequest") -> Dict:
        """
        Supplies information on the clinician associated with this task, as a
        FHIR Practitioner object (within a bundle).
        """
        assert self.has_clinician, (
            "Don't call Task._get_fhir_practitioner_bundle_entry() "
            "for tasks without a clinician"
        )
        practitioner = Practitioner(
            jsondict={
                Fc.NAME: [
                    HumanName(
                        jsondict={Fc.TEXT: self.get_clinician_name()}
                    ).as_json()
                ],
                # "qualification" is too structured.
                # There isn't anywhere to represent our other information, so
                # we jam it in to "telecom"/"other".
                Fc.TELECOM: [
                    ContactPoint(
                        jsondict={
                            Fc.SYSTEM: Fc.TELECOM_SYSTEM_OTHER,
                            Fc.VALUE: self.get_clinician_fhir_telecom_other(
                                req
                            ),
                        }
                    ).as_json()
                ],
            }
        ).as_json()
        return make_fhir_bundle_entry(
            resource_type_url=Fc.RESOURCE_TYPE_PRACTITIONER,
            identifier=self._get_fhir_practitioner_id(req),
            resource=practitioner,
        )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Questionnaire, QuestionnaireResponse
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_fhir_q_qr_bundle_entries(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Get a tuple of FHIR bundles: ``questionnaire_bundle_entry,
        questionnaire_response_bundle_entry``.

        A Questionnaire object represents the task in the abstract;
        QuestionnaireReponse items represent each answered question for a
        specific task instance.
        """
        # Ask the task for its details (which it may provide directly, by
        # overriding, or rely on autodiscovery for the default).
        aq_items = self.get_fhir_questionnaire(req)
        if DEBUG_SHOW_FHIR_QUESTIONNAIRE:
            if aq_items:
                qa_str = "\n".join(f"- {str(x)}" for x in aq_items)
                log.debug(f"FHIR questions/answers:\n{qa_str}")
            else:
                log.debug("No FHIR questionnaire data")

        # Do we have data?
        if not aq_items:
            return None, None

        # Now finish off:
        q_items = [aq.questionnaire_item() for aq in aq_items]
        qr_items = [aq.questionnaire_response_item() for aq in aq_items]
        q_bundle_entry = self._make_fhir_questionnaire_bundle_entry(
            req, q_items
        )
        qr_bundle_entry = self._make_fhir_questionnaire_response_bundle_entry(
            req, recipient, qr_items
        )
        return q_bundle_entry, qr_bundle_entry

    def _make_fhir_questionnaire_bundle_entry(
        self, req: "CamcopsRequest", q_items: List[Dict]
    ) -> Optional[Dict]:
        """
        Make a FHIR bundle entry describing this task, as a FHIR Questionnaire,
        from supplied Questionnaire items. Note: here we mean "abstract task",
        not "task instance".
        """
        # FHIR supports versioning of questionnaires. Might be useful if the
        # wording of questions change. Could either use FHIR's version
        # field or include the version in the identifier below. Either way
        # we'd need the version in the 'ifNoneExist' part of the request.
        q_identifier = self._get_fhir_questionnaire_id(req)

        # Other things we could add:
        # https://www.hl7.org/fhir/questionnaire.html
        #
        # date: Date last changed
        # useContext: https://www.hl7.org/fhir/metadatatypes.html#UsageContext
        help_url = self.help_url()
        questionnaire = Questionnaire(
            jsondict={
                Fc.NAME: self.shortname,  # Computer-friendly name
                Fc.TITLE: self.longname(req),  # Human name
                Fc.DESCRIPTION: help_url,  # Natural language description of the questionnaire  # noqa
                Fc.COPYRIGHT: help_url,  # Use and/or publishing restrictions
                Fc.VERSION: CAMCOPS_SERVER_VERSION_STRING,
                Fc.STATUS: Fc.QSTATUS_ACTIVE,  # Could also be: draft, retired, unknown  # noqa
                Fc.ITEM: q_items,
            }
        )
        return make_fhir_bundle_entry(
            resource_type_url=Fc.RESOURCE_TYPE_QUESTIONNAIRE,
            identifier=q_identifier,
            resource=questionnaire.as_json(),
        )

    def _make_fhir_questionnaire_response_bundle_entry(
        self,
        req: "CamcopsRequest",
        recipient: "ExportRecipient",
        qr_items: List[Dict],
    ) -> Dict:
        """
        Make a bundle entry from FHIR QuestionnaireResponse items (e.g. one for
        the response to each question in a quesionnaire-style task).
        """
        q_identifier = self._get_fhir_questionnaire_id(req)
        qr_identifier = self._get_fhir_questionnaire_response_id(req)

        # Status:
        # https://www.hl7.org/fhir/valueset-questionnaire-answers-status.html
        # It is probably undesirable to export tasks that are incomplete in the
        # sense of "not finalized". The user can control this (via the
        # FINALIZED_ONLY config option for exports). However, we also need to
        # handle finalized but incomplete data.
        if self.is_complete():
            status = Fc.QSTATUS_COMPLETED
        elif self.is_live_on_tablet():
            status = Fc.QSTATUS_IN_PROGRESS
        else:
            # Incomplete, but finalized.
            status = Fc.QSTATUS_STOPPED

        qr_jsondict = {
            # https://r4.smarthealthit.org does not like "questionnaire" in
            # this form:
            # FHIR Server; FHIR 4.0.0/R4; HAPI FHIR 4.0.0-SNAPSHOT)
            # error is:
            # Invalid resource reference found at
            # path[QuestionnaireResponse.questionnaire]- Resource type is
            # unknown or not supported on this server
            # - http://127.0.0.1:8000/fhir_questionnaire|phq9
            # http://hapi.fhir.org/baseR4/ (4.0.1 (R4)) is OK
            Fc.QUESTIONNAIRE: fhir_sysval_from_id(q_identifier),
            Fc.AUTHORED: self.fhir_when_task_created,
            Fc.STATUS: status,
            # TODO: Could also add:
            # https://www.hl7.org/fhir/questionnaireresponse.html
            # author: Person who received and recorded the answers
            # source: The person who answered the questions
            Fc.ITEM: qr_items,
        }

        if self.has_patient:
            qr_jsondict[Fc.SUBJECT] = self._get_fhir_subject_ref(
                req, recipient
            )

        return make_fhir_bundle_entry(
            resource_type_url=Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE,
            identifier=qr_identifier,
            resource=QuestionnaireResponse(qr_jsondict).as_json(),
            identifier_is_list=False,
        )

    # -------------------------------------------------------------------------
    # FHIR: functions to override if desired
    # -------------------------------------------------------------------------

    def get_fhir_questionnaire(
        self, req: "CamcopsRequest"
    ) -> List[FHIRAnsweredQuestion]:
        """
        Return FHIR information about a questionnaire: both about the task in
        the abstract (the questions) and the answers for this specific
        instance.

        May be overridden.
        """
        return self._fhir_autodiscover(req)

    def get_fhir_extra_bundle_entries(
        self, req: "CamcopsRequest", recipient: "ExportRecipient"
    ) -> List[Dict]:
        """
        Return a list of extra FHIR bundle entries, if relevant. (SNOMED-CT
        codes are done automatically; don't repeat those.)
        """
        return []

    def get_qtext(self, req: "CamcopsRequest", attrname: str) -> Optional[str]:
        """
        Returns the text associated with a particular question.
        The default implementation is a guess.

        Args:
            req:
                A :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`.
            attrname:
                Name of the attribute (field) on this task that represents the
                question.
        """
        return self.xstring(req, attrname, provide_default_if_none=False)

    def get_atext(
        self, req: "CamcopsRequest", attrname: str, answer_value: int
    ) -> Optional[str]:
        """
        Returns the text associated with a particular answer to a question.
        The default implementation is a guess.

        Args:
            req:
                A :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`.
            attrname:
                Name of the attribute (field) on this task that represents the
                question.
            answer_value:
                Answer value.
        """
        stringname = f"{attrname}_a{answer_value}"
        return self.xstring(req, stringname, provide_default_if_none=False)

    # -------------------------------------------------------------------------
    # FHIR automatic interrogation
    # -------------------------------------------------------------------------

    def _fhir_autodiscover(
        self, req: "CamcopsRequest"
    ) -> List[FHIRAnsweredQuestion]:
        """
        Inspect this task instance and create information about both the task
        in the abstract and the answers for this specific instance.
        """
        qa_items = []  # type: List[FHIRAnsweredQuestion]

        skip_fields = TASK_FREQUENT_FIELDS
        for attrname, column in gen_columns(self):
            if attrname in skip_fields:
                continue
            comment = column.comment
            coltype = column.type

            # Question text:
            retrieved_qtext = self.get_qtext(req, attrname)
            qtext_components = []
            if retrieved_qtext:
                qtext_components.append(retrieved_qtext)
            if comment:
                qtext_components.append(f"[{comment}]")
            if not qtext_components:
                qtext_components = (attrname,)
            if not qtext_components:
                qtext_components = (FHIR_UNKNOWN_TEXT,)
            qtext = " ".join(qtext_components)
            # Note that it's good to get the column comment in somewhere; these
            # often explain the meaning of the field quite well. It may or may
            # not be possible to get it into the option values -- many answer
            # types don't permit those. QuestionnaireItem records don't have a
            # comment field (see
            # https://www.hl7.org/fhir/questionnaire-definitions.html#Questionnaire.item),  # noqa
            # so the best we can do is probably to stuff it into the question
            # text, even if that causes some visual duplication.

            # Thinking about types:
            int_type = isinstance(coltype, Integer)
            bool_type = (
                is_sqlatype_binary(coltype)
                or isinstance(coltype, BoolColumn)
                or isinstance(coltype, Boolean)
                # For booleans represented as integers: it is better to be as
                # constraining as possible and say that only 0/1 options are
                # present by marking these as Boolean, which is less
                # complicated for the recipient than "integer but with possible
                # options 0 or 1". We will *also* show the possible options,
                # just to be clear.
            )
            if int_type:
                qtype = FHIRQuestionType.INTEGER
                atype = FHIRAnswerType.INTEGER
            elif isinstance(coltype, String):  # includes its subclass, Text
                qtype = FHIRQuestionType.STRING
                atype = FHIRAnswerType.STRING
            elif isinstance(coltype, Numeric):  # includes Float, Decimal
                qtype = FHIRQuestionType.QUANTITY
                atype = FHIRAnswerType.QUANTITY
            elif isinstance(
                coltype, (DateTime, PendulumDateTimeAsIsoTextColType)
            ):
                qtype = FHIRQuestionType.DATETIME
                atype = FHIRAnswerType.DATETIME
            elif isinstance(coltype, DateColType):
                qtype = FHIRQuestionType.DATE
                atype = FHIRAnswerType.DATE
            elif isinstance(coltype, Time):
                qtype = FHIRQuestionType.TIME
                atype = FHIRAnswerType.TIME
            elif bool_type:
                qtype = FHIRQuestionType.BOOLEAN
                atype = FHIRAnswerType.BOOLEAN
            else:
                raise NotImplementedError(f"Unknown column type: {coltype!r}")

            # Thinking about MCQ options:
            answer_options = None  # type: Optional[Dict[Any, str]]
            if (int_type or bool_type) and hasattr(
                column, COLATTR_PERMITTED_VALUE_CHECKER
            ):
                pvc = getattr(
                    column, COLATTR_PERMITTED_VALUE_CHECKER
                )  # type: PermittedValueChecker  # noqa
                if pvc is not None:
                    pv = pvc.permitted_values_inc_minmax()
                    if pv:
                        qtype = FHIRQuestionType.CHOICE
                        # ... has to be of type "choice" to transmit the
                        # possible values.
                        answer_options = {}
                        for v in pv:
                            answer_options[v] = (
                                self.get_atext(req, attrname, v)
                                or comment
                                or FHIR_UNKNOWN_TEXT
                            )

            # Assemble:
            qa_items.append(
                FHIRAnsweredQuestion(
                    qname=attrname,
                    qtext=qtext,
                    qtype=qtype,
                    answer_type=atype,
                    answer=getattr(self, attrname),
                    answer_options=answer_options,
                )
            )

        # We don't currently put any summary information into FHIR exports. I
        # think that isn't within the spirit of the system, but am not sure.
        # todo: Check if summary information should go into FHIR exports.

        return qa_items

    # -------------------------------------------------------------------------
    # Export (generically)
    # -------------------------------------------------------------------------

    def cancel_from_export_log(
        self, req: "CamcopsRequest", from_console: bool = False
    ) -> None:
        """
        Marks all instances of this task as "cancelled" in the export log, so
        it will be resent.
        """
        if self._pk is None:
            return
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTask,
        )  # delayed import

        # noinspection PyUnresolvedReferences
        statement = (
            update(ExportedTask.__table__)
            .where(ExportedTask.basetable == self.tablename)
            .where(ExportedTask.task_server_pk == self._pk)
            .where(
                not_(ExportedTask.cancelled) | ExportedTask.cancelled.is_(None)
            )
            .values(cancelled=1, cancelled_at_utc=req.now_utc)
        )
        # ... this bit: ... AND (NOT cancelled OR cancelled IS NULL) ...:
        # https://stackoverflow.com/questions/37445041/sqlalchemy-how-to-filter-column-which-contains-both-null-and-integer-values  # noqa
        req.dbsession.execute(statement)
        self.audit(
            req,
            "Task cancelled in export log (may trigger resending)",
            from_console,
        )

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(
        self, req: "CamcopsRequest", details: str, from_console: bool = False
    ) -> None:
        """
        Audits actions to this task.
        """
        audit(
            req,
            details,
            patient_server_pk=self.get_patient_server_pk(),
            table=self.tablename,
            server_pk=self._pk,
            from_console=from_console,
        )

    # -------------------------------------------------------------------------
    # Erasure (wiping, leaving record as placeholder)
    # -------------------------------------------------------------------------

    def manually_erase(self, req: "CamcopsRequest") -> None:
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
        self.cancel_from_export_log(req)

    def is_erased(self) -> bool:
        """
        Has the task been manually erased? See :func:`manually_erase`.
        """
        return self._manually_erased

    # -------------------------------------------------------------------------
    # Complete deletion
    # -------------------------------------------------------------------------

    def delete_entirely(self, req: "CamcopsRequest") -> None:
        """
        Completely delete this task, its lineage, and its dependants.
        """
        for task in self.get_lineage():
            task.delete_with_dependants(req)
        self.audit(req, "Task deleted")

    # -------------------------------------------------------------------------
    # Filtering tasks for the task list
    # -------------------------------------------------------------------------

    @classmethod
    def gen_text_filter_columns(
        cls,
    ) -> Generator[Tuple[str, Column], None, None]:
        """
        Yields tuples of ``attrname, column``, for columns that are suitable
        for text filtering.
        """
        for attrname, column in gen_columns(cls):
            if attrname.startswith("_"):  # system field
                continue
            if not is_sqlatype_string(column.type):
                continue
            yield attrname, column

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def get_text_filter_columns(cls) -> List[Column]:
        """
        Cached function to return a list of SQLAlchemy Column objects suitable
        for text filtering.
        """
        return [col for _, col in cls.gen_text_filter_columns()]

    def contains_text(self, text: str) -> bool:
        """
        Does this task contain the specified text?

        Args:
            text:
                string that must be present in at least one of our text
                columns

        Returns:
            is the strings present?
        """
        text = text.lower()
        for attrname, _ in self.gen_text_filter_columns():
            value = getattr(self, attrname)
            if value is None:
                continue
            assert isinstance(value, str), "Internal bug in contains_text"
            if text in value.lower():
                return True
        return False

    def contains_all_strings(self, strings: List[str]) -> bool:
        """
        Does this task contain all the specified strings?

        Args:
            strings:
                list of strings; each string must be present in at least
                one of our text columns

        Returns:
            are all strings present?
        """
        return all(self.contains_text(text) for text in strings)

    # -------------------------------------------------------------------------
    # Spreadsheet export for basic research dump
    # -------------------------------------------------------------------------

    def get_spreadsheet_pages(
        self, req: "CamcopsRequest"
    ) -> List["SpreadsheetPage"]:
        """
        Returns information used for the basic research dump in (e.g.) TSV
        format.
        """
        # 1. Our core fields, plus summary information
        main_page = self._get_core_spreadsheet_page(req)

        # 2. Patient details.
        if self.patient:
            main_page.add_or_set_columns_from_page(
                self.patient.get_spreadsheet_page(req)
            )
        pages = [main_page]

        # 3. +/- Ancillary objects
        for (
            ancillary
        ) in (
            self.gen_ancillary_instances()
        ):  # type: GenericTabletRecordMixin  # noqa
            page = ancillary._get_core_spreadsheet_page(req)
            pages.append(page)

        # 4. +/- Extra summary tables (inc. SNOMED)
        for est in self.get_all_summary_tables(req):
            pages.append(est.get_spreadsheet_page())

        # Done
        return pages

    def get_spreadsheet_schema_elements(
        self, req: "CamcopsRequest"
    ) -> Set[SummarySchemaInfo]:
        """
        Returns schema information used for spreadsheets -- more than just
        the database columns, and in the same format as the spreadsheets.
        """
        table_name = self.__tablename__

        # 1(a). Database columns: main table
        items = self._get_core_spreadsheet_schema()
        # 1(b). Summary information.
        for summary in self.get_summaries(req):
            items.add(
                SummarySchemaInfo.from_summary_element(table_name, summary)
            )

        # 2. Patient details
        if self.patient:
            items.update(
                self.patient.get_spreadsheet_schema_elements(req, table_name)
            )

        # 3. Ancillary objects
        for (
            ancillary
        ) in (
            self.gen_ancillary_instances()
        ):  # type: GenericTabletRecordMixin  # noqa
            items.update(ancillary._get_core_spreadsheet_schema())

        # 4. Extra summary tables
        for est in self.get_all_summary_tables(req):
            items.update(est.get_spreadsheet_schema_elements())

        return items

    # -------------------------------------------------------------------------
    # XML view
    # -------------------------------------------------------------------------

    def get_xml(
        self,
        req: "CamcopsRequest",
        options: TaskExportOptions = None,
        indent_spaces: int = 4,
        eol: str = "\n",
    ) -> str:
        """
        Returns XML describing the task.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            options: a :class:`camcops_server.cc_modules.cc_simpleobjects.TaskExportOptions`

            indent_spaces: number of spaces to indent formatted XML
            eol: end-of-line string

        Returns:
            an XML UTF-8 document representing the task.

        """  # noqa
        options = options or TaskExportOptions()
        tree = self.get_xml_root(req=req, options=options)
        return get_xml_document(
            tree,
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=options.xml_include_comments,
        )

    def get_xml_root(
        self, req: "CamcopsRequest", options: TaskExportOptions
    ) -> XmlElement:
        """
        Returns an XML tree. The return value is the root
        :class:`camcops_server.cc_modules.cc_xml.XmlElement`.

        Override to include other tables, or to deal with BLOBs, if the default
        methods are insufficient.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            options: a :class:`camcops_server.cc_modules.cc_simpleobjects.TaskExportOptions`
        """  # noqa
        # Core (inc. core BLOBs)
        branches = self._get_xml_core_branches(req=req, options=options)
        tree = XmlElement(name=self.tablename, value=branches)
        return tree

    def _get_xml_core_branches(
        self, req: "CamcopsRequest", options: TaskExportOptions = None
    ) -> List[XmlElement]:
        """
        Returns a list of :class:`camcops_server.cc_modules.cc_xml.XmlElement`
        elements representing stored, calculated, patient, and/or BLOB fields,
        depending on the options.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            options: a :class:`camcops_server.cc_modules.cc_simpleobjects.TaskExportOptions`
        """  # noqa
        options = options or TaskExportOptions(
            xml_include_plain_columns=True,
            xml_include_ancillary=True,
            include_blobs=False,
            xml_include_calculated=True,
            xml_include_patient=True,
            xml_include_snomed=True,
        )

        def add_comment(comment: XmlLiteral) -> None:
            if options.xml_with_header_comments:
                branches.append(comment)

        # Stored values +/- calculated values
        core_options = options.clone()
        core_options.include_blobs = False
        branches = self._get_xml_branches(req=req, options=core_options)

        # SNOMED-CT codes
        if options.xml_include_snomed and req.snomed_supported:
            add_comment(XML_COMMENT_SNOMED_CT)
            snomed_codes = self.get_snomed_codes(req)
            snomed_branches = []  # type: List[XmlElement]
            for code in snomed_codes:
                snomed_branches.append(code.xml_element())
            branches.append(
                XmlElement(name=XML_NAME_SNOMED_CODES, value=snomed_branches)
            )

        # Special notes
        add_comment(XML_COMMENT_SPECIAL_NOTES)
        for sn in self.special_notes:
            branches.append(sn.get_xml_root())

        # Patient details
        if self.is_anonymous:
            add_comment(XML_COMMENT_ANONYMOUS)
        elif options.xml_include_patient:
            add_comment(XML_COMMENT_PATIENT)
            patient_options = TaskExportOptions(
                xml_include_plain_columns=True,
                xml_with_header_comments=options.xml_with_header_comments,
            )
            if self.patient:
                branches.append(
                    self.patient.get_xml_root(req, patient_options)
                )

        # BLOBs
        if options.include_blobs:
            add_comment(XML_COMMENT_BLOBS)
            blob_options = TaskExportOptions(
                include_blobs=True,
                xml_skip_fields=options.xml_skip_fields,
                xml_sort_by_name=True,
                xml_with_header_comments=False,
            )
            branches += self._get_xml_branches(req=req, options=blob_options)

        # Ancillary objects
        if options.xml_include_ancillary:
            ancillary_options = TaskExportOptions(
                xml_include_plain_columns=True,
                xml_include_ancillary=True,
                include_blobs=options.include_blobs,
                xml_include_calculated=options.xml_include_calculated,
                xml_sort_by_name=True,
                xml_with_header_comments=options.xml_with_header_comments,
            )
            item_collections = []  # type: List[XmlElement]
            found_ancillary = False
            # We use a slightly more manual iteration process here so that
            # we iterate through individual ancillaries but clustered by their
            # name (e.g. if we have 50 trials and 5 groups, we do them in
            # collections).
            for attrname, rel_prop, rel_cls in gen_ancillary_relationships(
                self
            ):
                if not found_ancillary:
                    add_comment(XML_COMMENT_ANCILLARY)
                    found_ancillary = True
                itembranches = []  # type: List[XmlElement]
                if rel_prop.uselist:
                    ancillaries = getattr(
                        self, attrname
                    )  # type: List[GenericTabletRecordMixin]  # noqa
                else:
                    ancillaries = [
                        getattr(self, attrname)
                    ]  # type: List[GenericTabletRecordMixin]  # noqa
                for ancillary in ancillaries:
                    itembranches.append(
                        ancillary._get_xml_root(
                            req=req, options=ancillary_options
                        )
                    )
                itemcollection = XmlElement(name=attrname, value=itembranches)
                item_collections.append(itemcollection)
            item_collections.sort(key=lambda el: el.name)
            branches += item_collections

        # Completely separate additional summary tables
        if options.xml_include_calculated:
            item_collections = []  # type: List[XmlElement]
            found_est = False
            for est in self.get_extra_summary_tables(req):
                # ... not get_all_summary_tables(); we handled SNOMED
                # differently, above
                if not found_est and est.rows:
                    add_comment(XML_COMMENT_CALCULATED)
                    found_est = True
                item_collections.append(est.get_xml_element())
            item_collections.sort(key=lambda el: el.name)
            branches += item_collections

        return branches

    # -------------------------------------------------------------------------
    # HTML view
    # -------------------------------------------------------------------------

    def get_html(self, req: "CamcopsRequest", anonymise: bool = False) -> str:
        """
        Returns HTML representing the task, for our HTML view.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            anonymise: hide patient identifying details?
        """
        req.prepare_for_html_figures()
        return render(
            "task.mako",
            dict(
                task=self,
                anonymise=anonymise,
                signature=False,
                viewtype=ViewArg.HTML,
            ),
            request=req,
        )

    def title_for_html(
        self, req: "CamcopsRequest", anonymise: bool = False
    ) -> str:
        """
        Returns the plain text used for the HTML ``<title>`` block (by
        ``task.mako``), and also for the PDF title for PDF exports.

        Should be plain text only.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            anonymise: hide patient identifying details?
        """
        if anonymise:
            patient = "?"
        elif self.patient:
            patient = self.patient.prettystr(req)
        else:
            _ = req.gettext
            patient = _("Anonymous")
        tasktype = self.tablename
        when = format_datetime(
            self.get_creation_datetime(),
            DateFormat.ISO8601_HUMANIZED_TO_MINUTES,
            "",
        )
        return f"CamCOPS: {patient}; {tasktype}; {when}"

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf(self, req: "CamcopsRequest", anonymise: bool = False) -> bytes:
        """
        Returns a PDF representing the task.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            anonymise: hide patient identifying details?
        """
        html = self.get_pdf_html(req, anonymise=anonymise)  # main content
        if CSS_PAGED_MEDIA:
            return pdf_from_html(req, html=html)
        else:
            return pdf_from_html(
                req,
                html=html,
                header_html=render(
                    "wkhtmltopdf_header.mako",
                    dict(
                        inner_text=render(
                            "task_page_header.mako",
                            dict(task=self, anonymise=anonymise),
                            request=req,
                        )
                    ),
                    request=req,
                ),
                footer_html=render(
                    "wkhtmltopdf_footer.mako",
                    dict(
                        inner_text=render(
                            "task_page_footer.mako",
                            dict(task=self),
                            request=req,
                        )
                    ),
                    request=req,
                ),
                extra_wkhtmltopdf_options={
                    "orientation": (
                        "Landscape"
                        if self.use_landscape_for_pdf
                        else "Portrait"
                    )
                },
            )

    def get_pdf_html(
        self, req: "CamcopsRequest", anonymise: bool = False
    ) -> str:
        """
        Gets the HTML used to make the PDF (slightly different from the HTML
        used for the HTML view).
        """
        req.prepare_for_pdf_figures()
        return render(
            "task.mako",
            dict(
                task=self,
                anonymise=anonymise,
                pdf_landscape=self.use_landscape_for_pdf,
                signature=self.has_clinician,
                viewtype=ViewArg.PDF,
            ),
            request=req,
        )

    def suggested_pdf_filename(
        self, req: "CamcopsRequest", anonymise: bool = False
    ) -> str:
        """
        Suggested filename for the PDF copy (for downloads).

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            anonymise: hide patient identifying details?
        """
        cfg = req.config
        if anonymise:
            is_anonymous = True
        else:
            is_anonymous = self.is_anonymous
        patient = self.patient
        return get_export_filename(
            req=req,
            patient_spec_if_anonymous=cfg.patient_spec_if_anonymous,
            patient_spec=cfg.patient_spec,
            filename_spec=cfg.task_filename_spec,
            filetype=ViewArg.PDF,
            is_anonymous=is_anonymous,
            surname=patient.get_surname() if patient else "",
            forename=patient.get_forename() if patient else "",
            dob=patient.get_dob() if patient else None,
            sex=patient.get_sex() if patient else None,
            idnum_objects=patient.get_idnum_objects() if patient else None,
            creation_datetime=self.get_creation_datetime(),
            basetable=self.tablename,
            serverpk=self._pk,
        )

    def write_pdf_to_disk(self, req: "CamcopsRequest", filename: str) -> None:
        """
        Writes the PDF to disk, using ``filename``.
        """
        pdffile = open(filename, "wb")
        pdffile.write(self.get_pdf(req))

    # -------------------------------------------------------------------------
    # Metadata for e.g. RiO
    # -------------------------------------------------------------------------

    def get_rio_metadata(
        self,
        req: "CamcopsRequest",
        which_idnum: int,
        uploading_user_id: str,
        document_type: str,
    ) -> str:
        """
        Returns metadata for the task that Servelec's RiO electronic patient
        record may want.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            which_idnum: which CamCOPS ID number type corresponds to the RiO
                client ID?
            uploading_user_id: RiO user ID (string) of the user who will
                be recorded as uploading this information; see below
            document_type: a string indicating the RiO-defined document type
                (this is system-specific); see below

        Returns:
            a newline-terminated single line of CSV values; see below

        Called by
        :meth:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskFileGroup.export_task`.

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

          - ... here and
            :meth:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskFileGroup.export_task`

        - line terminator is <CR>

          - BUT see
            :meth:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskFileGroup.export_task`

        - user name limit is 10 characters, despite incorrect example

          - search for ``RIO_MAX_USER_LEN``

        - DocumentType is a code that maps to a human-readable document
          type; for example, "APT" might map to "Appointment Letter". These
          mappings are specific to the local system. (We will probably want
          one that maps to "Clinical Correspondence" in the absence of
          anything more specific.)

        - RiO will delete the files after it's processed them.

        - Filenames should avoid spaces, but otherwise any other standard
          ASCII code is fine within filenames.

          - see
            :meth:`camcops_server.cc_modules.cc_exportmodels.ExportedTaskFileGroup.export_task`

        """  # noqa

        try:
            client_id = self.patient.get_idnum_value(which_idnum)
        except AttributeError:
            client_id = ""
        title = "CamCOPS_" + self.shortname
        description = self.longname(req)
        author = self.get_clinician_name()  # may be blank
        document_date = format_datetime(
            self.when_created, DateFormat.RIO_EXPORT_UK
        )
        # This STRIPS the timezone information; i.e. it is in the local
        # timezone but doesn't tell you which timezone that is. (That's fine;
        # it should be local or users would be confused.)
        final_revision = 0 if self.is_live_on_tablet() else 1

        item_list = [
            client_id,
            uploading_user_id,
            document_type,
            title,
            description,
            author,
            document_date,
            final_revision,
        ]
        # UTF-8 is NOT supported by RiO for metadata. So:
        csv_line = ",".join(
            [f'"{mangle_unicode_to_ascii(x)}"' for x in item_list]
        )
        return csv_line + "\n"

    # -------------------------------------------------------------------------
    # HTML elements used by tasks
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_standard_clinician_comments_block(
        self, req: "CamcopsRequest", comments: str
    ) -> str:
        """
        HTML DIV for clinician's comments.
        """
        return render(
            "clinician_comments.mako", dict(comment=comments), request=req
        )

    def get_is_complete_td_pair(self, req: "CamcopsRequest") -> str:
        """
        HTML to indicate whether task is complete or not, and to make it
        very obvious visually when it isn't.
        """
        c = self.is_complete()
        td_class = "" if c else f' class="{CssClass.INCOMPLETE}"'
        return (
            f"<td>Completed?</td>"
            f"<td{td_class}><b>{get_yes_no(req, c)}</b></td>"
        )

    def get_is_complete_tr(self, req: "CamcopsRequest") -> str:
        """
        HTML table row to indicate whether task is complete or not, and to
        make it very obvious visually when it isn't.
        """
        return f"<tr>{self.get_is_complete_td_pair(req)}</tr>"

    def get_twocol_val_row(
        self, fieldname: str, default: str = None, label: str = None
    ) -> str:
        """
        HTML table row, two columns, without web-safing of value.

        Args:
            fieldname: field (attribute) name; the value will be retrieved
                from this attribute
            default: default to show if the value is ``None``
            label: descriptive label

        Returns:
            two-column HTML table row (label, value)

        """
        val = getattr(self, fieldname)
        if val is None:
            val = default
        if label is None:
            label = fieldname
        return tr_qa(label, val)

    def get_twocol_string_row(self, fieldname: str, label: str = None) -> str:
        """
        HTML table row, two columns, with web-safing of value.

        Args:
            fieldname: field (attribute) name; the value will be retrieved
                from this attribute
            label: descriptive label

        Returns:
            two-column HTML table row (label, value)
        """
        if label is None:
            label = fieldname
        return tr_qa(label, getattr(self, fieldname))

    def get_twocol_bool_row(
        self, req: "CamcopsRequest", fieldname: str, label: str = None
    ) -> str:
        """
        HTML table row, two columns, with Boolean Y/N formatter for value.

        Args:
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            fieldname: field (attribute) name; the value will be retrieved
                from this attribute
            label: descriptive label

        Returns:
            two-column HTML table row (label, value)
        """
        if label is None:
            label = fieldname
        return tr_qa(label, get_yes_no_none(req, getattr(self, fieldname)))

    def get_twocol_bool_row_true_false(
        self, req: "CamcopsRequest", fieldname: str, label: str = None
    ) -> str:
        """
        HTML table row, two columns, with Boolean true/false formatter for
        value.

        Args:
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            fieldname: field (attribute) name; the value will be retrieved
                from this attribute
            label: descriptive label

        Returns:
            two-column HTML table row (label, value)
        """
        if label is None:
            label = fieldname
        return tr_qa(label, get_true_false_none(req, getattr(self, fieldname)))

    def get_twocol_bool_row_present_absent(
        self, req: "CamcopsRequest", fieldname: str, label: str = None
    ) -> str:
        """
        HTML table row, two columns, with Boolean present/absent formatter for
        value.

        Args:
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            fieldname: field (attribute) name; the value will be retrieved
                from this attribute
            label: descriptive label

        Returns:
            two-column HTML table row (label, value)
        """
        if label is None:
            label = fieldname
        return tr_qa(
            label, get_present_absent_none(req, getattr(self, fieldname))
        )

    @staticmethod
    def get_twocol_picture_row(blob: Optional[Blob], label: str) -> str:
        """
        HTML table row, two columns, with PNG on right.

        Args:
            blob: the :class:`camcops_server.cc_modules.cc_blob.Blob` object
            label: descriptive label

        Returns:
            two-column HTML table row (label, picture)
        """
        return tr(label, get_blob_img_html(blob))

    # -------------------------------------------------------------------------
    # Field helper functions for subclasses
    # -------------------------------------------------------------------------

    def get_values(self, fields: List[str]) -> List:
        """
        Get list of object's values from list of field names.
        """
        return [getattr(self, f) for f in fields]

    def is_field_not_none(self, field: str) -> bool:
        """
        Is the field not None?
        """
        return getattr(self, field) is not None

    def any_fields_none(self, fields: List[str]) -> bool:
        """
        Are any specified fields None?
        """
        for f in fields:
            if getattr(self, f) is None:
                return True
        return False

    def all_fields_not_none(self, fields: List[str]) -> bool:
        """
        Are all specified fields not None?
        """
        return not self.any_fields_none(fields)

    def any_fields_null_or_empty_str(self, fields: List[str]) -> bool:
        """
        Are any specified fields either None or the empty string?
        """
        for f in fields:
            v = getattr(self, f)
            if v is None or v == "":
                return True
        return False

    def are_all_fields_not_null_or_empty_str(self, fields: List[str]) -> bool:
        """
        Are all specified fields neither None nor the empty string?
        """
        return not self.any_fields_null_or_empty_str(fields)

    def n_fields_not_none(self, fields: List[str]) -> int:
        """
        How many of the specified fields are not None?
        """
        total = 0
        for f in fields:
            if getattr(self, f) is not None:
                total += 1
        return total

    def n_fields_none(self, fields: List[str]) -> int:
        """
        How many of the specified fields are None?
        """
        total = 0
        for f in fields:
            if getattr(self, f) is None:
                total += 1
        return total

    def count_booleans(self, fields: List[str]) -> int:
        """
        How many of the specified fields evaluate to True (are truthy)?
        """
        total = 0
        for f in fields:
            value = getattr(self, f)
            if value:
                total += 1
        return total

    def all_truthy(self, fields: List[str]) -> bool:
        """
        Do all the specified fields evaluate to True (are they all truthy)?
        """
        for f in fields:
            value = getattr(self, f)
            if not value:
                return False
        return True

    def count_where(self, fields: List[str], wherevalues: List[Any]) -> int:
        """
        Count how many values for the specified fields are in ``wherevalues``.
        """
        return sum(1 for x in self.get_values(fields) if x in wherevalues)

    def count_wherenot(self, fields: List[str], notvalues: List[Any]) -> int:
        """
        Count how many values for the specified fields are NOT in
        ``notvalues``.
        """
        return sum(1 for x in self.get_values(fields) if x not in notvalues)

    def sum_fields(
        self, fields: List[str], ignorevalue: Any = None
    ) -> Union[int, float]:
        """
        Sum values stored in all specified fields (skipping any whose value is
        ``ignorevalue``; treating fields containing ``None`` as zero).
        """
        total = 0
        for f in fields:
            value = getattr(self, f)
            if value == ignorevalue:
                continue
            total += value if value is not None else 0
        return total

    def mean_fields(
        self, fields: List[str], ignorevalue: Any = None
    ) -> Union[int, float, None]:
        """
        Return the mean of the values stored in all specified fields (skipping
        any whose value is ``ignorevalue``).
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
        """
        Returns a list of field (column, attribute) names from a prefix.
        For example, ``fieldnames_from_prefix("q", 1, 5)`` produces
        ``["q1", "q2", "q3", "q4", "q5"]``.

        Args:
            prefix: string prefix
            start: first value (inclusive)
            end: last value (inclusive

        Returns:
            list of fieldnames, as above

        """
        return [prefix + str(x) for x in range(start, end + 1)]

    @staticmethod
    def fieldnames_from_list(
        prefix: str, suffixes: Iterable[Any]
    ) -> List[str]:
        """
        Returns a list of fieldnames made by appending each suffix to the
        prefix.

        Args:
            prefix: string prefix
            suffixes: list of suffixes, which will be coerced to ``str``

        Returns:
            list of fieldnames, as above

        """
        return [prefix + str(x) for x in suffixes]

    # -------------------------------------------------------------------------
    # Extra strings
    # -------------------------------------------------------------------------

    @classmethod
    def get_extrastring_taskname(cls) -> str:
        """
        Get the taskname used as the top-level key for this task's extra
        strings (loaded by the server from XML files). By default, this is the
        task's primary tablename, but tasks may override that via
        ``extrastring_taskname``.
        """
        return cls.extrastring_taskname or cls.tablename

    @classmethod
    def extrastrings_exist(cls, req: "CamcopsRequest") -> bool:
        """
        Does the server have any extra strings for this task?
        """
        return req.task_extrastrings_exist(cls.get_extrastring_taskname())

    @classmethod
    def wxstring(
        cls,
        req: "CamcopsRequest",
        name: str,
        defaultvalue: str = None,
        provide_default_if_none: bool = True,
    ) -> str:
        """
        Return a web-safe version of an extra string for this task.

        Args:
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            name: name (second-level key) of the string, within the set of
                this task's extra strings
            defaultvalue: default to return if the string is not found
            provide_default_if_none: if ``True`` and ``default is None``,
                return a helpful missing-string message in the style
                "string x.y not found"
        """
        if defaultvalue is None and provide_default_if_none:
            defaultvalue = f"[{cls.get_extrastring_taskname()}: {name}]"
        return req.wxstring(
            cls.get_extrastring_taskname(),
            name,
            defaultvalue,
            provide_default_if_none=provide_default_if_none,
        )

    @classmethod
    def xstring(
        cls,
        req: "CamcopsRequest",
        name: str,
        defaultvalue: str = None,
        provide_default_if_none: bool = True,
    ) -> str:
        """
        Return a raw (not necessarily web-safe) version of an extra string for
        this task.

        Args:
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            name: name (second-level key) of the string, within the set of
                this task's extra strings
            defaultvalue: default to return if the string is not found
            provide_default_if_none: if ``True`` and ``default is None``,
                return a helpful missing-string message in the style
                "string x.y not found"
        """
        if defaultvalue is None and provide_default_if_none:
            defaultvalue = f"[{cls.get_extrastring_taskname()}: {name}]"
        return req.xstring(
            cls.get_extrastring_taskname(),
            name,
            defaultvalue,
            provide_default_if_none=provide_default_if_none,
        )

    @classmethod
    def make_options_from_xstrings(
        cls,
        req: "CamcopsRequest",
        prefix: str,
        first: int,
        last: int,
        suffix: str = "",
    ) -> Dict[int, str]:
        """
        Creates a lookup dictionary from xstrings.

        Args:
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            prefix: prefix for xstring
            first: first value
            last: last value
            suffix: optional suffix

        Returns:
            dict: Each entry maps ``value`` to an xstring named
            ``<PREFIX><VALUE><SUFFIX>``.

        """
        d = {}  # type: Dict[int, str]
        if first > last:  # descending order
            for i in range(first, last - 1, -1):
                d[i] = cls.xstring(req, f"{prefix}{i}{suffix}")
        else:  # ascending order
            for i in range(first, last + 1):
                d[i] = cls.xstring(req, f"{prefix}{i}{suffix}")
        return d

    @staticmethod
    def make_options_from_numbers(first: int, last: int) -> Dict[int, str]:
        """
        Creates a simple dictionary mapping numbers to string versions of those
        numbers. Usually for subsequent (more interesting) processing!

        Args:
            first: first value
            last: last value

        Returns:
            dict

        """
        d = {}  # type: Dict[int, str]
        if first > last:  # descending order
            for i in range(first, last - 1, -1):
                d[i] = str(i)
        else:  # ascending order
            for i in range(first, last + 1):
                d[i] = str(i)
        return d


# =============================================================================
# Collating all task tables for specific purposes
# =============================================================================
# Function, staticmethod, classmethod?
# https://stackoverflow.com/questions/8108688/in-python-when-should-i-use-a-function-instead-of-a-method  # noqa
# https://stackoverflow.com/questions/11788195/module-function-vs-staticmethod-vs-classmethod-vs-no-decorators-which-idiom-is  # noqa
# https://stackoverflow.com/questions/15017734/using-static-methods-in-python-best-practice  # noqa


def all_task_tables_with_min_client_version() -> Dict[str, Version]:
    """
    Across all tasks, return a mapping from each of their tables to the
    minimum client version.

    Used by
    :func:`camcops_server.cc_modules.client_api.all_tables_with_min_client_version`.

    """  # noqa
    d = {}  # type: Dict[str, Version]
    classes = list(Task.gen_all_subclasses())
    for cls in classes:
        d.update(cls.all_tables_with_min_client_version())
    return d


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def tablename_to_task_class_dict() -> Dict[str, Type[Task]]:
    """
    Returns a mapping from task base tablenames to task classes.
    """
    d = {}  # type: Dict[str, Type[Task]]
    for cls in Task.gen_all_subclasses():
        d[cls.tablename] = cls
    return d


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def all_task_tablenames() -> List[str]:
    """
    Returns all task base table names.
    """
    d = tablename_to_task_class_dict()
    return list(d.keys())


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def all_task_classes() -> List[Type[Task]]:
    """
    Returns all task base table names.
    """
    d = tablename_to_task_class_dict()
    return list(d.values())


# =============================================================================
# Support functions
# =============================================================================


def get_from_dict(d: Dict, key: Any, default: Any = INVALID_VALUE) -> Any:
    """
    Returns a value from a dictionary. This is not a very complex function...
    all it really does in practice is provide a default for ``default``.

    Args:
        d: the dictionary
        key: the key
        default: value to return if none is provided
    """
    return d.get(key, default)
