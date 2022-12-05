#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_pythonversion.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Single place to determine the Python version required.**

Python v3.6 was required as of CamCOPS v2.3.1, 2019. That enables:

- f-strings (v3.6)

Python v3.7 was required as of CamCOPS v2.4.12, 2021. That enables:

- dataclasses (v3.7)

Python 3.8 was required as of CamCOPS v2.4.15, 2022. That enables:

- assignment expressions, the "walrus" operator, ``:=`` (v3.8)
- positional-only parameters, ``/`` (v3.8)
- f-string ``=`` syntax to debug a variable (v3.8)

Not yet available:

- new dictionary merge/update syntax (v3.9)
- string prefix/suffix removal functions (v3.9)
- use of generics like ``list`` (not just ``List``) for type hinting (v3.9)

- ``match/case`` statement, like C++'s ``switch`` (v3.10)
- ``|`` as well as ``Union`` for type hints (v3.10)
- explicit ``typing.TypeAlias`` annotation (v3.10)

Note that one can set the environment variable ``PYTHONDEVMODE=1`` to enable
extra checks, such as whether there are deprecation warnings with newer Python
versions.

Note that Python versions are referred to in:

- this file
- ``.github/workflows/*``
- ``server/setup.py``
- ``server/docker/dockerfiles/camcops.Dockerfile``
- ``server/tools/MAKE_LINUX_PACKAGES.py``

and separately (not necessarily within a CamCOPS virtual environment) in

- ``server/tools/install_virtualenv.py``
- ``tablet_qt/tools/build_qt.py``

"""

import sys

MINIMUM_PYTHON_VERSION = (3, 8)


def assert_minimum_python_version():
    """
    Asserts that this version of Python meets our minimum requirements.
    This function should be used except in installation environments where
    CamCOPS modules are unavailable.

    Raises:
        AssertionError

    Note that this module/function should use only Python 2 syntax!

    """
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        required = ".".join(str(x) for x in MINIMUM_PYTHON_VERSION)
        actual = ".".join(str(x) for x in sys.version_info)
        raise AssertionError(
            "Need Python %s or higher; this is %s" % (required, actual)
        )


if __name__ == "__main__":
    assert_minimum_python_version()
