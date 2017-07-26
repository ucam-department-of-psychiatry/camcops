#!/usr/bin/env python
# cc_configfile.py

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

import configparser
import logging
from typing import Any, Callable, List

log = logging.getLogger(__name__)


# =============================================================================
# Reading config files
# =============================================================================

def get_config_parameter(config: configparser.ConfigParser,
                         section: str,
                         param: str,
                         fn: Callable[[Any], Any],
                         default: Any) -> Any:
    """Fetch parameter from configparser INI file.

    Args:
        config: configparser object
        section: name of INI file section
        param: name of parameter within section
        fn: function to apply to string parameter (e.g. int)
        default: default value
    Returns:
        parameter value, or fn(default)
    """
    try:
        value = fn(config.get(section, param))
    except (TypeError, ValueError, configparser.NoOptionError):
        log.warning("Configuration variable {} not found or improper; "
                    "using default of {}".format(param, default))
        if default is None:
            value = default
        else:
            value = fn(default)
    return value


def get_config_parameter_boolean(config: configparser.ConfigParser,
                                 section: str,
                                 param: str,
                                 default: bool) -> bool:
    """Get Boolean parameter from configparser INI file.

    Args:
        config: configparser object
        section: name of INI file section
        param: name of parameter within section
        default: default value
    Returns:
        parameter value, or default
    """
    try:
        value = config.getboolean(section, param)
    except (TypeError, ValueError, configparser.NoOptionError):
        log.warning("Configuration variable {} not found or improper; "
                    "using default of {}".format(param, default))
        value = default
    return value


def get_config_parameter_loglevel(config: configparser.ConfigParser,
                                  section: str,
                                  param: str,
                                  default: int) -> int:
    """Get loglevel parameter from configparser INI file.

    Args:
        config: configparser object
        section: name of INI file section
        param: name of parameter within section
        default: default value
    Returns:
        parameter value, or default
    """
    try:
        value = config.get(section, param).lower()
        if value == "debug":
            return logging.DEBUG  # 10
        elif value == "info":
            return logging.INFO
        elif value in ["warn", "warning"]:
            return logging.WARN
        elif value == "error":
            return logging.ERROR
        elif value in ["critical", "fatal"]:
            return logging.CRITICAL  # 50
        else:
            raise ValueError
    except (TypeError, ValueError, configparser.NoOptionError, AttributeError):
        log.warning("Configuration variable {} not found or improper; "
                    "using default of {}".format(param, default))
        return default


def get_config_parameter_multiline(config: configparser.ConfigParser,
                                   section: str,
                                   param: str,
                                   default: List[str]) -> List[str]:
    try:
        multiline = config.get(section, param)
        return [x.strip() for x in multiline.splitlines() if x.strip()]
    except (TypeError, ValueError, configparser.NoOptionError):
        log.warning("Configuration variable {} not found or improper; "
                    "using default of {}".format(param, default))
        return default
