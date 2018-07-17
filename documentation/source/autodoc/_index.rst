..  documentation/source/autodoc/_index.rst

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

Automatic documentation of core server source code
==================================================

Server
------

.. There's no way to create >1 page except by starting with >1 file.

.. DO NOT include:
..      alembic/env.py -- import side effects

.. note::

    Full formatted source code is also available via the CamCOPS server's
    :ref:`introspection <introspection>` function.

..  toctree::
    :maxdepth: 1

    camcops.rst
    cc_modules/_index.rst
    tasks/_index.rst
