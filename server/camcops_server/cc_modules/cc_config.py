#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_config.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**Read and represent a CamCOPS config file.**

Also contains various types of demonstration config file (CamCOPS, but also
``supervisord``, Apache, etc.) and demonstration helper scripts (e.g. MySQL).

There are CONDITIONAL AND IN-FUNCTION IMPORTS HERE; see below. This is to
minimize the number of modules loaded when this is used in the context of the
client-side database script, rather than the webview.

Moreover, it should not use SQLAlchemy objects directly; see ``celery.py``.

In particular, I tried hard to use a "database-unaware" (unbound) SQLAlchemy
ExportRecipient object. However, when the backend re-calls the config to get
its recipients, we get errors like:

.. code-block:: none

    [2018-12-25 00:56:00,118: ERROR/ForkPoolWorker-7] Task camcops_server.cc_modules.celery_tasks.export_to_recipient_backend[ab2e2691-c2fa-4821-b8cd-2cbeb86ddc8f] raised unexpected: DetachedInstanceError('Instance <ExportRecipient at 0x7febbeeea7b8> is not bound to a Session; attribute refresh operation cannot proceed',)
    Traceback (most recent call last):
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/celery/app/trace.py", line 382, in trace_task
        R = retval = fun(*args, **kwargs)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/celery/app/trace.py", line 641, in __protected_call__
        return self.run(*args, **kwargs)
      File "/home/rudolf/Documents/code/camcops/server/camcops_server/cc_modules/celery_tasks.py", line 103, in export_to_recipient_backend
        schedule_via_backend=False)
      File "/home/rudolf/Documents/code/camcops/server/camcops_server/cc_modules/cc_export.py", line 255, in export
        req, recipient_names=recipient_names, all_recipients=all_recipients)
      File "/home/rudolf/Documents/code/camcops/server/camcops_server/cc_modules/cc_config.py", line 1460, in get_export_recipients
        valid_names = set(r.recipient_name for r in recipients)
      File "/home/rudolf/Documents/code/camcops/server/camcops_server/cc_modules/cc_config.py", line 1460, in <genexpr>
        valid_names = set(r.recipient_name for r in recipients)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/sqlalchemy/orm/attributes.py", line 242, in __get__
        return self.impl.get(instance_state(instance), dict_)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/sqlalchemy/orm/attributes.py", line 594, in get
        value = state._load_expired(state, passive)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/sqlalchemy/orm/state.py", line 608, in _load_expired
        self.manager.deferred_scalar_loader(self, toload)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/sqlalchemy/orm/loading.py", line 813, in load_scalar_attributes
        (state_str(state)))
    sqlalchemy.orm.exc.DetachedInstanceError: Instance <ExportRecipient at 0x7febbeeea7b8> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: http://sqlalche.me/e/bhk3)

"""  # noqa

import codecs
import collections
import configparser
import contextlib
import datetime
import multiprocessing
import os
import logging
import re
from typing import Dict, Generator, List, Optional, Union

from cardinal_pythonlib.configfiles import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_loglevel,
    get_config_parameter_multiline
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.randomness import create_base64encoded_randomness
from cardinal_pythonlib.reprfunc import auto_repr
from cardinal_pythonlib.sqlalchemy.alembic_func import (
    get_current_and_head_revision,
)
from cardinal_pythonlib.sqlalchemy.engine_func import (
    is_sqlserver,
    is_sqlserver_2008_or_later,
)
from cardinal_pythonlib.sqlalchemy.logs import pre_disable_sqlalchemy_extra_echo_log  # noqa
from cardinal_pythonlib.sqlalchemy.schema import get_table_names
from cardinal_pythonlib.sqlalchemy.session import (
    get_safe_url_from_engine,
    make_mysql_url,
)
from cardinal_pythonlib.wsgi.reverse_proxied_mw import ReverseProxiedMiddleware
import celery.schedules
from pendulum import DateTime as Pendulum
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqlASession

from camcops_server.cc_modules.cc_baseconstants import (
    ALEMBIC_BASE_DIR,
    ALEMBIC_CONFIG_FILENAME,
    ALEMBIC_VERSION_TABLE,
    CAMCOPS_EXECUTABLE,
    CAMCOPS_SERVER_DIRECTORY,
    DEFAULT_EXTRA_STRINGS_DIR,
    ENVVAR_CONFIG_FILE,
    LINUX_DEFAULT_LOCK_DIR,
    LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR,
    ON_READTHEDOCS,
    STATIC_ROOT_DIR,
)
from camcops_server.cc_modules.cc_cache import cache_region_static, fkg
from camcops_server.cc_modules.cc_constants import (
    ConfigParamExportRecipient,
    DEFAULT_CAMCOPS_LOGO_FILE,
    DEFAULT_CHERRYPY_SERVER_NAME,
    DEFAULT_GUNICORN_TIMEOUT_S,
    DEFAULT_HOST,
    DEFAULT_LOCAL_INSTITUTION_URL,
    DEFAULT_LOCAL_LOGO_FILE,
    DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES,
    DEFAULT_LOCKOUT_THRESHOLD,
    DEFAULT_MAX_THREADS,
    DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS,
    DEFAULT_PLOT_FONTSIZE,
    DEFAULT_PORT,
    DEFAULT_START_THREADS,
    DEFAULT_TIMEOUT_MINUTES,
    URL_PATH_ROOT,
)
from camcops_server.cc_modules.cc_exportrecipientinfo import (
    DEFAULT_PATIENT_SPEC_IF_ANONYMOUS,
    ExportRecipientInfo,
)
from camcops_server.cc_modules.cc_exception import raise_runtime_error
from camcops_server.cc_modules.cc_filename import (
    FilenameSpecElement,
    PatientSpecElementForFilename,
)
from camcops_server.cc_modules.cc_pyramid import MASTER_ROUTE_CLIENT_API
from camcops_server.cc_modules.cc_snomed import (
    get_all_task_snomed_concepts,
    get_icd9_snomed_concepts_from_xml,
    get_icd10_snomed_concepts_from_xml,
    SnomedConcept,
)
from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

pre_disable_sqlalchemy_extra_echo_log()

# =============================================================================
# Constants
# =============================================================================

CONFIG_FILE_SITE_SECTION = "site"
CONFIG_FILE_SERVER_SECTION = "server"
CONFIG_FILE_EXPORT_SECTION = "export"

VALID_RECIPIENT_NAME_REGEX = r"^[\w_-]+$"
# ... because we'll use them for filenames, amongst other things
# https://stackoverflow.com/questions/10944438/
# https://regexr.com/


# =============================================================================
# Demo config
# =============================================================================

DEFAULT_CELERY_BROKER_URL = "amqp://"
DEFAULT_DB_NAME = 'camcops'
DEFAULT_DB_USER = 'YYY_USERNAME_REPLACE_ME'
DEFAULT_DB_PASSWORD = 'ZZZ_PASSWORD_REPLACE_ME'
DEFAULT_DB_READONLY_USER = 'QQQ_USERNAME_REPLACE_ME'
DEFAULT_DB_READONLY_PASSWORD = 'PPP_PASSWORD_REPLACE_ME'
DEFAULT_TIMEZONE = "UTC"
DUMMY_INSTITUTION_URL = 'http://www.mydomain/'


class ConfigParamSite(object):
    """
    Parameters allowed in the main section of the CamCOPS config file.
    """
    ALLOW_INSECURE_COOKIES = "ALLOW_INSECURE_COOKIES"
    CAMCOPS_LOGO_FILE_ABSOLUTE = "CAMCOPS_LOGO_FILE_ABSOLUTE"
    CLIENT_API_LOGLEVEL = "CLIENT_API_LOGLEVEL"
    CTV_FILENAME_SPEC = "CTV_FILENAME_SPEC"
    DB_URL = "DB_URL"
    DB_ECHO = "DB_ECHO"
    DISABLE_PASSWORD_AUTOCOMPLETE = "DISABLE_PASSWORD_AUTOCOMPLETE"
    EXTRA_STRING_FILES = "EXTRA_STRING_FILES"
    LOCAL_INSTITUTION_URL = "LOCAL_INSTITUTION_URL"
    LOCAL_LOGO_FILE_ABSOLUTE = "LOCAL_LOGO_FILE_ABSOLUTE"
    LOCKOUT_DURATION_INCREMENT_MINUTES = "LOCKOUT_DURATION_INCREMENT_MINUTES"
    LOCKOUT_THRESHOLD = "LOCKOUT_THRESHOLD"
    PASSWORD_CHANGE_FREQUENCY_DAYS = "PASSWORD_CHANGE_FREQUENCY_DAYS"
    PATIENT_SPEC = "PATIENT_SPEC"
    PATIENT_SPEC_IF_ANONYMOUS = "PATIENT_SPEC_IF_ANONYMOUS"
    SESSION_COOKIE_SECRET = "SESSION_COOKIE_SECRET"
    SESSION_TIMEOUT_MINUTES = "SESSION_TIMEOUT_MINUTES"
    SNOMED_TASK_XML_FILENAME = "SNOMED_TASK_XML_FILENAME"
    SNOMED_ICD9_XML_FILENAME = "SNOMED_ICD9_XML_FILENAME"
    SNOMED_ICD10_XML_FILENAME = "SNOMED_ICD10_XML_FILENAME"
    TASK_FILENAME_SPEC = "TASK_FILENAME_SPEC"
    TRACKER_FILENAME_SPEC = "TRACKER_FILENAME_SPEC"
    WEBVIEW_LOGLEVEL = "WEBVIEW_LOGLEVEL"
    WKHTMLTOPDF_FILENAME = "WKHTMLTOPDF_FILENAME"


class ConfigParamServer(object):
    """
    Parameters allowed in the web server section of the CamCOPS config file.
    """
    CHERRYPY_LOG_SCREEN = "CHERRYPY_LOG_SCREEN"
    CHERRYPY_ROOT_PATH = "CHERRYPY_ROOT_PATH"
    CHERRYPY_SERVER_NAME = "CHERRYPY_SERVER_NAME"
    CHERRYPY_THREADS_MAX = "CHERRYPY_THREADS_MAX"
    CHERRYPY_THREADS_START = "CHERRYPY_THREADS_START"
    DEBUG_REVERSE_PROXY = "DEBUG_REVERSE_PROXY"
    DEBUG_SHOW_GUNICORN_OPTIONS = "DEBUG_SHOW_GUNICORN_OPTIONS"
    DEBUG_TOOLBAR = "DEBUG_TOOLBAR"
    GUNICORN_DEBUG_RELOAD = "GUNICORN_DEBUG_RELOAD"
    GUNICORN_NUM_WORKERS = "GUNICORN_NUM_WORKERS"
    GUNICORN_TIMEOUT_S = "GUNICORN_TIMEOUT_S"
    HOST = "HOST"
    PORT = "PORT"
    PROXY_HTTP_HOST = "PROXY_HTTP_HOST"
    PROXY_REMOTE_ADDR = "PROXY_REMOTE_ADDR"
    PROXY_REWRITE_PATH_INFO = "PROXY_REWRITE_PATH_INFO"
    PROXY_SCRIPT_NAME = "PROXY_SCRIPT_NAME"
    PROXY_SERVER_NAME = "PROXY_SERVER_NAME"
    PROXY_SERVER_PORT = "PROXY_SERVER_PORT"
    PROXY_URL_SCHEME = "PROXY_URL_SCHEME"
    SSL_CERTIFICATE = "SSL_CERTIFICATE"
    SSL_PRIVATE_KEY = "SSL_PRIVATE_KEY"
    TRUSTED_PROXY_HEADERS = "TRUSTED_PROXY_HEADERS"
    UNIX_DOMAIN_SOCKET = "UNIX_DOMAIN_SOCKET"


class ConfigParamExportGeneral(object):
    """
    Parameters allowed in the ``[export]`` section of the CamCOPS config file.
    """
    CELERY_BEAT_EXTRA_ARGS = "CELERY_BEAT_EXTRA_ARGS"
    CELERY_BEAT_SCHEDULE_DATABASE = "CELERY_BEAT_SCHEDULE_DATABASE"
    CELERY_BROKER_URL = "CELERY_BROKER_URL"
    CELERY_WORKER_EXTRA_ARGS = "CELERY_WORKER_EXTRA_ARGS"
    EXPORT_LOCKDIR = "EXPORT_LOCKDIR"
    RECIPIENTS = "RECIPIENTS"
    SCHEDULE = "SCHEDULE"
    SCHEDULE_TIMEZONE = "SCHEDULE_TIMEZONE"


def get_demo_config(extra_strings_dir: str = None,
                    lock_dir: str = None,
                    static_dir: str = None,
                    db_url: str = None) -> str:
    """
    Returns a demonstration config file based on the specified parameters.
    """
    extra_strings_dir = extra_strings_dir or DEFAULT_EXTRA_STRINGS_DIR
    extra_strings_spec = os.path.join(extra_strings_dir, '*')
    lock_dir = lock_dir or LINUX_DEFAULT_LOCK_DIR
    static_dir = static_dir or STATIC_ROOT_DIR
    # ...
    # http://www.debian.org/doc/debian-policy/ch-opersys.html#s-writing-init
    # https://people.canonical.com/~cjwatson/ubuntu-policy/policy.html/ch-opersys.html  # noqa
    session_cookie_secret = create_base64encoded_randomness(num_bytes=64)

    if not db_url:
        db_url = make_mysql_url(username=DEFAULT_DB_USER,
                                password=DEFAULT_DB_PASSWORD,
                                dbname=DEFAULT_DB_NAME)
    return """
