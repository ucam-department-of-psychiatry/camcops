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

The ``tools/release_new_version.py`` script will do most of the work required to
create a new release of the CamCOPS client and/or server. To see the options
available to this script, run it without any arguments. The script will advise
you on what needs to change before it can build the new release. To create new
versions of the CamCOPS client, the script needs to be run on:

* Linux (for Linux and 32/64-bit Android builds)
* Windows (for Windows 32/64-bit Windows builds)
* MacOS (for MacOS and iOS builds)

The builds are created under ``tablet_qt/build/<version>/qt_<qt_version>_<platform>``

When a git tag with a new release version number (e.g. v2.4.23) is pushed to
GitHub, an automated workflow will create the new release with the server DEB
and RPM files as artifacts. The client binaries can then be uploaded manually as
artifacts to the same release.

Code and documentation
----------------------

When the GitHub repository
https://github.com/ucam-department-of-psychiatry/camcops is updated with a new
version tag, the **stable** version of the docs at https://camcops.readthedocs.io/
is updated automatically. Pushing code to the master branch will update the
**latest** version of the docs.


Android client
--------------

The ``tools/release_new_version.py`` script will create and sign the Android APK
files and place them in
``tablet_qt/build/<version>/qt_<qt_version>_<platform>/android-build/build/outputs/apk/release``.


Google Play Store settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Developer URL is https://play.google.com/console/developers

- Content rating: by Google's definitions, CamCOPS hits criteria for references
  to illegal drugs (e.g. Deakin1HealthReview, and when strings are available,
  the various drug abuse scoring scales). Did not meet Google Play's criteria
  for sex, violence, etc.

- Note that "Pending publication" means you're waiting for Google Play to sort
  itself out, not that you have to do anything.

- Note re versions:

  The Google Developer site will check the version codes.

- **You upload a new version with** :menuselection:`--> CamCOPS -->
  Test and release  --> Production --> Create new release`.

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

  - If an upload fails validation, you should be able to delete the APK file from
    :menuselection:`--> CamCOPS -> Test and release --> Production --> Latest releases and bundles`
    and re-upload a fixed APK with the same version code.

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

The minimum and target SDK versions are specified in the ``camcops.pro`` project
file. See ``ANDROID_MIN_SDK_VERSION`` and ``ANDROID_TARGET_SDK_VERSION``.

.. csv-table::
   :file: play_store_release_history.csv
   :header-rows: 1

iOS client
----------

To deploy to the Apple Store:

- Start Xcode with ``open camcops.xcodeproj`` from ``tablet_qt/build/<version>/qt_<qt_version>_ios_armv8_64``.
  This will ensure any of your environment variables are available to Xcode.
- Set the Active scheme to be Any iOS Device (arm64)
- Archive the project (Product -> Archive)
- Select the Archive and then Distribute App to App Store Connect, accepting all the defaults

The progress bar may show 100% throughout the upload but you can watch the java
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

The ``tools/release_new_version.py`` script will create ``camcops.dmg`` under
``tablet_qt/build\<version>/qt_<qt_version>_macos_x86_64`` and this can be
uploaded to the GitHub release assets.


Windows client
--------------

The ``tools/release_new_version.py`` script will package the client via `Inno Setup`_.

To sign the installer executable you'll need a valid certificate and
`SignTool`_.

Upload the executable from the ``distributables`` directory to the
GitHub release assets.



Server
------

The ``tools/release_new_version.py`` script will upload the new version of the
CamCOPS Server to PyPI. the DEB and RPM files are created automatically by the
GitHub release workflow when the version tag is pushed.
