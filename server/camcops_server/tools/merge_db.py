#!/usr/bin/env python
# camcops_server/tools/merge_db.py

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

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from cardinal_pythonlib.sqlalchemy.merge_db import merge_db, TableIdentity
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_engine
from sqlalchemy.engine import create_engine

from ..cc_modules.cc_constants import ENVVAR_CONFIG_FILE
from ..cc_modules.cc_hl7 import HL7Message, HL7Run
from ..cc_modules.cc_request import command_line_request
from ..cc_modules.cc_session import CamcopsSession
from ..cc_modules.cc_storedvar import ServerStoredVar
from ..cc_modules.cc_sqlalchemy import Base

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge CamCOPS databases",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--config',
        default=os.environ.get(ENVVAR_CONFIG_FILE, None),
        help="Specify the CamCOPS configuration file. If this is not "
             "specified on the command line, the environment variable {} is "
             "examined.".format(ENVVAR_CONFIG_FILE))
    parser.add_argument(
        '--report_every', type=int, default=1000,
        help="Report progress every n rows"
    )
    parser.add_argument(
        '--echo', action="store_true",
        help="Echo SQL to source database"
    )
    parser.add_argument(
        '--dummy_run', action="store_true",
        help="Perform a dummy run only; do not alter destination database"
    )
    parser.add_argument(
        '--info_only', action="store_true",
        help="Show table information only; don't do any work"
    )
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="Be verbose"
    )
    parser.add_argument(
        '--skip_hl7_logs', action="store_true",
        help="Skip the {!r} table".format(HL7Run.__tablename__)
    )
    required_named = parser.add_argument_group('required named arguments')
    # https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments  # noqa
    required_named.add_argument(
        '--src',
        required=True,  # bad form, but there is safety in being explicit
        help="Source database (specified as an SQLAlchemy URL). The contents "
             "of this database will be merged into the database specified "
             "in the config file."
    )
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.verbose else logging.INFO
    main_only_quicksetup_rootlogger(level=loglevel)

    os.environ[ENVVAR_CONFIG_FILE] = args.config
    req = command_line_request()
    src_engine = create_engine(args.src, echo=args.echo,
                               pool_pre_ping=True)
    log.info("SOURCE: " + get_safe_url_from_engine(src_engine))
    log.info("DESTINATION: "  + get_safe_url_from_engine(req.engine))

    # Delay the slow import until we've checked our syntax
    log.info("Loading all models...")
    from ..cc_modules.cc_all_models import all_models_no_op  # delayed import
    all_models_no_op()
    log.info("Models loaded.")

    # Now, any special dependencies?
    # From the point of view of translating any tablet-related fields, the
    # actual (server) PK values are irrelevant; all relationships will be
    # identical if you change any PK (not standard database practice, but
    # convenient here).
    # The dependencies that do matter are server-side things, like user_id
    # variables.

    # For debugging only, some junk:
    # test_dependencies = [
    #     TableDependency(parent_tablename="patient",
    #                     child_tablename="_dirty_tables")
    # ]

    skip_tables = [
        TableIdentity(tablename=CamcopsSession.__tablename__),
        TableIdentity(tablename=ServerStoredVar.__tablename__),
    ]

    if args.skip_hl7_logs:
        skip_tables.extend([
            TableIdentity(tablename=HL7Message.__tablename__),
            TableIdentity(tablename=HL7Run.__tablename__),
        ])
    merge_db(
        base_class=Base,
        src_engine=src_engine,
        dst_session=req.dbsession,
        allow_missing_src_tables=False,
        allow_missing_src_columns=True,
        translate_fn=None,
        skip_tables=skip_tables,
        only_tables=None,
        # extra_table_dependencies=test_dependencies,
        extra_table_dependencies=None,
        info_only=args.info_only,
        dummy_run=args.dummy_run,
        report_every=args.report_every
    )


if __name__ == "__main__":
    main()