# Demonstration CamCOPS server configuration file.
# Created by CamCOPS server version {version} at {now}.
# See help at https://camcops.readthedocs.io/.

# =============================================================================
# CamCOPS site
# =============================================================================

[{CONFIG_FILE_SITE_SECTION}]

# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------

{cps.DB_URL} = {db_url}
{cps.DB_ECHO} = false

# -----------------------------------------------------------------------------
# URLs and paths
# -----------------------------------------------------------------------------

{cps.LOCAL_INSTITUTION_URL} = {DUMMY_INSTITUTION_URL}
{cps.LOCAL_LOGO_FILE_ABSOLUTE} = {static_dir}/logo_local.png
{cps.CAMCOPS_LOGO_FILE_ABSOLUTE} = {static_dir}/logo_camcops.png

{cps.EXTRA_STRING_FILES} = {extra_strings_spec}

{cps.SNOMED_TASK_XML_FILENAME} =
{cps.SNOMED_ICD9_XML_FILENAME} =
{cps.SNOMED_ICD10_XML_FILENAME} = 

{cps.WKHTMLTOPDF_FILENAME} =

# -----------------------------------------------------------------------------
# Login and session configuration
# -----------------------------------------------------------------------------

{cps.SESSION_COOKIE_SECRET} = camcops_autogenerated_secret_{session_cookie_secret}
{cps.SESSION_TIMEOUT_MINUTES} = 30
{cps.PASSWORD_CHANGE_FREQUENCY_DAYS} = 0
{cps.LOCKOUT_THRESHOLD} = 10
{cps.LOCKOUT_DURATION_INCREMENT_MINUTES} = 10
{cps.DISABLE_PASSWORD_AUTOCOMPLETE} = true

# -----------------------------------------------------------------------------
# Suggested filenames for saving PDFs from the web view
# -----------------------------------------------------------------------------

{cps.PATIENT_SPEC_IF_ANONYMOUS} = anonymous
{cps.PATIENT_SPEC} = {{{pse.SURNAME}}}_{{{pse.FORENAME}}}_{{{pse.ALLIDNUMS}}}

{cps.TASK_FILENAME_SPEC} = CamCOPS_{{patient}}_{{created}}_{{tasktype}}-{{serverpk}}.{{filetype}}
{cps.TRACKER_FILENAME_SPEC} = CamCOPS_{{patient}}_{{now}}_tracker.{{filetype}}
{cps.CTV_FILENAME_SPEC} = CamCOPS_{{patient}}_{{now}}_clinicaltextview.{{filetype}}

# -----------------------------------------------------------------------------
# Debugging options
# -----------------------------------------------------------------------------

{cps.WEBVIEW_LOGLEVEL} = info
{cps.CLIENT_API_LOGLEVEL} = info
{cps.ALLOW_INSECURE_COOKIES} = false


# =============================================================================
# Web server options
# =============================================================================

[{CONFIG_FILE_SERVER_SECTION}]

# -----------------------------------------------------------------------------
# Common web server options
# -----------------------------------------------------------------------------

{cpw.HOST} = {DEFAULT_HOST}
{cpw.PORT} = {DEFAULT_PORT}
{cpw.UNIX_DOMAIN_SOCKET} =
{cpw.SSL_CERTIFICATE} =
{cpw.SSL_PRIVATE_KEY} =

# -----------------------------------------------------------------------------
# WSGI options
# -----------------------------------------------------------------------------

{cpw.DEBUG_REVERSE_PROXY} = false
{cpw.DEBUG_TOOLBAR} = false
{cpw.PROXY_HTTP_HOST} =
{cpw.PROXY_REMOTE_ADDR} =
{cpw.PROXY_REWRITE_PATH_INFO} = false
{cpw.PROXY_SCRIPT_NAME} =
{cpw.PROXY_SERVER_NAME} =
{cpw.PROXY_SERVER_PORT} =
{cpw.PROXY_URL_SCHEME} =
{cpw.TRUSTED_PROXY_HEADERS} =
    HTTP_X_FORWARDED_HOST
    HTTP_X_FORWARDED_SERVER
    HTTP_X_FORWARDED_PORT
    HTTP_X_FORWARDED_PROTO
    HTTP_X_SCRIPT_NAME

