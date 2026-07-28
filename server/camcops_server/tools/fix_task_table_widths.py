#!/usr/bin/env python

"""
camcops_server/tools/fix_task_table_widths.py

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

Script to replace HTML table cell widths with CSS.

"""

import argparse
from dataclasses import dataclass
from enum import Enum
import os
import re


class State(Enum):
    LOOKING_FOR_TR = 1
    LOOKING_FOR_TH = 2
    PROCESSING_TH = 3


@dataclass
class Fixer:
    task_dir: str

    def __post_init__(self) -> None:
        self.table_heading_search = (
            #  (   1   )(         )( 3 )(4)(5 )( 6)( 7)(   8    )
            r"^(\s+\<th)( width=\")(\d+)(%)(\")(\>)(.+)(\</th\>$)"
        )
        self.tablename_search = r"^\s+__tablename__ = \"(.+)\"$"
        self.tr_search = r"^(\s+)\<tr.+$"
        self.css_class_search = r"([a-zA-Z\-]+)(.*)"
        self.css_class_replace = r"\g<1>"

    def fix(self) -> None:
        for basename in sorted(os.listdir(self.task_dir)):
            parts = os.path.splitext(basename)
            if parts[1] == ".py":
                task_file = os.path.join(self.task_dir, basename)
                self.fix_file(task_file)

    def fix_file(self, task_file: str) -> None:
        css = []
        lines = []

        with open(task_file, "r") as f_in:
            state = State.LOOKING_FOR_TR
            th_lines = []
            widths = {}
            col_classes = []
            tablename = os.path.splitext(os.path.basename(task_file))[0]

            tr_line = None
            tr_indent = None

            for line in f_in.readlines():
                m = re.match(self.tablename_search, line)
                if m is not None:
                    tablename = m.group(1)

                if state == State.LOOKING_FOR_TR:
                    m = re.match(self.tr_search, line)
                    if m is not None:
                        tr_line = f"{m.group(0)}\n"
                        tr_indent = len(m.group(1))
                        state = State.LOOKING_FOR_TH
                        continue

                m = re.match(self.table_heading_search, line)
                if m is not None:
                    if state == State.LOOKING_FOR_TH:
                        state = State.PROCESSING_TH

                    if state == State.PROCESSING_TH:
                        th = m.group(1)
                        width = m.group(3)
                        text = m.group(7)
                        end_th = m.group(8)

                        th_lines.append(f"{th}>{text}{end_th}")

                        name = re.sub(
                            self.css_class_search,
                            self.css_class_replace,
                            text.lower().replace("{", "").replace("}", ""),
                        )
                        assert tablename is not None
                        prefix = tablename.replace("_", "-")
                        col_class = f"{prefix}-{name}-col"
                        col_classes.append(col_class)
                        widths[col_class] = width

                        continue
                else:
                    if state == State.PROCESSING_TH:
                        assert tablename is not None
                        assert tr_line is not None
                        assert tr_indent is not None
                        lines.append(tr_line)
                        colgroup_indent = " " * (tr_indent + 4)
                        col_indent = " " * (tr_indent + 8)
                        lines.append(f"{colgroup_indent}<colgroup>\n")
                        css.append("")
                        for col_class in col_classes:
                            lines.append(
                                f'{col_indent}<col class="{col_class}" />\n'
                            )
                            css.append(f".{col_class} {{")
                            width = widths[col_class]
                            css.append(f"    width: {width}%;")
                            css.append("}")

                        lines.append(f"{colgroup_indent}</colgroup>\n")
                        lines.append("\n".join(th_lines))
                        state = State.LOOKING_FOR_TR
                        th_lines = []
                        widths = {}
                        col_classes = []
                        lines.append("\n")
                        tr_line = None
                    else:
                        if tr_line is not None:
                            lines.append(tr_line)
                            tr_line = None
                            state = State.LOOKING_FOR_TR

                lines.append(line)

        with open(task_file, "w") as f_out:
            for line in lines:
                f_out.write(f"{line}")

        print("\n".join(css))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace HTML table cell widths with CSS",
    )

    parser.add_argument(
        "task_dir", help="Directory containing task python files"
    )

    args = parser.parse_args()

    fixer = Fixer(**vars(args))
    fixer.fix()


if __name__ == "__main__":
    main()
