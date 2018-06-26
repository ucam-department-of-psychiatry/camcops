..  documentation/source/client/client_installation.rst

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

Installing and configuring the client
=====================================

Hardware and operating system requirements
------------------------------------------

See :ref:`hardware_requirements_client`.


.. _client_installation:

CamCOPS client installation
---------------------------

Android
~~~~~~~

Install the Android app directly from the Google Play Store:

- https://play.google.com/store/apps/details?id=org.camcops.camcops

Android: manual installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**This method is now deprecated. Use the Google Play Store method instead.**

Manual installation of an Android package is possible like this:

#. Ensure your Android device permits the installation of third-party apps:
   e.g. :menuselection:`Settings --> Security --> Unknown sources (Allow
   installation of apps from unknown sources)`.

#. Download and install the CamCOPS client (see :ref:`download <download>`) as
   an .APK (Android Package Kit) file.

iOS
~~~

This is currently suboptimal because CamCOPS is not yet in the Apple App Store,
and iOS makes it almost impossible to install third-party apps via other
routes. The only way is via an Individual or Enterprise Developer Account.

Apple operate a restricted distribution system for iOS. Apps available via the
App Store are publicly available and vetted by Apple. In addition, registered
developers can install apps on their test hardware, and can also produce
downloadable .IPA files. These IPA files are either locked to a specific subset
of tablets (via a development certificate) or installable on any tablet (via an
Enterprise distribution certificate); however, making Enterprise apps available
outside the company concerned would be a breach of contract (specifically, of
the iOS Developer Program Enterprise License Agreement). So the only way for
other users to use source code is to (a) download the source code, register as
Apple developers, and install the app to their own devices or distribute them
within their own organization as above; or (b) wait for the App Store version.

.. todo:: Submit CamCOPS to Apple App Store.

Windows
~~~~~~~

.. todo:: Package CamCOPS client for easier Windows distribution.

Linux
~~~~~

.. todo:: Package CamCOPS client for easier Linux distribution.


.. _configure_client:


Terminology: usernames and passwords in CamCOPS
-----------------------------------------------

.. note::
    We will often refer to the client as a “tablet”, because it often is, but
    it might equally be your laptop or desktop running Windows/Linux/OS X.

In a low-security environment, you’ll be your own administrator. In a
high-security environment, we’ll distinguish the user (“clinician”) from the
technical security person (“administrator”).

CamCOPS uses the following usernames and passwords:

- **TABLET PASSWORD.** Your tablet will need a password to unlock it. This is
  nothing to do with CamCOPS.

- **CAMCOPS APP PASSWORD.** The CamCOPS application will also need a password
  to unlock it. Without this, no access to CamCOPS encrypted data is possible.

- **CAMCOPS PRIVILEGED-MODE PASSWORD.** This password unlocks the deep dark
  secrets of the app. Whoever has this can, for example, change the server that
  the app sends its data to. In a high-security environment, this password is
  typically known to the administrator, but not the clinician.

- **CAMCOPS SERVER USERNAME** and **CAMCOPS SERVER PASSWORD.** These
  authenticate a user (who might be a clinician or an administrator) to the web
  interface, hosted by the CamCOPS server. You will use this username/password
  combination to (a) log in to the web site, and (b) upload data from your
  tablet, or register the tablet with the server. In more detail:

  - The CamCOPS app needs to know a username/password combination to register
    with a new server. (Registration is typically done by the administrator
    using their username/password.)

  - The CamCOPS app needs to know a username/password combination to upload
    data to the server. (Uploading is typically done by the clinician using
    their username/password. The app may or may not be allowed to store the
    password — that’s a local security policy decision — but it will store the
    username.)

  - You will type in your username and password to access the CamCOPS web
    viewer. This interface is used to view tasks that have been uploaded from
    tablets. Administrators can also use this interface to create or edit
    authorized users.

Configuring your tablet before using CamCOPS
--------------------------------------------

This section has nothing specifically to do with CamCOPS, but describes general
good security measures to take (or measures that your institution may oblige
you to take) with any mobile device holding sensitive information.

