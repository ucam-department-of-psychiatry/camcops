#!/usr/bin/env python
# camcops_server/tasks/photo.py

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

from typing import List, Optional

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_blob import Blob
from ..cc_modules.cc_html import answer, tr_qa
from ..cc_modules.cc_task import Ancillary, CtvInfo, CTV_INCOMPLETE, Task


# =============================================================================
# Photo
# =============================================================================

class Photo(Task):
    tablename = "photo"
    shortname = "Photo"
    longname = "Photograph"
    has_clinician = True

    fieldspecs = [
        dict(name="description", cctype="TEXT",
             comment="Description of the photograph"),
        dict(name="photo_blobid", cctype="INT",
             comment="ID of the BLOB (foreign key to blobs.id, given "
             "matching device and current/frozen record status)"),
        # IGNORED. REMOVE WHEN ALL PRE-2.0.0 TABLETS GONE:
        dict(name="rotation", cctype="INT",  # *** DEFUNCT as of v2.0.0  # noqa
             comment="Rotation (clockwise, in degrees) to be applied for "
                     "viewing"),
    ]
    blob_name_idfield_list = [
        ("photo_blob", "photo_blobid")
    ]

    def is_complete(self) -> bool:
        return self.photo_blobid is not None

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        if not self.description:
            return []
        return [CtvInfo(content=self.description)]

    def get_task_html(self) -> str:
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
            self.get_blob_img_html(self.photo_blobid)
        )


# =============================================================================
# PhotoSequence
# =============================================================================

class PhotoSequenceSinglePhoto(Ancillary):
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
        # IGNORED. REMOVE WHEN ALL PRE-2.0.0 TABLETS GONE:
        dict(name="rotation", cctype="INT",  # *** DEFUNCT as of v2.0.0  # noqa
             comment="Rotation (clockwise, in degrees) to be applied for "
                     "viewing"),
    ]
    sortfield = "seqnum"
    blob_name_idfield_list = [
        ("photo_blob", "photo_blobid")
    ]

    def get_html_table_rows(self) -> str:
        return """
            <tr class="subheading"><td>Photo {}: <b>{}</b></td></tr>
            <tr><td>{}</td></tr>
        """.format(
            self.seqnum + 1, ws.webify(self.description),
            self.get_blob_html(),
        )

    def get_blob(self) -> Optional[Blob]:
        return self.get_blob_by_id(self.photo_blobid)

    def get_blob_html(self) -> str:
        if self.photo_blobid is None:
            return "<i>(No picture)</i>"
        blob = self.get_blob()
        if blob is None:
            return "<i>(Missing picture)</i>"
        return blob.get_img_html()


class PhotoSequence(Task):
    tablename = "photosequence"
    shortname = "PhotoSequence"
    longname = "Photograph sequence"
    has_clinician = True

    fieldspecs = [
        dict(name="sequence_description", cctype="TEXT",
             comment="Description of the sequence of photographs"),
    ]
    dependent_classes = [PhotoSequenceSinglePhoto]

    def get_clinical_text(self) -> List[CtvInfo]:
        photos = self.get_photos()
        infolist = [CtvInfo(content=self.sequence_description)]
        for p in photos:
            infolist.append(CtvInfo(content=p.description))
        return infolist

    def get_num_photos(self) -> int:
        return self.get_ancillary_item_count(PhotoSequenceSinglePhoto)

    def get_photos(self) -> List[PhotoSequenceSinglePhoto]:
        return self.get_ancillary_items(PhotoSequenceSinglePhoto)

    def is_complete(self) -> bool:
        return bool(self.sequence_description and self.get_num_photos() > 0)

    def get_task_html(self) -> str:
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
