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
    # The GitHub syntax (for development only) is:
    # "libraryname @ git+https://github.com/owner/reponame@commitsignature#egg==libraryname-version"  # noqa: E501
    "alembic==1.14.1",  # database migrations
    "asteval==1.0.6",  # safe-ish alternative to eval
    "black==24.4.2",  # auto code formatter, keep in sync with .pre-commit-config.yaml  # noqa: E501
    "cardinal_pythonlib==2.0.5",  # RNC libraries
    "celery==5.3.6",  # background tasks
    "colander==1.7.0",  # serialization/deserialization from web forms
    "CherryPy==18.6.0",  # web server
    (  # deform: web forms
        "deform @ git+https://github.com/RudolfCardinal/deform@b40ea6ccf5fdd3116405e0d5233387bf34e20b37#egg=deform-3.0.0.dev0a"  # noqa: E501
        # ... "a" appended
        if DEFORM_SUPPORTS_CSP_NONCE
        else "deform==2.0.15"
    ),
    # 'deform-bootstrap==0.2.9',  # deform with layout made easier
    "distro==1.3.0",  # detecting Linux distribution  # REMOVE ONCE DOCKER PREFERRED  # noqa: E501
    "dogpile.cache==0.9.2",  # web caching
    "factory_boy==3.2.1",  # easier test data creation
    "Faker==4.1.1",  # create fake data; for test and dummy database creation
    "fhirclient==4.2.0",  # FHIR export
    "flake8==5.0.4",  # code checks, keep in sync with .pre-commit-config.yaml
    "flower==2.0.1",  # monitor for Celery
    "gunicorn==23.0.0",  # web server (Unix only)
    "hl7==0.3.5",  # For HL7 export
    "lockfile==0.12.2",  # File locking for background tasks
    "lxml==4.9.4",  # Will speed up openpyxl export [NO LONGER CRITICAL]
    "matplotlib==3.9.4",  # Used for trackers and some tasks. SLOW INSTALLATION.  # noqa: E501
    "numpy==1.26.4",  # Used by some tasks. SLOW INSTALLATION.
    "paginate==0.5.6",  # pagination for web server
    "pendulum==3.0.0",  # date/time classes
    "pexpect==4.8.0",  # for open_sqlcipher.py
    "pdfkit==1.0.0",  # wkhtmltopdf interface, for PDF generation from HTML
    "phonenumbers==8.12.30",  # phone number parsing, storing and validating
    "pycap==1.1.1",  # REDCap integration
    "Pillow==10.3.0",  # used by a dependency; pin for security warnings
    "Pygments==2.15.0",  # Syntax highlighting for introspection/DDL
    "pyexcel-ods3==0.6.0",  # ODS spreadsheet export
    "pyexcel-xlsx==0.6.0",  # XLSX spreadsheet export
    "pyotp==2.6.0",  # Multi-factor authentication
    "pyramid==1.10.8",  # web framework
    "pyramid_debugtoolbar==4.6.1",  # debugging for Pyramid
    "pytest==8.3.4",  # automatic testing
    "pytest-env==1.1.5",  # automatic testing
    "qrcode[pil]==7.2",  # for registering with Authenticators
    "requests==2.32.4",  # in fetch_snomed_codes.py and cc_sms.py, but also required by something else?  # noqa: E501
    "rich-argparse==0.5.0",  # colourful help
    "sadisplay==0.4.9",  # SQL Alchemy schema display script
    "scipy==1.13.1",  # used by some tasks. slow installation.
    "semantic_version==2.8.5",  # semantic versioning; better than semver
    "sqlalchemy==2.0.39",  # database access
    "statsmodels==0.14.4",  # e.g. logistic regression
    "twilio==7.9.3",  # SMS backend for Multi-factor authentication
    "urllib3==2.5.0",  # requests dependency
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
    "Babel==2.9.1",  # reads code, generates gettext files; dev only but was already installed  # noqa: E501
    "pre-commit==2.20.0",  # development only, various sanity checks on code
    "sphinx==4.2.0",  # development only
    "sphinxcontrib-applehelp==1.0.4",  # development only
    "sphinxcontrib-devhelp==1.0.2",  # development only
    "sphinxcontrib-htmlhelp==2.0.1",  # development only
    "sphinxcontrib-serializinghtml==1.1.5",  # development only
    "sphinxcontrib-qthelp==1.0.3",  # development only
    "sphinx_rtd_theme==1.0.0",  # development only
    # -------------------------------------------------------------------------
    # Dependencies of cardinal_pythonlib, whose versions we pin
    # -------------------------------------------------------------------------
    # mandatory
    "appdirs==1.4.4",
    "beautifulsoup4==4.9.1",
    "colorlog==4.1.0",
    "isodate==0.6.0",
    "openpyxl==3.0.7",  # also for pyexcel-xlsx
    "pandas==1.4.4",
    "prettytable==0.7.2",
    "psutil==6.1.1",  # process management, cardinal_pythonlib dependency, not currently used  # noqa: E501
    "pyparsing==2.4.7",
    "pypdf==6.0.0",  # Used by cardinal_pythonlib.pdf
    "python-dateutil==2.9.0.post0",  # date/time extensions.
    "sqlparse==0.5.0",
    # extra
    "py-bcrypt==0.4",  # used by cardinal_pythonlib.crypto
    # -------------------------------------------------------------------------
    # Dependencies of other things above
    # -------------------------------------------------------------------------
    "alabaster==0.7.12",  # for sphinx
    "amqp==5.3.1",  # for celery
    "Chameleon==3.8.1",  # for Deform
    "tornado==6.5",  # for celery
    "webob==1.8.8",  # for pyramid
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
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",  # noqa: E501
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
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
            "camcops_backup_mysql_database=cardinal_pythonlib.tools.backup_mysql_database:main",  # noqa: E501
            "camcops_windows_service=camcops_server.camcops_windows_service:main",  # noqa: E501
            "camcops_print_latest_github_version=camcops_server.tools.print_latest_github_version:main",  # noqa: E501
            "camcops_fetch_snomed_codes=camcops_server.tools.fetch_snomed_codes:main",  # noqa: E501
        ]
    },
)


# =============================================================================
# Clean up
# =============================================================================

# No, don't clean up, keeping the copy helps us with "pip install -e ."