# -----------------------------------------------------------------------------
# CherryPy options
# -----------------------------------------------------------------------------

{cpw.CHERRYPY_SERVER_NAME} = {DEFAULT_CHERRYPY_SERVER_NAME}
{cpw.CHERRYPY_THREADS_START} = {DEFAULT_START_THREADS}
{cpw.CHERRYPY_THREADS_MAX} = {DEFAULT_MAX_THREADS}
{cpw.CHERRYPY_LOG_SCREEN} = true
{cpw.CHERRYPY_ROOT_PATH} = {URL_PATH_ROOT}

# -----------------------------------------------------------------------------
# Gunicorn options
# -----------------------------------------------------------------------------

{cpw.GUNICORN_NUM_WORKERS} = {gunicorn_num_workers}
{cpw.GUNICORN_DEBUG_RELOAD} = False
{cpw.GUNICORN_TIMEOUT_S} = {DEFAULT_GUNICORN_TIMEOUT_S}
{cpw.DEBUG_SHOW_GUNICORN_OPTIONS} = False

# =============================================================================
# Export options
# =============================================================================

[{CONFIG_FILE_EXPORT_SECTION}]

{cpe.CELERY_BEAT_EXTRA_ARGS} =
{cpe.CELERY_BEAT_SCHEDULE_DATABASE} = {lock_dir}/camcops_celerybeat_schedule
{cpe.CELERY_BROKER_URL} = amqp://
{cpe.CELERY_WORKER_EXTRA_ARGS} =
{cpe.EXPORT_LOCKDIR} = {lock_dir}

{cpe.RECIPIENTS} =

{cpe.SCHEDULE_TIMEZONE} = {DEFAULT_TIMEZONE}
{cpe.SCHEDULE} =

