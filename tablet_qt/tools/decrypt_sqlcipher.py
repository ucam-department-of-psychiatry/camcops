#!/usr/bin/env python

"""
Tool to use SQLCipher to make a decrypted copy of a database.
"""

import argparse
import getpass
import logging
import os
import shutil
from subprocess import Popen, PIPE, STDOUT
import sys

log = logging.getLogger(__name__)

EXIT_FAIL = 1
PASSWORD_ENV_VAR = "DECRYPT_SQLCIPHER_PASSWORD"
SQLCIPHER_ENV_VAR = "SQLCIPHER"
SQLCIPHER_DEFAULT = "sqlcipher"


def string_to_sql_literal(s: str) -> None:
    return "'{}'".format(s.replace("'", "''"))


def main() -> None:
    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    logging.basicConfig(level=logging.DEBUG)

    # -------------------------------------------------------------------------
    # Command-line arguments
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Use SQLCipher to make a decrypted copy of a database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "encrypted",
        help="Filename of the existing encrypted database")
    parser.add_argument(
        "decrypted",
        help="Filename of the decrypted database to be created")
    parser.add_argument(
        "--password", type=str, default=None,
        help="Password (if blank, environment variable {} will be used, or you"
             " will be prompted)".format(PASSWORD_ENV_VAR))
    parser.add_argument(
        "--sqlcipher", type=str, default=None,
        help=(
            "SQLCipher executable file (if blank, environment variable {} "
            "will be used, or the default of {})"
        ).format(SQLCIPHER_ENV_VAR, repr(SQLCIPHER_DEFAULT)))
    parser.add_argument(
        "--encoding", type=str, default=sys.getdefaultencoding(),
        help="Encoding to use")
    progargs = parser.parse_args()
    # log.debug("Args: " + repr(progargs))

    # -------------------------------------------------------------------------
    # SQLCipher executable
    # -------------------------------------------------------------------------
    sqlcipher = (progargs.sqlcipher or os.environ.get(SQLCIPHER_ENV_VAR) or
                 SQLCIPHER_DEFAULT)

    # -------------------------------------------------------------------------
    # Check file existence
    # -------------------------------------------------------------------------
    if not os.path.isfile(progargs.encrypted):
        log.critical("No such file: {}".format(repr(progargs.encrypted)))
        sys.exit(EXIT_FAIL)
    if os.path.isfile(progargs.decrypted):
        log.critical("Destination already exists: {}".format(
            repr(progargs.decrypted)))
        sys.exit(EXIT_FAIL)
    if not shutil.which(sqlcipher):
        log.critical("Can't find SQLCipher at {}".format(repr(sqlcipher)))
        sys.exit(EXIT_FAIL)

    # -------------------------------------------------------------------------
    # Password
    # -------------------------------------------------------------------------
    password = progargs.password
    if password:
        log.debug("Using password from command-line arguments (NB danger: "
                  "visible to ps and similar tools)")
    elif PASSWORD_ENV_VAR in os.environ:
        password = os.environ[PASSWORD_ENV_VAR]
        log.debug("Using password from environment variable {}".format(PASSWORD_ENV_VAR))
    else:
        log.info("Password not on command-line or in environment variable {};"
                 " please enter it manually.".format(PASSWORD_ENV_VAR))
        password = getpass.getpass()

    # -------------------------------------------------------------------------
    # Run SQLCipher to do the work
    # -------------------------------------------------------------------------
    sql = """
-- Exit on any error
.bail on

-- Gain access to the encrypted database
PRAGMA key = {key};

-- Check we can read from old database (or quit without creating new one)
SELECT COUNT(*) FROM sqlite_master;

-- Create new database
ATTACH DATABASE '{plaintext}' AS plaintext KEY '';

-- Move data from one to the other
SELECT sqlcipher_export('plaintext');

-- Done
DETACH DATABASE plaintext;
.exit
    """.format(
        plaintext=progargs.decrypted,
        key=string_to_sql_literal(password),
    )
    cmdargs = [sqlcipher, progargs.encrypted]
    # log.debug("cmdargs: " + repr(cmdargs))
    # log.debug("stdin: " + sql)
    log.info("Calling SQLCipher ({})...".format(repr(sqlcipher)))
    p = Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout_bytes, stderr_bytes = p.communicate(
        input=sql.encode(progargs.encoding))
    stdout_str = stdout_bytes.decode(progargs.encoding)
    stderr_str = stderr_bytes.decode(progargs.encoding)
    retcode = p.returncode
    if retcode > 0:
        log.critical(
            "SQLCipher returned an error; its output is below. (Wrong "
            "password? Wrong passwords give the error 'file is encrypted or "
            "is not a database', as do non-database files.)")
        log.critical(stderr_str)
    else:
        log.info("Success. (The decrypted database {} is now a standard SQLite"
                 " plain-text database.)".format(repr(progargs.decrypted)))
    sys.exit(retcode)


if __name__ == '__main__':
    main()
