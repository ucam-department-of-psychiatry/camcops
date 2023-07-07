#!/usr/bin/env python

"""
camcops_server/tools/run_server_self_tests.py

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

**Run server self-tests.**

"""

import os
import subprocess
import sys

from cardinal_pythonlib.cmdline import cmdline_quote

from camcops_server.cc_modules.cc_baseconstants import CAMCOPS_SERVER_DIRECTORY
from camcops_server.conftest import TEST_DATABASE_FILENAME


def main() -> None:
    cmdargs = ["pytest"] + sys.argv[1:]
    formatted_args = cmdline_quote(cmdargs)
    print(
        f"""
- You can run tests manually via one of these methods:
    pytest                                              # all tests
    pytest FILE.py                                      # one test file
    pytest FILE.py::some_function                       # one test function
    pytest FILE.py::SomeClass                           # one test class
    pytest FILE.py::SomeClass::some_member_function     # function within class
    pytest -k search_term   # all matching test files, functions, classes, etc.

- Pytest will find additional options in:
    {CAMCOPS_SERVER_DIRECTORY}/conftest.py
    {CAMCOPS_SERVER_DIRECTORY}/pytest.ini
  ... if you are running pytest manually, RUN FROM THAT DIRECTORY.

- Note that an SQLite database is saved in
    {TEST_DATABASE_FILENAME}
  ... DELETE THAT AND RETRY IF THE TESTS FAIL!

- We'll do this now:
    cd {CAMCOPS_SERVER_DIRECTORY}
    {formatted_args}
"""
    )
    # https://stackoverflow.com/questions/36456920
    # examples:
    # pytest client_api_tests.py::ClientApiTests::test_client_api_validators
    # pytest webview_tests.py::WebviewTests::test_webview_constant_validators
    # pytest cc_validator_tests.py

    # print(f"cmdargs: {cmdargs!r}")
    input("Press Enter when ready...")
    os.chdir(CAMCOPS_SERVER_DIRECTORY)
    subprocess.run(cmdargs)


if __name__ == "__main__":
    main()
