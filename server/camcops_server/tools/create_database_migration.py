#!/usr/bin/env python
# camcops_server/tools/create_database_migration.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
"""

import argparse
import logging
import os
import subprocess

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

log = logging.getLogger(__name__)

N_SEQUENCE_CHARS = 4  # like Django

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
ALEMBIC_VERSIONS_DIR = os.path.join(SERVER_BASE_DIR, 'alembic', 'versions')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("message", help="Revision message")
    args = parser.parse_args()

    _, _, existing_version_filenames = next(os.walk(ALEMBIC_VERSIONS_DIR),
                                            (None, None, []))
    existing_version_filenames = [
        x for x in existing_version_filenames if x != "__init__.py"]
    log.debug("existing_version_filenames: " +
              repr(existing_version_filenames))
    current_seq_strs = [x[:N_SEQUENCE_CHARS]
                        for x in existing_version_filenames]
    current_seq_strs.sort()
    if not current_seq_strs:
        current_seq_str = None
        new_seq_no = 1
    else:
        current_seq_str = current_seq_strs[-1]
        new_seq_no = max(int(x) for x in current_seq_strs) + 1
    new_seq_str = str(new_seq_no).zfill(N_SEQUENCE_CHARS)

    log.info("""Generating new revision with Alembic...
    Last revision was: {}
    New revision will be: {}
    [If it fails with "Can't locate revision identified by...", you might need
    to DROP the alembic_version table.]
    """.format(current_seq_str, new_seq_str))

    os.chdir(SERVER_BASE_DIR)
    subprocess.call(['alembic', 'revision',
                     '--autogenerate',
                     '-m', args.message,
                     '--rev-id', new_seq_str])


if __name__ == "__main__":
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    main()
