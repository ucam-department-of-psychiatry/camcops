..  documentation/source/misc/download.rst

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

.. _download:

Downloading CamCOPS
===================

The Android app is at

- https://play.google.com/store/apps/details?id=org.camcops.camcops

Other client downloads, and server distributions, are at

- http://www.camcops.org/download/

The source code is at

- https://github.com/RudolfCardinal/CamCOPS


Android notes
~~~~~~~~~~~~~

- You are probably best off installing Android packages from the Google Play
  Store, because that's simpler. However, you can also install a ``.apk``
  (Android package file) directly.

  - To install an Android application from an APK file, you need to permit
    this: e.g. :menuselection:`Settings --> Security --> Unknown sources (Allow
    installation of apps from unknown sources)`.

  - Download ``camcops_VERSION.apk`` and install it.

  - In doing so, please be aware of the following browser bug:

    - The default Android browser (“Browser”) may fail to download from
      password-protected web sites (e.g. restricted CamCOPS downloads).
      This is a known bug in Android [#androidbug]_.

    - Download using another browser such as Chrome [#chrome]_ instead. Then
      run File Manager (or similar), find the APK that you just downloaded
      (try `/sdcard/Download`), and install it (e.g. “Complete action using:
      Package Installer”).


iOS notes
~~~~~~~~~

- Apple operate a restricted distribution system for iOS. Apps available via
  the App Store are publicly available and vetted by Apple. In addition,
  registered developers can install apps on their test hardware, and can also
  produce downloadable ``.ipa`` files. These IPA files are either locked to a
  specific subset of tablets (via a development certificate) or installable on
  any tablet (via an Enterprise distribution certificate); however, making
  Enterprise apps available outside the company concerned would be a breach of
  contract (specifically, of the iOS Developer Program Enterprise License
  Agreement). So: a restricted CPFT distribution will be available as
  ``camcops_VERSION_cpft.ipa`` but all other users will either have to (a)
  download the source code, register as Apple developers, and install the app
  to their own devices or distribute them within their own organization as
  above; or (b) wait for the App Store version.

Server notes
~~~~~~~~~~~~

- You can install the CamCOPS server Python package with:

    .. code-block:: bash

        pip install camcops-server

- Downloads are also available as ``.deb`` packages for Debian Linux (e.g.
  Ubuntu) and ``.rpm`` packages for e.g. CentOS.


Pending
~~~~~~~

- Apple App Store iOS download
- Windows client app download
- Linux client app download
- General distribution of server DEB/RPM package downloads


.. rubric:: Footnotes

.. [#androidbug]
    Android browser bug when using HTTP Basic Authentication:
    https://code.google.com/p/android/issues/detail?id=1353;
    http://stackoverflow.com/questions/17601647/apk-download-failure-if-behind-password-protected-site-on-stock-browser

.. [#chrome]
    https://play.google.com/store/apps/details?id=com.android.chrome
