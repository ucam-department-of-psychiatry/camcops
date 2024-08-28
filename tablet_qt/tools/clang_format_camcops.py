#!/usr/bin/env python

"""
tablet_qt/tools/clang_format_camcops.py

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

Run clang-format over all our C++ code.
The formatting is controlled by clang_format_camcops.yaml.

"""

# =============================================================================
# Imports
# =============================================================================

import argparse
from enum import Enum
import filecmp
import glob
import logging
import os
import shutil
from subprocess import Popen, PIPE
import sys
import tempfile
from typing import List, Set, Tuple

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter
from pygments.lexer import RegexLexer
from pygments.token import Comment, String, Text, Whitespace
from semantic_version import Version

from camcops_server.cc_modules.cc_baseconstants import (
    EXIT_SUCCESS,
    EXIT_FAILURE,
)

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

CLANG_FORMAT_VERSION = 15
CLANG_FORMAT_EXECUTABLE = f"clang-format-{CLANG_FORMAT_VERSION}"
DEFAULT_MAX_LINE_LENGTH = 79  # should match clang_format_camcops.yaml
DIFFTOOL = "meld"
ENC = sys.getdefaultencoding()
URL_INDICATORS = ("http://", "https://")


class Command(Enum):
    """
    Commands that can be given to this program. See "--help" for details.
    """

    CHECK = "check"
    DIFF = "diff"
    FINDLONGCOMMENTS = "findlongcomments"
    MODIFY = "modify"
    LIST = "list"
    PRINT = "print"


# =============================================================================
# Directories
# =============================================================================

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
CLANG_FORMAT_BASE_FILENAME = "clang_format_camcops.yaml"
CLANG_FORMAT_STYLE_FILE = os.path.abspath(
    os.path.join(THIS_DIR, CLANG_FORMAT_BASE_FILENAME)
)
CAMCOPS_CPP_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))

INCLUDE_GLOBS = [
    f"{CAMCOPS_CPP_DIR}/**/*.cpp",
    f"{CAMCOPS_CPP_DIR}/**/*.h",
]
EXCLUDE_GLOBS = [
    f"{CAMCOPS_CPP_DIR}/build**/**/*.cpp",
    f"{CAMCOPS_CPP_DIR}/build**/**/*.h",
    # Code by Qt whose format we won't fiddle with too much.
    f"{CAMCOPS_CPP_DIR}/**/boxlayouthfw.*",
    f"{CAMCOPS_CPP_DIR}/**/qcustomplot.*",
    f"{CAMCOPS_CPP_DIR}/**/qtlayouthelpers.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcachedresult.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcipherdriver.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcipherhelpers.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcipherresult.*",
]


# =============================================================================
# Find and print long comments
# =============================================================================


class CppCommentLexer(RegexLexer):
    """
    Pygments lexer to find C++ comments. Based on
    https://pygments.org/docs/lexerdevelopment/, but modified slightly.
    Now it produces all lines separately from within multiline comments,
    and deals with string literals a bit.
    """

    name = "C++ comment lexer"
    tokens = {
        "root": [
            # At the root level:
            # - We may as well remove plain newlines.
            (r"[\n]", Whitespace),
            # - Anything not including a forward slash or a double quote is
            #   text.
            (r"[^/\"]+", Text),
            # - The sequence /* starts a multiline comment (state: "comment").
            #   ADDED: [\n]?, to swallow a trailing newline.
            (r"/\*", Comment.Multiline, "comment"),
            # - The sequence // makes the rest of the line a comment.
            #   We can capture its contents in one go.
            #   It was r"//.*?$", but I'm not sure what the "?" was doing.
            (r"//.*$", Comment.Singleline),
            # - A double quote enters a string literal.
            (r"\"", String, "string"),
            # - A plain forward slash is still plain text.
            (r"/", Text),
        ],
        "comment": [
            # Within a multiline comment:
            # - Anything that doesn't include a star or a slash is
            #   part of the multiline comment. I have modified to end in $,
            #   thus creating separate tokens for each line.
            #   ADDED: swallow newlines
            (r"[\n]", Whitespace),
            #   PREVIOUSLY: (r"[^*/]+", Comment.Multiline),
            (r"[^*/\n]+", Comment.Multiline),
            # - DISABLED: the Pygments example used the following, meaning that
            #   a further /* entered a "deeper" level of comment, but that is
            #   not C++ syntax.
            #   (r"/\*", Comment.Multiline, "#push"),
            # - The sequence */ ends a multiline comment.
            (r"\*/", Comment.Multiline, "#pop"),
            # - A star or a forward slash, otherwise, remains within a comment.
            (r"[*/]", Comment.Multiline),
        ],
        "string": [
            # Within a string literal:
            # - We can escape double quotes.
            (r"\\\"", String),
            # - Otherwise a double quote ends the string.
            (r"\"", String, "#pop"),
            # - Anything else is part of the string (but we need to exclude
            #   a double quote here or it swallows up to the end of the line
            #   even beyond a closing quote; I'm not entirely sure why).
            (r"[^\"]+", String),
        ],
    }


