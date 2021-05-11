..  docs/source/developer/server_testing.rst

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


.. _pytest: https://docs.pytest.org/en/stable/


Testing the server code
=======================

The python code on the server is tested with pytest_

Tests are kept separate to the code they are testing in a ``tests`` sub-folder
with the filename of the module appended with ``_tests.py``. So the module
``camcops_server/cc_modules/cc_patient.py`` is tested in
``camcops_server/cc_modules/tests/cc_patient_tests.py``.

Test classes should end in ``Tests`` e.g. ``PatientTests``. Tests that require
an empty database should inherit from ``DemoRequestTestCase``. Tests that
require the demonstration database should inherit from
``DemoDatabaseTestCase``. See ``camcops_server/cc_modules/cc_unittest``. Tests
that do not require a database can just inherit from the standard python
``unittest.TestCase``

To run all tests whilst in the CamCOPS virtual environment:

  .. code-block:: bash

      cd server/camcops_server
      pytest

By default if there is an existing test database, this will be reused.


Custom CamCOPS pytest options:

--create-db           Create a new test database. Necessary when there have been schema changes.
--database-in-memory  Store the database in memory instead of on disk (sqlite only).
--echo                Log all SQL statements to the default log handler
--mysql               Use MySQL instead of the default sqlite
--db-name             Test database name (MySQL only, default test_camcops)
--db-user             Test database user (MySQL only, default camcops)
--db-password         Test database password (MySQL only, default camcops)


Some common standard pytest options:

-x           Stop on failure
-k wildcard  Run tests whose classes or files only match the wildcard
-s           Do not capture stdout and stderr. Necessary when debugging with e.g. pdb
