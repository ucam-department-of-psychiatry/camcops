 ..  docs/source/developer/setting_up.rst

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


Setting up a development environment
====================================

..  contents::
    :local:
    :depth: 3

Cloning the repository
----------------------

  .. code-block:: bash

      mkdir ~/dev
      cd ~/dev
      git clone git@github.com:ucam-department-of-psychiatry/camcops.git

Setting up the virtual environment
----------------------------------

  .. code-block:: bash

      python3 -m venv ~/.virtualenvs/camcops
      . ~/.virtualenvs/bin/activate


Installing the camcops_server packages
--------------------------------------

Ensure the virtualenv is activated as above.

  .. code-block:: bash

      cd ~/dev/camcops/camcops_server
      python -m pip install -e .


Installing the pre-commit hook
------------------------------

The pre-commit hook will sanity-check all files to be committed to the git
repository.

  .. code-block:: bash

      pre-commit install


Running the tests
-----------------

Now might be a good time to :ref:`run all the automated server tests <run_all_server_tests>`.
