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

import wand.image
# ... sudo apt-get install libmagickwand-dev; sudo pip install Wand

import cardinal_pythonlib.rnc_db as rnc_db

from .cc_constants import ERA_NOW, MIMETYPE_PNG, STANDARD_GENERIC_FIELDSPECS
from . import cc_db
from .cc_html import get_data_url, get_embedded_img_tag
from .cc_logger import BraceStyleAdapter
from .cc_pls import pls
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

class Blob(object):
    """Class representing a binary large object (BLOB).

    Has helper functions for PNG image processing.
    """
    TABLENAME = "blobs"
    FIELDSPECS_WITHOUT_BLOB = STANDARD_GENERIC_FIELDSPECS + [
        dict(name="id", cctype="INT_UNSIGNED", notnull=True,
             comment="BLOB (binary large object) primary key on the source "
                     "tablet device"),
        dict(name="tablename", cctype="TEXT", notnull=True,
             comment="Name of the table referring to this BLOB"),
        dict(name="tablepk", cctype="INT_UNSIGNED", notnull=True,
             comment="Primary key (id field) of the row referring to "
                     "this BLOB"),
        dict(name="fieldname", cctype="TEXT", notnull=True,
             comment="Field name of the field referring to this BLOB by ID"),
        dict(name="filename", cctype="TEXT",
             comment="Filename of the BLOB on the source tablet device (on "
                     "the source device, BLOBs are stored in files, not in "
                     "the database)"),
        dict(name="mimetype", cctype="MIMETYPE",
             comment="MIME type of the BLOB"),
        dict(name="image_rotation_deg_cw", cctype="INT",
             comment="For images: rotation to be applied, clockwise, in "
                     "degrees"),
    ]
    FIELDSPECS = FIELDSPECS_WITHOUT_BLOB + [
        dict(name="theblob", cctype="LONGBLOB",
             comment="The BLOB itself, a binary object containing arbitrary "
                     "information (such as a picture)"),
    ]
    FIELDS_WITHOUT_BLOB = [x["name"] for x in FIELDSPECS_WITHOUT_BLOB]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make associated database tables."""
        cc_db.create_standard_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    @classmethod
    def drop_views(cls) -> None:
        pls.db.drop_view(cls.TABLENAME + "_current")

    def __init__(self, serverpk: Optional[int]) -> None:
        """Initialize, loading from the database if necessary."""
        pls.db.fetch_object_from_db_by_pk(self, Blob.TABLENAME, Blob.FIELDS,
                                          serverpk)
        # self.dump()

    def dump(self) -> None:
        """Debugging option to dump the object."""
        rnc_db.dump_database_object(self, Blob.FIELDS_WITHOUT_BLOB)

    def get_rotated_image(self) -> Optional[bytes]:
        """Returns a binary image, having rotated if necessary, or None."""
        if not self.theblob:
            return None
        rotation = self.image_rotation_deg_cw
        if rotation is None or rotation % 360 == 0:
            return self.theblob
        with wand.image.Image(blob=self.theblob) as img:
            img.rotate(rotation)
            # return img.make_blob('png')
            return img.make_blob()  # no parameter => return in same format as supplied  # noqa

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
# Database lookup
# =============================================================================

def get_current_blob_by_client_info(device_id: int,
                                    clientpk: int,
                                    era: str) -> Optional[Blob]:
    """Returns the current Blob object, or None."""
    serverpk = cc_db.get_current_server_pk_by_client_info(
        Blob.TABLENAME, device_id, clientpk, era)
    if serverpk is None:
        log.debug("FAILED TO FIND BLOB: {}", clientpk)
        return None
    return Blob(serverpk)


def get_contemporaneous_blob_by_client_info(
        device_id: int,
        clientpk: int,
        era: str,
        referrer_added_utc: datetime.datetime,
        referrer_removed_utc: datetime.datetime) -> Optional[Blob]:
    """Returns a contemporaneous Blob object, or None.

    Use particularly to look up BLOBs matching old task records.
    """
    serverpk = cc_db.get_contemporaneous_server_pk_by_client_info(
        Blob.TABLENAME, device_id, clientpk, era,
        referrer_added_utc, referrer_removed_utc)
    # log.critical(
    #     "get_contemporaneous_blob_by_client_info: "
    #     "device_id = {}, "
    #     "clientpk = {}, "
    #     "era = {}, "
    #     "serverpk = {},"
    #     "referrer_added_utc = {}, "
    #     "referrer_removed_utc = {}",
    #     device_id,
    #     clientpk,
    #     era,
    #     serverpk,
    #     referrer_added_utc,
    #     referrer_removed_utc,
    # )
    if serverpk is None:
        log.debug("FAILED TO FIND BLOB: {}", clientpk)
        return None
    return Blob(serverpk)


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


def ccblob_unit_tests() -> None:
    """Unit tests for the cc_blob module."""
    current_pks = pls.db.fetchallfirstvalues(
        "SELECT _pk FROM {} WHERE _current".format(Blob.TABLENAME)
    )
    test_pks = [None, current_pks[0]] if current_pks else [None]
    for pk in test_pks:
        blob = Blob(pk)
        unit_tests_blob(blob)

    unit_test_ignore("", get_current_blob_by_client_info, "", 0, ERA_NOW)
    unit_test_ignore("", get_contemporaneous_blob_by_client_info,
                     "", 0, ERA_NOW, None, None)
