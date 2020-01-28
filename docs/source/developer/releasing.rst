..  docs/source/developer/releasing.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
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

- Push to the development repository.

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

- **You upload a new version with** :menuselection:`Release management --> App
  releases --> Manage [production track] --> Create Release`.

- Note also that if you try to install the .apk directly to a device that's
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
| 2.3.6         | 13                  | 2.3.6               | IN PROGRESS        | 23      | 28      |
|               |                     |                     |                    |         |         |
+---------------+---------------------+---------------------+--------------------+---------+---------+


Windows client
--------------

The client will be packaged automatically by the
``camcops_windows_innosetup.iss`` script, which runs under `Inno Setup`_.

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
