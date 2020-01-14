#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_debug.py

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

**Debugging utilities**

"""

import cProfile


# https://stackoverflow.com/questions/5375624/a-decorator-that-profiles-a-method-call-and-logs-the-profiling-result  # noqa
def profile(func):
    """
    Decorator to generate profiler output for slow code
    from camcops_server.cc_debug import profile.

    Add @profile to the function you want to profile.
    Will generate a file called <function name>.profile.

    Can be visualised with e.g. SnakeViz (pip install snakeviz)
    """

    def wrapper(*args, **kwargs):
        datafn = func.__name__ + ".profile"
        prof = cProfile.Profile()
        retval = prof.runcall(func, *args, **kwargs)
        prof.dump_stats(datafn)

        return retval

    return wrapper
