#!/usr/bin/env python

"""
tools/decrypt_sqlcipher.py

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

Tool to use SQLCipher to make a decrypted copy of a database.
"""

import argparse
import getpass
import logging
import os
import shutil
from subprocess import Popen, PIPE
import sys
from typing import NoReturn

from cardinal_pythonlib.logs import BraceStyleAdapter
from rich_argparse import ArgumentDefaultsRichHelpFormatter

log = BraceStyleAdapter(logging.getLogger(__name__))

EXIT_FAIL = 1
PASSWORD_ENV_VAR = "DECRYPT_SQLCIPHER_PASSWORD"
SQLCIPHER_ENV_VAR = "SQLCIPHER"
SQLCIPHER_DEFAULT = "sqlcipher"


def string_to_sql_literal(s: str) -> str:
    return "'{}'".format(s.replace("'", "''"))


def main() -> NoReturn:
    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    logging.basicConfig(level=logging.DEBUG)

    # -------------------------------------------------------------------------
    # Command-line arguments
    # -------------------------------------------------------------------------
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        description="Use SQLCipher to make a decrypted copy of a database",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    parser.add_argument(
        "encrypted", help="Filename of the existing encrypted database"
    )
    parser.add_argument(
        "decrypted", help="Filename of the decrypted database to be created"
    )
    parser.add_argument(
        "--password",
        type=str,
        default=None,
        help="Password (if blank, environment variable {} will be used, or you"
        " will be prompted)".format(PASSWORD_ENV_VAR),
    )
    parser.add_argument(
        "--sqlcipher",
        type=str,
        default=None,
        help=(
            "SQLCipher executable file (if blank, environment variable {} "
            "will be used, or the default of {})"
        ).format(SQLCIPHER_ENV_VAR, repr(SQLCIPHER_DEFAULT)),
    )
    parser.add_argument(
        "--cipher_compatibility",
        type=int,
        default=None,
        help=(
            "Use compatibility settings for this major version of SQLCipher "
            "(e.g. 3)"
        ),
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default=sys.getdefaultencoding(),
        help="Encoding to use",
    )
    progargs = parser.parse_args()
    # log.debug("Args: " + repr(progargs))

    # -------------------------------------------------------------------------
    # SQLCipher executable
    # -------------------------------------------------------------------------
    sqlcipher = (
        progargs.sqlcipher
        or os.environ.get(SQLCIPHER_ENV_VAR)
        or SQLCIPHER_DEFAULT
    )

    # -------------------------------------------------------------------------
    # Check file existence
    # -------------------------------------------------------------------------
    if not os.path.isfile(progargs.encrypted):
        log.critical("No such file: {!r}", progargs.encrypted)
        sys.exit(EXIT_FAIL)
    if os.path.isfile(progargs.decrypted):
        log.critical("Destination already exists: {!r}", progargs.decrypted)
        sys.exit(EXIT_FAIL)
    if not shutil.which(sqlcipher):
        log.critical("Can't find SQLCipher at {!r}", sqlcipher)
        sys.exit(EXIT_FAIL)

    # -------------------------------------------------------------------------
    # Password
    # -------------------------------------------------------------------------
    password = progargs.password
    if password:
        log.debug(
            "Using password from command-line arguments (NB danger: "
            "visible to ps and similar tools)"
        )
    elif PASSWORD_ENV_VAR in os.environ:
        password = os.environ[PASSWORD_ENV_VAR]
        log.debug(
            "Using password from environment variable {}", PASSWORD_ENV_VAR
        )
    else:
        log.info(
            "Password not on command-line or in environment variable {};"
            " please enter it manually.",
            PASSWORD_ENV_VAR,
        )
        password = getpass.getpass()

    # -------------------------------------------------------------------------
    # Run SQLCipher to do the work
    # -------------------------------------------------------------------------
    sql_commands = [
        "-- Exit on any error",
        ".bail on",
        "",
        "-- Gain access to the encrypted database",
        "PRAGMA key = {key};".format(key=string_to_sql_literal(password)),
    ]
    if progargs.cipher_compatibility is not None:
        sql_commands += [
            "PRAGMA cipher_compatibility = {};".format(
                progargs.cipher_compatibility
            )
        ]
    sql_commands += [
        "",
        "-- Check we can read from old database "
        "(or quit without creating new one)",
        "SELECT COUNT(*) FROM sqlite_master;",
        "",
        "-- Create new database",
        "ATTACH DATABASE '{plaintext}' AS plaintext KEY '';".format(
            plaintext=progargs.decrypted
        ),
        "",
        "-- Move data from one to the other",
        "SELECT sqlcipher_export('plaintext');",
        "",
        "-- Done",
        "DETACH DATABASE plaintext;",
        ".exit",
    ]
    sql = "\n".join(sql_commands)
    cmdargs = [sqlcipher, progargs.encrypted]
    # log.debug("cmdargs: " + repr(cmdargs))
    # log.debug("stdin: " + sql)
    log.info("Calling SQLCipher ({!r})...", sqlcipher)
    p = Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout_bytes, stderr_bytes = p.communicate(
        input=sql.encode(progargs.encoding)
    )
    stderr_str = stderr_bytes.decode(progargs.encoding)
    retcode = p.returncode
    if retcode > 0:
        log.critical(
            "SQLCipher returned an error; its output is below. "
            "(Wrong password? Wrong passwords give the error "
            "'file is encrypted or is not a database', "
            "as do non-database files.)"
        )
        log.critical(stderr_str)
    else:
        log.info(
            "Success. (The decrypted database {!r} is now a standard "
            "SQLite plain-text database.)",
            progargs.decrypted,
        )
    sys.exit(retcode)


if __name__ == "__main__":
    main()
