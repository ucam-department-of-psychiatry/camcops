#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_language.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**Constants for languages/internationalization.**

This represents known languages. Compare ``language.cpp`` on the client.

At present we don't make this user-configurable and arbitrary (e.g. via an XML
file to define languages), largely because it would a little complexity for the
user, and because there's not much point in adding a language to the server
without adding it for the client, too -- and the client needs recompiling.

"""

DANISH = "da-DK"
ENGLISH_UK = "en-GB"

DEFAULT_LANGUAGE = ENGLISH_UK

POSSIBLE_LANGUAGES = (
    (DANISH, "Dansk"),
    (ENGLISH_UK, "English (UK)"),
)