iPad
~~~~

- Set up appropriate security on your tablet. For a research environment with
  no patient-identifiable data, this may involve no work. But for a secure
  environment:

  - :menuselection:`Home --> Settings  -->  General --> Passcode Lock`

    - :menuselection:`... --> Simple passcode = OFF`. Why? Because 4-digit
      passcodes are weak; use a strong password [#passwordstrength]_, and don’t
      forget it! We’ll call this the TABLET PASSWORD.

    - :menuselection:`... --> Turn passcode on`

    - :menuselection:`... --> Require passcode = immediately`

    - :menuselection:`... --> Erase data = ON` (which will erase all data on
      the iPad after 10 failed passcode attempts).

- Setting a passcode lock automatically encrypts data on the iPad
  [#iossetpasswordencryptsdata]_ [#ioskeychainvulnerable]_.

- Install CamCOPS; see :ref:`above <client_installation>`.

Android
~~~~~~~

- Set up appropriate security on your tablet. For a research environment with
  no patient-identifiable data, this may involve no work. But for a secure
  environment:

  - Plug in the tablet; charge its battery fully. (Encryption takes a while and
    requires a charged tablet that’s plugged in.)

  - :menuselection:`Settings --> Security --> Screen lock --> Password`

  - Enter a strong password [#passwordstrength]_, and don’t forget it! We’ll
    call this the TABLET PASSWORD.

  - :menuselection:`Settings --> Security --> Encryption --> Encrypt tablet -->
    Encrypt tablet` ... which may take a while.

- Install CamCOPS; see :ref:`above <client_installation>`.


Configuring CamCOPS before using it
-----------------------------------

**Using the CamCOPS server’s web interface, the administrator should:**

- Create a username and password for the new user.

- Add that user to one or more :ref:`groups <groups>`.

- For each group, edit the user’s group permissions. Normal settings:

  - *Permitted to upload from a tablet/device?* Almost certainly YES.

  - *Permitted to register tablet/client devices?* May be NO in very high
    security environments (in which case the administrator will have to use the
    tablet to register it on behalf of the final user); YES is more convenient.

  - *May view (browse) records from all patients when no patient filter set?*
    Almost certainly NO, for confidentiality reasons.

  - *May perform bulk data dumps?* YES for researchers needing this function;
    otherwise NO.

  - *May run reports?* Reports cover a mixture of administrative and
    patient-finding functions. If in doubt, choose NO.

  - *May add special notes to tasks?* Likely to be YES for senior users.

  - *User is a privileged group administrator for this group?* Usually NO.
    If you say yes, the user will be able to create new users and manage this
    group.

**On the tablet, the administrator should:**

#. Touch the padlock (top right) to unlock. (The first time CamCOPS is run,
   there will be no lock passwords; you need to set them, as below.)

#. :menuselection:`Settings --> Set privileged mode (for items marked †)` (the
   icon at the top right will now show a golden pair of padlocks).

#. :menuselection:`Settings --> (†) Change privileged-mode password.` Enter a
   password for this tablet; do NOT tell the clinician; keep it in your
   Administrator’s Safe.

#. :menuselection:`Settings --> Change app password.` Enter a starting password
   for the clinician (their CAMCOPS APP PASSWORD); tell the clinician what this
   is.

#. :menuselection:`Settings --> (†) Configure server settings`.

   - Set the server hostname

   - Set the server path

   - Ensure “Validate SSL certificates?” is set to “Yes”.

   - Choose the “Store user’s server password?” option. Your users will
     probably thank you for choosing “Yes”. The especially security-conscious
     may want “No”. (This setting determines whether the tablet will store an
     encrypted version of the user’s password; it allows the user to unlock
     CamCOPS with their CamCOPS app password, but then not to have to re-enter
     their CamCOPS server password each time they upload.)

   - Other values can typically be left as the default.

   - Save those settings.

#. Assuming you will not allow the user to register devices with the server,
   you’ll have to do it yourself:

   #. :menuselection:`Settings --> User settings --> Username on server.`
      Enter your administrative CAMCOPS SERVER USERNAME. (Don’t enter a
      password here, even if you allow users to store their password; you don’t
      want your administrator’s password saved.)

   #. Save those settings.

   #. :menuselection:`Settings --> (†) Register this device with the server.`
      (It will ask for your administrative CAMCOPS SERVER PASSWORD, and then
      should initiate communication with the server, and succeed). Until
      registration has succeeded, the app will not be able to upload.

   #. Optionally, to be nice to the user: :menuselection:`Settings --> User
      settings --> Username`; enter the clinician’s CAMCOPS SERVER USERNAME;
      save those settings.

#. Ensure you haven’t accidentally stored your administrative password in the
   app (:menuselection:`Settings --> User settings`). If you followed the
   instructions above, you won’t have done.

#. Touch the padlock until it shows the red, locked icon. You can now give the
   tablet to your clinician.

**The clinician should then:**

- If the whole tablet is locked, unlock it with the TABLET PASSWORD.

- Touch the padlock to unlock. You will need your CAMCOPS APP PASSWORD,
  supplied to you by your administrator.

- :menuselection:`Settings --> Change app password.` Change the password to a
  strong password that you like [#passwordstrength]_. Remember it.

- :menuselection:`Settings --> Intellectual property (IP) permissions.`
  Answer all the questions honestly and save your changes.

- :menuselection:`Settings --> User settings.` Set these:

  - Device friendly name: e.g. “Joe Smith’s LPS iPad”.

  - Username on server: your CAMCOPS SERVER USERNAME, supplied to you by your
    administrator.

  - *If your administrator has allowed you to store your server password:*
    Password on server: your CAMCOPS SERVER PASSWORD, supplied to you by your
    administrator.

  - Default clinician’s specialty, name, professional registration, post,
    contact details: set values that you would typically enter in patients’
    notes. For example, a UK doctor might have: specialty = "Liaison
    psychiatry"; name = "Dr John Doe"; professional registration = "GMC#
    123456"; post = "Consultant"; contact details = "extension 1234; bleep
    5678".

.. note::

    The clinician’s name that you enter will be automatically processed into
    prefix/forename/surname components for HL-7 diagnosis (DG1) segments, if
    you use a recognized format. Recognized formats include, for example,
    Prefix Forename Surname (where prefix is Dr, Prof, Miss, Mrs, Ms, Mr, Sr,
    with or without full stops); Forename Surname; Surname, Forename. If the
    software doesn’t recognize the format, it will put the whole name verbatim
    into the surname field for DG-1 codes.

Good to go! See :ref:`using the tablet app <client_using>`.

Other CamCOPS app settings
--------------------------

Questionnaire font size
~~~~~~~~~~~~~~~~~~~~~~~

:menuselection:`Settings --> Questionnaire font size.` Choose a font size that
you like.

Upload after each task is complete?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:menuselection:`Settings --> User settings --> Offer to upload every time a
task is edited?`


Other tablet settings that can affect CamCOPS
---------------------------------------------

Turn off auditory interruptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If beeps and buzzes from other apps would interfere with your use of CamCOPS,
disable them.

- For Android: :menuselection:`Android Settings --> Sound --> Volume`; then
  turn off things like “Ringtone” (for phones), “Notifications”, and “System”.

- For iOS: :menuselection:`iOS Settings --> Notifications`, and turn “Sounds”
  off.


.. rubric:: Footnotes

.. [#passwordstrength]
    xkcd *Password Strength:* http://xkcd.com/936/.

.. [#iossetpasswordencryptsdata]
    http://support.apple.com/kb/ht4175

.. [#ioskeychainvulnerable]
    The iPad's keychain is still vulnerable to attack: see summary at
    http://www.maravis.com/ios-device-encryption-not-effective/, or PDF at
    http://www.maravis.com/blog/wp-content/uploads/iOS-device-encryption-security.pdf.
    However, CamCOPS does not store its passwords in the keychain, and app
    storage is separate from the keychain.
