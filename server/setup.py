#!/usr/bin/env python
# setup.py

"""
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

camcops_server setup file

To use:

    python setup.py sdist --extras

    twine upload dist/*

To install in development mode:

    pip install -e .

"""
# https://packaging.python.org/en/latest/distributing/#working-in-development-mode
# http://python-packaging-user-guide.readthedocs.org/en/latest/distributing/
# http://jtushman.github.io/blog/2013/06/17/sharing-code-across-applications-with-python/  # noqa

import argparse
import fnmatch
import os
from pprint import pformat
from setuptools import setup, find_packages
import shutil
import subprocess
import sys
from typing import List

from camcops_server.cc_modules.cc_baseconstants import (
    INTROSPECTABLE_EXTENSIONS,
    TABLET_SOURCE_COPY_DIR,
)
from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
)

# =============================================================================
# Constants
# =============================================================================

# Extensions and file patterns
COPYABLE_EXTENSIONS = INTROSPECTABLE_EXTENSIONS + ['.png']
SKIP_PATTERNS = ['*.pyc', '~*']  # files not to add

# Directories
THIS_DIR = os.path.abspath(os.path.dirname(__file__))  # .../camcops/server
EGG_DIR = os.path.join(THIS_DIR, 'camcops_server.egg-info')
CAMCOPS_ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))  # .../camcops  # noqa
DOC_ROOT_DIR = os.path.join(CAMCOPS_ROOT_DIR, "documentation")
CAMCOPS_SERVER_DIR = os.path.join(THIS_DIR, 'camcops_server')

# Files
MANIFEST_FILE = os.path.join(THIS_DIR, 'MANIFEST.in')
PIP_REQ_FILE = os.path.join(THIS_DIR, 'requirements.txt')
DOCMAKER = os.path.join(DOC_ROOT_DIR, "rebuild_docs_and_distribute.py")

# Arguments
EXTRAS_ARG = 'extras'

