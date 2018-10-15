#!/usr/bin/env python

"""
tools/reformat_source.py

===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

Clean up source code.

"""

import argparse
import logging
from os import pardir, walk
from os.path import abspath, dirname, join, splitext
from sys import stdout
from typing import List, TextIO

from cardinal_pythonlib.fileops import relative_filename_within_dir
from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

log = logging.getLogger(__name__)

# =============================================================================
# Directories
# =============================================================================

THIS_DIR = abspath(dirname(__file__))  # .../camcops/server/tools
CAMCOPS_ROOT_DIR = abspath(join(THIS_DIR, pardir, pardir))  # .../camcops
SERVER_ROOT_DIR = join(CAMCOPS_ROOT_DIR, 'server')  # .../camcops/server
TABLET_ROOT_DIR = join(CAMCOPS_ROOT_DIR, 'tablet_qt')  # .../camcops/tablet_qt

# =============================================================================
# Content
# =============================================================================

TRANSITION = "==============================================================================="  # noqa
CORRECT_COPYRIGHT_LINES = """
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
""".strip().splitlines()
CORRECT_SHEBANG = "#!/usr/bin/env python"
RST_COMMENT_LINE = ".."
SHEBANG_START = "#!"
TRIPLE_DOUBLEQUOTE = '"""'
BLANK = ""
MISSING_RST_TITLE = "**Missing title.**"

CR = "\r"
LF = "\n"
NL = LF
SPACE = " "
TAB = "\t"
HASH = "#"
HASH_SPACE = "# "
PYTHON_EXTENSION = ".py"


# =============================================================================
# PythonProcessor
# =============================================================================

class PythonProcessor(object):
    """
    Class to read a Python source file and reformat its shebang/docstring etc.
    """

    def __init__(self, full_path: str, top_dir: str) -> None:
        """

        Args:
            full_path:
                full path to source file
            top_dir:
                directory from which we calculate a relative filename to be
                shown
        """
        self.full_path = full_path
        self.advertised_filename = relative_filename_within_dir(
            full_path, top_dir)
        self.needs_rewriting = False
        self.source_lines = []  # type: List[str]
        self.dest_lines = []  # type: List[str]
        self._read_source()
        self._create_dest()

    def _read_source(self) -> None:
        """
        Reads the source file.
        """
        with open(self.full_path, "rt") as f:
            for linenum, line_with_nl in enumerate(f.readlines(), start=1):
                line_without_newline = (
                    line_with_nl[:-1] if line_with_nl.endswith(NL)
                    else line_with_nl
                )
                if TAB in line_without_newline:
                    self._warn("Tab character at line {}".format(linenum))
                if CR in line_without_newline:
                    self._warn("Carriage return character at line {} "
                               "(Windows CR+LF endings?)".format(linenum))
                self.source_lines.append(line_without_newline)

    def _create_dest(self) -> None:
        """
        Creates an internal representation of the destination file.

        This is where the thinking happens
        """
        in_body = False
        in_docstring = False
        in_copyright = False
        copyright_done = False
        docstring_done = False
        swallow_blanks_in_docstring = False
        for linenum, sl in enumerate(self.source_lines, start=1):
            dl = sl

            if dl.endswith(SPACE):
                self._debug("Line {} ends in whitespace".format(linenum))
                dl = dl.rstrip()

            if not in_body:

                if linenum == 1:
                    # Shebang
                    if not dl.startswith(SHEBANG_START):
                        self._warn("File does not start with shebang; "
                                   "first line was {!r}".format(dl))
                        self._too_risky()
                        return
                    if dl != CORRECT_SHEBANG:
                        self._debug("Rewriting shebang; was {!r}".format(dl))
                    dl = CORRECT_SHEBANG

                if (linenum == 2 and dl.startswith(HASH_SPACE) and
                        dl.endswith(PYTHON_EXTENSION)):
                    self._debug(
                        "Removing filename comment: {!r}".format(dl))
                    dl = None

                elif TRIPLE_DOUBLEQUOTE in dl:
                    if not dl.startswith(TRIPLE_DOUBLEQUOTE):
                        self._debug_line(linenum, dl)
                        self._warn("Triple-quote not at start of line")
                        self._too_risky()
                        return
                    if in_docstring:  # docstring finishing
                        in_docstring = False
                        docstring_done = True
                        in_body = True
                        # ... and keep dl, so we write the end of the
                        # docstring, potentially with e.g. "# noqa" on the end
                    elif not docstring_done:  # docstring starting
                        in_docstring = True
                        # self._critical("adding our new docstring")
                        # Write our new docstring's start
                        self.dest_lines.append(TRIPLE_DOUBLEQUOTE)
                        self.dest_lines.append(self.advertised_filename)
                        self.dest_lines.append(BLANK)
                        self.dest_lines.extend(CORRECT_COPYRIGHT_LINES)
                        self.dest_lines.append(BLANK)
                        swallow_blanks_in_docstring = True
                        if dl == TRIPLE_DOUBLEQUOTE:
                            dl = None  # don't write another triple-quote line
                        else:
                            dl = dl[len(TRIPLE_DOUBLEQUOTE):]

                elif in_docstring:
                    # Reading within the source docstring

                    if dl == TRANSITION:
                        if in_copyright:  # copyright finishing
                            in_copyright = False
                            copyright_done = True
                            dl = None  # we've already replaced with our own
                        elif not copyright_done:
                            in_copyright = True
                            dl = None  # we've already replaced with our own

                    elif in_copyright:
                        dl = None  # we've already replaced with our own

                    elif dl == RST_COMMENT_LINE:
                        dl = None  # remove these

                    elif swallow_blanks_in_docstring:
                        # self._debug_line(linenum, dl)
                        if dl == BLANK:
                            dl = None
                        elif copyright_done:
                            swallow_blanks_in_docstring = False

            if dl is not None:
                # self._debug_line(linenum, dl, "adding ")
                self.dest_lines.append(dl)

        if not docstring_done:
            # The source file didn't have a docstring!
            new_docstring_lines = [
                BLANK,
                TRIPLE_DOUBLEQUOTE,
                self.advertised_filename,
                BLANK,
            ] + CORRECT_COPYRIGHT_LINES + [
                BLANK,
                MISSING_RST_TITLE,
                TRIPLE_DOUBLEQUOTE
            ]
            self._warn("File had no docstring; adding one. "
                       "Will need manual edit to add RST title. "
                       "Search for {!r}".format(MISSING_RST_TITLE))
            self.dest_lines[1:1] = new_docstring_lines

        self.needs_rewriting = self.dest_lines != self.source_lines

    @staticmethod
    def _debug_line(linenum: int, line: str, extramsg: str = "") -> None:
        """
        Writes a debugging report on a line.
        """
        log.critical("{}Line {}: {!r}".format(extramsg, linenum, line))

    def _logmsg(self, msg: str) -> str:
        """
        Formats a log message.
        """
        return "{}: {}".format(self.advertised_filename, msg)

    def _critical(self, msg: str) -> None:
        """
        Shows a critical message.
        """
        log.critical(self._logmsg(msg))

    def _warn(self, msg: str) -> None:
        """
        Shows a warning.
        """
        log.warning(self._logmsg(msg))

    def _info(self, msg: str) -> None:
        """
        Shows an info message.
        """
        log.info(self._logmsg(msg))

    def _debug(self, msg: str) -> None:
        """
        Shows a debugging message.
        """
        log.debug(self._logmsg(msg))

    def _too_risky(self) -> None:
        """
        Shows a warning and sets this file as not for processing
        """
        self._warn("Don't know how to process file")
        self.needs_rewriting = False

    def show(self) -> None:
        """
        Writes the destination to stdout.
        """
        self._write(stdout)

    def rewrite_file(self) -> None:
        """
        Rewrites the source file.
        """
        if not self.needs_rewriting:
            return
        self._info("Rewriting file")
        with open(self.full_path) as outfile:
            self._write(outfile)

    def _write(self, destination: TextIO) -> None:
        """
        Writes the converted output to a destination.
        """
        for line in self.dest_lines:
            destination.write(line + NL)


