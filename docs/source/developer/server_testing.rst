..  docs/source/developer/server_testing.rst

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


.. _pytest: https://docs.pytest.org/en/stable/
.. _Factory Boy: https://factoryboy.readthedocs.io/en/stable/

Testing the server code
=======================

The python code on the server is tested with pytest_

Tests are kept separate to the code they are testing in a ``tests`` sub-folder
with the filename of the module appended with ``_tests.py``. So the module
``camcops_server/cc_modules/cc_patient.py`` is tested in
``camcops_server/cc_modules/tests/cc_patient_tests.py``.

Test classes should end in ``Tests`` e.g. ``PatientTests``. A number of
``unittest.TestCase`` subclasses are defined in
``camcops_server/cc_modules/cc_unittest``.

- Tests that require an empty database and a request object should inherit from
  ``DemoRequestTestCase``.

- Tests that require a minimal database setup (system user, superuser set on the
  request object, group administrator and a server device) should inherit from
  ``BasicDatabaseTestCase``.

- Tests that require the demonstration database, which has a patient and two
  instances of each type of task should inherit from ``DemoDatabaseTestCase``.

- Tests that do not require a database
  can just inherit from the standard python ``unittest.TestCase``.

Use `Factory Boy`_ test factories to create test instances of SQLAlchemy
database models. See ``camcops_server/cc_modules/cc_testfactories.py`` and
``camcops_server/tasks/tests/factories.py``.

.. _run_all_server_tests:

To run all tests whilst in the CamCOPS virtual environment:

  .. code-block:: bash

      cd server/camcops_server
      pytest

By default if there is an existing test database, this will be reused.


Custom CamCOPS pytest options:

--create-db           Create a new test database. Necessary when there have been schema changes.
--database-in-memory  Store the database in memory instead of on disk (SQLite only).
--echo                Log all SQL statements to the default log handler
--mysql               Use MySQL instead of the default SQLite
--db-url              SQLAlchemy test database URL (MySQL only, default: mysql+mysqldb://camcops:camcops@localhost:3306/test_camcops?charset=utf8


Some common standard pytest options:

-x           Stop on failure
-k wildcard  Run tests whose classes or files only match the wildcard
-s           Do not capture stdout and stderr. Necessary when debugging with e.g. pdb
--ff         Run previously failed tests first
