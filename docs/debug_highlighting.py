#!/usr/bin/env python

"""
docs/debug_highlighting.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

Debug highlighting errors with pygments

"""

from argparse import ArgumentParser

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from rich_argparse import RichHelpFormatter


def main() -> None:
    parser = ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument("filename")
    parser.add_argument("lexer")

    args = parser.parse_args()

    lexer = get_lexer_by_name(args.lexer)
    lexer.add_filter("raiseonerror")

    with open(args.filename, "r") as f:
        source = f.read()
        formatter = HtmlFormatter(linenos=False, linenostart=1)

        highlight(source, lexer, formatter)


if __name__ == "__main__":
    main()
