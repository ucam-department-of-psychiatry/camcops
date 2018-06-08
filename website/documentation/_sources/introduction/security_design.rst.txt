..  documentation/source/introduction/security_design.rst

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

.. _security_design:

Security design
===============

The CamCOPS security model is multi-layered. It is not enough to have a
“secure” tablet app; there are other things you must do as well.

Summary
-------

- CamCOPS can operate in a :ref:`de-identified mode <patient_identification>`,
  in which case security concerns are lower. What follows assumes the use of
  identifiable, high-risk data.

- CamCOPS is designed to operate offline (i.e. the tablet will hold
  identifiable data for a while), but to move that data securely to the server
  as soon as possible.

- On the tablet, data is always encrypted by CamCOPS. You can also enable
  whole-device encryption on your tablet defice. See :ref:`tablet configuration
  <configure_client>`. Details are below.

- CamCOPS also provides security systems so (a) you can hand a device to a
  subject, without that subject seeing other subjects’ data, and (b) so it can
  be used in an institutional context where administrators apply security
  policies that individual clinicians can’t alter.

- The link and the server also need to be secure. See below.

Tablet security
---------------

To meet NHS mobile data protection standards [#nhsscotmobiledatasec]_, a tablet
holding “sensitive information” of a significant degree of sensitivity
requires:

- whole-disk encryption
- a strong password

For relevant CamCOPS platforms:

- All CamCOPS clients apply AES-256 [#aes256]_ to all data. Additionally:

- Android 3+ devices allow on-device encryption (encrypting applications’ data
  area) with a passcode [#androidencryption]_.

- Apple iPads and related iOS devices invoke encryption when a passcode is
  entered [#iosencryption]_.

- Both these platforms have sandboxes to prevent one application seeing
  another’s data [#androidsandbox]_ [#iossandbox]_.

You should enable tablet encryption, choosing a strong password for your
tablet; see :ref:`tablet configuration <configure_client>`.

CamCOPS app security
--------------------

Basics
~~~~~~

- The CamCOPS application has three security modes: LOCKED, UNLOCKED, and
  PRIVILEGED.

- In the LOCKED mode, the application is locked to a single patient and can
  only view or add records pertaining to that patient, or anonymous tasks. This
  mode is designed for handing the device to a patient.

- In the UNLOCKED mode, all data may be viewed and edited, and data may be
  uploaded to the server. This mode is designed for use by clinicians. The user
  may change the app password that unlocks the app.

- PRIVILEGED mode is designed for administrator use. In PRIVILEGED mode,
  features such as the following are unlocked:

  - configuring the link to a server, and registering the device with a server;

  - viewing local data as SQL, and (if the device permits) exporting the local
    database to an SQL file in an insecure storage area (e.g. an SD card).

- The application starts in the LOCKED mode. (Otherwise, someone handed a
  tablet with CamCOPS running in the LOCKED mode could restart the app and
  thereby gain UNLOCKED access.)

- We envisage that in typical NHS use, an administrator would set up CamCOPS to
  point to the appropriate NHS server and then give the clinician(s) the app
  (unlock) password but not the privileged-mode password.

Internally in the tablet app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- CamCOPS stores all its data in `SQLite <https://www.sqlite.org/index.html>`_
  databases, encrypted at all times via AES-256 by `SQLCipher
  <https://www.zetetic.net/sqlcipher/>`_.

- The app never sends patient-identifiable data to the tablet’s logging stream,
  so a malicious user who plugs the tablet into a debugging computer (e.g.: USB
  debugging enabled on tablet; run `adb logcat` on the computer) won’t see
  patient-identifiable data that way.

- The CamCOPS app stores its app (unlock) and privileged-mode codes using
  bcrypt hashes (themselves stored in the AES-256-encrypted SQLCipher
  database). The passwords themselves are not stored.

- The administrator may choose whether the CamCOPS app stores the user’s server
  password:

  - using reversible encryption (more convenient but fractionally less secure;
    the password would be vulnerable to a skilled attacker with both the
    tablet OS’s unlock code and the CamCOPS password)

  - not at all (more secure, but requires the user to enter it at each upload).

- The app sets `android:allowBackup="false"`, thus opting out of the Android
  backup-and-restore infrastructure [#androidbackuprestore]_ (otherwise, access
  to the CamCOPS database data would be possible for someone with the tablet
  password [#androiddatawithoutroot]_, though this would still be AES-256
  encrypted).

Link security
-------------

- The link to the server is constrained to use HTTPS and therefore link
  encryption.

- By default, the app will insist on a validated SSL certificate (though this
  can be turned off by the administrator for low-security environments using a
  self-signed [“snake oil”] SSL certificate).

- Privileged-mode access is required to change the server; therefore, from a
  non-privileged clinician’s point of view, the device is locked to a single
  server.

Server security
---------------

Communication between tablet and server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The server requires username/password identification (or subsequent secure
  session token authentication) before it will accept an upload.

- The server requires that the device (identified by a unique device number) be
  registered before it will accept an upload.

- Users require an additional permission, set on the server, before they can
  register a device. (We envisage that in practice, device registration would
  be managed by an administrator for high-security environments.)

- The server only accepts incoming data; it will not provide data to a device.
  (Therefore, even a hand-crafted application masquerading as an instance of
  CamCOPS and in possession of a valid username, password, and device ID cannot
  download any data.)

- The server will not add new fields or tables based on the claims of the
  uploading agent.

- The server takes standard precautions against SQL injection [#sqlinjection]_.

Communication between user and server using the web front end
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The web front end should be constrained to HTTPS to ensure link security.

- Access is governed by username/password pairs.

Internally in the server
~~~~~~~~~~~~~~~~~~~~~~~~

- The server should be secured in standard fashion. These are matters outside
  CamCOPS. Standard security considerations include:

  - physical access
  - visibility on public networks (preferably not!)
  - firewall configuration
  - SSH access
  - inappropriate provision of information by a misconfigured web server
  - database security
  - security of physical backups

- The server stores CamCOPS passwords using bcrypt hashes.

Security against data loss
--------------------------

- Crashes in the CamCOPS application should not (and in our experience do not)
  affect data integrity, as the SQLite backend is designed to cope with this
  [#sqliterobust].

“Analytics” security
--------------------

CamCOPS doesn’t send a copy of your data back to its base. Your data is private
to you.

Audit trails
------------

- Tablet-side audit trails are minimal, but the application time-stamps all
  tasks at their creation, and time-stamps the last modification to any record,
  in addition to collecting information relevant to the time it takes to
  complete each task.

- The CamCOPS application maintains a number of task-specific tables (e.g.
  `patient`, `phq9`, `gad7`). It uploads table-wise (and the entire upload
  process is atomic). To each record, the server adds fields allowing an audit
  trail; see table structure. When a record is modified or deleted, the old
  versions are kept.

- The server’s tables therefore contain a snapshot of each device’s current
  state, and a complete audit trail, whose granularity is the frequency of
  uploads from a particular device.

- Read access requests to the server (via the web viewer) are also audited, as
  are command-line CamCOPS operations.

Legacy security
---------------

The code is open-source, and should only include content from
tasks/questionnaires that are in the public domain or where permission exists
to use the task in perpetuity.

Black Hat’s options
-------------------

What would it take to steal CamCOPS data?

- A non-technical attack [#socialattack]_.

- Steal a tablet, the tablet’s password, and its CamCOPS app password together;
  this would allow records to be viewed on that device.

- Steal a tablet, the tablet’s password, its CamCOPS app password, and its
  CamCOPS privileged-mode password together; this would allow records to be
  sent to a dark server of the attacker’s choosing.

- Steal a tablet that hasn’t been properly secured with a device password; this
  would eliminate the requirement for the tablet’s password from all of the
  above.

- Break into the server and gain direct access to its database. This emphasizes
  the importance of securing the server.

These methods of attack sound plausible but should not be possible:

- Steal a tablet and the tablet’s password, root the device, and access the
  database directly; then you only have to break AES-256 to decrypt the 
  database [#aes256]_. (Hint: that’s hard.)

- Steal a tablet and the tablet’s password, download the open-source CamCOPS
  application, modify it, install it over the existing application without
  deleting the application data, and use the modified application to export
  data. Why not? (1) Apps installed on both Android and iOS tablets are
  digitally signed, and an app attempting to install with a different digital
  signature will not be accepted as a replacement for the original, and
  therefore will not gain access to the original app’s data. (2) The CamCOPS
  database is still AES-256-encrypted.

- Steal an Android tablet (but not the tablet password), modify the operating
  system, use it to read the data. Why not? (1) This should not work as long as
  filesystem encryption is enabled; the necessary keys are not stored on the
  device [#androidfilesystemencryption]_. (2) The CamCOPS database is still
  AES-256-encrypted.

Match to NHS security requirements
----------------------------------

Mobile device
~~~~~~~~~~~~~

- I’ve not found an England-wide NHS mobile security standard, but the Scottish
  one is this: [#nhsscotmobiledatasec]_.

- That standard classifies the data using a traffic-light system. CamCOPS data
  could include patient-identifiable information and information on patients’
  mental states, so it would definitely not be GREEN. It might be AMBER
  (causing distress/significant embarrassment if lost; low risk to a person’s
  safety if lost); it might be RED (risk of harm to mental health if lost;
  causing significant distress if lost; constitute a substantial breach of
  privacy; etc.).

- The standard specifies a minimum password strength.

  - For tablet passwords: this is primarily a device issue and both Android and
    iOS devices can be configured for alphanumeric passwords, not just 4-digit
    PINs.

  - CamCOPS doesn't restrict password type for its app passwords; ensure that
    your users choose a sufficiently secure password [#passwordstrength]_.

- AMBER and RED levels require whole-disk encryption for NHS-owned devices.

- Personally-owned devices would be discouraged or prohibited for AMBER and RED
  information, since security is difficult to enforce. Specifically, they are
  prohibited for RED data, and may be considered for AMBER data but only if set
  up so that no data is stored on the device itself and a remote wipe is
  possible for residual data (which would negate the “transiently offline”
  capabilities of CamCOPS). Therefore, by these standards only NHS-owned
  official devices should be considered for CamCOPS.

  - Note, however, that *all* CamCOPS information is encrypted, even if
    CamCOPS is installed on an unencrypted device.

- Removable media for AMBER or RED information must be encrypted. In practice,
  CamCOPS’s function to export to an SD card would only be accessible to
  administrative staff.

- So the minimum for each tablet is likely to be:

  - mandate a decent password on iPads or Android tablets, and for CamCOPS;

  - mandate the whole-disk encryption option on Android tablets;

  - perhaps ensure that clinicians don’t have access to the Privileged mode (by
    having an administrator configure and password-protect each device – this
    takes ~30 seconds).

Server
~~~~~~

- Full security is required on the server.

- In particular, consideration should be given to restricting access to devices
  from within an appropriate domain (e.g. within a given NHS Trust or
  university).


.. rubric:: Footnotes

.. [#nhsscotmobiledatasec]
    NHS Scotland: CEL 25 (2012):
    http://www.sehd.scot.nhs.uk/mels/CEL2012_25.pdf

.. [#aes256]
    https://en.wikipedia.org/wiki/Advanced_Encryption_Standard

.. [#androidencryption]
    http://security.stackexchange.com/questions/10529/are-there-actually-any-advantages-to-android-full-disk-encryption;
    http://source.android.com/tech/encryption/android_crypto_implementation.html;
    http://support.google.com/android/bin/answer.py?hl=en&answer=1663755

.. [#iosencryption]
    http://www.macworld.com/article/1160313/iPad_security.html;
    http://images.apple.com/ipad/business/docs/iOS_Security_May12.pdf

.. [#androidsandbox]
    http://developer.android.com/guide/topics/security/permissions.html

.. [#iossandbox]
    http://images.apple.com/ipad/business/docs/iOS_Security_May12.pdf

.. [#androidbackuprestore]
    http://developer.android.com/guide/topics/manifest/application-element.html#allowbackup

.. [#androiddatawithoutroot]
    https://blog.shvetsov.com/2013/02/access-android-app-data-without-root.html?m=1

.. [#sqlinjection]
    xkcd *Exploits of a Mom:* https://xkcd.com/327/

.. [#sqliterobust]
    Testing: http://www.sqlite.org/testing.html.
    Atomic COMMIT: http://www.sqlite.org/atomiccommit.html

.. [#socialattack]
    xkcd *Security:* https://xkcd.com/538/

.. [#passwordstrength]
    xkcd *Password Strength:* https://xkcd.com/936/

.. [#androidfilesystemencryption]
    http://source.android.com/devices/tech/security/
