#!/usr/bin/env python
# camcops_server/cc_modules/cc_db.py

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
"""

from collections import OrderedDict
import logging
from typing import (Any, Dict, Generator, List, Optional, Set, Tuple, Type,
                    TYPE_CHECKING, TypeVar, Union)

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_columns
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer

from .cc_constants import ERA_NOW
from .cc_sqla_coltypes import (
    CamcopsColumn,
    EraColType,
    gen_ancillary_relationships,
    gen_camcops_blob_columns,
    PendulumDateTimeAsIsoTextColType,
    PermittedValueChecker,
    RelationshipInfo,
    SemanticVersionColType,
)
from .cc_summaryelement import SummaryElement
from .cc_tsv import TsvPage
from .cc_version import CAMCOPS_SERVER_VERSION
from .cc_xml import (
    make_xml_branches_from_blobs,
    make_xml_branches_from_columns,
    make_xml_branches_from_summaries,
    XML_COMMENT_STORED,
    XML_COMMENT_CALCULATED,
    XmlElement,
)

if TYPE_CHECKING:
    from .cc_blob import Blob
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))

T = TypeVar('T')


# =============================================================================
# Base classes implementing common fields
# =============================================================================

# noinspection PyAttributeOutsideInit
class GenericTabletRecordMixin(object):
    """
    From the server's perspective, _pk is unique.
    However, records are defined also in their tablet context, for which
    an individual tablet (defined by the combination of _device_id and _era)
    sees its own PK, "id".
    """
    __tablename__ = None  # type: str  # sorts out some mixin type checking

    # -------------------------------------------------------------------------
    # On the server side:
    # -------------------------------------------------------------------------

    # Plain columns

    # noinspection PyMethodParameters
    @declared_attr
    def _pk(cls) -> Column:
        return Column(
            "_pk", Integer,
            primary_key=True, autoincrement=True, index=True,
            comment="(SERVER) Primary key (on the server)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _device_id(cls) -> Column:
        return Column(
            "_device_id", Integer, ForeignKey("_security_devices.id"),
            nullable=False, index=True,
            comment="(SERVER) ID of the source tablet device"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _era(cls) -> Column:
        return Column(
            "_era", EraColType,
            nullable=False, index=True,
            comment="(SERVER) 'NOW', or when this row was preserved and "
                    "removed from the source device (UTC ISO 8601)",
        )
        # ... note that _era is textual so that plain comparison
        # with "=" always works, i.e. no NULLs -- for USER comparison too, not
        # just in CamCOPS code

    # noinspection PyMethodParameters
    @declared_attr
    def _current(cls) -> Column:
        return Column(
            "_current", Boolean,
            nullable=False, index=True,
            comment="(SERVER) Is the row current (1) or not (0)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_added_exact(cls) -> Column:
        return Column(
            "_when_added_exact", PendulumDateTimeAsIsoTextColType,
            comment="(SERVER) Date/time this row was added (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_added_batch_utc(cls) -> Column:
        return Column(
            "_when_added_batch_utc", DateTime,
            comment="(SERVER) Date/time of the upload batch that added this "
                    "row (DATETIME in UTC)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _adding_user_id(cls) -> Column:
        return Column(
            "_adding_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that added this row",
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_removed_exact(cls) -> Column:
        return Column(
            "_when_removed_exact", PendulumDateTimeAsIsoTextColType,
            comment="(SERVER) Date/time this row was removed, i.e. made "
                    "not current (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _when_removed_batch_utc(cls) -> Column:
        return Column(
            "_when_removed_batch_utc", DateTime,
            comment="(SERVER) Date/time of the upload batch that removed "
                    "this row (DATETIME in UTC)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _removing_user_id(cls) -> Column:
        return Column(
            "_removing_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that removed this row"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _preserving_user_id(cls) -> Column:
        return Column(
            "_preserving_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that preserved this row"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _forcibly_preserved(cls) -> Column:
        return Column(
            "_forcibly_preserved", Boolean, default=False,
            comment="(SERVER) Forcibly preserved by superuser (rather than "
                    "normally preserved by tablet)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _predecessor_pk(cls) -> Column:
        return Column(
            "_predecessor_pk", Integer,
            comment="(SERVER) PK of predecessor record, prior to modification"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _successor_pk(cls) -> Column:
        return Column(
            "_successor_pk", Integer,
            comment="(SERVER) PK of successor record  (after modification) "
                    "or NULL (whilst live, or after deletion)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erased(cls) -> Column:
        return Column(
            "_manually_erased", Boolean, default=False,
            comment="(SERVER) Record manually erased (content destroyed)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erased_at(cls) -> Column:
        return Column(
            "_manually_erased_at", PendulumDateTimeAsIsoTextColType,
            comment="(SERVER) Date/time of manual erasure (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erasing_user_id(cls) -> Column:
        return Column(
            "_manually_erasing_user_id", Integer,
            ForeignKey("_security_users.id"),
            comment="(SERVER) ID of user that erased this row manually"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _camcops_version(cls) -> Column:
        return Column(
            "_camcops_version", SemanticVersionColType,
            default=CAMCOPS_SERVER_VERSION,
            comment="(SERVER) CamCOPS version number of the uploading device"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _addition_pending(cls) -> Column:
        return Column(
            "_addition_pending", Boolean, nullable=False, default=False,
            comment="(SERVER) Addition pending?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _removal_pending(cls) -> Column:
        return Column(
            "_removal_pending", Boolean, default=False,
            comment="(SERVER) Removal pending?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _group_id(cls) -> Column:
        return Column(
            "_group_id", Integer, ForeignKey("_security_groups.id"),
            nullable=False, index=True,
            comment="(SERVER) ID of group to which this record belongs"
        )

    RESERVED_FIELDS = [  # fields that tablets can't upload
        "_pk",
        "_device_id",
        "_era",
        "_current",
        "_when_added_exact",
        "_when_added_batch_utc",
        "_adding_user_id",
        "_when_removed_exact",
        "_when_removed_batch_utc",
        "_removing_user_id",
        "_preserving_user_id",
        "_forcibly_preserved",
        "_predecessor_pk",
        "_successor_pk",
        "_manually_erased",
        "_manually_erased_at",
        "_manually_erasing_user_id",
        "_camcops_version",
        "_addition_pending",
        "_removal_pending",
        "_group_id",
    ]  # but more generally: they start with "_"...

    # -------------------------------------------------------------------------
    # Fields that *all* client tables have:
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @declared_attr
    def id(cls) -> Column:
        return Column(
            "id", Integer,
            nullable=False, index=True,
            comment="(TASK) Primary key (task ID) on the tablet device"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def when_last_modified(cls) -> Column:
        return Column(
            "when_last_modified", PendulumDateTimeAsIsoTextColType,
            index=True,  # ... as used by database upload script
            comment="(STANDARD) Date/time this row was last modified on the "
                    "source tablet device (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def _move_off_tablet(cls) -> Column:
        return Column(
            "_move_off_tablet", Boolean, default=False,
            comment="(SERVER/TABLET) Record-specific preservation pending?"
        )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @declared_attr
    def _device(cls) -> RelationshipProperty:
        return relationship("Device")

    # noinspection PyMethodParameters
    @declared_attr
    def _adding_user(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls._adding_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _removing_user(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls._removing_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _preserving_user(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls._preserving_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _manually_erasing_user(cls) -> RelationshipProperty:
        return relationship("User",
                            foreign_keys=[cls._manually_erasing_user_id])

    # noinspection PyMethodParameters
    @declared_attr
    def _group(cls) -> RelationshipProperty:
        return relationship("Group",
                            foreign_keys=[cls._group_id])

    # -------------------------------------------------------------------------
    # Fetching attributes
    # -------------------------------------------------------------------------

    def get_pk(self) -> Optional[int]:
        return self._pk

    def get_era(self) -> Optional[str]:
        return self._era

    def get_device_id(self) -> Optional[int]:
        return self._device_id

    def get_group_id(self) -> Optional[int]:
        return self._group_id

    # -------------------------------------------------------------------------
    # Autoscanning objects and their relationships
    # -------------------------------------------------------------------------

    def _get_xml_root(self,
                      req: "CamcopsRequest",
                      skip_attrs: List[str] = None,
                      include_plain_columns: bool=True,
                      include_blobs: bool = True,
                      include_calculated: bool = True,
                      sort_by_attr: bool = True) -> XmlElement:
        """
        Called to create an XML root object for records ancillary to Task
        objects. Tasks themselves use a more complex mechanism.
        """
        skip_attrs = skip_attrs or []  # type: List[str]
        # "__tablename__" will make the type checker complain, as we're
        # defining a function for a mixin that assumes it's mixed in to a
        # SQLAlchemy Base-derived class
        # noinspection PyUnresolvedReferences
        return XmlElement(
            name=self.__tablename__,
            value=self._get_xml_branches(
                req=req,
                skip_attrs=skip_attrs,
                include_plain_columns=include_plain_columns,
                include_blobs=include_blobs,
                include_calculated=include_calculated,
                sort_by_attr=sort_by_attr
            )
        )

    def _get_xml_branches(self,
                          req: "CamcopsRequest",
                          skip_attrs: List[str],
                          include_plain_columns: bool = True,
                          include_blobs: bool = True,
                          include_calculated: bool = True,
                          sort_by_attr: bool = True) -> List[XmlElement]:
        """
        Gets the values of SQLAlchemy columns as XmlElement objects.
        Optionally, find any SQLAlchemy relationships that are relationships
        to Blob objects, and include them too.

        Used by _get_xml_root above, but also by Tasks themselves.
        """
        # log.critical("_get_xml_branches for {!r}", self)
        skip_attrs = skip_attrs or []  # type: List[str]
        stored_branches = []  # type: List[XmlElement]
        if include_plain_columns:
            stored_branches += make_xml_branches_from_columns(
                self, skip_fields=skip_attrs)
        if include_blobs:
            stored_branches += make_xml_branches_from_blobs(
                req, self, skip_fields=skip_attrs)
        if sort_by_attr:
            stored_branches.sort(key=lambda el: el.name)
        branches = [XML_COMMENT_STORED] + stored_branches
        # Calculated
        if include_calculated:
            branches.append(XML_COMMENT_CALCULATED)
            branches.extend(make_xml_branches_from_summaries(
                self.get_summaries(req),
                skip_fields=skip_attrs,
                sort_by_name=sort_by_attr
            ))
        # log.critical("... branches for {!r}: {!r}", self, branches)
        return branches

    def _get_core_tsv_page(self, req: "CamcopsRequest",
                           heading_prefix: str = "") -> TsvPage:
        row = OrderedDict()
        for attrname, column in gen_columns(self):
            row[heading_prefix + attrname] = getattr(self, attrname)
        for s in self.get_summaries(req):
            row[heading_prefix + s.name] = s.value
        return TsvPage(name=self.__tablename__, rows=[row])

    # -------------------------------------------------------------------------
    # Erasing (overwriting data, not deleting the database records)
    # -------------------------------------------------------------------------

    def manually_erase_with_dependants(self, req: "CamcopsRequest") -> None:
        """
        Manually erases a standard record and marks it so erased.
        The object remains _current (if it was), as a placeholder, but its
        contents are wiped.
        WRITES TO DATABASE.
        """
        if self._manually_erased or self._pk is None or self._era == ERA_NOW:
            # ... _manually_erased: don't do it twice
            # ... _pk: basic sanity check
            # ... _era: don't erase things that are current on the tablet
            return
        # 1. "Erase my dependants"
        for ancillary in self.gen_ancillary_instances_even_noncurrent():
            ancillary.manually_erase_with_dependants(req)
        for blob in self.gen_blobs_even_noncurrent():
            blob.manually_erase_with_dependants(req)
        # 2. "Erase me"
        erasure_attrs = []  # type: List[str]
        for attrname, column in gen_columns(self):
            if attrname.startswith("_"):  # system field
                continue
            if not column.nullable:  # this should cover FKs
                continue
            if column.foreign_keys:  # ... but to be sure...
                continue
            erasure_attrs.append(attrname)
        for attrname in erasure_attrs:
            setattr(self, attrname, None)
        self._current = False
        self._manually_erased = True
        self._manually_erased_at = req.now
        self._manually_erasing_user_id = req.user_id

    def delete_with_dependants(self, req: "CamcopsRequest") -> None:
        if self._pk is None:
            return
        # 1. "Delete my dependants"
        for ancillary in self.gen_ancillary_instances_even_noncurrent():
            ancillary.delete_with_dependants(req)
        for blob in self.gen_blobs_even_noncurrent():
            blob.delete_with_dependants(req)
        # 2. "Delete me"
        dbsession = SqlASession.object_session(self)
        dbsession.delete(self)

    def gen_attrname_ancillary_pairs(self) \
            -> Generator[Tuple[str, "GenericTabletRecordMixin"], None, None]:
        for attrname, rel_prop, rel_cls in gen_ancillary_relationships(self):
            if rel_prop.uselist:
                ancillaries = getattr(self, attrname)  # type: List[GenericTabletRecordMixin]  # noqa
            else:
                ancillaries = [getattr(self, attrname)]  # type: List[GenericTabletRecordMixin]  # noqa
            for ancillary in ancillaries:
                if ancillary is None:
                    continue
                yield attrname, ancillary

    def gen_ancillary_instances(self) -> Generator["GenericTabletRecordMixin",
                                                   None, None]:
        for attrname, ancillary in self.gen_attrname_ancillary_pairs():
            yield ancillary

    def gen_ancillary_instances_even_noncurrent(self) \
            -> Generator["GenericTabletRecordMixin", None, None]:
        seen = set()  # type: Set[GenericTabletRecordMixin]
        for ancillary in self.gen_ancillary_instances():
            for lineage_member in ancillary.get_lineage():
                if lineage_member in seen:
                    continue
                seen.add(lineage_member)
                yield lineage_member

    def gen_blobs(self) -> Generator["Blob", None, None]:
        for id_attrname, column in gen_camcops_blob_columns(self):
            relationship_attr = column.blob_relationship_attr_name
            blob = getattr(self, relationship_attr)
            if blob is None:
                continue
            yield blob

    def gen_blobs_even_noncurrent(self) -> Generator["Blob", None, None]:
        seen = set()  # type: Set["Blob"]
        for blob in self.gen_blobs():
            if blob is None:
                continue
            for lineage_member in blob.get_lineage():
                if lineage_member in seen:
                    continue
                seen.add(lineage_member)
                yield lineage_member

    def get_lineage(self) -> List["GenericTabletRecordMixin"]:
        """
        Returns all records that are part of the same "lineage", that is:
        matching on id/device_id/era, but including both current and any
        historical non-current versions.
        """
        dbsession = SqlASession.object_session(self)
        cls = self.__class__
        q = dbsession.query(cls)\
            .filter(cls.id == self.id)\
            .filter(cls._device_id == self._device_id)\
            .filter(cls._era == self._era)
        return list(q)

    # -------------------------------------------------------------------------
    # History functions for server-side editing
    # -------------------------------------------------------------------------

    def set_predecessor(self, req: "CamcopsRequest",
                        predecessor: "GenericTabletRecordMixin") -> None:
        """
        Used for some unusual server-side manipulations (e.g. editing patient
        details).
        The "self" object replaces the predecessor, so "self" becomes current
        and refers back to "predecessor", while "predecessor" becomes
        non-current and refers forward to "self".
        """
        assert predecessor._current
        # We become new and current, and refer to our predecessor
        self._device_id = predecessor._device_id
        self._era = predecessor._era
        self._current = True
        self._when_added_exact = req.now
        self._when_added_batch_utc = req.now_utc
        self._adding_user_id = req.user_id
        if self._era != ERA_NOW:
            self._preserving_user_id = req.user_id
            self._forcibly_preserved = True
        self._predecessor_pk = predecessor._pk
        self._camcops_version = predecessor._camcops_version
        self._group_id = predecessor._group_id
        # Make our predecessor refer to us
        if self._pk is None:
            req.dbsession.add(self)  # ensure we have a PK, part 1
            req.dbsession.flush()  # ensure we have a PK, part 2
        predecessor._set_successor(req, self)

    def _set_successor(self, req: "CamcopsRequest",
                       successor: "GenericTabletRecordMixin") -> None:
        """
        See set_predecessor() above.
        """
        assert successor._pk is not None
        self._current = False
        self._when_removed_exact = req.now
        self._when_removed_batch_utc = req.now_utc
        self._removing_user_id = req.user_id
        self._successor_pk = successor._pk

    def mark_as_deleted(self, req: "CamcopsRequest") -> None:
        """
        Ends the history chain and marks this record as non-current.
        """
        if self._current:
            self._when_removed_exact = req.now
            self._when_removed_batch_utc = req.now_utc
            self._removing_user_id = req.user_id
            self._current = False

    def create_fresh(self, req: "CamcopsRequest", device_id: int,
                     era: str, group_id: int) -> None:
        """
        Used to create a record from scratch.
        """
        self._device_id = device_id
        self._era = era
        self._group_id = group_id
        self._current = True
        self._when_added_exact = req.now
        self._when_added_batch_utc = req.now_utc
        self._adding_user_id = req.user_id

    # -------------------------------------------------------------------------
    # Override this if you provide summaries
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_summaries(self, req: "CamcopsRequest") -> List[SummaryElement]:
        """
        Return a list of summary value objects, for this database object
        (not any dependent classes/tables).
        """
        return []  # type: List[SummaryElement]

    def get_summary_names(self, req: "CamcopsRequest") -> List[str]:
        """
        Returns a list of summary field names.
        """
        return [x.name for x in self.get_summaries(req)]


# =============================================================================
# Relationships
# =============================================================================

def ancillary_relationship(
        parent_class_name: str,
        ancillary_class_name: str,
        ancillary_fk_to_parent_attr_name: str,
        ancillary_order_by_attr_name: str = None,
        read_only: bool = True) -> RelationshipProperty:
    """
    Implements a one-to-many relationship, i.e. one parent to many ancillaries.
    """
    parent_pk_attr_name = "id"  # always
    return relationship(
        ancillary_class_name,
        primaryjoin=(
            "and_("
            " remote({a}.{fk}) == foreign({p}.{pk}), "
            " remote({a}._device_id) == foreign({p}._device_id), "
            " remote({a}._era) == foreign({p}._era), "
            " remote({a}._current) == True "
            ")".format(
                a=ancillary_class_name,
                fk=ancillary_fk_to_parent_attr_name,
                p=parent_class_name,
                pk=parent_pk_attr_name,
            )
        ),
        uselist=True,
        order_by="{a}.{f}".format(a=ancillary_class_name,
                                  f=ancillary_order_by_attr_name),
        viewonly=read_only,
        info={
            RelationshipInfo.IS_ANCILLARY: True,
        },
        # ... "info" is a user-defined dictionary; see
        # http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship.params.info  # noqa
        # http://docs.sqlalchemy.org/en/latest/orm/internals.html#MapperProperty.info  # noqa
    )


# =============================================================================
# Field creation assistance
# =============================================================================

# TypeEngineBase = TypeVar('TypeEngineBase', bound=TypeEngine)

def add_multiple_columns(
        cls: Type,
        prefix: str,
        start: int,
        end: int,
        coltype=Integer,
        # this type fails: Union[Type[TypeEngineBase], TypeEngine]
        # ... https://stackoverflow.com/questions/38106227
        # ... https://github.com/python/typing/issues/266
        colkwargs: Dict[str, Any] = None,
        comment_fmt: str = None,
        comment_strings: List[str] = None,
        minimum: Union[int, float] = None,
        maximum: Union[int, float] = None,
        pv: List[Any] = None) -> None:
    """
    Add a sequence of SQLAlchemy columns to a class.
    Called from a metaclass.

    :param cls: class to which to add columns

    :param prefix: Fieldname will be prefix + str(n), where n defined as below.

    :param start: Start of range.

    :param end: End of range. Thus: i will range from 0 to (end - start)
        inclusive; n will range from start to end inclusive.

    :param coltype: SQLAlchemy column type, in either of these formats: (a)
        ``Integer`` (of general type ``Type[TypeEngine]``?); (b) ``Integer()``
        (of general type ``TypeEngine``).

    :param colkwargs: SQLAlchemy column arguments, as in
        ``Column(name, coltype, **colkwargs)``

    :param comment_fmt: Format string defining field comments. Substitutable
        values are:
        ``{n}``: field number (from range).
        ``{s}``: comment_strings[i], or "" if out of range.

    :param comment_strings: see comment_fmt

    :param minimum: minimum permitted value, or None

    :param maximum: maximum permitted value, or None

    :param pv: list of permitted values, or None

    """
    colkwargs = {} if colkwargs is None else colkwargs  # type: Dict[str, Any]
    comment_strings = comment_strings or []
    for n in range(start, end + 1):
        nstr = str(n)
        i = n - start
        colname = prefix + nstr
        if comment_fmt:
            s = ""
            if 0 <= i < len(comment_strings):
                s = comment_strings[i] or ""
            colkwargs["comment"] = comment_fmt.format(n=n, s=s)
        if minimum is not None or maximum is not None or pv is not None:
            colkwargs["permitted_value_checker"] = PermittedValueChecker(
                minimum=minimum,
                maximum=maximum,
                permitted_values=pv
            )
            setattr(cls, colname, CamcopsColumn(colname, coltype, **colkwargs))
        else:
            setattr(cls, colname, Column(colname, coltype, **colkwargs))