# =============================================================================
# Top-level functions
# =============================================================================

def walk_source_dir(top_dir: str,
                    show_only: bool = True,
                    rewrite: bool = False,
                    process_only_filenum: int = None) -> None:
    """
    Walk a directory, finding Python files and rewriting them.

    Args:
        top_dir: directory to descend into
        show_only: show results (to stdout) only; don't rewrite
        rewrite: write the changes
        process_only_filenum: only process this file number (1-based index);
            for debugging only
    """
    filenum = 0
    for dirpath, dirnames, filenames in walk(top_dir):
        for filename in filenames:
            fullname = join(dirpath, filename)
            extension = splitext(filename)[1]
            if extension != PYTHON_EXTENSION:
                # log.debug("Skipping non-Python file: {}".format(fullname))
                continue

            filenum += 1

            if process_only_filenum and filenum != process_only_filenum:
                continue

            log.info("Processing file {}: {}".format(filenum, fullname))
            proc = PythonProcessor(fullname, top_dir)
            if show_only:
                proc.show()
            elif rewrite:
                proc.rewrite_file()


def main() -> None:
    """
    Command-line entry point. See command-line help.
    """
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Reformat source files")
    parser.add_argument(
        "--rewrite", action="store_true",
        help="Rewrite the files")
    parser.add_argument(
        "--show", action="store_true",
        help="Show the files to stdout")
    parser.add_argument(
        "--process_only_filenum", type=int,
        help="Only process this file number (1-based index) in each "
             "directory; for debugging only")

    args = parser.parse_args()

    rewrite = args.rewrite
    show_only = args.show
    process_only_filenum = args.process_only_filenum

    if not rewrite and not show_only:
        log.warning("Not rewriting and not showing; will just catalogue files "
                    "and report things it's changing")

    walk_source_dir(SERVER_ROOT_DIR,
                    show_only=show_only,
                    rewrite=rewrite,
                    process_only_filenum=process_only_filenum)
    walk_source_dir(TABLET_ROOT_DIR,
                    show_only=show_only,
                    rewrite=rewrite,
                    process_only_filenum=process_only_filenum)


if __name__ == "__main__":
    main()
