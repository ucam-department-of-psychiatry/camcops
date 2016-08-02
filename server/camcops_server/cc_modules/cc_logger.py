#!/usr/bin/env python3
# cc_logger.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging
import os
from typing import List

from colorlog import ColoredFormatter


LOG_COLORS = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}
LOG_FORMAT = (
    '%(asctime)s.%(msecs)03d:%(levelname)s:{}:%(name)s:%(message)s'.format(
        os.getpid()))
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


def get_colour_handler(extranames: List[str] = None) -> logging.StreamHandler:
    extras = ":" + ":".join(extranames) if extranames else ""
    fmt = (
        "%(cyan)s%(asctime)s.%(msecs)03d %(name)s{extras}:%(levelname)s: "
        "%(log_color)s%(message)s"
    ).format(extras=extras)
    cf = ColoredFormatter(
        fmt,
        datefmt=LOG_DATEFMT,
        reset=True,
        log_colors=LOG_COLORS,
        secondary_log_colors={},
        style='%'
    )
    ch = logging.StreamHandler()
    ch.setFormatter(cf)
    return ch


# noinspection PyShadowingNames
def configure_logger_for_colour(log: logging.Logger,
                                level: int = logging.INFO,
                                remove_existing: bool = False,
                                extranames: List[str] = None) -> None:
    """
    Applies a preconfigured datetime/colour scheme to a logger.
    Should ONLY be called from the "if __name__ == 'main'" script:
        https://docs.python.org/3.4/howto/logging.html#library-config
    """
    if remove_existing:
        log.handlers = []  # http://stackoverflow.com/questions/7484454
    log.addHandler(get_colour_handler(extranames))
    log.setLevel(level)


def main_only_quicksetup_rootlogger(level: int = logging.DEBUG) -> None:
    # Nasty. Only call from "if __name__ == '__main__'" clauses!
    rootlogger = logging.getLogger()
    configure_logger_for_colour(rootlogger, level)
    logging.basicConfig(level=logging.DEBUG)


# =============================================================================
# Logger
# =============================================================================

main_only_quicksetup_rootlogger(logging.INFO)

# Webview logger
log = logging.getLogger("camcops_wv")
log.setLevel(logging.INFO)

# Database client logger
dblog = logging.getLogger("camcops_db")
dblog.setLevel(logging.INFO)

# levels are DEBUG, INFO, WARN/WARNING, ERROR, CRITICAL/FATAL
# -- level may be changed by config
