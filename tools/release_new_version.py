#!/usr/bin/env python

r"""
tools/release_new_version.py

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

"""

import logging
import sys

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

EXIT_FAILURE = 1

log = logging.getLogger(__name__)


# https://stackoverflow.com/questions/1871549/determine-if-python-is-running-inside-virtualenv
def in_virtualenv() -> bool:
    return (
        hasattr(sys, "real_prefix") or
        (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )


def main() -> None:
    if not in_virtualenv():
        log.error("release_new_version.py must be run inside virtualenv")
        sys.exit(EXIT_FAILURE)

    # What do we want this script to do?

    # Check or bump all the version numbers
    # Update the changelog
    # Tag the Git repository
    # Build the Ubuntu server packages (deb/rpm)
    # Build the pypi server package
    # Distribute the server packages to GitHub and PyPI

    # Build the client (depending on the platform)
    # Distribute to Play Store / Apple Store / GitHub

    # Ideally we want to do all the checks before tagging and building
    # so we don't get the version numbers spiralling out of control


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    main()
