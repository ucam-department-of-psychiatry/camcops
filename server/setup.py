#!/usr/bin/env python

"""
setup.py

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

**camcops_server setup.py file, to build Python packages**

To use:

    python setup.py sdist

    twine upload dist/*

To install in development mode:

    pip install -e .

"""

import os
from setuptools import setup, find_packages

from camcops_server.cc_modules.cc_baseconstants import (
    DEFORM_SUPPORTS_CSP_NONCE,
)
from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
)


# =============================================================================
# Constants
# =============================================================================

# Directories
THIS_DIR = os.path.abspath(os.path.dirname(__file__))  # .../camcops/server

# Get the long description from the README file
with open(os.path.join(THIS_DIR, "README.rst"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

# Package dependencies
# - See what's installed with: pip freeze | sort --ignore-case
INSTALL_REQUIRES = [
    # -------------------------------------------------------------------------
    # Direct dependencies of CamCOPS
    # -------------------------------------------------------------------------
    "alembic==1.4.2",  # database migrations
    "asteval==0.9.25",  # safe-ish alternative to eval
    "cardinal_pythonlib==1.1.24",  # RNC libraries
    "celery==5.2.2",  # background tasks
    "colander==1.7.0",  # serialization/deserialization from web forms
    "CherryPy==18.6.0",  # web server
    (  # deform: web forms
        "deform @ git+https://github.com/RudolfCardinal/deform@b40ea6ccf5fdd3116405e0d5233387bf34e20b37#egg=deform-3.0.0.dev0a"  # noqa
        # ... "a" appended
        if DEFORM_SUPPORTS_CSP_NONCE
        else "deform==2.0.15"
    ),
    # 'deform-bootstrap==0.2.9',  # deform with layout made easier
    "distro==1.3.0",  # detecting Linux distribution  # REMOVE ONCE DOCKER PREFERRED  # noqa
    "dogpile.cache==0.9.2",  # web caching
    "factory_boy==3.2.1",  # easier test data creation
    "Faker==4.1.1",  # create fake data; for test and dummy database creation
    # FHIR export, our fork until https://github.com/smart-on-fhir/client-py/pull/105 is merged  # noqa
    "fhirclient @ git+https://github.com/ucam-department-of-psychiatry/client-py@128bbe3c2194a51ba6ff8cf880ef2fdb9bfcc2d6#egg=fhirclient-4.0.0.1",  # noqa: E501
    "flower==1.2.0",  # monitor for Celery
    "gunicorn==20.1.0",  # web server (Unix only)
    "hl7==0.3.5",  # For HL7 export
    # Celery dependency for Python <= 3.7; workaround import error
    # https://github.com/celery/celery/issues/7783; scheduled to be fixed in
    # Celery 5.3
    "importlib-metadata<5.0",
    "lockfile==0.12.2",  # File locking for background tasks
    "lxml==4.9.1",  # Will speed up openpyxl export [NO LONGER CRITICAL]
    "matplotlib==3.2.2",  # Used for trackers and some tasks. SLOW INSTALLATION.  # noqa
    "numpy==1.23.5",  # Used by some tasks. SLOW INSTALLATION.
    "paginate==0.5.6",  # pagination for web server
    "pendulum==2.1.2",  # date/time classes
    "pexpect==4.8.0",  # for open_sqlcipher.py
    "pdfkit==1.0.0",  # wkhtmltopdf interface, for PDF generation from HTML
    "phonenumbers==8.12.30",  # phone number parsing, storing and validating
    "pycap==1.1.1",  # REDCap integration
    "Pillow==9.3.0",  # used by a dependency; pin for security warnings
    "Pygments==2.13.0",  # Syntax highlighting for introspection/DDL
    "pyexcel-ods3==0.6.0",  # ODS spreadsheet export
    "pyexcel-xlsx==0.6.0",  # XLSX spreadsheet export
    "pyotp==2.6.0",  # Multi-factor authentication
    "pyramid==1.10.8",  # web framework
    "pyramid_debugtoolbar==4.6.1",  # debugging for Pyramid
    "pytest==7.2.0",  # automatic testing
    "qrcode[pil]==7.2",  # for registering with Authenticators
    "requests==2.26",  # in fetch_snomed_codes.py and cc_sms.py, but also required by something else?  # noqa
    "rich-argparse==0.5.0",  # colourful help
    "sadisplay==0.4.9",  # SQL Alchemy schema display script
    "scipy==1.9.3",  # used by some tasks. slow installation.
    "semantic_version==2.8.5",  # semantic versioning; better than semver
    "sqlalchemy==1.3.24",  # database access
    "statsmodels==0.13.5",  # e.g. logistic regression
    "twilio==7.9.3",  # SMS backend for Multi-factor authentication
    "urllib3==1.26.7",  # dependency, pinned to avoid vulnerabilities
    "Wand==0.6.1",  # ImageMagick binding
    # -------------------------------------------------------------------------
    # Not installed here
    # -------------------------------------------------------------------------
    # mysqlclient -- installed via Docker
    # 'PyMySQL==0.7.1',
    # ... for mysql+pymysql://... BEWARE FURTHER UPGRADES (e.g. to 0.7.11); may
    # break Pendulum handling
    # todo: setup.py: fix PyMySQL upgrade problem
    # -------------------------------------------------------------------------
    # Direct requirements of CamCOPS development tools
    # -------------------------------------------------------------------------
    "Babel==2.9.1",  # reads code, generates gettext files; dev only but was already installed  # noqa
    "pre-commit==2.20.0",  # development only, various sanity checks on code
    "scrapy==2.6.2",  # development only
    "sphinx==4.2.0",  # development only
    "sphinx_rtd_theme==1.0.0",  # development only
    # -------------------------------------------------------------------------
    # Dependencies of cardinal_pythonlib, whose versions we pin
    # -------------------------------------------------------------------------
    # mandatory
    "appdirs==1.4.4",
    "beautifulsoup4==4.9.1",
    "colorlog==4.1.0",
    "isodate==0.6.0",
    "openpyxl==3.0.4",  # also for pyexcel-xlsx
    "pandas==1.3.4",
    "prettytable==0.7.2",
    "psutil==5.7.0",
    "pyparsing==2.4.7",
    "pypdf==3.1.0",  # Used by cardinal_pythonlib.pdf
    "python-dateutil==2.8.1",  # date/time extensions.
    "sqlparse==0.4.2",
    # extra
    "py-bcrypt==0.4",  # used by cardinal_pythonlib.crypto
    # -------------------------------------------------------------------------
    # Dependencies of other things above
    # -------------------------------------------------------------------------
    "alabaster==0.7.12",  # for sphinx
    "amqp==5.0.6",  # for celery
    "Chameleon==3.8.1",  # for Deform
    "tornado==6.1",  # for celery
    "webob==1.8.6",  # for pyramid
]


# =============================================================================
# setup args
# =============================================================================

setup(
    name="camcops_server",
    version=CAMCOPS_SERVER_VERSION_STRING,
    description="CamCOPS server",
    long_description=LONG_DESCRIPTION,
    # The project's main homepage.
    url="https://camcops.readthedocs.org/",
    # Author details
    author="Rudolf Cardinal",
    author_email="rnc1001@cam.ac.uk",
    # Choose your license
    license="GNU General Public License v3 or later (GPLv3+)",
    # See https://pypi.org/classifiers/
    classifiers=[
        # How mature is this project?
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",  # noqa
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    keywords="cardinal",
    packages=find_packages(),  # finds all the .py files in subdirectories
    include_package_data=True,  # use MANIFEST.in during install?
    install_requires=INSTALL_REQUIRES,
    entry_points={
        "console_scripts": [
            # Format is 'script=module:function".
            "camcops_server=camcops_server.camcops_server:main",
            "camcops_server_meta=camcops_server.camcops_server_meta:meta_main",
            "camcops_backup_mysql_database=cardinal_pythonlib.tools.backup_mysql_database:main",  # noqa
            "camcops_windows_service=camcops_server.camcops_windows_service:main",  # noqa
            "camcops_print_latest_github_version=camcops_server.tools.print_latest_github_version:main",  # noqa
            "camcops_fetch_snomed_codes=camcops_server.tools.fetch_snomed_codes:main",  # noqa
        ]
    },
)


# =============================================================================
# Clean up
# =============================================================================

# No, don't clean up, keeping the copy helps us with "pip install -e ."
