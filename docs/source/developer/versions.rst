..  docs/source/developer/versions.rst

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

.. _versions:

Versions of software etc. used by CamCOPS
=========================================

+----------------+---------+---------------------------------------------------+
| Name           | Version | Supported until                                   |
+==============+=========+=====================================================+
| Debian         | 11      | 2026-08-31;                                       |
| (Docker image) |         | https://wiki.debian.org/LTS                       |
+----------------+---------+---------------------------------------------------+
| Eigen          | 3.4.0   | ?. Last release was 2021-08-18 and there is more  |
|                |         | recent activity at                                |
|                |         | https://gitlab.com/libeigen/eigen                 |
+----------------+---------+---------------------------------------------------+
| FFmpeg         | 6.0     | ?; https://endoflife.date/ffmpeg                  |
+----------------+---------+---------------------------------------------------+
| OpenSSL        | 3.0.x   | 2026-09-07 (LTS);                                 |
|                |         | https://www.openssl.org/policies/releasestrat.html|
+----------------+---------+---------------------------------------------------+
| Python         | 3.9     | 2025-10-05                                        |
+----------------+---------+---------------------------------------------------+
|                | 3.10    | 2026-10-31                                        |
+----------------+---------+---------------------------------------------------+
|                | 3.11    | 2027-10-31                                        |
+----------------+---------+---------------------------------------------------+
|                | 3.12    | 2028-10-31;                                       |
|                |         | https://devguide.python.org/versions/             |
+----------------+---------+---------------------------------------------------+
| Qt             | 6.5.x   | 2026-03-31 (LTS) but 6.5.x branch now             |
|                |         | commercial-only with delayed open source release. |
|                |         | Latest non-commercial, non-LTS release is 6.6.    |
|                |         | https://endoflife.date/qt                         |
+----------------+---------+---------------------------------------------------+
| SQLAlchemy     | 1.4     | Still maintained but will reach EOL when 2.1      |
|                |         | becomes the next major release.                   |
|                |         | Upgrade to 2.0 is encouraged.                     |
|                |         | https://www.sqlalchemy.org/download.html          |
+----------------+---------+---------------------------------------------------+
| SQL Cipher     | 4.5.5   | ?; based on SQLite 3.42.0                         |
+----------------+---------+---------------------------------------------------+