def report_line(
    filename: str, linenum: int, text: str, bare: bool = False
) -> None:
    """
    Prints a line to stdout, preceded by its filename and line number, in
    conventional format.
    """
    if bare:
        print(text)
    else:
        print(f"{filename}:{linenum}, length {len(text)}: {text}")


def get_line_at_pos(contents: str, pos: int) -> Tuple[int, str]:
    """
    Takes a multi-line string, and an integer (zero-based) position. Returns
    a tuple of the line number and the line text, containing that position.
    """
    before = contents[:pos]
    start_of_line = before[before.rfind("\n") + 1 :]
    rest_of_line = contents[pos : contents.find("\n", pos)]
    linetext = start_of_line + rest_of_line
    linenum = before.count("\n") + 1
    return linenum, linetext


def print_long_comments(
    filename: str,
    maxlinelength: int = DEFAULT_MAX_LINE_LENGTH,
    ignore_urls: bool = False,
    bare: bool = False,
    debugtokens: bool = False,
) -> int:
    """
    Print any line in the file that is longer than maxlinelength and contains,
    or is part of, a C++ comment. Returns the number of long lines.

    Args:
        filename:
            File to read.
        maxlinelength:
            Maximum permissible line length.
        ignore_urls:
            Ignore any lines that contain a string from URL_INDICATORS.
        bare:
            Print offending lines bare.
        debugtokens:
            Report tokens, for debugging.
    """
    log.debug(
        f"Searching for comment lines >{maxlinelength} characters: {filename}"
    )

    num_long_lines = 0

    lines_seen = set()  # type: Set[int]
    with open(filename) as f:
        contents = f.read()
    lexer = CppCommentLexer()
    for pos, tokentype, tokentext in lexer.get_tokens_unprocessed(contents):
        if debugtokens:
            log.debug(f"{pos=}, {tokentype=}, {tokentext=}")
        if tokentype in (Comment.Multiline, Comment.Singleline):
            linenum, linetext = get_line_at_pos(contents, pos)
            if linenum not in lines_seen:
                lines_seen.add(linenum)
                if len(linetext) > maxlinelength:
                    if ignore_urls:
                        if any(u in linetext for u in URL_INDICATORS):
                            continue
                    report_line(filename, linenum, linetext, bare=bare)
                    num_long_lines += 1

    return num_long_lines


# =============================================================================
# Apply clang-format to our source code
# =============================================================================


