#!/usr/bin/env python

r"""
tools/multiline_replace_camcops.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

**Replace chunks of text in source code.**

This rather ugly program is intended to be edited as required; it's for
development use only.

It operates recursively. If backups are enabled, it will leave files ending
with "~" behind. To clean up, use

.. code-block:: bash

    find . -name "*~" -exec rm {} \;

"""


import codecs
from fnmatch import fnmatch
import os
import shutil
from typing import List

_this_directory = os.path.dirname(os.path.abspath(__file__))  # server/tools
CAMCOPS_SERVER_DIRECTORY = os.path.abspath(os.path.join(
    _this_directory, os.pardir, os.pardir))  # camcops_server

INPUTDIR = CAMCOPS_SERVER_DIRECTORY
VALID_EXTENSIONS = [
    ".cpp",
    ".css",
    ".h",
    ".html",
    ".java",
    ".js",
    ".pl",
    ".py",
    ".txt"
]
EXCLUDE_PATTERNS = [  # via fnmatch.fnmatch()
    "*/moc_*.cpp",  # Qt MOC files
    "*/docs/build/*",  # docs
]

FROM_STRING = """
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
"""

TO_STRING = """
    Copyright (C) 2012-2020 University of Cambridge.
    Created by Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
"""

ENCODING = "utf-8"


def replace_string_in_file(find_str: str,
                           replace_str: str,
                           filename: str,
                           create_backup: bool = True,
                           dummy_run: bool = False,
                           verbose: bool = False) -> None:
    """
    Replaces all ``find_str`` by ``replace_str`` in file ``filename``.
    """
    with codecs.open(filename, encoding=ENCODING) as input_file:
        old_content = input_file.read()
    new_content = old_content.replace(find_str, replace_str)
    if new_content == old_content:
        if verbose:
            print(f"No change required: {filename}")
        return
    if dummy_run:
        print(f"Dummy run: would have rewritten: {filename}")
        return

    print(f"Rewriting: {filename}")
    temp_name = filename + '~~'
    with open(temp_name, 'w', encoding=ENCODING) as output_file:
        output_file.write(new_content)
    if create_backup:
        backup_name = filename + '~'
        shutil.copy2(filename, backup_name)
    os.replace(temp_name, filename)


def process(rootdir: str,
            find_str: str,
            replace_str: str,
            valid_extensions: List[str],
            exclude_patterns: List[str],
            create_backup: bool = True,
            dummy_run: bool = True) -> None:
    for (dirpath, dirnames, filenames) in os.walk(rootdir):
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext not in valid_extensions:
                continue
            fullpath = os.path.join(dirpath, filename)
            if not os.path.isfile(fullpath):
                continue
            if any(fnmatch(fullpath, pattern) for pattern in exclude_patterns):
                continue
            replace_string_in_file(
                find_str=find_str,
                replace_str=replace_str,
                filename=fullpath,
                create_backup=create_backup,
                dummy_run=dummy_run
            )


if __name__ == '__main__':
    process(
        rootdir=INPUTDIR,
        find_str=FROM_STRING,
        replace_str=TO_STRING,
        valid_extensions=VALID_EXTENSIONS,
        exclude_patterns=EXCLUDE_PATTERNS,
        create_backup=True,
        dummy_run=True
    )
