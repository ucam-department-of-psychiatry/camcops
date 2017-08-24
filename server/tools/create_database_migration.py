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
from os import pardir
from os.path import abspath, dirname, join

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from cardinal_pythonlib.sqlalchemy.alembic_func import create_database_migration_numbered_style  # noqa

log = logging.getLogger(__name__)

N_SEQUENCE_CHARS = 4  # like Django
CURRENT_DIR = dirname(abspath(__file__))  # camcops/server/tools
SERVER_BASE_DIR = abspath(join(CURRENT_DIR, pardir))  # camcops/server
SERVER_PACKAGE_DIR = join(SERVER_BASE_DIR, "camcops_server")  # # camcops/server/camcops_server  # noqa
ALEMBIC_INI_FILE = join(SERVER_PACKAGE_DIR, "alembic.ini")
ALEMBIC_VERSIONS_DIR = join(SERVER_PACKAGE_DIR, 'alembic', 'versions')


def main() -> None:
    """
    Note special difficulty with "variant" types, such as
        Integer().with_variant(...)

    which are (2017-08-21, alembic==0.9.4) rendered as "sa.Variant()" only
    with a MySQL backend.
    
    - https://bitbucket.org/zzzeek/alembic/issues/433/variant-base-not-taken-into-account-when
    - https://bitbucket.org/zzzeek/alembic/issues/131/create-special-rendering-for-variant
    """  # noqa
    parser = argparse.ArgumentParser()
    parser.add_argument("message", help="Revision message")
    args = parser.parse_args()
    create_database_migration_numbered_style(
        alembic_ini_file=ALEMBIC_INI_FILE,
        alembic_versions_dir=ALEMBIC_VERSIONS_DIR,
        message=args.message,
        n_sequence_chars=N_SEQUENCE_CHARS
    )


if __name__ == "__main__":
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    main()
