#!/usr/bin/env python
# cc_math.py

"""
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
"""

import math
from typing import Optional, Union


def safe_logit(x: Union[float, int]) -> Optional[float]:
    if x > 1 or x < 0:
        return None  # can't take log of negative number
    if x == 1:
        return float("inf")
    if x == 0:
        return float("-inf")
    return math.log(x / (1 - x))
