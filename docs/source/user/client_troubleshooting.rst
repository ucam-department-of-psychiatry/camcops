..  docs/source/user/client_troubleshooting.rst

..  Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).
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


.. _client_troubleshooting:

Troubleshooting client problems
===============================

..  contents::
    :local:
    :depth: 3

Windows client fails to start
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``MF.dll`` missing under Windows Server.

  What follows assumes 64-bit CamCOPS under 64-bit Windows.

  This error can appear under e.g. Windows Server 2008 R2 64-bit (Windows
  6.1.7601), when the CamCOPS client is launched. This component is part of
  "normal" desktop Windows, but not Windows Server
  (https://serverfault.com/questions/562362/program-missing-dlls). Download and
  install the Windows Media Services 2008 for Windows Server 2008 R2 package
  from https://www.microsoft.com/en-gb/download/details.aspx?id=20424. (See
  also
  https://support.microsoft.com/en-ca/help/963697/how-to-install-windows-media-services-for-windows-server-2008-r2;
  potentially relevant.)

  The trouble is that this creates thousands of directories within
  ``C:\Windows\winsxs``, each with a single file in, so (for example)
  ``MF.DLL`` and ``MFPlat.DLL`` are in separate directories.

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

Tablet upload fails with error “Read timed out”
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Likely problem: slow network, large BLOB (binary large object – e.g. a big
photo). For example, in one of our tests a BLOB took more than 17 s to upload,
so the tablet needs to wait at least that long after starting to send it.
Increase the tablet’s network timeout (e.g. to 60000 ms or more) in Settings →
Server settings.

A photo-based task says "No camera"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS asks Qt for available cameras. This message indicates that none were
found. This is usually a hardware configuration problem.

- Under Linux, run ``cheese``; does this find a camera?

- If you're using a laptop, does it have a special function key combination to
  enable/disable the camera?

What if it crashes?
~~~~~~~~~~~~~~~~~~~

This shouldn’t happen; please note down any error details and let us know! To
forcibly stop and restart the app:

*Android 4.3*

- Settings → More → Application Manager → CamCOPS → Force stop

- Then start the app again as usual.

*iOS 7*

- Double-click the Home button

- Swipe left/right until you find the CamCOPS app’s preview

- Swipe the app preview up to close it

- Then start the app again as usual

*Windows*

- Close it as usual; if it refuses to close, kill it via the Task Manager.
