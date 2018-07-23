..  documentation/source/developer/design_notes.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.


Design notes
============

A few design decisions are documented here. See also:

- :ref:`Patient/subject identification <patient_identification>`

- :ref:`Security design <security_design>`


Client SQLCipher databases
--------------------------

The CamCOPS client uses two databases (typically called `camcops_data.sqlite`
and `camcops_sys.sqlite`), stored in the device’s user-specific private area
(e.g. `~/local/share/camcops under Linux`). Note that some operating systems
(e.g. Android, iOS) are designed for single-user use and don’t have the concept
of a per-user private area. The ‘data’ database holds user data (patients,
patient data) and the ‘sys’ database contains configuration information, stored
strings, and the like. Both are encrypted with AES-256 via SQLCipher. They use
the same passphrase for user convenience, but different encryption keys
[#sqlcipher]_.

The decision to use two databases rather than one is so that, in emergencies,
the ‘data’ database can be processed (viewed, rescued) without the need to
share the ‘sys’ database and its information. It also simplifies the upload
process a little (as the client can simply upload everything from the ‘data’
database and nothing from the ‘sys’ database).

Inline CSS
----------

The server currently provides CSS inline. It could refer to CSS as files, so
that browsers cache them better. However, inline CSS is still required for PDF
creation, and it’s not clear this is an important performance constraint.

SFTP export
-----------

Not necessary, as one can mount an SFTP directory via NFS, then just export as a
plain file.

Anonymisation
-------------

Proper anonymisation is Somebody Else’s Business; CamCOPS supports convenient
export for subsequent anonymisation (see, for example, CRATE;
https://github.com/RudolfCardinal/crate).

BLOB handling
-------------

- It's clearly preferable to have BLOBs in the database (rather than on the
  filesystem), both on the server and the client (server: easier to manage;
  client: within secure encrypted database).

- It's also clearly preferable to have BLOBs in their own table (server:
  doesn't slow down all other tables; client: can upload record-by-record for
  BLOBs and table-by-table for other things).

- Then, regarding storage/access within the client...

  - Writing images to a BLOB is a slow operation: it's the QImage to QByteArray
    conversion (and reverse conversion) that's relatively slow. This slows down
    rotation. The rotation operation itself, on a QImage, is fast.

- Possible client strategies, then:

  - Blob/Field handle QByteArray only; QuImage deals with all the rotation.
    Slow for the client but simple.

  - Blob/Field deal with a combination of a QByteArray (written as PNG to the
    database) and a "rotation" field, and client/server rotate on the fly.

    - Should make the client rotation operation fast.
    - Could store rotation field in the task table, as before, but that is
      particularly inelegant.
    - Could make Blob and/or Field objects image-aware, and have them store
      rotation as an extra field in the blob table.
    - Also allows the potential to preserve more source information, e.g. EXIF,
      because no image manipulations are stored.

    - ... for example:

      .. code-block:: cpp

        new integer field: blob.image_rotation_deg_ccw
        new text field: blob.filetype   // e.g. "png"

        QImage Blob::image() const;  // and cache it
        void Blob::rotateImage(int angle);
        void Blob::setImage(const QImage& image);

        QImage FieldRef::image() const;
        void FieldRef::rotateImage(int angle);

  - Store only final rotated images and do the rotation in the background.

- I tried the Blob method (with rotation as a field in the Blob table) --
  massively faster than before. Makes the difference between dire and
  respectable performance.

Why not code it all in Java?
----------------------------

- The default Java UI is Swing:
  https://www.reddit.com/r/java/comments/383e2c/whats_the_actual_modern_way_to_make_a_gui_with/

- Swing is not portable to iOS:
  http://creamtec.com/products/ajaxswing/solutions/java_swing_ui_on_ipad.html

- JavaFX is another GUI standard, which is newer. It's not supported on all
  operating systems (though it does support iOS):
  http://stackoverflow.com/questions/20860931/is-it-possible-to-run-javafx-applications-on-ios-android-or-windows-phone-8
  https://www.youtube.com/watch?v=a3dAteWr40k&feature=youtu.be

- SQLite would be via JDBC or similar
  http://stackoverflow.com/questions/41233/java-and-sqlite

- Also, http://tech.jonathangardner.net/wiki/Why_Java_Sucks;
  http://steve-yegge.blogspot.com/2006/03/execution-in-kingdom-of-nouns.html

.. rubric:: Footnotes

.. [#sqlcipher] See https://www.zetetic.net/sqlcipher/design/
