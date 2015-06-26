#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

import wand.image
# ... sudo apt-get install libmagickwand-dev; sudo pip install Wand

import pythonlib.rnc_db as rnc_db
import pythonlib.rnc_web as ws

from cc_constants import ERA_NOW, STANDARD_GENERIC_FIELDSPECS
import cc_db
from cc_logger import logger
from cc_pls import pls
import cc_xml

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
    ]
    FIELDSPECS = FIELDSPECS_WITHOUT_BLOB + [
        dict(name="theblob", cctype="LONGBLOB",
             comment="The BLOB itself, a binary object containing arbitrary "
                     "information (such as a picture)"),
    ]
    FIELDS_WITHOUT_BLOB = [x["name"] for x in FIELDSPECS_WITHOUT_BLOB]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns=False):
        """Make associated database tables."""
        cc_db.create_standard_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, serverpk):
        """Initialize, loading from the database if necessary."""
        pls.db.fetch_object_from_db_by_pk(self, Blob.TABLENAME, Blob.FIELDS,
                                          serverpk)
        # self.dump()

    def dump(self):
        """Debugging option to dump the object."""
        rnc_db.dump_database_object(self, Blob.FIELDS_WITHOUT_BLOB)

    def get_rotated_image(self, rotation_clockwise_deg=0):
        """Returns a binary PNG image, having rotated if necessary, or None."""
        if not self.theblob:
            return None
        if rotation_clockwise_deg is None or rotation_clockwise_deg % 360 == 0:
            return self.theblob
        with wand.image.Image(blob=self.theblob) as img:
            img.rotate(rotation_clockwise_deg)
            return img.make_blob('png')

    def get_png_img_html(self, rotation_clockwise_deg=0):
        """Returns an HTML IMG tag encoding the PNG, or ''."""
        image_bits = self.get_rotated_image(rotation_clockwise_deg)
        if not image_bits:
            return ""
        return ws.get_png_img_html(image_bits)

    def get_png_xml_tuple(self, name, rotation_clockwise_deg=0):
        """Returns an XmlElementTuple for this object."""
        image_bits = self.get_rotated_image(rotation_clockwise_deg)
        return cc_xml.get_xml_blob_tuple(name, image_bits)

    def get_png_data_url(self):
        """Returns a data URL encapsulating the PNG, or ''."""
        if not self.theblob:
            return ""
        return ws.get_png_data_url(self.theblob)

    def is_valid_png(self):
        """Checks to see if the BLOB appears to be a valid PNG."""
        return ws.is_valid_png(self.theblob)


# =============================================================================
# Database lookup
# =============================================================================

def get_current_blob_by_client_info(device, clientpk, era):
    """Returns the current Blob object, or None."""
    serverpk = cc_db.get_current_server_pk_by_client_info(
        Blob.TABLENAME, device, clientpk, era)
    if serverpk is None:
        logger.debug("FAILED TO FIND BLOB: " + str(clientpk))
        return None
    return Blob(serverpk)


def get_contemporaneous_blob_by_client_info(device, clientpk, era,
                                            referrer_added_utc,
                                            referrer_removed_utc):
    """Returns a contemporaneous Blob object, or None.

    Use particularly to look up BLOBs matching old task records.
    """
    serverpk = cc_db.get_contemporaneous_server_pk_by_client_info(
        Blob.TABLENAME, device, clientpk, era,
        referrer_added_utc, referrer_removed_utc)
    if serverpk is None:
        logger.debug("FAILED TO FIND BLOB: " + str(clientpk))
        return None
    return Blob(serverpk)


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_blob(blob):
    """Unit tests for the Blob class."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    from cc_unittest import unit_test_ignore

    # skip Blob.make_tables
    unit_test_ignore("", blob.dump)
    unit_test_ignore("", blob.get_rotated_image)
    unit_test_ignore("", blob.get_rotated_image, rotation_clockwise_deg=90)
    unit_test_ignore("", blob.get_png_img_html)
    unit_test_ignore("", blob.get_png_img_html, rotation_clockwise_deg=90)
    unit_test_ignore("", blob.get_png_xml_tuple, "name")
    unit_test_ignore("", blob.get_png_xml_tuple, "name",
                     rotation_clockwise_deg=90)
    unit_test_ignore("", blob.get_png_data_url)
    unit_test_ignore("", blob.is_valid_png)


def unit_tests():
    """Unit tests for the cc_blob module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    from cc_unittest import unit_test_ignore

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
