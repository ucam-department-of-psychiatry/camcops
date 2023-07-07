..  docs/source/developer/penetration_testing.rst

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

.. _ZAP: https://www.zaproxy.org/


Penetration testing
===================

Via OWASP Zed Attack Proxy (ZAP)
--------------------------------

Get ZAP going:

- Download ZAP_, e.g. as the Linux installer.

- Run the installer, e.g. via ``sudo ZAP_2_9_0_unix.sh``. By default it
  installs to ``/opt/zaproxy``.
- Run ZAP with ``/opt/zaproxy/zap.sh &``
- Say no to "Do you want to persist the ZAP Session?"

Get CamCOPS going:

- Make sure your CamCOPS configuration file doesn't have any "developer
  low-security" flags set. Thus, ensure:

  .. code-block:: ini

    ALLOW_INSECURE_COOKIES = False
    # ... if set to True, you will get the alerts:
    # - Cookie No HttpOnly Flag
    # - Cookie Without Secure Flag

- Fire up CamCOPS, e.g. with ``camcops_server serve_cherrypy``.

Then test. Perform the following tests. Every time you change code and
re-attack, delete all previous alerts (or you won't know if you've fixed them).
Once you're eliminated all alerts (except exempted ones as below), proceed to
the next attack.

1.  In "Quick Start", click "Automated scan", enter the CamCOPS root URL (e.g.
    ``https://127.0.0.1:8088/``) into ZAP and click "Attack". This performs an
    automatic scan without login.

2.  Attack the client API, e.g. ``https://127.0.0.1:8088/api``.

3.  Attack the rest of the site.

    - In "Quick Start", click "Manual Explore". Choose the root URL again,
      launch Firefox from ZAP (with a fancy HUD!), log in, and explore.

    - Do the ZAP HUD tutorial the first time round. (Delete the cumulative
      alerts after this!)

    - Mark the CamCOPS local site as "in scope".

    - Turn on Attack Mode.

    - Browse and watch the data fly.

The attacks will lock out your user at some point; use ``camcops_server
enable_user`` to re-enable it.

**Alerts not fixed,** as they relate to third-party code and are low risk, or
are deliberate:

- ``Information Disclosure - Suspicious Comments`` (risk: "Informational") in
  ``deform.js``, ``jquery-2.0.3.min.js``, ``jquery.form-3.09.js``, and
  ``jquery.maskedinput-1.3.1.min.js``.

- ``Timestamp Disclosure - Unix`` (risk: "Informational") in
  ``deform_static/css/bootstrap.min.css`` (several) and
  ``deform_static/css/form.css``.

- ``Application Error Disclosure`` at ``/crash`` -- that is the point of the
  ``/crash`` page, available only to superusers.
