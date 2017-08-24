#!/usr/bin/env python
# camcops_server/tools/create_db_from_scratch.py

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
import sys

from cardinal_pythonlib.logs import (
    main_only_quicksetup_rootlogger,
    print_report_on_all_logs,
)

from ..cc_modules.cc_alembic import create_database_from_scratch
from ..cc_modules.cc_config import get_default_config_from_os_env
from ..cc_modules.cc_constants import ENVVAR_CONFIG_FILE

log = logging.getLogger(__name__)

DEBUG_LOGS = False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create CamCOPS database from scratch (AVOID; use migrate "
                    "instead)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="Be verbose"
    )
    required_named = parser.add_argument_group('required named arguments')
    required_named.add_argument(
        '--config', required=True,
        help="Specify the CamCOPS configuration file. No defaults allowed; "
             "this is a dangerous operation."
    )
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.verbose else logging.INFO
    main_only_quicksetup_rootlogger(level=loglevel)

    os.environ[ENVVAR_CONFIG_FILE] = args.config

    cfg = get_default_config_from_os_env()
    create_database_from_scratch(cfg)

    if DEBUG_LOGS:
        print_report_on_all_logs()


if __name__ == "__main__":
    main()
