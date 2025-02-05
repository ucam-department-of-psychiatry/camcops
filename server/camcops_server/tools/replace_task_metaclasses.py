#!/usr/bin/env python

"""
camcops_server/tools/replace_task_metaclasses.py

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

Script to replace Task metaclasses with __init_subclass__ method on the Task
class.

"""

from enum import auto, Enum
import glob
import os
import re


TOOLS_DIR = os.path.dirname(os.path.realpath(__file__))
SERVER_ROOT = os.path.join(TOOLS_DIR, "..")
TASKS_DIR = os.path.join(SERVER_ROOT, "tasks")


class State(Enum):
    FINDING_METACLASS = auto()
    FINDING_INIT_DEF = auto()
    FINDING_INIT_RETURN = auto()
    FINDING_END_INIT = auto()
    FINDING_START_CLASS = auto()
    FINDING_END_CLASS = auto()
    FINDING_END_GLOBALS = auto()


class MetaclassReplacer:
    def replace_files(self) -> None:
        for filename in glob.glob(os.path.join(TASKS_DIR, "*.py")):
            self.state = State.FINDING_METACLASS
            self.output = []
            with open(filename, "r") as f:
                print(filename)
                for self.line in f.readlines():
                    if self.state == State.FINDING_METACLASS:
                        if self.find_declarative_meta():
                            print("Found declarative meta")
                            self.state = State.FINDING_INIT_DEF
                            self.pre_metaclass_init = []
                            continue
                        self.output.append(self.line)
                    if self.state == State.FINDING_INIT_DEF:
                        if self.find_start_init():
                            print("Found start_init")
                            self.state = State.FINDING_INIT_RETURN
                            continue
                    if self.state == State.FINDING_INIT_RETURN:
                        if self.find_init_return():
                            print("Found init return")
                            self.state = State.FINDING_END_INIT
                            self.metaclass_init = [
                                f'\n    def __init_subclass__(cls: Type["{self.class_name}"], **kwargs) -> None:\n'
                            ]
                            continue

                    if self.state == State.FINDING_END_INIT:
                        if self.find_end_init():
                            print("Found end init")
                            self.metaclass_init.append(
                                "        super().__init_subclass__(**kwargs)\n\n"
                            )
                            self.state = State.FINDING_START_CLASS
                            continue
                        self.metaclass_init.append(self.line)
                    if self.state == State.FINDING_START_CLASS:
                        if self.find_start_class():
                            print("found start class")
                            self.class_defn = [self.line]
                            if self.find_end_class():
                                self.write_class_definition()
                                self.state = State.FINDING_END_GLOBALS
                                continue

                            self.state = State.FINDING_END_CLASS
                            continue
                    if self.state == State.FINDING_END_CLASS:
                        self.class_defn.append(self.line)
                        if self.find_end_class():
                            print("found end class")
                            self.write_class_definition()
                            self.state = State.FINDING_END_GLOBALS

                            continue
                    if self.state == State.FINDING_END_GLOBALS:
                        if self.find_end_globals():
                            print("Found end globals")
                            self.output += self.metaclass_init
                            self.state = State.FINDING_METACLASS
                        self.output.append(self.line)

            with open(filename, "w") as f:
                for line in self.output:
                    f.write(line)

    def write_class_definition(self) -> None:
        for cd in self.class_defn:
            cd = cd.replace(f"metaclass={self.class_name}Metaclass", "")
            if cd.strip() != ",":
                self.output.append(cd)

    def find_declarative_meta(self) -> bool:
        regex = r"class (.+)Metaclass\(DeclarativeMeta\):"
        m = re.match(regex, self.line)
        if m is not None:
            self.class_name = m.group(1)
            return True

        return False

    def find_start_init(self) -> bool:
        regex = r"    def __init__\("

        return re.match(regex, self.line) is not None

    def find_end_init(self) -> bool:
        regex = r"        super\(\)\.__init__\(name, bases, classdict\)"

        return re.match(regex, self.line) is not None

    def find_init_return(self) -> bool:
        return ")" in self.line

    def find_start_class(self) -> bool:
        regex = rf"class {self.class_name}"
        return re.match(regex, self.line) is not None

    def find_end_class(self) -> bool:
        return "):" in self.line

    def find_end_globals(self):
        return "@" in self.line or "(" in self.line

    def write_output(self):
        pass


def main() -> None:
    replacer = MetaclassReplacer()
    replacer.replace_files()


if __name__ == "__main__":
    main()