def runit(cmdargs: List[str]) -> Tuple[str, str, int]:
    """
    Run an external command. Return tuple: stdout, stderr, returncode.
    """
    log.debug(cmdargs)
    p = Popen(cmdargs, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    output = output.decode(ENC)
    error = error.decode(ENC)
    return output, error, p.returncode


def clang_format_camcops_source() -> None:
    """
    Apply clang-format to CamCOPS C++ source code, to standardize code style.
    """
    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument(
        "command",
        type=str,
        choices=[x.value for x in Command],
        help=f"Command to execute. "
        f"{Command.CHECK.value!r}: ensure nothing needs modifying; return "
        f"exit code {EXIT_SUCCESS} if everything is OK and {EXIT_FAILURE} if "
        f"something needs fixing. "
        f"{Command.DIFF.value!r}: launch a diff for the first file specified. "
        f"{Command.FINDLONGCOMMENTS.value!r}: show lines that include or are "
        f"part of a C++ comment and are longer than the permitted length. "
        f"{Command.LIST.value!r}: list files only. "
        f"{Command.MODIFY.value!r}: modify all files in place. "
        f"{Command.PRINT.value!r}: print all results to stdout.",
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="*",
        help="Files to modify (leave blank for all).",
    )
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
    parser.add_argument(
        "--clangformat",
        type=str,
        default=shutil.which(CLANG_FORMAT_EXECUTABLE),
        help=f"Path to clang-format. Priority: (1) this argument, (2) the "
        f"results of 'which {CLANG_FORMAT_EXECUTABLE}'.",
    )
    parser.add_argument(
        "--maxlinelength",
        type=int,
        default=DEFAULT_MAX_LINE_LENGTH,
        help=f"Maximum line length for {Command.FINDLONGCOMMENTS.value!r} "
        f"command (does not affect clang-format, which is governed by our "
        f"preset {CLANG_FORMAT_BASE_FILENAME})",
    )
    parser.add_argument(
        "--ignore_urls",
        action="store_true",
        help=f"For {Command.FINDLONGCOMMENTS.value!r}, ignore any line that "
        f"contains any of: {URL_INDICATORS!r}",
    )
    parser.add_argument(
        "--bare",
        action="store_true",
        help=f"For {Command.FINDLONGCOMMENTS.value!r}, print lines bare",
    )
    parser.add_argument(
        "--debugtokens",
        action="store_true",
        help=f"For {Command.FINDLONGCOMMENTS.value!r}, show tokens. "
        f"Requires --verbose",
    )
    parser.add_argument(
        "--diffall",
        action="store_true",
        help=f"For {Command.DIFF.value!r}: proceed to diff all files, not "
        f"just the first",
    )
    parser.add_argument(
        "--diffskipidentical",
        action="store_true",
        help=f"For {Command.DIFF.value!r}: skip files that are identical "
        f"after reformatting",
    )
    parser.add_argument(
        "--difftool",
        type=str,
        default=shutil.which(DIFFTOOL),
        help=f"Tool to use for diff. Priority: (1) this argument, (2) the "
        f"results of 'which {DIFFTOOL}'",
    )
    args = parser.parse_args()

    if args.clangformat is None:
        log.error(
            "No clangformat executable was found on the path "
            f"({CLANG_FORMAT_EXECUTABLE!r}) and no "
            "--clangformat argument was specified"
        )
        sys.exit(EXIT_FAILURE)

    output, error, retcode = runit([args.clangformat, "--version"])
    if retcode:
        raise RuntimeError(f"clang-format error: \n{error}")

    version_words = output.split()
    version_number_index = version_words.index("version") + 1

    version = Version(version_words[version_number_index])
    if version.major != CLANG_FORMAT_VERSION:
        log.error(
            f"clang-format version {version.major} != {CLANG_FORMAT_VERSION}"
        )
        sys.exit(EXIT_FAILURE)

    command = Command(args.command)

    main_only_quicksetup_rootlogger(
        level=logging.DEBUG if args.verbose else logging.INFO
    )

    # -------------------------------------------------------------------------
    # Files
    # -------------------------------------------------------------------------

    # Files to process:
    if args.files:
        cpp_files = args.files
    else:
        cpp_files = set()  # type: Set[str]
        for inc in INCLUDE_GLOBS:
            cpp_files = cpp_files.union(glob.glob(inc, recursive=True))
        for exc in EXCLUDE_GLOBS:
            cpp_files = cpp_files.difference(glob.glob(exc, recursive=True))
        cpp_files = sorted(cpp_files)  # type: List[str]

    # -------------------------------------------------------------------------
    # Build clazy command
    # -------------------------------------------------------------------------
    # Basic arguments
    common_clangformat_args = [
        args.clangformat,  # executable
        "--Werror",  # warnings as errors
        f"-style=file:{CLANG_FORMAT_STYLE_FILE}",  # style control file
    ]
    if command == Command.MODIFY:
        common_clangformat_args.append("-i")  # edit in place
    if args.verbose:
        common_clangformat_args.append("--verbose")  # be verbose

    # -------------------------------------------------------------------------
    # Run it
    # -------------------------------------------------------------------------
    success = True
    for filename in cpp_files:
        filename = os.path.abspath(filename)
        if command == Command.CHECK:
            log.info(f"Checking: {filename}")
        elif command == Command.DIFF:
            log.info(f"Diff: {filename}")
        elif command == Command.FINDLONGCOMMENTS:
            num_long_lines = print_long_comments(
                filename,
                maxlinelength=args.maxlinelength,
                ignore_urls=args.ignore_urls,
                bare=args.bare,
                debugtokens=args.debugtokens,
            )
            if num_long_lines > 0:
                success = False
            continue
        elif command == Command.LIST:
            print(filename)
            continue
        elif command == Command.MODIFY:
            log.info(f"Modifying: {filename}")
        else:
            log.info(f"Printing: {filename}")
        # If we are in modification mode, the next command does the
        # modification directly:
        clangformatcmd = common_clangformat_args + [filename]
        output, error, retcode = runit(clangformatcmd)
        if retcode:
            raise RuntimeError("clang-format error: \n" + error)
        if command in (Command.CHECK, Command.DIFF):
            with tempfile.TemporaryDirectory() as tempdir:
                newfilename = os.path.join(
                    tempdir, os.path.basename(filename) + ".altered"
                )
                with open(newfilename, "wt") as f:
                    f.write(output)
                if command == Command.DIFF:
                    # Diff
                    if args.diffskipidentical and filecmp.cmp(
                        filename, newfilename
                    ):
                        log.info(f"Skipping unmodified file: {filename}")
                        continue
                    diffcmd = [args.difftool, filename, newfilename]
                    runit(diffcmd)
                    if not args.diffall:
                        log.info("Stopping after first diff")
                        break  # no more files
                else:
                    # Check
                    if not filecmp.cmp(filename, newfilename):
                        # Files differ
                        log.warning(f"File would be modified: {filename}")
                        success = False

        elif command == Command.PRINT:
            # Print
            print(output)

    sys.exit(EXIT_SUCCESS if success else EXIT_FAILURE)


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == "__main__":
    clang_format_camcops_source()
