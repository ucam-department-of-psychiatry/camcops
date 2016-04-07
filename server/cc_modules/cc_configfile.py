#!/usr/bin/env python3
# cc_configfile.py

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

import configparser
import logging

from .cc_logger import log


# =============================================================================
# Reading config files
# =============================================================================

def get_config_parameter(config, section, param, fn, default):
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


def get_config_parameter_boolean(config, section, param, default):
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


def get_config_parameter_loglevel(config, section, param, default):
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


def get_config_parameter_multiline(config, section, param, default):
    try:
        multiline = config.get(section, param)
        return [x.strip() for x in multiline.splitlines() if x.strip()]
    except (TypeError, ValueError, configparser.NoOptionError):
        log.warning("Configuration variable {} not found or improper; "
                    "using default of {}".format(param, default))
        return default
