#!/usr/bin/env python
# camcops_server/cc_modules/cc_blob.py

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

import datetime
import logging
from typing import Optional

from cardinal_pythonlib.logs import BraceStyleAdapter
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, LargeBinary, Text
import wand.image

from .cc_constants import ERA_NOW, MIMETYPE_PNG
from .cc_db import GenericTabletRecordMixin
from .cc_html import get_data_url, get_embedded_img_tag
from .cc_sqla_coltypes import (
    IntUnsigned,
    MimeTypeColType,
    # TableNameColType, # *** to be added once Alembic up
)
from .cc_request import CamcopsRequest
from .cc_sqlalchemy import Base
from .cc_unittest import unit_test_ignore
from .cc_xml import get_xml_blob_tuple, XmlElement

log = BraceStyleAdapter(logging.getLogger(__name__))

# ExactImage API documentation is a little hard to find. See:
#   http://www.exactcode.com/site/open_source/exactimage
#   man econvert # after sudo apt-get install exactimage
#   https://exactcode.de/exact-image/trunk/api/api.hh <-- THIS ONE
#   http://fossies.org/linux/privat/exact-image-0.8.9.tar.gz:a/exact-image-0.8.9/examples/test.py  # noqa
#   http://lickmychip.com/2012/07/26/playing-with-exactimage/
#   https://github.com/romainneutron/ExactImage-PHP
# Also, rotation is not simple!
# Wand seems much better: http://docs.wand-py.org/en/0.3.5/


# =============================================================================
# Blob class
# =============================================================================

class Blob(GenericTabletRecordMixin, Base):
    """
    Class representing a binary large object (BLOB).

    Has helper functions for PNG image processing.
    """
    __tablename__ = "blobs"
    id = Column(
        "id", IntUnsigned,
        nullable=False,
        comment="BLOB (binary large object) primary key on the source "
                "tablet device"
    )
    tablename = Column(
        "tablename", Text,  # *** change to TableNameColType once Alembic up
        nullable=False,
        comment="Name of the table referring to this BLOB"
    )
    tablepk = Column(
        "tablepk", IntUnsigned,
        nullable=False,
        comment="Primary key (id field) of the row referring to this BLOB"
    )
    fieldname = Column(
        "fieldname", Text,  # *** change to TableNameColType once Alembic up
        nullable=False,
        comment="Field name of the field referring to this BLOB by ID"
    )
    filename = Column(
        "filename", Text,  # Text is correct; filenames can be long
        comment="Filename of the BLOB on the source tablet device (on "
                "the source device, BLOBs are stored in files, not in "
                "the database)"
    )
    mimetype = Column(
        "mimetype", MimeTypeColType,
        comment="MIME type of the BLOB"
    )
    image_rotation_deg_cw = Column(
        "image_rotation_deg_cw", Integer,
        comment="For images: rotation to be applied, clockwise, in degrees"
    )
    theblob = Column(
        "theblob", LargeBinary,
        comment="The BLOB itself, a binary object containing arbitrary "
                "information (such as a picture)"
    )

    @classmethod
    def get_current_blob_by_client_info(cls,
                                        dbsession: SqlASession,
                                        device_id: int,
                                        clientpk: int,
                                        era: str) -> Optional['Blob']:
        """Returns the current Blob object, or None."""
        blob = dbsession.query(cls)\
            .filter(cls.id == clientpk)\
            .filter(cls._device_id == device_id)\
            .filter(cls._era == era)\
            .filter(cls._current == True)\
            .first()  # type: Optional[Blob]  # noqa
        return blob

    @classmethod
    def get_contemporaneous_blob_by_client_info(
            cls,
            dbsession: SqlASession,
            device_id: int,
            clientpk: int,
            era: str,
            referrer_added_utc: datetime.datetime,
            referrer_removed_utc: Optional[datetime.datetime]) \
            -> Optional['Blob']:
        """
        Returns a contemporaneous Blob object, or None.

        Use particularly to look up BLOBs matching old task records.
        """
        blob = dbsession.query(cls)\
            .filter(cls.id == clientpk)\
            .filter(cls._device_id == device_id)\
            .filter(cls._era == era)\
            .filter(cls._when_added_batch_utc <= referrer_added_utc)\
            .filter(cls._when_removed_batch_utc == referrer_removed_utc)\
            .first()  # type: Optional[Blob]
        # Note, for referrer_removed_utc: if this is None, then the comparison
        # "field == None" is made; otherwise "field == value".
        # Since SQLAlchemy translates "== None" to "IS NULL", we're OK.
        # https://stackoverflow.com/questions/37445041/sqlalchemy-how-to-filter-column-which-contains-both-null-and-integer-values  # noqa
        return blob

    def get_rotated_image(self) -> Optional[bytes]:
        """Returns a binary image, having rotated if necessary, or None."""
        if not self.theblob:
            return None
        rotation = self.image_rotation_deg_cw
        if rotation is None or rotation % 360 == 0:
            return self.theblob
        with wand.image.Image(blob=self.theblob) as img:
            img.rotate(rotation)
            return img.make_blob()
            # ... no parameter => return in same format as supplied

    def get_img_html(self) -> str:
        """Returns an HTML IMG tag encoding the BLOB, or ''."""
        image_bits = self.get_rotated_image()
        if not image_bits:
            return ""
        return get_embedded_img_tag(self.mimetype or MIMETYPE_PNG, image_bits)
        # Historically, CamCOPS supported only PNG, so add this as a default

    def get_image_xml_tuple(self, name: str) -> XmlElement:
        """Returns an XmlElementTuple for this object."""
        image_bits = self.get_rotated_image()
        return get_xml_blob_tuple(name, image_bits)

    def get_data_url(self) -> str:
        """Returns a data URL encapsulating the BLOB, or ''."""
        if not self.theblob:
            return ""
        return get_data_url(self.mimetype or MIMETYPE_PNG, self.theblob)


