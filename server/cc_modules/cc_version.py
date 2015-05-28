#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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
# Version constants and configuration variables read by shell scripts
# =============================================================================

CAMCOPS_SERVER_VERSION = 1.40
CAMCOPS_CHANGEDATE = "2015-05-28"
# ... must use double quotes; read by a Perl regex in MAKE_PACKAGE
MINIMUM_TABLET_VERSION = 1.14
USE_WEASYPRINT = False
# ... will be converted to lower case and then matches /bin/...
# for shell script truth values
