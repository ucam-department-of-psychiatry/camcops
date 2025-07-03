#!/usr/bin/env python

"""
tools/make_xml_skeleton.py

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

**Creates an XML string file skeleton (with placeholder text) from a real
one.**

For developer use only.

"""

from typing import Optional

import argparse
from lxml import etree
import sys

from rich_argparse import ArgumentDefaultsRichHelpFormatter


def print_skeleton(xml_filename: str, replacement_text: Optional[str]) -> None:
    """
    Creates and prints the XML skeleton.

    Args:
        xml_filename: filename to read
        replacement_text: text to replace contents with
    """
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
    tree = etree.parse(xml_filename, parser)

    parent_map = {c: p for p in tree.iter() for c in p}

    for string in list(tree.iter("string")):
        name = string.attrib["name"]
        parent = parent_map[string]
        parent_index = parent.index(string)
        parent.remove(string)
        new_string = etree.Element("string", attrib={"name": name})

        if replacement_text is not None:
            new_string.text = replacement_text
        else:
            new_string.text = f"({name})"
        parent.insert(parent_index, new_string)

    tree.write(
        sys.stdout.buffer,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )


def main() -> None:
    """
    Command-line entry point.
    """
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        "Create an XML string file skeleton, with placeholder text, from a "
        "real but secret string file. Writes to stdout.",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    parser.add_argument("filename", type=str, help="Input filename")
    parser.add_argument(
        "--replacement",
        type=str,
        default=None,
        help=(
            "Replace string contents with this; default is to use the "
            "name attribute on the containing string element"
        ),
    )
    args = parser.parse_args()
    print_skeleton(
        xml_filename=args.filename,
        replacement_text=args.replacement,
    )


if __name__ == "__main__":
    main()
