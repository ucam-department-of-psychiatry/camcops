..  docs/source/user/download.rst

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


.. _download:

Downloading CamCOPS
===================

..  contents::
    :local:
    :depth: 3


Overview
~~~~~~~~

The Android app is in the Google Play Store at

- https://play.google.com/store/apps/details?id=org.camcops.camcops

The iOS app is in the Apple App Store at

- https://apps.apple.com/us/app/camcops/id1554490054

Windows client downloads, and server distributions, are at

- https://github.com/RudolfCardinal/camcops/releases

The source code is at

- https://github.com/RudolfCardinal/CamCOPS


Windows client notes
~~~~~~~~~~~~~~~~~~~~

Windows installation is very straightforward. The installer (created using
`Inno Setup`_) embeds a 32-bit and a 64-bit version of CamCOPS and will install
the one appropriate to the operating system.


Android client notes
~~~~~~~~~~~~~~~~~~~~

You are probably best off installing Android packages from the Google Play
Store, because that's simpler. However, you can also install a ``.apk``
(Android package file) directly.

- To install an Android application from an APK file, you need to permit this:
  e.g. :menuselection:`Settings --> Security --> Unknown sources (Allow
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


iOS client notes
~~~~~~~~~~~~~~~~

Install from the Apple App Store.


Server notes
~~~~~~~~~~~~

You can install the CamCOPS server Python package with:

  .. code-block:: bash

    pip install camcops-server

Downloads are also available as ``.deb`` packages for Debian Linux (e.g.
Ubuntu) and ``.rpm`` packages for e.g. CentOS.


Pending
~~~~~~~

- Linux client app download
- Windows server package (unless PyPI is enough)


===============================================================================

.. rubric:: Footnotes

.. [#androidbug]
    Android browser bug when using HTTP Basic Authentication:
    https://code.google.com/p/android/issues/detail?id=1353;
    http://stackoverflow.com/questions/17601647/apk-download-failure-if-behind-password-protected-site-on-stock-browser

.. [#chrome]
    https://play.google.com/store/apps/details?id=com.android.chrome
