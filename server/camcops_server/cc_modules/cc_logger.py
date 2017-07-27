#!/usr/bin/env python
# camcops_server/cc_modules/cc_logger.py

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

from inspect import Parameter, signature
import logging
import os
from typing import Any, Dict, List, Tuple

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


# - https://docs.python.org/3/howto/logging-cookbook.html#use-of-alternative-formatting-styles  # noqa
# - https://stackoverflow.com/questions/13131400/logging-variable-data-with-new-format-string  # noqa
# - https://stackoverflow.com/questions/13131400/logging-variable-data-with-new-format-string/24683360#24683360  # noqa
# ... plus modifications to use inspect.signature() not inspect.getargspec()
# ... plus a performance tweak so we're not calling signature() every time
# See also:
# - https://www.simonmweber.com/2014/11/24/python-logging-traps.html

class BraceMessage(object):
    def __init__(self,
                 fmt: str,
                 args: Tuple[Any, ...],
                 kwargs: Dict[str, Any]) -> None:
        # This version uses args and kwargs, not *args and **kwargs, for
        # performance reasons:
        # https://stackoverflow.com/questions/31992424/performance-implications-of-unpacking-dictionaries-in-python  # noqa
        # ... and since we control creation entirely, we may as well go fast
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs
        # print("Creating BraceMessage with: fmt={}, args={}, "
        #       "kwargs={}".format(repr(fmt), repr(args), repr(kwargs)))

    def __str__(self) -> str:
        return self.fmt.format(*self.args, **self.kwargs)


class BraceStyleAdapter(logging.LoggerAdapter):
    def __init__(self,
                 logger: logging.Logger,
                 pass_special_logger_args: bool = True,
                 strip_special_logger_args_from_fmt: bool = False) -> None:
        """
        Wraps a logger so we can use {}-style string formatting.

        Args:
            logger:
                a logger
            pass_special_logger_args:
                should we continue to pass any special arguments to the logger
                itself? True is standard; False probably brings a slight
                performance benefit, but prevents log.exception() from working
                properly, as the 'exc_info' parameter will be stripped.
            strip_special_logger_args_from_fmt:
                If we're passing special arguments to the logger, should we
                remove them from the argments passed to the string formatter?
                There is no obvious cost to saying no.
        """
        super().__init__(logger=logger, extra=None)
        self.pass_special_logger_args = pass_special_logger_args
        self.strip_special_logger_args_from_fmt = strip_special_logger_args_from_fmt  # noqa
        # getargspec() returns:
        #   named tuple: ArgSpec(args, varargs, keywords, defaults)
        #   ... args = list of parameter names
        #   ... varargs = names of the * parameters, or None
        #   ... keywords = names of the ** parameters, or None
        #   ... defaults = tuple of default argument values, or None
        # signature() returns a Signature object:
        #   ... parameters: ordered mapping of name -> Parameter
        #   ... ... https://docs.python.org/3/library/inspect.html#inspect.Parameter  # noqa
        # Direct equivalence:
        #   https://github.com/praw-dev/praw/issues/541
        # So, old:
        # logargnames = getargspec(self.logger._log).args[1:]
        # and new:
        # noinspection PyProtectedMember
        sig = signature(self.logger._log)
        self.logargnames = [p.name for p in sig.parameters.values()
                            if p.kind == Parameter.POSITIONAL_OR_KEYWORD]
        # e.g.: ['level', 'msg', 'args', 'exc_info', 'extra', 'stack_info']
        # print("self.logargnames: " + repr(self.logargnames))

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(level):
            # print("log: msg={}, args={}, kwargs={}".format(
            #     repr(msg), repr(args), repr(kwargs)))
            if self.pass_special_logger_args:
                msg, log_kwargs = self.process(msg, kwargs)
                # print("... log: msg={}, log_kwargs={}".format(
                #     repr(msg), repr(log_kwargs)))
            else:
                log_kwargs = {}
            # noinspection PyProtectedMember
            self.logger._log(level, BraceMessage(msg, args, kwargs), (),
                             **log_kwargs)

    def process(self, msg: str,
                kwargs: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        special_param_names = [k for k in kwargs.keys()
                               if k in self.logargnames]
        log_kwargs = {k: kwargs[k] for k in special_param_names}
        # ... also: remove them from the starting kwargs?
        if self.strip_special_logger_args_from_fmt:
            for k in special_param_names:
                kwargs.pop(k)
        return msg, log_kwargs


if __name__ == '__main__':
    main_only_quicksetup_rootlogger(logging.INFO)
    log = BraceStyleAdapter(logging.getLogger(__name__))
    log.info("1. Hello!")
    log.info("1. Hello, {}!", "world")
    log.info("1. Hello, foo={foo}, bar={bar}!", foo="foo", bar="bar")
    log.info("1. Hello, {}; foo={foo}, bar={bar}!", "world", foo="foo",
             bar="bar")
    log.info("1. Hello, {}; foo={foo}, bar={bar}!", "world", foo="foo",
             bar="bar", extra={'somekey': 'somevalue'})