# =============================================================================
# Details for each export recipient
# =============================================================================

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Example recipient
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Example (disabled because it's not in the {cpe.RECIPIENTS} list above)

[recipient:recipient_A]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # How to export
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{cpr.TRANSMISSION_METHOD} = hl7
{cpr.PUSH} = true
{cpr.TASK_FORMAT} = pdf
{cpr.XML_FIELD_COMMENTS} = true

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # What to export
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{cpr.ALL_GROUPS} = false
{cpr.GROUPS} =
    myfirstgroup
    mysecondgroup

{cpr.START_DATETIME_UTC} =
{cpr.END_DATETIME_UTC} =
{cpr.FINALIZED_ONLY} = true
{cpr.INCLUDE_ANONYMOUS} = true
{cpr.PRIMARY_IDNUM} = 1
{cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY} = true

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Options applicable to database exports
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
{cpr.DB_URL} = some_sqlalchemy_url
{cpr.DB_ECHO} = false
{cpr.DB_INCLUDE_BLOBS} = true
{cpr.DB_ADD_SUMMARIES} = true
{cpr.DB_PATIENT_ID_PER_ROW} = false

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Options applicable to e-mail exports
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
{cpr.EMAIL_HOST} = mysmtpserver.mydomain
{cpr.EMAIL_PORT} = 587
{cpr.EMAIL_USE_TLS} = true
{cpr.EMAIL_HOST_USERNAME} = myusername
{cpr.EMAIL_HOST_PASSWORD} = mypassword
{cpr.EMAIL_FROM} = CamCOPS computer <noreply@myinstitution.mydomain>
{cpr.EMAIL_SENDER} =
{cpr.EMAIL_REPLY_TO} = CamCOPS clinical administrator <admin@myinstitution.mydomain>
{cpr.EMAIL_TO} =
    Perinatal Psychiatry Admin <perinatal@myinstitution.mydomain>

{cpr.EMAIL_CC} =
    Dr Alice Bradford <alice.bradford@myinstitution.mydomain>
    Dr Charles Dogfoot <charles.dogfoot@myinstitution.mydomain>

{cpr.EMAIL_BCC} =
    superuser <root@myinstitution.mydomain>

{cpr.EMAIL_PATIENT_SPEC_IF_ANONYMOUS} = anonymous
{cpr.EMAIL_PATIENT_SPEC} = {{{pse.SURNAME}}}, {{{pse.FORENAME}}}, {{{pse.ALLIDNUMS}}}
{cpr.EMAIL_SUBJECT} = CamCOPS task for {{patient}}, created {{created}}: {{tasktype}}, PK {{serverpk}}
{cpr.EMAIL_BODY_IS_HTML} = false
{cpr.EMAIL_BODY} =
    Please find attached a new CamCOPS task for manual filing to the electronic
    patient record of
    
        {{patient}}
        
    Task type: {{tasktype}}
    Created: {{created}}
    CamCOPS server primary key: {{serverpk}}
    
    Yours faithfully,
    
    The CamCOPS computer.
    
{cpr.EMAIL_KEEP_MESSAGE} = false

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Options applicable to HL7
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{cpr.HL7_HOST} = myhl7server.mydomain
{cpr.HL7_PORT} = 2575
{cpr.HL7_PING_FIRST} = true
{cpr.HL7_NETWORK_TIMEOUT_MS} = 10000
{cpr.HL7_KEEP_MESSAGE} = false
{cpr.HL7_KEEP_REPLY} = false
{cpr.HL7_DEBUG_DIVERT_TO_FILE} =
{cpr.HL7_DEBUG_TREAT_DIVERTED_AS_SENT} = false

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Options applicable to file transfers/attachments
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{cpr.FILE_PATIENT_SPEC} = {{surname}}_{{forename}}_{{idshortdesc1}}{{idnum1}}
{cpr.FILE_PATIENT_SPEC_IF_ANONYMOUS} = anonymous
{cpr.FILE_FILENAME_SPEC} = /my_nfs_mount/mypath/CamCOPS_{{patient}}_{{created}}_{{tasktype}}-{{serverpk}}.{{filetype}}
{cpr.FILE_MAKE_DIRECTORY} = true
{cpr.FILE_OVERWRITE_FILES} = false
{cpr.FILE_EXPORT_RIO_METADATA} = false
{cpr.FILE_SCRIPT_AFTER_EXPORT} =

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Extra options for RiO metadata for file-based export
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{cpr.RIO_IDNUM} = 2
{cpr.RIO_UPLOADING_USER} = CamCOPS
{cpr.RIO_DOCUMENT_TYPE} = CC

    """.format(  # noqa
        CONFIG_FILE_EXPORT_SECTION=CONFIG_FILE_EXPORT_SECTION,
        CONFIG_FILE_SERVER_SECTION=CONFIG_FILE_SERVER_SECTION,
        CONFIG_FILE_SITE_SECTION=CONFIG_FILE_SITE_SECTION,
        cpe=ConfigParamExportGeneral,
        cpr=ConfigParamExportRecipient,
        cps=ConfigParamSite,
        cpw=ConfigParamServer,
        db_url=db_url,
        DEFAULT_CHERRYPY_SERVER_NAME=DEFAULT_CHERRYPY_SERVER_NAME,
        DEFAULT_DB_NAME=DEFAULT_DB_NAME,
        DEFAULT_DB_PASSWORD=DEFAULT_DB_PASSWORD,
        DEFAULT_DB_USER=DEFAULT_DB_USER,
        DEFAULT_GUNICORN_TIMEOUT_S=DEFAULT_GUNICORN_TIMEOUT_S,
        DEFAULT_HOST=DEFAULT_HOST,
        DEFAULT_MAX_THREADS=DEFAULT_MAX_THREADS,
        DEFAULT_PORT=DEFAULT_PORT,
        DEFAULT_START_THREADS=DEFAULT_START_THREADS,
        DEFAULT_TIMEZONE=DEFAULT_TIMEZONE,
        DUMMY_INSTITUTION_URL=DUMMY_INSTITUTION_URL,
        extra_strings_spec=extra_strings_spec,
        fse=FilenameSpecElement,
        gunicorn_num_workers=2 * multiprocessing.cpu_count(),
        lock_dir=lock_dir,
        now=str(Pendulum.now()),
        pse=PatientSpecElementForFilename,
        session_cookie_secret=session_cookie_secret,
        static_dir=static_dir,
        URL_PATH_ROOT=URL_PATH_ROOT,
        version=CAMCOPS_SERVER_VERSION_STRING,
    )


# =============================================================================
# Demo configuration files, other than the CamCOPS config file itself
# =============================================================================

DEFAULT_SOCKET_FILENAME = "/tmp/.camcops.sock"


def get_demo_supervisor_config(
        specimen_internal_port: int = DEFAULT_PORT,
        specimen_socket_file: str = DEFAULT_SOCKET_FILENAME) -> str:
    """
    Returns a demonstration ``supervisord`` config file based on the
    specified parameters.
    """
    return """
# =============================================================================
# Demonstration 'supervisor' (supervisord) config file for CamCOPS.
# Created by CamCOPS version {version} at {now}.
# =============================================================================
    # - Supervisor is a system for controlling background processes running on
    #   UNIX-like operating systems. See:
    #       http://supervisord.org
    #
    # - On Ubuntu systems, you would typically install supervisor with
    #       sudo apt install supervisor
    #   and then save this file as
    #       /etc/supervisor/conf.d/camcops.conf
    #
    # - IF YOU EDIT THIS FILE, run:
    #       sudo service supervisor restart
    #
    # - TO MONITOR SUPERVISOR, run:
    #       sudo supervisorctl status
    #   ... or just "sudo supervisorctl" for an interactive prompt.
    #
    # NOTES ON THE SUPERVISOR CONFIG FILE AND ENVIRONMENT:
    #
    # - Indented lines are treated as continuation (even in commands; no need
    #   for end-of-line backslashes or similar).
    # - The downside of that is that indented comment blocks can join onto your
    #   commands! Beware that.
    # - You can't put quotes around the directory variable
    #   (http://stackoverflow.com/questions/10653590).
    # - Python programs that are installed within a Python virtual environment
    #   automatically use the virtualenv's copy of Python via their shebang;
    #   you do not need to specify that by hand, nor the PYTHONPATH.
    # - The "environment" setting sets the OS environment. The "--env"
    #   parameter to gunicorn, if you use it, sets the WSGI environment.
    # - Creating a group (see below; a.k.a. a "heterogeneous process group")
    #   allows you to control all parts of CamCOPS together, as "camcops" in
    #   this example (see
    #   http://supervisord.org/configuration.html#group-x-section-settings).
    #
    # SPECIFIC EXTRA NOTES FOR CAMCOPS:
    #
    # - The MPLCONFIGDIR environment variable specifies a cache directory for 
    #   matplotlib, which greatly speeds up its subsequent loading.
    # - The typical "web server" user is "www-data" under Ubuntu Linux and
    #   "apache" under CentOS.

[program:camcops_server]

command = {CAMCOPS_EXECUTABLE} serve_gunicorn
    --config {CAMCOPS_CONFIG}

directory = {CAMCOPS_SERVER_DIRECTORY}
environment = MPLCONFIGDIR="{LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR}"
user = {USER}
stdout_logfile = {LOGDIR}/camcops_server.log
redirect_stderr = true
autostart = true
autorestart = true
startsecs = 30
stopwaitsecs = 60

[program:camcops_workers]

command = {CAMCOPS_EXECUTABLE} launch_workers
    --config {CAMCOPS_CONFIG}

directory = {CAMCOPS_SERVER_DIRECTORY}
environment = MPLCONFIGDIR="{LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR}"
user = {USER}
stdout_logfile = {LOGDIR}/camcops_workers.log
redirect_stderr = true
autostart = true
autorestart = true
startsecs = 30
stopwaitsecs = 60

[program:camcops_scheduler]

command = {CAMCOPS_EXECUTABLE} launch_scheduler
    --config {CAMCOPS_CONFIG}

directory = {CAMCOPS_SERVER_DIRECTORY}
environment = MPLCONFIGDIR="{LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR}"
user = {USER}
stdout_logfile = {LOGDIR}/camcops_scheduler.log
redirect_stderr = true
autostart = true
autorestart = true
startsecs = 30
stopwaitsecs = 60

[group:camcops]

programs = camcops_server, camcops_workers, camcops_scheduler

    """.format(
        CAMCOPS_CONFIG="/etc/camcops/camcops.conf",
        CAMCOPS_EXECUTABLE=CAMCOPS_EXECUTABLE,
        CAMCOPS_SERVER_DIRECTORY=CAMCOPS_SERVER_DIRECTORY,
        LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR=LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR,
        LOGDIR="/var/log/supervisor",
        now=str(Pendulum.now()),
        specimen_internal_port=specimen_internal_port,
        specimen_socket_file=specimen_socket_file,
        USER="www-data",
        version=CAMCOPS_SERVER_VERSION_STRING,
    )


def get_demo_apache_config(
        urlbase: str = "/camcops",
        specimen_internal_port: int = DEFAULT_PORT,
        specimen_socket_file: str = DEFAULT_SOCKET_FILENAME) -> str:
    """
    Returns a demo Apache HTTPD config file section applicable to CamCOPS.
    """
    return """
    # Demonstration Apache config file section for CamCOPS.
    # Created by CamCOPS version {version} at {now}.
    #
    # Under Ubuntu, the Apache config will be somewhere in /etc/apache2/
    # Under CentOS, the Apache config will be somewhere in /etc/httpd/
    #
    # This section should go within the <VirtualHost> directive for the secure
    # (SSL, HTTPS) part of the web site.

<VirtualHost *:443>
    # ...

    # =========================================================================
    # CamCOPS
    # =========================================================================
    # Apache operates on the principle that the first match wins. So, if we
    # want to serve CamCOPS but then override some of its URLs to serve static
    # files faster, we define the static stuff first.

        # ---------------------------------------------------------------------
        # 1. Serve static files
        # ---------------------------------------------------------------------
        # a) offer them at the appropriate URL
        # b) provide permission
        # c) disable ProxyPass for static files

        # Change this: aim the alias at your own institutional logo.

    Alias {urlbase}/static/logo_local.png {STATIC_ROOT_DIR}/logo_local.png

        # We move from more specific to less specific aliases; the first match
        # takes precedence. (Apache will warn about conflicting aliases if
        # specified in a wrong, less-to-more-specific, order.)

    Alias {urlbase}/static/ {STATIC_ROOT_DIR}/

    <Directory {STATIC_ROOT_DIR}>
        Require all granted

        # ... for old Apache version (e.g. 2.2), use instead:
        # Order allow,deny
        # Allow from all
    </Directory>

        # Don't ProxyPass the static files; we'll serve them via Apache.

    ProxyPassMatch ^{urlbase}/static/ !

        # ---------------------------------------------------------------------
        # 2. Proxy requests to the CamCOPS web server and back; allow access
        # ---------------------------------------------------------------------
        # ... either via an internal TCP/IP port (e.g. 1024 or higher, and NOT
        #     accessible to users);
        # ... or, better, via a Unix socket, e.g. /tmp/.camcops.sock
        #
        # NOTES
        # - When you ProxyPass {urlbase}, you should browse to
        #       https://YOURSITE{urlbase}
        #   and point your tablet devices to
        #       https://YOURSITE{urlbase}{MASTER_ROUTE_CLIENT_API}
        # - Don't specify trailing slashes for the ProxyPass and
        #   ProxyPassReverse directives.
        #   If you do, http://host/camcops will fail though
        #              http://host/camcops/ will succeed.
        # - Ensure that you put the CORRECT PROTOCOL (http, https) in the rules
        #   below.
        # - For ProxyPass options, see https://httpd.apache.org/docs/2.2/mod/mod_proxy.html#proxypass
        #   ... including "retry=0" to stop Apache disabling the connection for
        #       a while on failure.
        # - Using a socket
        #   - this requires Apache 2.4.9, and passes after the '|' character a
        #     URL that determines the Host: value of the request; see
        #     https://httpd.apache.org/docs/trunk/mod/mod_proxy.html#proxypass
        # - CamCOPS MUST BE TOLD about its location and protocol, because that
        #   information is critical for synthesizing URLs, but is stripped out
        #   by the reverse proxy system. There are two ways:
        #   (i)  specifying headers or WSGI environment variables, such as
        #        the HTTP(S) headers X-Forwarded-Proto and X-Script-Name below
        #        (CamCOPS is aware of these);
        #   (ii) specifying options to "camcops serve", including
        #           --script_name
        #           --scheme
        #        and optionally
        #           --server
        #
        # So:
        #
        # ~~~~~~~~~~~~~~~~~
        # (a) Reverse proxy
        # ~~~~~~~~~~~~~~~~~
        #
        # PORT METHOD
        # Note the use of "http" (reflecting the backend), not https (like the
        # front end).

    ProxyPass {urlbase} http://127.0.0.1:{specimen_internal_port} retry=0
    ProxyPassReverse {urlbase} http://127.0.0.1:{specimen_internal_port} retry=0

        # UNIX SOCKET METHOD (Apache 2.4.9 and higher)
        #
        # The general syntax is:
        #
        #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|PROTOCOL://HOST/EXTRA_URL_FOR_BACKEND retry=0
        #
        # Note that:
        #
        #   - the protocol should be http, not https (Apache deals with the
        #     HTTPS part and passes HTTP on)
        #   - the URL should not have a trailing slash
        #   - the EXTRA_URL_FOR_BACKEND needs to be (a) unique for each
        #     instance or Apache will use a single worker for multiple
        #     instances, and (b) blank for the backend's benefit. Since those
        #     two conflict when there's >1 instance, there's a problem.
        #   - Normally, HOST is given as localhost. It may be that this problem
        #     is solved by using a dummy unique value for HOST:
        #     https://bz.apache.org/bugzilla/show_bug.cgi?id=54101#c1
        #
        # If your Apache version is too old, you will get the error
        #
        #   "AH00526: Syntax error on line 56 of /etc/apache2/sites-enabled/SOMETHING:
        #    ProxyPass URL must be absolute!"
        #
        # On Ubuntu, if your Apache is too old, you could use
        #
        #   sudo add-apt-repository ppa:ondrej/apache2
        #
        # ... details at https://launchpad.net/~ondrej/+archive/ubuntu/apache2
        #
        # If you get this error:
        #
        #   AH01146: Ignoring parameter 'retry=0' for worker 'unix:/tmp/.camcops_gunicorn.sock|https://localhost' because of worker sharing
        #   https://wiki.apache.org/httpd/ListOfErrors
        #
        # ... then your URLs are overlapping and should be redone or sorted;
        # see http://httpd.apache.org/docs/2.4/mod/mod_proxy.html#workers
        #
        # The part that must be unique for each instance, with no part a
        # leading substring of any other, is THIS_BIT in:
        #
        #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|http://localhost/THIS_BIT retry=0
        #
        # If you get an error like this:
        #
        #   AH01144: No protocol handler was valid for the URL /SOMEWHERE. If you are using a DSO version of mod_proxy, make sure the proxy submodules are included in the configuration using LoadModule.
        #
        # Then do this:
        #
        #   sudo a2enmod proxy proxy_http
        #   sudo apache2ctl restart
        #
        # If you get an error like this:
        #
        #   ... [proxy_http:error] [pid 32747] (103)Software caused connection abort: [client 109.151.49.173:56898] AH01102: error reading status line from remote server httpd-UDS:0
        #       [proxy:error] [pid 32747] [client 109.151.49.173:56898] AH00898: Error reading from remote server returned by /camcops_bruhl/webview
        #
        # then check you are specifying http://, not https://, in the ProxyPass
        #
        # Other information sources:
        #
        # - https://emptyhammock.com/projects/info/pyweb/webconfig.html

    # ProxyPass /camcops unix:{specimen_socket_file}|http://dummy1 retry=0
    # ProxyPassReverse /camcops unix:{specimen_socket_file}|http://dummy1 retry=0

        # ~~~~~~~~~~~~~~~~~~~~~~~~~
        # (b) Allow proxy over SSL.
        # ~~~~~~~~~~~~~~~~~~~~~~~~~
        # Without this, you will get errors like:
        #   ... SSL Proxy requested for wombat:443 but not enabled [Hint: SSLProxyEngine]
        #   ... failed to enable ssl support for 0.0.0.0:0 (httpd-UDS)

    SSLProxyEngine on

    <Location /camcops>

            # ~~~~~~~~~~~~~~~~
            # (c) Allow access
            # ~~~~~~~~~~~~~~~~

        Require all granted

        # ... for old Apache version (e.g. 2.2), use instead:
        # Order allow,deny
        # Allow from all

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # (d) Tell the proxied application that we are using HTTPS, and
            #     where the application is installed
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #     ... https://stackoverflow.com/questions/16042647
            #
            # EITHER enable mod_headers (e.g. "sudo a2enmod headers") and set:

        RequestHeader set X-Forwarded-Proto https
        RequestHeader set X-Script-Name {urlbase}

            # and call CamCOPS like:
            #
            # camcops serve_gunicorn \\
            #       --config SOMECONFIG \\
            #       --trusted_proxy_headers \\
            #           HTTP_X_FORWARDED_HOST \\
            #           HTTP_X_FORWARDED_SERVER \\
            #           HTTP_X_FORWARDED_PORT \\
            #           HTTP_X_FORWARDED_PROTO \\
            #           HTTP_X_SCRIPT_NAME
            #
            # (X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Server are
            # supplied by Apache automatically)
            #
            # ... OR specify those options by hand in the CamCOPS command.

    </Location>

        # ---------------------------------------------------------------------
        # 3. For additional instances
        # ---------------------------------------------------------------------
        # (a) duplicate section 1 above, editing the base URL and CamCOPS
        #     connection (socket/port);
        # (b) you will also need to create an additional CamCOPS instance,
        #     as above;
        # (c) add additional static aliases (in section 2 above).
        #
        # HOWEVER, consider adding more CamCOPS groups, rather than creating
        # additional instances; the former are *much* easier to administer!


    #==========================================================================
    # SSL security (for HTTPS)
    #==========================================================================

        # You will also need to install your SSL certificate; see the
        # instructions that came with it. You get a certificate by creating a
        # certificate signing request (CSR). You enter some details about your
        # site, and a software tool makes (1) a private key, which you keep
        # utterly private, and (2) a CSR, which you send to a Certificate
        # Authority (CA) for signing. They send back a signed certificate, and
        # a chain of certificates leading from yours to a trusted root CA.
        #
        # You can create your own (a 'snake-oil' certificate), but your tablets
        # and browsers will not trust it, so this is a bad idea.
        #
        # Once you have your certificate: edit and uncomment these lines:

    # SSLEngine on

    # SSLCertificateKeyFile /etc/ssl/private/my.private.key

        # ... a private file that you made before creating the certificate
        # request, and NEVER GAVE TO ANYBODY, and NEVER WILL (or your
        # security is broken and you need a new certificate).

    # SSLCertificateFile /etc/ssl/certs/my.public.cert

        # ... signed and supplied to you by the certificate authority (CA),
        # from the public certificate you sent to them.

    # SSLCertificateChainFile /etc/ssl/certs/my-institution.ca-bundle

        # ... made from additional certificates in a chain, supplied to you by
        # the CA. For example, mine is univcam.ca-bundle, made with the
        # command:
        #
        # cat TERENASSLCA.crt UTNAddTrustServer_CA.crt AddTrustExternalCARoot.crt > univcam.ca-bundle

</VirtualHost>

    """.format(  # noqa
        MASTER_ROUTE_CLIENT_API=MASTER_ROUTE_CLIENT_API,
        now=str(Pendulum.now()),
        specimen_internal_port=specimen_internal_port,
        specimen_socket_file=specimen_socket_file,
        STATIC_ROOT_DIR=STATIC_ROOT_DIR,
        urlbase=urlbase,
        version=CAMCOPS_SERVER_VERSION_STRING,
    )


def get_demo_mysql_create_db() -> str:
    """
    Returns a demonstration MySQL script to create a CamCOPS database.
    (The database structure is then provided by the CamCOPS ``upgrade_db``
    command.)
    """
    return """
# First, from the Linux command line, log in to MySQL as root:

mysql --host=127.0.0.1 --port=3306 --user=root --password
# ... or the usual short form: mysql -u root -p

# Create the database:

CREATE DATABASE {DEFAULT_DB_NAME};

# Ideally, create another user that only has access to the CamCOPS database.
# You should do this, so that you don’t use the root account unnecessarily.

GRANT ALL PRIVILEGES ON {DEFAULT_DB_NAME}.* TO '{DEFAULT_DB_USER}'@'localhost' IDENTIFIED BY '{DEFAULT_DB_PASSWORD}';

# For future use: if you plan to explore your database directly for analysis,
# you may want to create a read-only user. Though it may not be ideal (check:
# are you happy the user can see the audit trail?), you can create a user with
# read-only access to the entire database like this:

GRANT SELECT {DEFAULT_DB_NAME}.* TO '{DEFAULT_DB_READONLY_USER}'@'localhost' IDENTIFIED BY '{DEFAULT_DB_READONLY_PASSWORD}';

# All done. Quit MySQL:

exit
    """.format(  # noqa
        DEFAULT_DB_NAME=DEFAULT_DB_NAME,
        DEFAULT_DB_USER=DEFAULT_DB_USER,
        DEFAULT_DB_PASSWORD=DEFAULT_DB_PASSWORD,
        DEFAULT_DB_READONLY_USER=DEFAULT_DB_READONLY_USER,
        DEFAULT_DB_READONLY_PASSWORD=DEFAULT_DB_READONLY_PASSWORD,
    )


def get_demo_mysql_dump_script() -> str:
    """
    Returns a demonstration script to dump all current MySQL databases.
    """
    return """#!/bin/bash

# Minimal simple script to dump all current MySQL databases.
# This file must be READABLE ONLY BY ROOT (or equivalent, backup)!
# The password is in cleartext.
# Once you have copied this file and edited it, perform:
#     sudo chown root:root <filename>
#     sudo chmod 700 <filename>
# Then you can add it to your /etc/crontab for regular execution.

BACKUPDIR='/var/backups/mysql'
BACKUPFILE='all_my_mysql_databases.sql'
USERNAME='root'  # MySQL username
PASSWORD='PPPPPP_REPLACE_ME'  # MySQL password

# Make directory unless it exists already:

mkdir -p $BACKUPDIR

# Dump the database:

mysqldump -u $USERNAME -p$PASSWORD --all-databases --force > $BACKUPDIR/$BACKUPFILE

# Make sure the backups (which may contain sensitive information) are only
# readable by the 'backup' user group:

cd $BACKUPDIR
chown -R backup:backup *
chmod -R o-rwx *
chmod -R ug+rw *

    """  # noqa


# =============================================================================
# Helper functions
# =============================================================================

def raise_missing(section: str, parameter: str) -> None:
    msg = "Config file: missing/blank parameter {} in section [{}]".format(
        parameter, section
    )
    raise_runtime_error(msg)


# =============================================================================
# CrontabEntry
# =============================================================================

class CrontabEntry(object):
    """
    Class to represent a ``crontab``-style entry.
    """
    def __init__(self,
                 line: str = None,
                 minute: Union[str, int, List[int]] = None,
                 hour: Union[str, int, List[int]] = None,
                 day_of_week: Union[str, int, List[int]] = None,
                 day_of_month: Union[str, int, List[int]] = None,
                 month_of_year: Union[str, int, List[int]] = None,
                 content: str = None) -> None:
        """
        Args:
            line:
                line of the form ``m h dow dom moy content content content``.
            minute:
                crontab "minute" entry
            hour:
                crontab "hour" entry
            day_of_week:
                crontab "day_of_week" entry
            day_of_month:
                crontab "day_of_month" entry
            month_of_year:
                crontab "month_of_year" entry
            content:
                crontab "thing to run" entry
        """
        has_line = bool(line)
        has_components = bool(minute and hour and day_of_week and
                              day_of_month and month_of_year and content)
        assert has_line != has_components, (
            "Specify either a crontab line or all the time components"
        )
        if has_line:
            components = line.split()
            assert len(components) >= 6, (
                "Must specify 5 time components and then contents"
            )
            minute, hour, day_of_week, day_of_month, month_of_year = (
                components[0:5]
            )
            content = " ".join(components[5:])

        self.minute = minute
        self.hour = hour
        self.day_of_week = day_of_week
        self.day_of_month = day_of_month
        self.month_of_year = month_of_year
        self.content = content

    def __repr__(self) -> str:
        return auto_repr(self, sort_attrs=False)

    def __str__(self) -> str:
        return "{} {} {} {} {} {}".format(
            self.minute,
            self.hour,
            self.day_of_week,
            self.day_of_month,
            self.month_of_year,
            self.content
        )

    def get_celery_schedule(self) -> celery.schedules.crontab:
        """
        Returns the corresponding Celery schedule.

        Returns:
            a :class:`celery.schedules.crontab`

        Raises:
            :exc:`celery.schedules.ParseException` if the input can't be parsed
        """
        return celery.schedules.crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year,
        )


# =============================================================================
# Configuration class. (It gets cached on a per-process basis.)
# =============================================================================

class CamcopsConfig(object):
    """
    Class representing the CamCOPS configuration.
    """

    def __init__(self, config_filename: str,
                 config_text: str = None) -> None:
        """
        Initialize by reading the config file.

        Args:
            config_filename: filename of the config file (usual method)
            config_text: text contents of the config file (alternative method
                for special circumstances); overrides ``config_filename``
        """
        def _get_str(section: str, paramname: str,
                     default: str = None) -> Optional[str]:
            return get_config_parameter(
                parser, section, paramname, str, default)

        def _get_bool(section: str, paramname: str, default: bool) -> bool:
            return get_config_parameter_boolean(
                parser, section, paramname, default)

        def _get_int(section: str, paramname: str,
                     default: int = None) -> Optional[int]:
            return get_config_parameter(
                parser, section, paramname, int, default)

        def _get_optional_int(section: str, paramname: str) -> Optional[int]:
            _s = get_config_parameter(parser, section, paramname, str, None)
            if not _s:
                return None
            try:
                return int(_s)
            except (TypeError, ValueError):
                log.warning(
                    "Configuration variable {} not found or improper in "
                    "section [{}]; using default of {!r}",
                    paramname, section, None)
                return None

        def _get_multiline(section: str, paramname: str) -> List[str]:
            return get_config_parameter_multiline(
                parser, section, paramname, [])

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Open config file
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.camcops_config_filename = config_filename
        parser = configparser.ConfigParser()

        if config_text:
            log.info("Reading config from supplied string")
            parser.read_string(config_text)
        else:
            if not config_filename:
                raise AssertionError(
                    "Environment variable {} not specified (and no "
                    "command-line alternative given)".format(
                        ENVVAR_CONFIG_FILE))
            log.info("Reading from config file: {!r}", config_filename)
            with codecs.open(config_filename, "r", "utf8") as file:
                parser.read_file(file)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Main section (in alphabetical order)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        s = CONFIG_FILE_SITE_SECTION
        cs = ConfigParamSite

        self.allow_insecure_cookies = _get_bool(s, cs.ALLOW_INSECURE_COOKIES, False)  # noqa

        self.camcops_logo_file_absolute = _get_str(s, cs.CAMCOPS_LOGO_FILE_ABSOLUTE, DEFAULT_CAMCOPS_LOGO_FILE)  # noqa
        self.ctv_filename_spec = _get_str(s, cs.CTV_FILENAME_SPEC)

        self.db_url = parser.get(s, cs.DB_URL)
        # ... no default: will fail if not provided
        self.db_echo = _get_bool(s, cs.DB_ECHO, False)
        self.client_api_loglevel = get_config_parameter_loglevel(parser, s, cs.CLIENT_API_LOGLEVEL, logging.INFO)  # noqa
        logging.getLogger("camcops_server.cc_modules.client_api").setLevel(self.client_api_loglevel)  # noqa
        # ... MUTABLE GLOBAL STATE (if relatively unimportant); *** fix

        self.disable_password_autocomplete = _get_bool(s, cs.DISABLE_PASSWORD_AUTOCOMPLETE, True)  # noqa

        self.extra_string_files = _get_multiline(s, cs.EXTRA_STRING_FILES)

        self.local_institution_url = _get_str(s, cs.LOCAL_INSTITUTION_URL, DEFAULT_LOCAL_INSTITUTION_URL)  # noqa
        self.local_logo_file_absolute = _get_str(s, cs.LOCAL_LOGO_FILE_ABSOLUTE, DEFAULT_LOCAL_LOGO_FILE)  # noqa
        self.lockout_threshold = _get_int(s, cs.LOCKOUT_THRESHOLD, DEFAULT_LOCKOUT_THRESHOLD)  # noqa
        self.lockout_duration_increment_minutes = _get_int(s, cs.LOCKOUT_DURATION_INCREMENT_MINUTES, DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES)  # noqa

        self.password_change_frequency_days = _get_int(s, cs.PASSWORD_CHANGE_FREQUENCY_DAYS, DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS)  # noqa
        self.patient_spec_if_anonymous = _get_str(s, cs.PATIENT_SPEC_IF_ANONYMOUS, DEFAULT_PATIENT_SPEC_IF_ANONYMOUS)  # noqa
        self.patient_spec = _get_str(s, cs.PATIENT_SPEC)
        # currently not configurable, but easy to add in the future:
        self.plot_fontsize = DEFAULT_PLOT_FONTSIZE

        session_timeout_minutes = _get_int(s, cs.SESSION_TIMEOUT_MINUTES, DEFAULT_TIMEOUT_MINUTES)  # noqa
        self.session_cookie_secret = _get_str(s, cs.SESSION_COOKIE_SECRET)
        self.session_timeout = datetime.timedelta(minutes=session_timeout_minutes)  # noqa
        self.snomed_task_xml_filename = _get_str(s, cs.SNOMED_TASK_XML_FILENAME)  # noqa
        self.snomed_icd9_xml_filename = _get_str(s, cs.SNOMED_ICD9_XML_FILENAME)  # noqa
        self.snomed_icd10_xml_filename = _get_str(s, cs.SNOMED_ICD10_XML_FILENAME)  # noqa

        self.task_filename_spec = _get_str(s, cs.TASK_FILENAME_SPEC)
        self.tracker_filename_spec = _get_str(s, cs.TRACKER_FILENAME_SPEC)

        self.webview_loglevel = get_config_parameter_loglevel(parser, s, cs.WEBVIEW_LOGLEVEL, logging.INFO)  # noqa
        logging.getLogger().setLevel(self.webview_loglevel)  # root logger
        # ... MUTABLE GLOBAL STATE (if relatively unimportant) *** fix
        self.wkhtmltopdf_filename = _get_str(s, cs.WKHTMLTOPDF_FILENAME)

        # More validity checks for the main section:
        if not self.patient_spec_if_anonymous:
            raise_missing(s, cs.PATIENT_SPEC_IF_ANONYMOUS)
        if not self.patient_spec:
            raise_missing(s, cs.PATIENT_SPEC)
        if not self.session_cookie_secret:
            raise_missing(s, cs.SESSION_COOKIE_SECRET)
        if not self.task_filename_spec:
            raise_missing(s, cs.TASK_FILENAME_SPEC)
        if not self.tracker_filename_spec:
            raise_missing(s, cs.TRACKER_FILENAME_SPEC)
        if not self.ctv_filename_spec:
            raise_missing(s, cs.CTV_FILENAME_SPEC)

        # To prevent errors:
        del s
        del cs

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Web server/WSGI section
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ws = CONFIG_FILE_SERVER_SECTION
        cw = ConfigParamServer

        self.cherrypy_log_screen = _get_bool(ws, cw.CHERRYPY_LOG_SCREEN, True)
        self.cherrypy_root_path = _get_str(ws, cw.CHERRYPY_ROOT_PATH, URL_PATH_ROOT)  # noqa
        self.cherrypy_server_name = _get_str(ws, cw.CHERRYPY_SERVER_NAME, DEFAULT_CHERRYPY_SERVER_NAME)  # noqa
        self.cherrypy_threads_max = _get_int(ws, cw.CHERRYPY_THREADS_MAX, DEFAULT_MAX_THREADS)  # noqa
        self.cherrypy_threads_start = _get_int(ws, cw.CHERRYPY_THREADS_START, DEFAULT_START_THREADS)  # noqa
        self.debug_reverse_proxy = _get_bool(ws, cw.DEBUG_REVERSE_PROXY, False)
        self.debug_show_gunicorn_options = _get_bool(ws, cw.DEBUG_SHOW_GUNICORN_OPTIONS, False)  # noqa
        self.debug_toolbar = _get_bool(ws, cw.DEBUG_TOOLBAR, False)
        self.gunicorn_debug_reload = _get_bool(ws, cw.GUNICORN_DEBUG_RELOAD, False)  # noqa
        self.gunicorn_num_workers = _get_int(ws, cw.GUNICORN_NUM_WORKERS, 2 * multiprocessing.cpu_count())  # noqa
        self.gunicorn_timeout_s = _get_int(ws, cw.GUNICORN_TIMEOUT_S, DEFAULT_GUNICORN_TIMEOUT_S)  # noqa
        self.host = _get_str(ws, cw.HOST, DEFAULT_HOST)
        self.port = _get_int(ws, cw.PORT, DEFAULT_PORT)
        self.proxy_http_host = _get_str(ws, cw.PROXY_HTTP_HOST)
        self.proxy_remote_addr = _get_str(ws, cw.PROXY_REMOTE_ADDR)
        self.proxy_rewrite_path_info = _get_bool(ws, cw.PROXY_REWRITE_PATH_INFO, False)  # noqa
        self.proxy_script_name = _get_str(ws, cw.PROXY_SCRIPT_NAME)
        self.proxy_server_name = _get_str(ws, cw.PROXY_SERVER_NAME)
        self.proxy_server_port = _get_optional_int(ws, cw.PROXY_SERVER_PORT)
        self.proxy_url_scheme = _get_str(ws, cw.PROXY_URL_SCHEME)
        self.ssl_certificate = _get_str(ws, cw.SSL_CERTIFICATE)
        self.ssl_private_key = _get_str(ws, cw.SSL_PRIVATE_KEY)
        self.trusted_proxy_headers = _get_multiline(ws, cw.TRUSTED_PROXY_HEADERS)  # noqa
        self.unix_domain_socket = _get_str(ws, cw.UNIX_DOMAIN_SOCKET)

        for tph in self.trusted_proxy_headers:
            if tph not in ReverseProxiedMiddleware.ALL_CANDIDATES:
                raise ValueError(
                    "Invalid {} value specified: was {!r}, options are "
                    "{}".format(
                        cw.TRUSTED_PROXY_HEADERS,
                        tph,
                        ReverseProxiedMiddleware.ALL_CANDIDATES))

        del ws
        del cw

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Export section
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        es = CONFIG_FILE_EXPORT_SECTION
        ce = ConfigParamExportGeneral

        self.celery_beat_extra_args = _get_multiline(es, ce.CELERY_BEAT_EXTRA_ARGS)  # noqa
        self.celery_beat_schedule_database = _get_str(es, ce.CELERY_BEAT_SCHEDULE_DATABASE)  # noqa
        if not self.celery_beat_schedule_database:
            raise_missing(es, ce.CELERY_BEAT_SCHEDULE_DATABASE)
        self.celery_broker_url = _get_str(es, ce.CELERY_BROKER_URL, DEFAULT_CELERY_BROKER_URL)  # noqa
        self.celery_worker_extra_args = _get_multiline(es, ce.CELERY_WORKER_EXTRA_ARGS)  # noqa

        self.export_lockdir = _get_str(es, ce.EXPORT_LOCKDIR)
        if not self.export_lockdir:
            raise_missing(es, ConfigParamExportGeneral.EXPORT_LOCKDIR)

        self.export_recipient_names = _get_multiline(CONFIG_FILE_EXPORT_SECTION, ce.RECIPIENTS)  # noqa
        # http://stackoverflow.com/questions/335695/lists-in-configparser
        duplicates = [name for name, count in
                      collections.Counter(self.export_recipient_names).items()
                      if count > 1]
        if duplicates:
            raise ValueError("Duplicate export recipients specified: "
                             "{!r}".format(duplicates))
        for recip_name in self.export_recipient_names:
            if re.match(VALID_RECIPIENT_NAME_REGEX, recip_name) is None:
                raise ValueError(
                    "Recipient names must be alphanumeric or _- only; was "
                    "{!r}".format(recip_name))
        if len(set(self.export_recipient_names)) != len(self.export_recipient_names):  # noqa
            raise ValueError("Recipient names contain duplicates")
        self._export_recipients = None  # type: List[ExportRecipientInfo]
        self._read_export_recipients(parser)

        self.schedule_timezone = _get_str(es, ce.SCHEDULE_TIMEZONE, DEFAULT_TIMEZONE)  # noqa

        self.crontab_entries = []  # type: List[CrontabEntry]
        crontab_lines = _get_multiline(es, ce.SCHEDULE)
        for crontab_line in crontab_lines:
            if crontab_line.startswith("#"):  # comment line
                continue
            crontab_entry = CrontabEntry(line=crontab_line)
            if crontab_entry.content not in self.export_recipient_names:
                raise ValueError(
                    "{} setting exists for non-existent recipient {}".format(
                        ce.SCHEDULE, crontab_entry.content))
            self.crontab_entries.append(crontab_entry)

        del es
        del ce

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Other attributes
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self._sqla_engine = None

    # -------------------------------------------------------------------------
    # Database functions
    # -------------------------------------------------------------------------

    def get_sqla_engine(self) -> Engine:
        """
        Returns an SQLAlchemy :class:`Engine`.

        I was previously misinterpreting the appropriate scope of an Engine.
        I thought: create one per request.
        But the Engine represents the connection *pool*.
        So if you create them all the time, you get e.g. a
        'Too many connections' error.

        "The appropriate scope is once per [database] URL per application,
        at the module level."

        - https://groups.google.com/forum/#!topic/sqlalchemy/ZtCo2DsHhS4
        - https://stackoverflow.com/questions/8645250/how-to-close-sqlalchemy-connection-in-mysql

        Now, our CamcopsConfig instance is cached, so there should be one of
        them overall. See get_config() below.

        Therefore, making the engine a member of this class should do the
        trick, whilst avoiding global variables.
        """  # noqa
        if self._sqla_engine is None:
            self._sqla_engine = create_engine(
                self.db_url,
                echo=self.db_echo,
                pool_pre_ping=True,
                # pool_size=0,  # no limit (for parallel testing, which failed)
            )
            log.debug("Created SQLAlchemy engine for URL {}",
                      get_safe_url_from_engine(self._sqla_engine))
        return self._sqla_engine

    @property
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def get_all_table_names(self) -> List[str]:
        """
        Returns all table names from the database.
        """
        log.debug("Fetching database table names")
        engine = self.get_sqla_engine()
        return get_table_names(engine=engine)

    def get_dbsession_raw(self) -> SqlASession:
        """
        Returns a raw SQLAlchemy Session.
        Avoid this -- use :func:`get_dbsession_context` instead.
        """
        engine = self.get_sqla_engine()
        maker = sessionmaker(bind=engine)
        dbsession = maker()  # type: SqlASession
        return dbsession

    @contextlib.contextmanager
    def get_dbsession_context(self) -> Generator[SqlASession, None, None]:
        """
        Context manager to provide an SQLAlchemy session that will COMMIT
        once we've finished, or perform a ROLLBACK if there was an exception.
        """
        dbsession = self.get_dbsession_raw()
        # noinspection PyBroadException
        try:
            yield dbsession
            dbsession.commit()
        except Exception:
            dbsession.rollback()
            raise
        finally:
            dbsession.close()

    def _assert_valid_database_engine(self) -> None:
        """
        Assert that our backend database is a valid type.

        Specifically, we prohibit:

        - SQL Server versions before 2008: they don't support timezones
          and we need that.
        """
        engine = self.get_sqla_engine()
        if not is_sqlserver(engine):
            return
        assert is_sqlserver_2008_or_later(engine), (
            "If you use Microsoft SQL Server as the back-end database for a "
            "CamCOPS server, it must be at least SQL Server 2008. Older "
            "versions do not have time zone awareness."
        )

    def _assert_database_is_at_head(self) -> None:
        """
        Assert that the current database is at its head (most recent) revision,
        by comparing its Alembic version number (written into the Alembic
        version table of the database) to the most recent Alembic revision in
        our ``camcops_server/alembic/versions`` directory.
        """
        current, head = get_current_and_head_revision(
            database_url=self.db_url,
            alembic_config_filename=ALEMBIC_CONFIG_FILENAME,
            alembic_base_dir=ALEMBIC_BASE_DIR,
            version_table=ALEMBIC_VERSION_TABLE,
        )
        if current == head:
            log.debug("Database is at correct (head) revision of {}", current)
        else:
            raise_runtime_error(
                "Database structure is at version {} but should be at "
                "version {}. CamCOPS will not start. Please use the "
                "'upgrade_db' command to fix this.".format(current, head))

    def assert_database_ok(self) -> None:
        """
        Asserts that our database engine is OK and our database structure is
        correct.
        """
        self._assert_valid_database_engine()
        self._assert_database_is_at_head()

    # -------------------------------------------------------------------------
    # SNOMED-CT functions
    # -------------------------------------------------------------------------

    def get_task_snomed_concepts(self) -> Dict[str, SnomedConcept]:
        """
        Returns all SNOMED-CT concepts for tasks.

        Returns:
            dict: maps lookup strings to :class:`SnomedConcept` objects
        """
        if not self.snomed_task_xml_filename:
            return {}
        return get_all_task_snomed_concepts(self.snomed_task_xml_filename)

    def get_icd9cm_snomed_concepts(self) -> Dict[str, List[SnomedConcept]]:
        """
        Returns all SNOMED-CT concepts for ICD-9-CM codes supported by CamCOPS.

        Returns:
            dict: maps ICD-9-CM codes to :class:`SnomedConcept` objects
        """
        if not self.snomed_icd9_xml_filename:
            return {}
        return get_icd9_snomed_concepts_from_xml(self.snomed_icd9_xml_filename)

    def get_icd10_snomed_concepts(self) -> Dict[str, List[SnomedConcept]]:
        """
        Returns all SNOMED-CT concepts for ICD-10-CM codes supported by
        CamCOPS.

        Returns:
            dict: maps ICD-10 codes to :class:`SnomedConcept` objects
        """
        if not self.snomed_icd10_xml_filename:
            return {}
        return get_icd10_snomed_concepts_from_xml(
            self.snomed_icd10_xml_filename)

    # -------------------------------------------------------------------------
    # Export functions
    # -------------------------------------------------------------------------

    def _read_export_recipients(
            self,
            parser: configparser.ConfigParser = None) -> None:
        """
        Loads
        :class:`camcops_server.cc_modules.cc_exportrecipientinfo.ExportRecipientInfo`
        objects from the config file. Stores them in
        ``self._export_recipients``.

        Note that these objects are **not** associated with a database session.

        Args:
            parser: optional :class:`configparser.ConfigParser` object.
        """
        self._export_recipients = []  # type: List[ExportRecipientInfo]
        for recip_name in self.export_recipient_names:
            log.debug("Loading export config for recipient {!r}", recip_name)
            recipient = ExportRecipientInfo.read_from_config(
                parser=parser, recipient_name=recip_name)
            self._export_recipients.append(recipient)

    def get_all_export_recipient_info(self) -> List["ExportRecipientInfo"]:
        """
        Returns all export recipients (in their "database unaware" form)
        specified in the config.

        Returns:
            list: of
            :class:`camcops_server.cc_modules.cc_exportrecipientinfo.ExportRecipientInfo`
        """  # noqa
        return self._export_recipients

    # -------------------------------------------------------------------------
    # File-based locks
    # -------------------------------------------------------------------------

    def get_export_lockfilename_db(self, recipient_name: str) -> str:
        """
        Returns a full path to a lockfile suitable for locking for a
        whole-database export to a particular export recipient.

        Args:
            recipient_name: name of the recipient

        Returns:
            a filename
        """
        filename = "camcops_export_db_{}".format(recipient_name)
        # ".lock" is appended automatically by the lockfile package
        return os.path.join(self.export_lockdir, filename)

    def get_export_lockfilename_task(self, recipient_name: str,
                                     basetable: str, pk: int) -> str:
        """
        Returns a full path to a lockfile suitable for locking for a
        single-task export to a particular export recipient.

        Args:
            recipient_name: name of the recipient
            basetable: task base table name
            pk: server PK of the task

        Returns:
            a filename
        """
        filename = "camcops_export_task_{}_{}_{}".format(
            recipient_name, basetable, pk)
        # ".lock" is appended automatically by the lockfile package
        return os.path.join(self.export_lockdir, filename)

    def get_master_export_recipient_lockfilename(self) -> str:
        """
        When we are modifying export recipients, we check "is this information
        the same as the current version in the databse", and if not, we write
        fresh information to the database. If lots of processes do that at the
        same time, we have a problem (usually a database deadlock) -- hence
        this lock.

        Returns:
            a filename
        """
        filename = "camcops_master_export_recipient"
        # ".lock" is appended automatically by the lockfile package
        return os.path.join(self.export_lockdir, filename)

    def get_celery_beat_pidfilename(self) -> str:
        """
        Process ID file (pidfile) used by ``celery beat --pidfile ...``.
        """
        filename = "camcops_celerybeat.pid"
        return os.path.join(self.export_lockdir, filename)


# =============================================================================
# Get config filename from an appropriate environment (WSGI or OS)
# =============================================================================

def get_config_filename_from_os_env() -> str:
    """
    Returns the config filename to use, from our operating system environment
    variable.

    (We do NOT trust the WSGI environment for this.)
    """
    config_filename = os.environ.get(ENVVAR_CONFIG_FILE)
    if not config_filename:
        raise AssertionError(
            "OS environment did not provide the required "
            "environment variable {}".format(ENVVAR_CONFIG_FILE))
    return config_filename


# =============================================================================
# Cached instances
# =============================================================================

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def get_config(config_filename: str) -> CamcopsConfig:
    """
    Returns a :class:`camcops_server.cc_modules.cc_config.CamcopsConfig` from
    the specified config filename.

    Cached.
    """
    return CamcopsConfig(config_filename)


# =============================================================================
# Get default config
# =============================================================================

def get_default_config_from_os_env() -> CamcopsConfig:
    """
    Returns the :class:`camcops_server.cc_modules.cc_config.CamcopsConfig`
    representing the config filename that we read from our operating system
    environment variable.
    """
    if ON_READTHEDOCS:
        return CamcopsConfig(config_filename="", config_text=get_demo_config())
    else:
        return get_config(get_config_filename_from_os_env())


# =============================================================================
# NOTES
# =============================================================================

TO_BE_IMPLEMENTED_AS_COMMAND_LINE_SWITCH = """

# -----------------------------------------------------------------------------
# Export to a staging database for CRIS, CRATE, or similar anonymisation
# software (anonymisation staging database; ANONSTAG)
# -----------------------------------------------------------------------------

{cp.ANONSTAG_DB_URL} = {anonstag_db_url}
{cp.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE} = /tmp/camcops_cris_dd_draft.tsv

*** Note that we must check that the anonymisation staging database doesn't
    have the same URL as the main one (or "isn't the same one" in a more
    robust fashion)! Because this is so critical, probably best to:
    - require a completely different database name
    - ensure no table names overlap (e.g. add a prefix)

"""
