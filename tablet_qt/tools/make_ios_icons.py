#!/usr/bin/env python

"""
tools/build_ios_icons.py

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

**Make icons for iOS (iPhone and iPad).**

For developer use only.

"""

from lxml import etree
import os
from os.path import abspath, dirname, join
import re
from subprocess import run

# Source: https://doc.qt.io/qt-5/ios-platform-notes.html#application-assets

icons = {
    "AppIcon29x29.png: 29 x 29",
    "AppIcon29x29@2x.png: 58 x 58",
    "AppIcon29x29@2x~ipad.png: 58 x 58",
    "AppIcon29x29~ipad.png: 29 x 29",
    "AppIcon40x40@2x.png: 80 x 80",
    "AppIcon40x40@2x~ipad.png: 80 x 80",
    "AppIcon40x40~ipad.png: 40 x 40",
    "AppIcon50x50@2x~ipad.png: 100 x 100",
    "AppIcon50x50~ipad.png: 50 x 50",
    "AppIcon57x57.png: 57 x 57",
    "AppIcon57x57@2x.png: 114 x 114",
    "AppIcon60x60@2x.png: 120 x 120",
    "AppIcon72x72@2x~ipad.png: 144 x 144",
    "AppIcon72x72~ipad.png: 72 x 72",
    "AppIcon76x76@2x~ipad.png: 152 x 152",
    "AppIcon76x76~ipad.png: 76 x 76",
}

CURRENT_DIR = dirname(abspath(__file__))  # camcops/tablet_qt/tools
TABLET_QT_DIR = abspath(join(CURRENT_DIR, os.pardir))  # camcops/tablet_qt
IOS_DIR = join(TABLET_QT_DIR, "ios")  # camcops/tablet_qt/ios

DOCS_DIR = abspath(join(CURRENT_DIR, os.pardir, os.pardir, "docs"))
ORIGINAL_ICON = join(DOCS_DIR, "source", "images", "camcops_icon_500.png")

XML_FILE = join(IOS_DIR, "temp_icons.xml")

def append_icon_xml(root, key_name, filenames):
    key = etree.SubElement(root, "key")
    key.text = key_name

    dict_tag = etree.SubElement(root, "dict")
    key = etree.SubElement(dict_tag, "key")
    key.text = "CFBundlePrimaryIcon"

    dict_tag = etree.SubElement(dict_tag, "dict")
    key = etree.SubElement(dict_tag, "key")
    key.text = "CFBundleIconFiles"
    array = etree.SubElement(dict_tag, "array")

    for filename in filenames:
        string = etree.SubElement(array, "string")
        string.text = filename


def main() -> None:
    regex = r"(.+): (\d+) x (\d+)"

    ipad_filenames = []
    filenames = []

    for icon in icons:
        (filename, x, y) = re.findall(regex, icon)[0]
        scaled_icon = join(IOS_DIR, filename)
        run(["convert",
             ORIGINAL_ICON,
             "-resize", x,
             "-alpha", "remove",
             scaled_icon], check=True)

        if "ipad" not in filename:
            filenames.append(filename)

        ipad_filenames.append(filename)

    filenames.sort()
    ipad_filenames.sort()

    root = etree.Element("dict")
    append_icon_xml(root, "CFBundleIcons", filenames)
    append_icon_xml(root, "CFBundleIcons~ipad", ipad_filenames)

    f = open(XML_FILE, "w")
    f.write(etree.tostring(root, pretty_print=True, encoding="unicode"))
    f.close()


if __name__ == "__main__":
    main()
