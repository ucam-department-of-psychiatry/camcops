#!/usr/bin/env python

r"""
pre_commit_hooks/pre_commit_hook.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

pre-commit hook script that runs lint & sort

Usage: cd .git/hooks/pre-commit;
       ln -s ../../pre_commit_hooks/pre_commit_hook.py

Linting and sorting ensures we don't get cosmetic commits later
that break git blame history for no reason.

To avoid unexpected side effects, this script won't stash changes.
So if you have non-commited changes that break this you'll need to
stash your changes before commiting.
"""

import logging
import os
from subprocess import CalledProcessError, run
import sys
from typing import List


EXIT_FAILURE = 1

PRECOMMIT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.join(PRECOMMIT_DIR, '..')
PYTHON_SOURCE_DIR = os.path.join(PROJECT_ROOT,
                                 'server', 'camcops_server')
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'setup.cfg')

log = logging.getLogger(__name__)


class PreCommitException(Exception):
    pass


def run_with_check(args: List[str]):
    run(args, check=True)


def check_python_style() -> None:
    run_with_check([
        'pylava',
        '-o', CONFIG_FILE,
        PYTHON_SOURCE_DIR,
    ])


def check_imports_sorted() -> None:
    # https://github.com/timothycrosley/isort
    run_with_check([
        'isort',
        '-c',  # Check only, do not make changes
        '-rc',  # Recursive
        '--diff',  # Show diffs
        '-sp', CONFIG_FILE,
        PYTHON_SOURCE_DIR
    ])


# https://stackoverflow.com/questions/1871549/determine-if-python-is-running-inside-virtualenv
def in_virtualenv():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )


def main() -> None:
    if not in_virtualenv():
        log.error("pre_commit_hook.py must be run inside virtualenv")
        sys.exit(EXIT_FAILURE)

    try:
        check_python_style()
        check_imports_sorted()
    except CalledProcessError as e:
        log.error(str(e))
        log.error("Pre-commit hook failed. Check errors above")
        sys.exit(EXIT_FAILURE)


if __name__ == '__main__':
    main()
