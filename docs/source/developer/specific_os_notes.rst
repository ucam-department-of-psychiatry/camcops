..  docs/source/developer/specific_os_notes.rst

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

.. _Git: https://git-scm.com/
.. _Homebrew: https://brew.sh/
.. _Python: https://www.python.com/
.. _Qt: https://www.qt.io/
.. _Xcode: https://developer.apple.com/xcode/


Specific OS notes
-----------------


.. _client_windows_server:

CamCOPS client won't run under Windows Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Under Windows, server, ``MF.dll`` is reported as missing.

What follows assumes 64-bit CamCOPS under 64-bit Windows.

This error can appear under e.g. Windows Server 2008 R2 64-bit (Windows
6.1.7601), when the CamCOPS client is launched. This component is part of
"normal" desktop Windows, but not Windows Server
(https://serverfault.com/questions/562362/program-missing-dlls). Download and
install the Windows Media Services 2008 for Windows Server 2008 R2 package from
https://www.microsoft.com/en-gb/download/details.aspx?id=20424. (See also
https://support.microsoft.com/en-ca/help/963697/how-to-install-windows-media-services-for-windows-server-2008-r2;
potentially relevant.)

The trouble is that this creates thousands of directories within
``C:\Windows\winsxs``, each with a single file in, so (for example) ``MF.DLL``
and ``MFPlat.DLL`` are in separate directories.

So, copy the most recent OS-relevant version of the following into
``C:\Windows\system32``:

- ``MF.DLL``
- ``MFPlat.DLL``
- ``EVR.DLL``
- ``MFReadWrite.DLL``
- ``api-ms-win-core-winrt-l1-1-0.dll.DLL`` -- **stuck; missing**

For example, from an administrative command prompt:

.. code-block:: bat

    cd c:\windows\system32
    copy C:\Windows\winsxs\amd64_microsoft-windows-mediafoundation_31bf3856ad364e35_6.1.7601.24146_none_faf014703c95b62f\mf.dll .
    copy C:\Windows\winsxs\amd64_microsoft-windows-mfplat_31bf3856ad364e35_6.1.7601.23471_none_5516292583660fc2\mfplat.dll .
    copy C:\Windows\winsxs\amd64_microsoft-windows-enhancedvideorenderer_31bf3856ad364e35_6.1.7601.23471_none_ee0e0e23fc773db4\evr.dll .
    copy C:\Windows\winsxs\amd64_microsoft-windows-mfreadwrite_31bf3856ad364e35_6.1.7601.17514_none_177bed732ea3f85f\mfreadwrite.dll .

See:

- https://forums.plex.tv/t/mfplat-dll-fix-for-windows-server/149701
- https://serverfault.com/questions/275314/should-i-add-syswow64-to-my-system-path-to-get-32bit-programs-in-the-path

Not yet fixed.

**Decision:** Windows Server is an unsuitable OS for the CamCOPS client. (It
should be fine for the CamCOPS server!) Use a client edition of Windows for
the CamCOPS client.


.. _set_up_imac_for_dev:

Setting up an iMac for CamCOPS development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    Avoid using a Mac Mini; they are too weedy (e.g. a 2012 model: 2.5 GHz
    dual-core Intel Core i5, 4 GB RAM, 500 Gb HD) and compiling Qt takes ages.
    Our 2019 development machine is an iMac 21.5", 3.2 GHz 6-core (12-thread)
    Intel Core i7-8700, 32 GB RAM, 1 TB SSD; that's fine.

- General computer setup. This includes picking an Apple ID (generally) as well
  as creating a user.

- Download and install the open-source edition of Qt_. This gets you Qt
  Creator. You'll need to log in with your Qt account.

  - Installing Qt triggers installation part of Xcode, if it wasn't already
    installed. But not all.

  - Maybe include also the Qt Installer Framework.

  - To make it show up in Launchpad, create a symlink to ``~/Qt/Qt
    Creator.app`` in ``/Applications``, e.g. with
    ``ln -s ~/Qt/Qt\ Creator.app/ /Applications/Qt\ Creator``.

- Install Xcode_ in full from the App Store. Run it, agree to conditions.
  Installing Xcode automatically installs the iOS SDK.

- Download and install Git_.

  - Since this is a third-party app, you need to enable installation first, or
    when it complains. :menuselection:`Apple icon [top left] --> System
    Preferences --> Security & Privacy --> General --> Allow apps downloaded
    from...`

- Fire up a terminal and clone the Git repository (e.g. to ``~/camcops/``).

- Download and install Python_ 3 (MacOS comes with Python 2).

- Make and activate a Python 3 virtual environment (e.g. in
  ``~/dev/venvs/camcops/``).

- Save some time and effort in the future with a script like this:

  .. code-block:: bash

    #!/usr/bin/env bash
    # ~/ACTIVATE_CAMCOPS_VENV.sh

    export CAMCOPS_SOURCE_DIR=~/camcops
    export CAMCOPS_VENV=~/dev/venvs/camcops
    export CAMCOPS_QT_BASE_DIR=~/dev/qt_local_build

    . ${CAMCOPS_VENV}/bin/activate
    cd ${CAMCOPS_SOURCE_DIR}

- However, this won't affect environment variables for GUI applications. So to
  get Qt Creator to see the environment variable:

  - see https://superuser.com/questions/476752/setting-environment-variables-in-os-x-for-gui-applications

  - edit ``~/Qt/Qt Creator.app/Contents/Info.plist`` and add a section like:

    .. code-block:: none

        <key>LSEnvironment</key
        <dict>
            <key>CAMCOPS_QT_BASE_DIR</key>
            <string>/Users/camcops/dev/qt_local_build</string>
        </dict>

  - force a refresh by doing this:

    .. code-block:: bash

        /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user
        killall Finder

- Same some time and effort by executing ``pip install -e .`` from the
  ``$CAMCOPS_SOURCE_DIR/server`` directory. This installs all the Python
  dependencies for the CamCOPS server, which is overkill, but includes packages
  used by the :ref:`build_qt.py <build_qt>` script.

- Install Homebrew_.

- Run ``${CAMCOPS_SOURCE_DIR}/tablet_qt/tools/build_qt.py --build_all`` and
  every time it stops and says there's an OS command missing, follow its
  suggestion.

  - See :ref:`Building the CamCOPS client <dev_building_client>` and
    :ref:`build_qt`.
