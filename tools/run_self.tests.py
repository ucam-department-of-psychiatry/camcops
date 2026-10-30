#!/usr/bin/env python

"""
tools/run_self_tests.py

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

**Run self-tests.**

"""

import os
import subprocess
import sys

from cardinal_pythonlib.cmdline import cmdline_quote

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.relpath(os.path.join(THIS_DIR, ".."))


def main() -> None:
    cmdargs = ["pytest"] + sys.argv[1:]
    formatted_args = cmdline_quote(cmdargs)
    print(f"""
- You can run tests manually via one of these methods:
    pytest                                              # all tests
    pytest FILE.py                                      # one test file
    pytest FILE.py::some_function                       # one test function
    pytest FILE.py::SomeClass                           # one test class
    pytest FILE.py::SomeClass::some_member_function     # function within class
    pytest -k search_term   # all matching test files, functions, classes, etc.

- Pytest will find additional options in:
    {PROJECT_ROOT}/conftest.py
    {PROJECT_ROOT}/pytest.ini
  ... if you are running pytest manually, RUN FROM THAT DIRECTORY.

- Note that an SQLite database is saved in
    camcops_test.sqlite
  ... DELETE THAT AND RETRY IF THE TESTS FAIL!

- We'll do this now:
    cd {PROJECT_ROOT}
    {formatted_args}
""")
    # https://stackoverflow.com/questions/36456920
    # examples:
    # pytest client_api_tests.py::ClientApiTests::test_client_api_validators
    # pytest webview_tests.py::WebviewTests::test_webview_constant_validators
    # pytest cc_validator_tests.py

    # print(f"cmdargs: {cmdargs!r}")
    input("Press Enter when ready...")
    os.chdir(PROJECT_ROOT)
    subprocess.run(cmdargs)


if __name__ == "__main__":
    main()
