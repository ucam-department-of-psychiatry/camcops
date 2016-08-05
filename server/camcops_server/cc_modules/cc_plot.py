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

import cardinal_pythonlib.rnc_plot as rnc_plot

from .cc_logger import log

# =============================================================================
# Import matplotlib
# =============================================================================

# We need to use os.environ, since pls won't be initialized yet. That goes
# for anything that affects imports (to avoid the complexity of delayed
# imports).
if 'MPLCONFIGDIR' in os.environ:
    # 1+2. Use a writable static directory (speeds pyplot loads hugely).
    MPLCONFIGDIR = os.environ['MPLCONFIGDIR']
else:
    # 1. Make a temporary directory (must be a directory per process, I'm sure)
    MPLCONFIGDIR = tempfile.mkdtemp()
    # 2. Ensure temporary directory is removed when this process exits.
    atexit.register(lambda: shutil.rmtree(MPLCONFIGDIR, ignore_errors=True))

# 3. Tell matplotlib about this directory prior to importing it
#    http://matplotlib.org/faq/environment_variables_faq.html
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR

# 4. Another nasty matplotlib hack
#    matplotlib.font_manager reads os.environ.get('HOME') directly, and
#    searches ~/.fonts for fonts. That's fine unless a user is calling with
#    sudo -u USER, leaving $HOME as it was but removing the permissions - then
#    matplotlib crashes out with e.g.
#       PermissionError: [Errno 13] Permission denied: '/home/rudolf/.fonts/SABOI___.TTF'  # noqa
#    Note that an empty string won't help either, since the check is
#    "is not None".
#    You can't assign None to an os.environ member; see
#    http://stackoverflow.com/questions/3575165; do this:
if 'HOME' in os.environ:
    del os.environ['HOME']

# 5. Import matplotlib
log.info("importing matplotlib (can be slow) (MPLCONFIGDIR={})...".format(
    MPLCONFIGDIR))
import matplotlib  # noqa

# 6. Set the backend
matplotlib.use("Agg")  # also the default backend
# ... http://matplotlib.org/faq/usage_faq.html#what-is-a-backend
# ... http://matplotlib.org/faq/howto_faq.html
# matplotlib.use("cairo") # cairo backend corrupts some SVG figures

# Load this once so we can tell the user we're importing it and it's slow
import matplotlib.pyplot  # noqa
log.info("... finished importing matplotlib")

# THEN DO e.g. # import matplotlib.pyplot as plt


# =============================================================================
# Functions to configure matplotlib
# =============================================================================

def set_matplotlib_fontsize(fontsize: float) -> None:
    """Sets the font size for matplotlib."""
    rnc_plot.set_matplotlib_fontsize(matplotlib, fontsize)


def do_nothing() -> None:
    """Call to justify an import, as seen by pyflakes, whereas the real
    justification is to configure matplotlib at first import."""
    pass
