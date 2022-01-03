..  docs/source/developer/releasing.rst

..  Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).
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

.. _Inno Setup: http://www.jrsoftware.org/isinfo.php
.. _SignTool: https://docs.microsoft.com/en-gb/windows/win32/seccrypto/signtool

.. _dev_releasing:

Releasing CamCOPS
=================

First build the client for all appropriate platforms (see :ref:`Building the
CamCOPS client <dev_building_client>`).

If the client or server core has changed, remember to ensure appropriate
strings are internationalized (see :ref:`Internationalization
<dev_internationalization>`).

Releasing a new client and server involves the following steps:


Code and documentation
----------------------

- Push to Github (https://github.com/RudolfCardinal/camcops). This also
  automatically updates the docs at https://camcops.readthedocs.io/.


Android client
--------------

Google Play Store settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Developer URL is https://play.google.com/apps/publish
  :menuselection:`--> pick your application
  --> e.g. Release management --> App releases`

- App category: "Utility/other".

- Content rating: by Google's definitions, CamCOPS hits criteria for references
  to illegal drugs (e.g. Deakin1HealthReview, and when strings are available,
  the various drug abuse scoring scales). Did not meet Google Play's criteria
  for sex, violence, etc.

- Note that "Pending publication" means you're waiting for Google Play to sort
  itself out, not that you have to do anything.

- Note re versions:

  - As above, the AndroidManifest.xml has an INTEGER version, so we may as
    well use consecutive numbers. See the release history below.

  The Google Developer site will check the version codes.
  Failed uploads can sometimes block that version number.

- **You upload a new version with** :menuselection:`[Release] Production -->
  Create Release`.

  - You can upload two files with the same name (e.g.
    ``android-build-release-signed.apk``) -- for example, one for 32-bit ARM
    (``armeabi-v7a``) and one for 64-bit ARM (``arm64-v8a``). **But** they
    can't have the same version number. See
    https://developer.android.com/google/play/publishing/multiple-apks.html.
    What Google prefer is an "Android App Bundle". Qt might not support this
    yet:
    https://www.qt.io/blog/2019/06/28/comply-upcoming-requirements-google-play.
    The 64-bit version should have the higher version number. (You upload both
    APK files before saving/reviewing/rolling out the single release.)

  .. todo: look at creating an Android App Bundle for multiple architectures. Does Qt now support this?

- Note also that if you try to install the ``.apk`` directly to a device that's
  had an installation from Google Play Store, you'll get the error
  INSTALL_FAILED_UPDATE_INCOMPATIBLE (I think). Or if you mix debug/release
  versions.

- Finally, note that there can be a significant delay between uploading a new
  release and client devices seeing it on Google Play (or even being able to
  see it at https://play.google.com/store, or via the direct link at
  https://play.google.com/store/apps/details?id=org.camcops.camcops). Perhaps
  10 minutes to the main web site?


Google Play Store release history
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------+---------------------+---------------------+--------------------+---------+---------+
| Google Play   | AndroidManifest.xml | AndroidManifest.xml | To Play Store on   | Minimum | Target  |
| Store release | version code        | name                |                    | Android | Android |
| name          |                     |                     |                    | API     | API     |
+===============+=====================+=====================+====================+=========+=========+
| 2.0.1 (beta)  | 2                   | 2.0.1               | 2017-08-04         | 16      | 23      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.0.4 (beta)  | 3                   | 2.0.4               | 2017-10-22         | 16      | 23      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.2.3 (beta)  | 5                   | 2.2.3               | 2018-06-25         | 16      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.2.4 (beta)  | 6                   | 2.2.4               | 2018-07-18         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.2.6 (beta)  | 7                   | 2.2.6               | 2018-07-31         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.2.7         | 8                   | 2.2.7               | 2018-08-19         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.2.8 to      | N/A, internal only  | N/A, internal only  | N/A, internal only | 23      | 26      |
| 2.3.0         |                     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.3.1         | 9                   | 2.3.1               | 2019-03-24         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.3.2         | 10                  | 2.3.2               | 2019-04-05         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.3.3         | 11                  | 2.3.3               | 2019-06-15         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.3.4         | 12                  | 2.3.4               | 2019-06-21         | 23      | 26      |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.1         | 15 (32-bit ARM);    | 2.4.1               | 2021-02-10         | 23      | 29      |
|               | 16 (64-bit ARM)     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.2         | N/A, identical      | N/A                 | N/A                | 23      | 29      |
|               | to 2.4.3            |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.3         | 17 (32-bit ARM);    | 2.4.3               | 2021-03-30         | 23      | 29      |
|               | 18 (64-bit ARM)     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.4         | N/A, server only    | N/A                 | N/A                | 23      | 29      |
|               |                     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.5         | N/A, macOS only     | N/A                 | N/A                | 23      | 29      |
|               |                     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.6         | 19 (32-bit ARM);    | 2.4.6               | 2021-05-08         | 23      | 29      |
|               | 20 (64-bit ARM)     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.7         | N/A, server only    | N/A                 | N/A                | 23      | 29      |
|               |                     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.8         | 21 (32-bit ARM);    | 2.4.8               | 2021-07-15         | 23      | 29      |
|               | 22 (64-bit ARM)     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.9         | 23 (32-bit ARM);    | 2.4.9               | 2021-08-10         | 23      | 29      |
|               | 24 (64-bit ARM)     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.10        | N/A, server only    | N/A                 | N/A                | 23      | 29      |
|               |                     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+
| 2.4.11        | 25 (32-bit ARM);    | 2.4.11              | 2021-10-08         | 23      | 29      |
|               | 26 (64-bit ARM)     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+

Note: target API of 30 required as of Nov 2021:
https://android-developers.googleblog.com/2020/11/new-android-app-bundle-and-target-api.html


iOS client
----------

To deploy to the Apple Store:

- Up the version numbers in Info.plist
- Build the project first in QtCreator for iOS (arm64) device, release
- Start Xcode
- Load the xcodeproj file for this build into Xcode
- Set the Active scheme to be Any iOS Device (arm64)
- Archive the project (Product -> Archive)
- Open the Organizer (Window -> Organizer)
- Select the Archive and then Distribute App to App Store Connect, accepting all the defaults

The progress bar shows 100% throughout the upload but you can watch the java
process on the Network tab of the Activity Monitor.

Validate App does not run the same set of tests as the App Store does. Even if
after half an hour your package is successfully uploaded to App Store Connect
there may still be problems, of which you will be notified by email several
minutes later.

If you want to debug the .ipa file sent to App Store Connect, choose the
"Export" option. It's a zip file.

The archive process will result in a broken symlink when you next build the project
in QtCreator (error message mkdir failed). You can just delete it.


MacOS client
------------
Build in QtCreator as usual then sign for distribution outside the Apple Store as a dmg file:

    .. code-block:: bash

        codesign --verify --verbose --timestamp --sign "Developer ID Application: UNIVERSITY OF CAMBRIDGE DEPARTMENT OF PSYCHIATRY (XXXXXXXXXX)" --options runtime camcops.app
        /path/to/macos/qt/install/bin/macdeployqt camcops.app -verbose=3 -dmg -no-strip

This should sign with a valid Developer ID certificate, include a secure timestamp and have the hardened runtime enabled.
``macdeployqt`` can also do code signing but doesn't support all the required options, so we do it separately.

To notarize the app with Apple (to prevent malicious software warnings), you
need to know the app-specific password for ``altool`` which was generated at
https://appleid.apple.com/ and then:

    .. code-block:: bash

       xcrun altool -t osx -f camcops.dmg --primary-bundle-id "uk.ac.cam.psychiatry.camcops.dmg" --notarize-app -u <ACCOUNT OWNER APPLE ID>

You will be prompted to enter the app-specific password generated by the account owner.

You can watch the upload progress in the Activity Monitor app (Network tab, look out for ``java`` process after a few minutes).

After the upload has finished, you should see something like:

    .. code-block:: bash

       No errors uploading 'camcops.dmg'
       RequestUUID = 12345678-9abc-def0-1234-56789abcdef0

You can check progress with:

    .. code-block:: bash

       xcrun altool --notarization-info 12345678-9abc-def0-1234-56789abcdef0 -u <ACCOUNT OWNER APPLE ID>

Again use the app-specific password.

If notarization failed, follow the link to the log file in a browser to see what the problem was.

If it passed, run this command:

   .. code-block:: bash

      xcrun stapler staple -v camcops.dmg

``camcops.dmg`` can now be uploaded to the GitHub release assets.


Windows client
--------------

The client will be packaged automatically by the
``camcops_windows_innosetup.iss`` script, which runs under `Inno Setup`_.

To sign the executables you'll need a valid certificate and a tool such as
`SignTool`_. This is distributed as part of the Windows 10 SDK.

Within Inno Setup, select :menuselection:`Tools --> Configure Sign
Tools...`. Add a tool called ``signtool`` with a command to sign the executable.

For example:

``C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe sign /f C:\Users\Me\Downloads\certificate.p12 /tr http://timestamp.sectigo.com /td SHA256 /p "password" $f``

.. warning::

    Under Windows, be particularly careful that both the 32-bit and 64-bit
    versions are fresh. Sometimes :menuselection:`Build --> Clean All` doesn't
    seem to delete all the old executables -- just delete the whole build tree
    manually if need be. Check from the development root directory with
    ``dir camcops.exe /s``.

Upload to https://github.com/RudolfCardinal/camcops/releases with a tag named
``v<VERSION_NUMBER>``.


Server
------

- Create the Debian (``.deb``) and CentOS (``.rpm``) editions using the
  ``server/tools/MAKE_LINUX_PACKAGES.py`` script. Binaries will end up in
  ``server/packagebuild/``. Upload to
  https://github.com/RudolfCardinal/camcops/releases with a tag named
  ``v<VERSION_NUMBER>``.

- The step above will also create a Python distibution in ``server/dist/``.
  (If you want to run that step by itself, use
  ``server/MAKE_PYTHON_PACKAGE.sh``.)
  Upload it to PyPI via ``twine upload dist/camcops_server-VERSION.tar.gz``.
