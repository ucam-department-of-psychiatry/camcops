#!/usr/bin/env python
# camcops_server/cc_modules/cc_simpleobjects.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from enum import Enum
from typing import List, Optional

import numpy as np


DEFAULT_TRACKER_ASPECT_RATIO = 2.0  # width / height


class LabelAlignment(Enum):
    center = "center"
    top = "top"
    bottom = "bottom"
    baseline = "baseline"


class TrackerLabel(object):
    def __init__(self,
                 y: float,
                 label: str,
                 vertical_alignment: LabelAlignment = LabelAlignment.center):
        self.y = y
        self.label = label
        self.vertical_alignment = vertical_alignment


class TrackerAxisTick(object):
    def __init__(self, y: float, label: str):
        self.y = y
        self.label = label


class TrackerInfo(object):
    """
    Tasks return one or more of these (one for each tracker to be shown), from
    which tracker displays are created.
    """
    def __init__(self,
                 value: float,
                 plot_label: str = None,
                 axis_label: str = None,
                 axis_min: float = None,
                 axis_max: float = None,
                 axis_ticks: Optional[List[TrackerAxisTick]] = None,
                 horizontal_lines: Optional[List[float]] = None,
                 horizontal_labels: Optional[List[TrackerLabel]] = None,
                 aspect_ratio: Optional[float] = DEFAULT_TRACKER_ASPECT_RATIO):
        self.value = value
        self.plot_label = plot_label
        self.axis_label = axis_label
        self.axis_min = axis_min
        self.axis_max = axis_max
        self.axis_ticks = axis_ticks or []
        self.horizontal_lines = horizontal_lines or []
        self.horizontal_labels = horizontal_labels or []
        self.aspect_ratio = aspect_ratio


def equally_spaced_ndarray(start: float, stop: float, num: int,
                           endpoint: bool = True) -> np.ndarray:
    """
    Produces equally spaced numbers. See
    https://stackoverflow.com/questions/477486/how-to-use-a-decimal-range-step-value.

    Args:
        start: starting value
        stop: stopping value
        num: number of values to return
        endpoint: include the endpoint?

    Returns:
        list of floats

    """  # noqa
    return np.linspace(start, stop, num, endpoint=endpoint, dtype=float)


def equally_spaced_float(start: float, stop: float, num: int,
                         endpoint: bool = True) -> List[float]:
    """
    Returns a float equivalent of :func:`equally_spaced_float` (q.v.).
    """
    return list(equally_spaced_ndarray(start, stop, num, endpoint=endpoint))


def equally_spaced_int(start: int, stop: int, step: int,
                       endpoint: bool = True) -> List[int]:
    """
    Almost a synonym for :func:`range`!

    Args:
        start: starting value
        stop: stopping value (INCLUSIVE if endpoint is True)
        step: step size
        endpoint: bool

    Returns:
        list of integers
    """
    if endpoint:
        if start <= stop:  # normal
            range_stop = stop + 1
        else:  # counting backwards: start > stop
            range_stop = stop - 1
    else:
        range_stop = stop
    return list(range(start, range_stop, step))


def regular_tracker_axis_ticks_float(
        start: float, stop: float, num: int,
        endpoint: bool = True) -> List[TrackerAxisTick]:
    """
    Args:
        start: starting value
        stop: stopping value
        num: number of values to return
        endpoint: include the endpoint?

    Returns:
        a list of simple numerical TrackerAxisTick objects

    """
    ticks = []  # type: List[TrackerAxisTick]
    for val in equally_spaced_ndarray(start, stop, num, endpoint=endpoint):
        ticks.append(TrackerAxisTick(val, str(val)))
    return ticks


def regular_tracker_axis_ticks_int(
        start: int, stop: int, step: int,
        endpoint: bool = True) -> List[TrackerAxisTick]:
    """
    Args:
        start: starting value
        stop: stopping value
        step: step size
        endpoint: include the endpoint?

    Returns:
        a list of simple numerical TrackerAxisTick objects

    """
    ticks = []  # type: List[TrackerAxisTick]
    for val in equally_spaced_int(start, stop, step, endpoint=endpoint):
        ticks.append(TrackerAxisTick(val, str(val)))
    return ticks
