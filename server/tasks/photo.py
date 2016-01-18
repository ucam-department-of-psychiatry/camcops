#!/usr/bin/env python3
# photo.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

import pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from cc_modules.cc_html import (
    answer,
    tr_qa,
)
from cc_modules.cc_task import Ancillary, Task


# =============================================================================
# Photo
# =============================================================================

class Photo(Task):
    tablename = "photo"
    shortname = "Photo"
    longname = "Photograph"
    fieldspecs = [
        dict(name="description", cctype="TEXT",
             comment="Description of the photograph"),
        dict(name="photo_blobid", cctype="INT",
             comment="ID of the BLOB (foreign key to blobs.id, given "
             "matching device and current/frozen record status)"),
        dict(name="rotation", cctype="INT",
             comment="Rotation (clockwise, in degrees) to be applied for "
             "viewing"),
    ]
    has_clinician = True
    pngblob_name_idfield_rotationfield_list = [
        ("photo_blob", "photo_blobid", "rotation")
    ]

    def is_complete(self):
        return (self.photo_blobid is not None)

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        if not self.description:
            return []
        return [{"content": self.description}]

    def get_task_html(self):
        return """
            <table class="taskdetail">
                <tr class="subheading"><td>Description</td></tr>
                <tr><td>{}</td></tr>
                <tr class="subheading"><td>Photo</td></tr>
                <tr><td>{}</td></tr>
            </table>
        """.format(
            answer(ws.webify(self.description), default="(No description)",
                   default_for_blank_strings=True),
            # ... xhtml2pdf crashes if the contents are empty...
            self.get_blob_png_html(self.photo_blobid, self.rotation)
        )


# =============================================================================
# PhotoSequence
# =============================================================================

class PhotoSequence_SinglePhoto(Ancillary):
    tablename = "photosequence_photos"
    fkname = "photosequence_id"
    fieldspecs = [
        dict(name="photosequence_id", notnull=True, cctype="INT",
             comment="FK to photosequence"),
        dict(name="seqnum", notnull=True, cctype="INT",
             comment="Sequence number of this photo"),
        dict(name="description", cctype="TEXT",
             comment="Description of the photograph"),
        dict(name="photo_blobid", cctype="INT",
             comment="ID of the BLOB (foreign key to blobs.id, given "
             "matching device and current/frozen record status)"),
        dict(name="rotation", cctype="INT",
             comment="Rotation (clockwise, in degrees) to be applied for "
             "viewing"),
    ]
    sortfield = "seqnum"
    pngblob_name_idfield_rotationfield_list = [
        ("photo_blob", "photo_blobid", "rotation")
    ]

    def get_html_table_rows(self):
        return """
            <tr class="subheading"><td>Photo {}: <b>{}</b></td></tr>
            <tr><td>{}</td></tr>
        """.format(
            self.seqnum + 1, ws.webify(self.description),
            self.get_blob_png_html(),
        )

    def get_blob(self):
        return self.get_blob_by_id(self.photo_blobid)

    def get_blob_png_html(self):
        if self.photo_blobid is None:
            return "<i>(No picture)</i>"
        blob = self.get_blob()
        if blob is None:
            return "<i>(Missing picture)</i>"
        return blob.get_png_img_html(self.rotation)


class PhotoSequence(Task):
    tablename = "photosequence"
    shortname = "PhotoSequence"
    longname = "Photograph sequence"
    fieldspecs = [
        dict(name="sequence_description", cctype="TEXT",
             comment="Description of the sequence of photographs"),
    ]
    has_clinician = True
    dependent_classes = [PhotoSequence_SinglePhoto]

    def get_clinical_text(self):
        photos = self.get_photos()
        d = [{"content": self.sequence_description}]
        for p in photos:
            d.append({"content": p.description})
        return d

    def get_num_photos(self):
        return self.get_ancillary_item_count(PhotoSequence_SinglePhoto)

    def get_photos(self):
        return self.get_ancillary_items(PhotoSequence_SinglePhoto)

    def is_complete(self):
        return bool(self.sequence_description and self.get_num_photos() > 0)

    def get_task_html(self):
        photos = self.get_photos()
        html = """
            <div class="summary">
                <table class="summary">
                    {is_complete}
                    {num_photos}
                    {description}
                </table>
            </div>
            <table class="taskdetail">
        """.format(
            is_complete=self.get_is_complete_tr(),
            num_photos=tr_qa("Number of photos", len(photos)),
            description=tr_qa("Description", self.sequence_description),
        )
        for p in photos:
            html += p.get_html_table_rows()
        html += """
            </table>
        """
        return html