# Get the long description from the README file
with open(os.path.join(THIS_DIR, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

# Package dependencies
INSTALL_REQUIRES = [
    # 'aenum==2.0.9',  # advanced enums
    'alembic==0.9.9',  # database migrations
    # 'arrow==0.10.0',  # better datetime
    'cardinal_pythonlib==1.0.23',  # RNC libraries
    'colorlog==3.1.4',  # colour in logs
    'CherryPy==16.0.2',  # web server
    'deform==2.0.5',  # web forms
    # 'deform-bootstrap==0.2.9',  # deform with layout made easier
    'distro==1.3.0',  # detecting Linux distribution
    'dogpile.cache==0.6.6',  # web caching
    'gunicorn==19.8.1',
    # Alternative 'internal' web server. Installs fine under Windows, but won't run (ImportError: No module named 'fcntl').  # noqa
    'hl7==0.3.4',  # For HL7 export
    'lockfile==0.12.2',  # File locking for background tasks
    'matplotlib==2.2.0',
    # Used for trackers and some tasks. SLOW INSTALLATION.  # noqa
    'mysqlclient==1.3.13',  # for mysql+mysqldb://...
    'numpy==1.14.5',  # Used by some tasks. SLOW INSTALLATION.
    'paginate==0.5.6',  # pagination for web server
    'pendulum==2.0.2',  # better than Arrow
    'pdfkit==0.6.1',  # wkhtmltopdf interface, for PDF generation from HTML
    'py-bcrypt==0.4',  # Used by rnc_crypto; for bcrypt
    'Pygments==2.2.0',  # Syntax highlighting for introspection
    'PyMySQL==0.7.1',
    # for mysql+pymysql://... BEWARE FURTHER UPGRADES (e.g. to 0.7.11); may break Pendulum handling *** FIX THIS *** # noqa
    'PyPDF2==1.26.0',  # Used by rnc_pdf.py
    'pyramid==1.9.2',  # web framework
    'pyramid_debugtoolbar==4.4',  # debugging for Pyramid
    'python-dateutil==2.7.3',  # Date/time extensions.
    'pytz==2018.5',  # Timezone definitions, specifically UTC.
    'scipy==1.1.0',  # Used by some tasks. SLOW INSTALLATION.
    'semantic_version==2.6.0',  # semantic versioning; better than semver
    'sqlalchemy==1.2.8',  # database access
    # 'SQLAlchemy-Utils==0.32.16',  # extra column types
    'typing==3.6.4',  # part of stdlib in Python 3.5, but not 3.4
    'Wand==0.4.4',
    # ImageMagick for Python; used e.g. for BLOB PNG display; may need "sudo apt-get install libmagickwand-dev"  # noqa
    # Incompatible with Python 3.5; use paginate instead # 'WebHelpers==1.3',  # e.g. paginator and other tools for Pyramid  # noqa
    # 'Werkzeug==0.11.3',  # Profiling middleware
]


# =============================================================================
# Helper functions
# =============================================================================

def mkdir_p(path: str, verbose: bool = False) -> None:
    if verbose:
        print("Making directory: {}".format(path))
    os.makedirs(path, exist_ok=True)


def deltree(path: str, verbose: bool = False) -> None:
    if verbose:
        print("Deleting directory: {}".format(path))
    shutil.rmtree(path, ignore_errors=True)


def copier(src: str, dst: str, follow_symlinks: bool = True,
           verbose: bool = False) -> None:
    # Cleaner than a long "ignore" argument to shutil.copytree
    base, ext = os.path.splitext(os.path.basename(src))
    if ext.lower() not in COPYABLE_EXTENSIONS or base.startswith('.'):
        if verbose:
            print("Ignoring: {}".format(src))
        return
    if verbose:
        print("Copying {} -> {}".format(src, dst))
    # noinspection PyArgumentList
    shutil.copy2(src, dst, follow_symlinks=follow_symlinks)


def delete_empty_directories(root_dir: str, verbose: bool = False) -> None:
    # Based on
    # - http://stackoverflow.com/questions/26774892/how-to-find-recursively-empty-directories-in-python  # noqa
    # - https://docs.python.org/3/library/os.html
    empty_dirs = []
    for dir_, subdirs, files in os.walk(root_dir, topdown=False):
        all_subs_empty = True  # until proven otherwise
        for sub in subdirs:
            sub_fullpath = os.path.join(dir_, sub)
            if sub_fullpath not in empty_dirs:
                all_subs_empty = False
                break
        if all_subs_empty and len(files) == 0:
            empty_dirs.append(dir_)
            deltree(dir_, verbose=verbose)


def add_all_files(root_dir: str,
                  filelist: List[str],
                  absolute: bool = False,
                  include_n_parents: int = 0,
                  verbose: bool = False,
                  skip_patterns: List[str] = None) -> None:
    skip_patterns = skip_patterns or SKIP_PATTERNS
    if absolute:
        base_dir = root_dir
    else:
        base_dir = os.path.abspath(
            os.path.join(root_dir, *(['..'] * include_n_parents)))
    for dir_, subdirs, files in os.walk(root_dir, topdown=True):
        if absolute:
            final_dir = dir_
        else:
            final_dir = os.path.relpath(dir_, base_dir)
        for filename in files:
            _, ext = os.path.splitext(filename)
            final_filename = os.path.join(final_dir, filename)
            if any(fnmatch.fnmatch(final_filename, pattern)
                   for pattern in skip_patterns):
                if verbose:
                    print("Skipping: {}".format(final_filename))
                continue
            if verbose:
                print("Adding: {}".format(final_filename))
            filelist.append(final_filename)


# =============================================================================
# There's a nasty caching effect. So remove the old ".egg_info" directory
# =============================================================================
# http://blog.codekills.net/2011/07/15/lies,-more-lies-and-python-packaging-documentation-on--package_data-/  # noqa

deltree(EGG_DIR, verbose=True)

# Also...
# 1. Empircally, MANIFEST.in can get things copied.
# 2. Empirically, no MANIFEST.in but package_data can get things copied into
#    the .gz file, but not into the final distribution after installation.
# 3. So, we'll auto-write a MANIFEST.in
# 4. Argh! Still not installing
# - http://stackoverflow.com/questions/13307408/python-packaging-data-files-are-put-properly-in-tar-gz-file-but-are-not-install  # noqa
# - http://stackoverflow.com/questions/13307408/python-packaging-data-files-are-put-properly-in-tar-gz-file-but-are-not-install/32635882#32635882  # noqa
# - I think the problem is that MANIFEST.in paths need to be relative to the
#   location of setup.py, whereas package_data paths are relative to each
#   package (e.g. camcops_server).
# 5. AND... include_package_data
# - http://stackoverflow.com/questions/13307408/python-packaging-data-files-are-put-properly-in-tar-gz-file-but-are-not-install  # noqa
# - http://danielsokolowski.blogspot.co.uk/2012/08/setuptools-includepackagedata-option.html  # noqa


# =============================================================================
# Perform special actions if we're building a package
# =============================================================================
# Our script may be run by the developer (python setup.py sdist), or by pip
# (as a consequence of "pip install ..."). We only want to do the copying of
# source tablet files into our tree in the former situation. So we accept a
# special argument, act on it if present, and pass all other arguments (by
# writing them back to sys.argv) to the Python setuptools internals.

parser = argparse.ArgumentParser()
parser.add_argument(
    '--' + EXTRAS_ARG, action='store_true',
    help=(
        "USE THIS TO CREATE PACKAGES (e.g. 'python setup.py sdist --{}. "
        "Copies extra info in.".format(EXTRAS_ARG)
    )
)
our_args, leftover_args = parser.parse_known_args()
sys.argv[1:] = leftover_args

extra_files = []  # type: List[str]

if getattr(our_args, EXTRAS_ARG):
    src_tablet_qt = os.path.join(THIS_DIR, '..', 'tablet_qt')
    required_dirs = [src_tablet_qt]

    for d in required_dirs:
        if not os.path.isdir(d):
            print("You have used the --{} argument, but directory {!r} is "
                  "missing. That argument is only for use in development, to "
                  "create a Python package.".format(EXTRAS_ARG, d))
            sys.exit(1)

    # -------------------------------------------------------------------------
    # Documentation: Old OpenOffice/PDF manual format
    # -------------------------------------------------------------------------
    #
    # print("Converting manual ({!r}) to PDF ({!r})".format(
    #     MANUAL_FILENAME_ODT, MANUAL_FILENAME_PDF))
    # try:
    #     os.remove(MANUAL_FILENAME_PDF)  # don't delete the wrong one (again...)  # noqa
    # except OSError:
    #     pass
    # with tempfile.TemporaryDirectory() as tmpdirname:
    #     libreoffice_args = [
    #         "soffice",
    #         "--convert-to", "pdf:writer_pdf_Export",
    #         "--outdir", tmpdirname,
    #         MANUAL_FILENAME_ODT
    #     ]
    #     print("... calling: {!r}".format(libreoffice_args))
    #     subprocess.check_call(libreoffice_args)  # this is pretty nippy!
    #     shutil.move(
    #         os.path.join(tmpdirname, MANUAL_FILENAME_PDF_STEM),
    #         MANUAL_FILENAME_PDF
    #     )
    # assert os.path.exists(MANUAL_FILENAME_PDF), (
    #     "If this fails, there are a number of possible reasons, but one is "
    #     "simply that you're using LibreOffice for something else!"
    # )

    # -------------------------------------------------------------------------
    # Documentation (Sphinx format)
    # -------------------------------------------------------------------------
    print("Building and copying documentation...")
    subprocess.call([DOCMAKER])

    # -------------------------------------------------------------------------
    # Copy tablet source
    # -------------------------------------------------------------------------
    dst_tablet = TABLET_SOURCE_COPY_DIR
    print("Creating copy of tablet source files in {}".format(dst_tablet))

    dst_tablet_qt = os.path.join(dst_tablet, 'tablet_qt')

    deltree(dst_tablet)
    mkdir_p(dst_tablet)
    deltree(dst_tablet_qt)
    # noinspection PyArgumentList
    shutil.copytree(src=src_tablet_qt, dst=dst_tablet_qt, copy_function=copier)
    delete_empty_directories(dst_tablet)

    # -------------------------------------------------------------------------
    # Add extra files
    # -------------------------------------------------------------------------

    add_all_files(dst_tablet, extra_files, absolute=False, include_n_parents=1)
    # include_n_parents=1 means they start with "tablet_source_copy/"

    extra_files.append('alembic.ini')
    add_all_files(os.path.join(CAMCOPS_SERVER_DIR, 'alembic'),
                  extra_files, absolute=False, include_n_parents=1)
    add_all_files(os.path.join(CAMCOPS_SERVER_DIR, 'docs'),
                  extra_files, absolute=False, include_n_parents=1)
    add_all_files(os.path.join(CAMCOPS_SERVER_DIR, 'extra_strings'),
                  extra_files, absolute=False, include_n_parents=1)
    add_all_files(os.path.join(CAMCOPS_SERVER_DIR, 'extra_string_templates'),
                  extra_files, absolute=False, include_n_parents=1)
    add_all_files(os.path.join(CAMCOPS_SERVER_DIR, 'static'),
                  extra_files, absolute=False, include_n_parents=1)
    add_all_files(os.path.join(CAMCOPS_SERVER_DIR, 'templates'),
                  extra_files, absolute=False, include_n_parents=1)

    extra_files.sort()
    print("EXTRA_FILES: \n{}".format(pformat(extra_files)))

    # -------------------------------------------------------------------------
    # Write manifest
    # -------------------------------------------------------------------------
    MANIFEST_LINES = ['include camcops_server/' + x for x in extra_files]
    with open(MANIFEST_FILE, 'wt') as manifest:
        manifest.writelines([
            "# This is an AUTOCREATED file, MANIFEST.in; see setup.py and DO "
            "NOT EDIT BY HAND"])
        manifest.write("\n\n" + "\n".join(MANIFEST_LINES) + "\n")

    # -------------------------------------------------------------------------
    # Write requirements.txt
    # -------------------------------------------------------------------------
    with open(PIP_REQ_FILE, "w") as req_file:
        # subprocess.run(["pip", "freeze"], stdout=req_file)
        for line in INSTALL_REQUIRES:
            req_file.write(line + "\n")


# =============================================================================
# setup args
# =============================================================================

setup(
    name='camcops_server',

    version=CAMCOPS_SERVER_VERSION_STRING,

    description='CamCOPS server',
    long_description=LONG_DESCRIPTION,

    # The project's main homepage.
    url='https://www.camcops.org/',

    # Author details
    author='Rudolf Cardinal',
    author_email='rudolf@pobox.com',

    # Choose your license
    license='GNU General Public License v3 or later (GPLv3+)',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa

        'Natural Language :: English',

        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',

        'Topic :: Software Development :: Libraries',
    ],

    keywords='cardinal',

    packages=find_packages(),  # finds all the .py files in subdirectories

    # package_data ?
    # - http://blog.codekills.net/2011/07/15/lies,-more-lies-and-python-packaging-documentation-on--package_data-/  # noqa
    # - http://stackoverflow.com/questions/29036937/how-can-i-include-package-data-without-a-manifest-in-file  # noqa
    #
    # or MANIFEST.in ?
    # - http://stackoverflow.com/questions/24727709/i-dont-understand-python-manifest-in  # noqa
    # - http://stackoverflow.com/questions/1612733/including-non-python-files-with-setup-py  # noqa
    #
    # or both?
    # - http://stackoverflow.com/questions/3596979/manifest-in-ignored-on-python-setup-py-install-no-data-files-installed  # noqa
    # ... MANIFEST gets the files into the distribution
    # ... package_data gets them installed in the distribution
    #
    # data_files is from distutils, and we're using setuptools
    # - https://docs.python.org/3.5/distutils/setupscript.html#installing-additional-files  # noqa

    package_data={
        'camcops_server': extra_files,
    },

    include_package_data=True,  # use MANIFEST.in during install?

    install_requires=INSTALL_REQUIRES,

    entry_points={
        'console_scripts': [
            # Format is 'script=module:function".
            'camcops=camcops_server.camcops:main',
            'camcops_meta=camcops_server.camcops_meta:meta_main',
            'camcops_backup_mysql_database=cardinal_pythonlib.tools.backup_mysql_database:main',  # noqa
        ],
    },
)


# =============================================================================
# Clean up
# =============================================================================

# No, don't clean up, keeping the copy helps us with "pip install -e ."
