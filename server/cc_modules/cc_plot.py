#!/usr/bin/env python3
# cc_plot.py

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

# =============================================================================
# Basic imports
# =============================================================================

import atexit
import os
import shutil
import tempfile

import pythonlib.rnc_plot as rnc_plot


# =============================================================================
# Import matplotlib
# =============================================================================

# 1. Make a temporary directory (must be a directory per process, I'm sure)
MPLCONFIGDIR = tempfile.mkdtemp()

# 2. Ensure temporary directory is removed when this process exits.
atexit.register(lambda: shutil.rmtree(MPLCONFIGDIR, ignore_errors=True))

# 3. Tell matplotlib about this directory prior to importing it
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR

# 4. Import matplotlib
import matplotlib

# 5. Set the backend
matplotlib.use("Agg")
# ... http://matplotlib.org/faq/usage_faq.html#what-is-a-backend
# ... http://matplotlib.org/faq/howto_faq.html
# matplotlib.use("cairo") # cairo backend corrupts some SVG figures

# THEN DO e.g. # import matplotlib.pyplot as plt


# =============================================================================
# Functions to configure matplotlib
# =============================================================================

def set_matplotlib_fontsize(fontsize):
    """Sets the font size for matplotlib."""
    rnc_plot.set_matplotlib_fontsize(matplotlib, fontsize)


def do_nothing():
    """Call to justify an import, as seen by pyflakes, whereas the real
    justification is to configure matplotlib at first import."""
    pass