# =============================================================================
# Relationships
# =============================================================================

def blob_relationship(classname: str,
                      blob_id_col_attr_name: str,
                      read_only: bool = True) -> RelationshipProperty:
    """
    Simplifies creation of BLOB relationships.
    In a class definition, use like this:

        class Something(Base):

            photo_blobid = CamcopsColumn(
                "photo_blobid", Integer,
                is_blob_id_field=True, blob_field_xml_name="photo_blob"
            )

            photo = blob_relationship("Something", "photo_blobid")

            # ... can't use Something directly as it's not yet been fully
            #     defined, but we want the convenience of defining this
            #     relationship here without the need to use metaclasses.
            # ... SQLAlchemy's primaryjoin uses Python-side names (class and
            #     attribute), rather than SQL-side names (table and column),
            #     at least for its fancier things:
            # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#relationship-primaryjoin  # noqa

    """
    return relationship(
        Blob,
        primaryjoin=(
            "and_("
            " remote(Blob.id) == foreign({cls}.{fk}), "
            " remote(Blob._device_id) == foreign({cls}._device_id), "
            " remote(Blob._era) == foreign({cls}._era), "
            " remote(Blob._current) == True "
            ")".format(cls=classname, fk=blob_id_col_attr_name)
        ),
        uselist=False,
        viewonly=read_only
    )


# =============================================================================
# Unit tests
# =============================================================================

def get_blob_img_html(blob: Optional[Blob]) -> str:
    """Get HTML IMG tag with embedded data, or HTML error message."""
    if blob is None:
        return "<i>(No picture)</i>"
    return blob.get_img_html()


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_blob(blob: Blob) -> None:
    """Unit tests for the Blob class."""
    # skip Blob.make_tables
    unit_test_ignore("", blob.dump)
    unit_test_ignore("", blob.get_rotated_image)
    unit_test_ignore("", blob.get_img_html)
    unit_test_ignore("", blob.get_image_xml_tuple, "name")
    unit_test_ignore("", blob.get_data_url)


def ccblob_unit_tests(req: CamcopsRequest) -> None:
    """Unit tests for the cc_blob module."""
    dbsession = req.dbsession
    # noinspection PyProtectedMember
    blobs = dbsession.query(Blob)\
        .filter(Blob._current == True)\
        .all()  # noqa
    if not blobs:
        blobs = [Blob()]
    for blob in blobs:
        unit_tests_blob(blob)

    unit_test_ignore("", Blob.get_current_blob_by_client_info,
                     dbsession, 0, 0, ERA_NOW)
    unit_test_ignore("", Blob.get_contemporaneous_blob_by_client_info,
                     dbsession, 0, 0, ERA_NOW, None, None)
