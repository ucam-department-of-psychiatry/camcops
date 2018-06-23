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
