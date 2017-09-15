#!/usr/bin/env python
# camcops/server/tools/MAKE_PACKAGE.py

"""
For CentOS, you need to get Python 3 installed. For Centos 6, 64-bit:

    # http://stackoverflow.com/questions/8087184/installing-python3-on-rhel

    sudo yum install https://centos6.iuscommunity.org/ius-release.rpm

then for Python 3.4:
    sudo yum install python34u

or for Python 3.5 (with some other helpful things):
    sudo yum install python35u python35u-pip libxml2-devel libxslt-devel python35u-devel gcc

Note that you can get CentOS version/architecture with:

    cat /etc/centos-release
    uname -a
"""  # noqa

# We could use a temporary directory for the Debian build,
# but it's helpful to be able to see what it's doing as well.
# ... actually, let's do that, using mkdtemp(), so it'll linger if the build
# fails.

import argparse
import getpass
import logging
import os
from os.path import join
# import re
import shutil
import string
import subprocess
import sys
import tempfile

from cardinal_pythonlib.file_io import (
    get_lines_without_comments,
    remove_gzip_timestamp,
    webify_file,
    write_text,
    write_gzipped_text,
)
from cardinal_pythonlib.fileops import (
    # chown_r,
    copyglob,
    mkdir_p,
    # preserve_cwd,
)
from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

from camcops_server.cc_modules.cc_config import (
    DEFAULT_DB_NAME,
    DEFAULT_DB_PASSWORD,
    DEFAULT_DB_USER,
    get_demo_config,
)
from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
    CAMCOPS_CHANGEDATE,
)

# =============================================================================
# Python version requirements; set up logging
# =============================================================================

if sys.version_info[0] < 3:
    raise AssertionError("Need Python 3 or higher")
if sys.version_info[1] < 5:
    raise AssertionError("Need Python 3.5 or higher")

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', '-v', action='store_true')
args = parser.parse_args()
main_only_quicksetup_rootlogger(level=logging.DEBUG if args.verbose
                                else logging.INFO)

# =============================================================================
# URL defaults and other constants
# =============================================================================

PACKAGE = "camcops"

DSTSYSTEMPYTHON = 'python3'
# ... must be present on the path on the destination system

CAMCOPSHOSTNAME = 'mycomputer.mydomain'
URLBASE = 'camcops'
WEBVIEWSCRIPT = 'webview'
TABLETSCRIPT = 'database'

DEFAULT_GUNICORN_PORT = 8006
DEFAULT_GUNICORN_SOCKET = '/tmp/.camcops_gunicorn.sock'
# ... must be writable by the relevant user


# =============================================================================
# Helper functions
# =============================================================================

def workpath(workdir: str, destpath: str) -> str:
    """Suppose
        workdir == '/home/myuser/debianbuilding'
        destpath == '/usr/lib/mylib'
    then returns:
        '/home/myuser/debianbuilding/usr/lib/mylib'
    """
    if destpath[0] == os.sep:
        return join(workdir, destpath[1:])
    else:
        return join(workdir, destpath)


BASHFUNC = r"""

#------------------------------------------------------------------------------
# Helper functions
#------------------------------------------------------------------------------

command_exists()
{
    # arguments: $1 is the command to test
    # returns 0 (true) for found, 1 (false) for not found
    if command -v $1 >/dev/null; then return 0; else return 1; fi
}

running_centos()
{
    if [ -f /etc/system-release ] ; then
        SYSTEM=`cat /etc/system-release | cut -d' ' -f1`
        # VERSION=`cat /etc/system-release | cut -d' ' -f3`
        # SYSTEM_ID=\$SYSTEM-\$VERSION
        if ["$SYSTEM" == "CentOS"] ; then
            return 0  # true
        fi
    fi
    return 1  # false
}

service_exists()
{
    # Ubuntu used to give "unrecognized service" and now gives "not-found" (16.10)
    # grep for multiple patterns: http://unix.stackexchange.com/questions/37313/how-do-i-grep-for-multiple-patterns

    # arguments: $1 is the service being tested
    if service $1 status 2>&1 | grep -E 'unrecognized service|not-found' >/dev/null ; then
        return 1  # false
    fi
    return 0  # true
}

service_supervisord_command()
{
    # The exact supervisor program name is impossible to predict (e.g. in
    # "supervisorctl stop camcops-gunicorn"), so we just start/stop everything.
    # Ubuntu: service supervisor
    # CentOS: service supervisord

    cmd=$1
    if service_exists supervisord ; then
        echo "Executing: service supervisord $cmd"
        service supervisord $cmd || echo "Can't $cmd supervisord"
    else
        if service_exists supervisor ; then
            echo "Executing: service supervisor $cmd"
            service supervisor $cmd || echo "Can't $cmd supervisor"
        else
            echo "Don't know which supervisor/supervisord service to $cmd"
        fi
    fi
}

stop_supervisord()
{
    service_supervisord_command stop
}

restart_supervisord()
{
    service_supervisord_command restart
}

"""  # noqa


# =============================================================================
# Check prerequisites
# =============================================================================
# http://stackoverflow.com/questions/2806897
if os.geteuid() == 0:
    log.critical("This script should not be run using sudo or as the root user")
    sys.exit(1)

log.info("Checking prerequisites")
PREREQUISITES = (
    "alien dpkg-deb fakeroot find git gzip lintian rpmrebuild".split())
for cmd in PREREQUISITES:
    if shutil.which(cmd) is None:
        log.warning("""
To install Alien:
    sudo apt-get install alien
To install rpmrebuild:
    1. Download RPM from http://rpmrebuild.sourceforge.net/, e.g.
        cd /tmp
        wget http://downloads.sourceforge.net/project/rpmrebuild/rpmrebuild/2.11/rpmrebuild-2.11-1.noarch.rpm
    2. Convert to DEB:
        fakeroot alien --to-deb rpmrebuild-2.11-1.noarch.rpm
    3. Install:
        sudo dpkg --install rpmrebuild_2.11-2_all.deb
        """)  # noqa
        log.critical("{} command not found; stopping".format(cmd))
        sys.exit(1)


# RPM issues
# 1. A dummy camcops-prerequisites package works but is inelegant.
# 2. Alien seems to strip dependencies.
# 3. rpmrebuild does the job albeit not wholly intuitive documentation!
#    It also allows you to see what Alien was doing.

# =============================================================================
# Directory constants
# =============================================================================

THIS_DIR = os.path.dirname(os.path.abspath(__file__))  # tools
SETUP_PY_DIR = os.path.abspath(join(THIS_DIR, os.pardir))
PROJECT_BASE_DIR = os.path.abspath(join(THIS_DIR, os.pardir, os.pardir))
os.chdir(SETUP_PY_DIR)  # or setup.py looks in wrong places?

DSTBASEDIR = join('/usr/share', PACKAGE)
# Lintian dislikes files/subdirectories in: /usr/bin/X, /usr/local/X, /opt/X
# It dislikes images in /usr/lib

TMPDIR = tempfile.mkdtemp()
log.info("Temporary working directory: " + TMPDIR)
WRKDIR = join(TMPDIR, 'debian')
RPMTOPDIR = join(TMPDIR, 'rpmbuild')

SRCSERVERDIR = join(PROJECT_BASE_DIR, 'server')
WEBDOCSDIR = join(PROJECT_BASE_DIR, 'website', 'documentation')
PACKAGEDIR = join(SRCSERVERDIR, 'packagebuild')

WEB_VERSION_FILES_DIR = join(WEBDOCSDIR, 'version')

DSTDOCDIR = join('/usr/share/doc', PACKAGE)
WRKDOCDIR = workpath(WRKDIR, DSTDOCDIR)

WRKBASEDIR = workpath(WRKDIR, DSTBASEDIR)

DEBDIR = join(WRKDIR, 'DEBIAN')
# ... where Debian package control information lives
DEBOVERRIDEDIR = workpath(WRKDIR, '/usr/share/lintian/overrides')

DSTCONSOLEFILEDIR = '/usr/bin'
SETUPSCRIPTNAME = PACKAGE
WRKCONSOLEFILEDIR = workpath(WRKDIR, DSTCONSOLEFILEDIR)

WRKSERVERDIR = join(WRKBASEDIR, 'server')
DSTSERVERDIR = join(DSTBASEDIR, 'server')

SRCEXTRASTRINGS = join(SRCSERVERDIR, 'extra_strings')
WRKEXTRASTRINGS = join(WRKSERVERDIR, 'extra_strings')
DSTEXTRASTRINGS = join(DSTSERVERDIR, 'extra_strings')
SRCEXTRASTRINGTEMPLATES = join(SRCSERVERDIR, 'extra_string_templates')
WRKEXTRASTRINGTEMPLATES = join(WRKSERVERDIR, 'extra_string_templates')

DSTTEMPDIR = join(DSTBASEDIR, 'tmp')

SRCTOOLDIR = join(SRCSERVERDIR, 'tools')
WRKTOOLDIR = join(WRKSERVERDIR, 'tools')
DSTTOOLDIR = join(DSTSERVERDIR, 'tools')
VENVSCRIPT = 'install_virtualenv.py'
WKHTMLTOPDFSCRIPT = 'install_wkhtmltopdf.py'
METASCRIPT = 'camcops_meta.py'
DSTVENVSCRIPT = join(DSTTOOLDIR, VENVSCRIPT)
DSTWKHTMLTOPDFSCRIPT = join(DSTTOOLDIR, WKHTMLTOPDFSCRIPT)

MAINSCRIPTNAME = 'camcops.py'

METASCRIPTNAME = '{}_meta'.format(PACKAGE)

DSTMANDIR = '/usr/share/man/man1'  # section 1 for user commands
WRKMANDIR = workpath(WRKDIR, DSTMANDIR)

DSTSUPERVISORCONFDIR = '/etc/supervisor/conf.d'
WRKSUPERVISORCONFDIR = workpath(WRKDIR, DSTSUPERVISORCONFDIR)

DSTCONFIGDIR = join('/etc', PACKAGE)
WRKCONFIGDIR = workpath(WRKDIR, DSTCONFIGDIR)

DSTDPKGDIR = '/var/lib/dpkg/info'

DSTLOCKDIR = join('/var/lock', PACKAGE)
DSTPYTHONVENV = join(DSTBASEDIR, 'venv')
DSTVENVBIN = join(DSTPYTHONVENV, 'bin')
DSTPYTHONCACHE = join(DSTBASEDIR, '.cache')

# SRCSTATICDIR = join(SRCSERVERDIR, 'static')
SRCSTATICDIR = join(SRCSERVERDIR, 'camcops_server', 'static')
WRKSTATICDIR = join(WRKSERVERDIR, 'static')
DSTSTATICDIR = join(DSTSERVERDIR, 'static')

DSTMPLCONFIGDIR = '/var/cache/{}/matplotlib'.format(PACKAGE)
# Lintian dislikes using /var/local
WRKMPLCONFIGDIR = workpath(WRKDIR, DSTMPLCONFIGDIR)

# =============================================================================
# File constants
# =============================================================================

DSTCONSOLEFILE = join(DSTCONSOLEFILEDIR, SETUPSCRIPTNAME)
WRKCONSOLEFILE = join(WRKCONSOLEFILEDIR, SETUPSCRIPTNAME)

WRKMETACONSOLEFILE = join(WRKCONSOLEFILEDIR, METASCRIPTNAME)
DSTMETACONSOLEFILE = join(DSTCONSOLEFILEDIR, METASCRIPTNAME)

WRKMANFILE_BASE = join(WRKMANDIR, SETUPSCRIPTNAME + '.1')  # '.gz' appended
DSTMANFILE = join(DSTMANDIR, SETUPSCRIPTNAME + '.1.gz')
WRKMETAMANFILE_BASE = join(WRKMANDIR, METASCRIPTNAME + '.1')  # '.gz' appended
DSTMETAMANFILE = join(DSTMANDIR, METASCRIPTNAME + '.1.gz')

WRKDBDUMPFILE = join(WRKBASEDIR, 'demo_mysql_dump_script')
WEBDOCDBDUMPFILE = join(WEBDOCSDIR, 'demo_mysql_dump_script')
WRKMYSQLCREATION = join(WRKBASEDIR, 'demo_mysql_database_creation')
WEBDOCSMYSQLCREATION = join(WEBDOCSDIR, 'demo_mysql_database_creation')
WRKINSTRUCTIONS = join(WRKBASEDIR, 'instructions.txt')
DSTINSTRUCTIONS = join(DSTBASEDIR, 'instructions.txt')
WEBDOCINSTRUCTIONS = join(WEBDOCSDIR, 'instructions.txt')

DST_SUPERVISOR_CONF_FILE = join(DSTSUPERVISORCONFDIR, PACKAGE + '.conf')
WRK_SUPERVISOR_CONF_FILE = workpath(WRKDIR, DST_SUPERVISOR_CONF_FILE)
WEBDOC_SUPERVISOR_CONF_FILE = join(WEBDOCSDIR, 'supervisord_camcops.conf')

DSTCONFIGFILE = join(DSTCONFIGDIR, PACKAGE + '.conf')
WRKCONFIGFILE = join(WRKCONFIGDIR, PACKAGE + '.conf')
WEBDOCSCONFIGFILE = join(WEBDOCSDIR, PACKAGE + '.conf')

DSTHL7LOCKFILESTEM = join(DSTLOCKDIR, PACKAGE + '.hl7')
DSTSUMMARYTABLELOCKFILESTEM = join(DSTLOCKDIR, PACKAGE + '.summarytables')
# http://www.debian.org/doc/debian-policy/ch-opersys.html#s-writing-init

DSTREADME = join(DSTDOCDIR, 'README.txt')
WRKREADME = join(WRKDOCDIR, 'README.txt')

DEB_REQ_FILE = join(SRCSERVERDIR, 'requirements-deb.txt')
RPM_REQ_FILE = join(SRCSERVERDIR, 'requirements-rpm.txt')

DSTVENVPYTHON = join(DSTVENVBIN, 'python')
DSTVENVPIP = join(DSTVENVBIN, 'pip')

# For these names, see setup.py:
DST_CAMCOPS_LAUNCHER = join(DSTVENVBIN, 'camcops')
DST_CAMCOPS_META_LAUNCHER = join(DSTVENVBIN, 'camcops_meta')

# =============================================================================
# Version number and conditionals
# =============================================================================

MAINVERSION = CAMCOPS_SERVER_VERSION_STRING
CHANGEDATE = CAMCOPS_CHANGEDATE

DEBVERSION = MAINVERSION + '-1'
PACKAGENAME = join(
    PACKAGEDIR,
    '{PACKAGE}_{DEBVERSION}_all.deb'.format(PACKAGE=PACKAGE,
                                            DEBVERSION=DEBVERSION))
# upstream_version-debian_revision --
# see http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version

log.info("mainversion: {}".format(MAINVERSION))
log.info("changedate: {}".format(CHANGEDATE))


# =============================================================================
# Directories, files
# =============================================================================
# print("Deleting old workspace")
# shutil.rmtree(WRKDIR, ignore_errors=True)  # CAUTION!

# =============================================================================
log.info("Building Python package")
# =============================================================================

SETUP_PY = join(SRCSERVERDIR, 'setup.py')
SDIST_BASEFILENAME = ('camcops_server-{}.tar.gz'.format(MAINVERSION))
SRC_SDIST_FILE = join(SRCSERVERDIR, 'dist', SDIST_BASEFILENAME)
WRK_SDIST_FILE = join(WRKSERVERDIR, SDIST_BASEFILENAME)
DST_SDIST_FILE = join(DSTSERVERDIR, SDIST_BASEFILENAME)

try:
    log.info("Deleting old {} if it exists".format(SRC_SDIST_FILE))
    os.remove(SRC_SDIST_FILE)
except OSError:
    pass
cmdargs = ['python', SETUP_PY, 'sdist', '--extras']  # special!
log.info("Command: {}".format(cmdargs))
subprocess.check_call(cmdargs)
remove_gzip_timestamp(SRC_SDIST_FILE)

# =============================================================================
log.info("Making directories")
# =============================================================================
mkdir_p(DEBDIR)
mkdir_p(DEBOVERRIDEDIR)
mkdir_p(PACKAGEDIR)
mkdir_p(RPMTOPDIR)
mkdir_p(WRKCONFIGDIR)
mkdir_p(WRKCONSOLEFILEDIR)
mkdir_p(WRKDIR)
mkdir_p(WRKDOCDIR)
mkdir_p(WRKEXTRASTRINGS)
mkdir_p(WRKEXTRASTRINGTEMPLATES)
mkdir_p(WRKMANDIR)
mkdir_p(WRKMPLCONFIGDIR)
mkdir_p(WRKSERVERDIR)
mkdir_p(WRKSTATICDIR)
mkdir_p(WRKSUPERVISORCONFDIR)
mkdir_p(WRKTOOLDIR)
for d in "BUILD,BUILDROOT,RPMS,RPMS/noarch,SOURCES,SPECS,SRPMS".split(","):
    mkdir_p(join(RPMTOPDIR, d))

# =============================================================================
log.info("Copying files")
# =============================================================================
copyglob(join(SRCSERVERDIR, 'requirements*.txt'), WRKSERVERDIR)
copyglob(join(SRCSERVERDIR, 'changelog.Debian'), WRKDOCDIR)
subprocess.check_call(['gzip', '-n', '-9',
                       join(WRKDOCDIR, 'changelog.Debian')])
copyglob(join(SRCSERVERDIR, 'changelog.Debian'), WEB_VERSION_FILES_DIR)
# ... for the web site

copyglob(join(SRCSTATICDIR, '*'), WRKSTATICDIR, allow_nothing=True)
copyglob(join(SRCEXTRASTRINGS, '*'), WRKEXTRASTRINGS, allow_nothing=True)
copyglob(join(SRCEXTRASTRINGTEMPLATES, '*'), WRKEXTRASTRINGTEMPLATES,
         allow_nothing=True)
copyglob(join(SRCTOOLDIR, VENVSCRIPT), WRKTOOLDIR)
copyglob(join(SRCTOOLDIR, WKHTMLTOPDFSCRIPT), WRKTOOLDIR)

shutil.copyfile(SRC_SDIST_FILE, WRK_SDIST_FILE)

# =============================================================================
log.info("Creating man page. Will be installed as " + DSTMANFILE)
# =============================================================================
# http://www.fnal.gov/docs/products/ups/ReferenceManual/html/manpages.html

write_gzipped_text(WRKMANFILE_BASE, r""".\" Manpage for {SETUPSCRIPTNAME}.
.\" Contact rudolf@pobox.com to correct errors or typos.
.TH man 1 "{CHANGEDATE}" "{MAINVERSION}" "{SETUPSCRIPTNAME} man page"

.SH NAME
{SETUPSCRIPTNAME} \- run the CamCOPS command-line tool

.SH SYNOPSIS
.B {SETUPSCRIPTNAME} [
.I options
.B ] [
.I config-file
.B ]

.SH DESCRIPTION
The CamCOPS command-line tool allows you to create main tables (also specifying
the meaning of ID numbers), temporary summary tables, and superusers. It can
send HL7 messages and export files. It can perform some other test functions
and perform some user administration tasks. All other administration is via the
web interface.

A prerequisite is a MySQL database. For details, see http://www.camcops.org/

By default, the configuration file is {DSTCONFIGFILE},
and is readable only by the Apache user (typically www-data on Debian/Ubuntu
and apache on CentOS).

You may need to use "sudo -u www-data {SETUPSCRIPTNAME}" or
"sudo {SETUPSCRIPTNAME}", so that the script can read this file.

You will also need to point your web server (e.g. Apache) at the CamCOPS
scripts; see http://www.camcops.org/

.SH FOR DETAILS
.IP "camcops --help"
show all options

.SH EXAMPLES

.IP "sudo camcops --maketables /etc/camcops/camcops.conf"
Rebuild the tables for a database pointed to by
.B /etc/camcops/camcops.conf
, the specimen configuration file.

.SH SEE ALSO
http://www.camcops.org/

.SH AUTHOR
Rudolf Cardinal (rudolf@pobox.com)
""".format(
    SETUPSCRIPTNAME=SETUPSCRIPTNAME,
    CHANGEDATE=CHANGEDATE,
    MAINVERSION=MAINVERSION,
    DSTCONFIGFILE=DSTCONFIGFILE,
))

# =============================================================================
log.info("Creating man page. Will be installed as " + DSTMETAMANFILE)
# =============================================================================
# http://www.fnal.gov/docs/products/ups/ReferenceManual/html/manpages.html

write_gzipped_text(WRKMETAMANFILE_BASE, r""".\" Manpage for {METASCRIPTNAME}.
.\" Contact rudolf@pobox.com to correct errors or typos.
.TH man 1 "{CHANGEDATE}" "{MAINVERSION}" "{METASCRIPTNAME} man page"

.SH NAME
{METASCRIPTNAME} \- run the CamCOPS meta-command-line

.IP "camcops_meta --help"
show all options

.SH SEE ALSO
http://www.camcops.org/

.SH AUTHOR
Rudolf Cardinal (rudolf@pobox.com)
""".format(
    METASCRIPTNAME=METASCRIPTNAME,
    CHANGEDATE=CHANGEDATE,
    MAINVERSION=MAINVERSION,
    DSTCONFIGFILE=DSTCONFIGFILE,
))

# =============================================================================
log.info("Creating links to documentation. Will be installed as " + DSTREADME)
# =============================================================================
write_text(WRKREADME, """
CamCOPS: the Cambridge Cognitive and Psychiatric Test Kit

See http://www.camcops.org for documentation.
See also {DSTINSTRUCTIONS}
""".format(
    DSTINSTRUCTIONS=DSTINSTRUCTIONS,
))

# =============================================================================
log.info("Creating config file. Will be installed as " + DSTCONFIGFILE)
# =============================================================================
demo_config = get_demo_config(
    camcops_base_dir=DSTBASEDIR,
    extra_strings_dir=DSTEXTRASTRINGS,
    hl7_lockfile_stem=DSTHL7LOCKFILESTEM,
    lock_dir=DSTLOCKDIR,
    static_dir=DSTSTATICDIR,
    summary_table_lock_file_stem=DSTSUMMARYTABLELOCKFILESTEM
)
write_text(WRKCONFIGFILE, demo_config)
webify_file(WRKCONFIGFILE, WEBDOCSCONFIGFILE)


# =============================================================================
log.info("Creating launch script. Will be installed as " + DSTCONSOLEFILE)
# =============================================================================
write_text(WRKCONSOLEFILE, """#!/bin/bash
# Launch script for CamCOPS command-line tool.

echo 'Launching CamCOPS command-line tool...' >&2

{DST_CAMCOPS_LAUNCHER} "$@"

""".format(
    DST_CAMCOPS_LAUNCHER=DST_CAMCOPS_LAUNCHER,
))


# =============================================================================
log.info("Creating {} launch script. Will be installed as {}".format(
    METASCRIPTNAME, DSTMETACONSOLEFILE))
# =============================================================================
write_text(WRKMETACONSOLEFILE, """#!/bin/bash
# Launch script for CamCOPS meta-command tool tool.

echo 'Launching CamCOPS meta-command tool...' >&2

{DST_CAMCOPS_META_LAUNCHER} "$@"

""".format(
    DST_CAMCOPS_META_LAUNCHER=DST_CAMCOPS_META_LAUNCHER,
))


# =============================================================================
# echo "Creating wkhtmltopdf.sh launch screen to use standalone X server"
# =============================================================================
#
# cat << EOF > $WRKBASEDIR/wkhtmltopdf.sh
# #!/bin/bash
# xvfb-run --auto-servernum --server-args="-screen 0 640x480x16" \
#   /usr/bin/wkhtmltopdf "\$@"
# EOF


# =============================================================================
log.info("Creating control file")
# =============================================================================

DEPENDS_DEB = get_lines_without_comments(DEB_REQ_FILE)
DEPENDS_RPM = get_lines_without_comments(RPM_REQ_FILE)

write_text(join(DEBDIR, 'control'), """Package: {PACKAGE}
Version: {DEBVERSION}
Section: science
Priority: optional
Architecture: all
Maintainer: Rudolf Cardinal <rudolf@pobox.com>
Depends: {DEPENDENCIES}
Recommends: mysql-workbench
Description: Cambridge Cognitive and Psychiatric Test Kit (CamCOPS), server
 packages.
 This package contains the files necessary to run a CamCOPS server and receive
 information from the CamCOPS tablet applications (iOS, Android).
 .
 For more details, see http://www.camcops.org/
""".format(
    PACKAGE=PACKAGE,
    DEBVERSION=DEBVERSION,
    DEPENDENCIES=", ".join(DEPENDS_DEB),
))


# =============================================================================
log.info("Creating conffiles file. Will be installed as " +
         join(DSTDPKGDIR, PACKAGE + '.conffiles'))
# =============================================================================
configfiles = [DSTCONFIGFILE,
               DST_SUPERVISOR_CONF_FILE]
write_text(join(DEBDIR, 'conffiles'), "\n".join(configfiles))
# If a configuration file is removed by the user, it won't be reinstalled:
#   http://www.debian.org/doc/debian-policy/ap-pkg-conffiles.html
# In this situation, do "sudo aptitude purge camcops" then reinstall.


# =============================================================================
log.info("Creating preinst file. Will be installed as " +
         join(DSTDPKGDIR, PACKAGE + '.preinst'))
# =============================================================================
write_text(join(DEBDIR, 'preinst'), """#!/bin/bash
# Exit on any errors? (Lintian strongly advises this.)
set -e

{BASHFUNC}

echo '{PACKAGE}: preinst file executing'

# Would be nice just to shut down camcops processes. But there can be
# several, on live systems, and it's hard to predict what they're called. We
# need them shut down if we're going to check/reinstall the virtual
# environment (otherwise it'll be busy). So although we tried this:

stop_supervisord

echo '{PACKAGE}: preinst file finished'

""".format(
    BASHFUNC=BASHFUNC,
    PACKAGE=PACKAGE,
))

# =============================================================================
log.info("Creating postinst file. Will be installed as " +
         join(DSTDPKGDIR, PACKAGE + '.postinst'))
# =============================================================================

write_text(join(DEBDIR, 'postinst'), """#!/bin/bash
# Exit on any errors? (Lintian strongly advises this.)
set -e

echo '{PACKAGE}: postinst file executing'

{BASHFUNC}

#------------------------------------------------------------------------------
# Install Python virtual environment with packages
#------------------------------------------------------------------------------

echo 'About to install virtual environment'
export XDG_CACHE_HOME={DSTPYTHONCACHE}
{DSTSYSTEMPYTHON} {DSTVENVSCRIPT} {DSTPYTHONVENV} --skippackagechecks

echo 'About to install CamCOPS into virtual environment'
{DSTVENVPIP} install {DST_SDIST_FILE}

#------------------------------------------------------------------------------
echo 'Creating lockfile directory'
#------------------------------------------------------------------------------

mkdir -p {DSTLOCKDIR}

#------------------------------------------------------------------------------
# Set permissions
#------------------------------------------------------------------------------
# Ubuntu: www-data
# CentOS: apache

APACHEUSER=""
getent passwd www-data >/dev/null 2>&1 && APACHEUSER=www-data
if [[ -z "$APACHEUSER" ]]; then
    getent passwd apache >/dev/null 2>&1 && APACHEUSER=apache
fi

echo '{PACKAGE}: Setting permissions'
chmod 600 {DSTCONFIGFILE}
if [[ ! -z "$APACHEUSER" ]]; then
    chown $APACHEUSER:$APACHEUSER {DSTCONFIGFILE}
    chown $APACHEUSER:$APACHEUSER {DSTLOCKDIR}
    chown $APACHEUSER:$APACHEUSER {DSTMPLCONFIGDIR}
    chown $APACHEUSER:$APACHEUSER {DST_SUPERVISOR_CONF_FILE}
fi

#------------------------------------------------------------------------------
# NO - GUNICORN FIXES THIS // If Apache is installed, restart it
#------------------------------------------------------------------------------
# if command_exists apachectl; then
#     # OK for Ubuntu (apachectl = link to apache2ctl), CentOS
#     echo '{PACKAGE}: Restarting Apache (apachectl restart)'
#     apachectl restart
# fi

#------------------------------------------------------------------------------
# Restart supervisor process(es)
#------------------------------------------------------------------------------

restart_supervisord

#------------------------------------------------------------------------------
# Other things that we don't want strict dependencies on, or can't install now
#------------------------------------------------------------------------------

echo "========================================================================"
echo "1.  You may also need to install:"
echo "    [Ubuntu]"
echo "        sudo apt-get install apache2 libapache2-mod-proxy-html libapache2-mod-xsendfile"
# libapache2-mod-wsgi
echo "        sudo a2enmod proxy_http  # may be unnecessary"
echo "        sudo apt-get install mysql-client mysql-server"
echo "    [CentOS]"
echo "        sudo yum install httpd mod_proxy mod_xsendfile"
# mod_wsgi
echo "        sudo yum install mysql55 mysql55-server libmysqlclient-dev"
echo
echo "2.  Can't install wkhtmltopdf right now (dpkg database will be locked)."
echo "    Later, run this once:"
echo "    sudo {DSTSYSTEMPYTHON} {DSTWKHTMLTOPDFSCRIPT}"
echo "========================================================================"

echo '{PACKAGE}: postinst file finished'

""".format(  # noqa
    BASHFUNC=BASHFUNC,
    DST_SUPERVISOR_CONF_FILE=DST_SUPERVISOR_CONF_FILE,
    DSTCONFIGFILE=DSTCONFIGFILE,
    DSTLOCKDIR=DSTLOCKDIR,
    DSTMPLCONFIGDIR=DSTMPLCONFIGDIR,
    DSTPYTHONCACHE=DSTPYTHONCACHE,
    DSTPYTHONVENV=DSTPYTHONVENV,
    DST_SDIST_FILE=DST_SDIST_FILE,
    DSTSYSTEMPYTHON=DSTSYSTEMPYTHON,
    DSTVENVPIP=DSTVENVPIP,
    DSTVENVSCRIPT=DSTVENVSCRIPT,
    DSTWKHTMLTOPDFSCRIPT=DSTWKHTMLTOPDFSCRIPT,
    PACKAGE=PACKAGE,
))


# =============================================================================
log.info("Creating prerm file. Will be installed as " +
         join(DSTDPKGDIR, PACKAGE + '.prerm'))
# =============================================================================
write_text(join(DEBDIR, 'prerm'), """#!/bin/bash
set -e

{BASHFUNC}

echo '{PACKAGE}: prerm file executing'

stop_supervisord

# Must use -f or an error will cause the prerm (and package removal) to fail
# See /var/lib/dpkg/info/MYPACKAGE.prerm for manual removal!
find {DSTBASEDIR} -name '*.pyc' -delete
find {DSTBASEDIR} -name '*.pyo' -delete

# uninstall our package from venv (mainly for development, so we can re-use
# version numbers

{DSTVENVPIP} uninstall --yes camcops_server

echo '{PACKAGE}: prerm file finished'

""".format(
    BASHFUNC=BASHFUNC,
    PACKAGE=PACKAGE,
    DSTBASEDIR=DSTBASEDIR,
    DSTVENVPIP=DSTVENVPIP,
))

# =============================================================================
log.info("Creating postrm file. Will be installed as " +
         join(DSTDPKGDIR, PACKAGE + '.postrm'))
# =============================================================================
write_text(join(DEBDIR, 'postrm'), """#!/bin/bash
set -e

{BASHFUNC}

echo '{PACKAGE}: postrm file executing'

restart_supervisord

echo '{PACKAGE}: postrm file finished'

""".format(
    BASHFUNC=BASHFUNC,
    PACKAGE=PACKAGE,
    DSTBASEDIR=DSTBASEDIR,
))

# =============================================================================
log.info("Creating Lintian override file")
# =============================================================================
write_text(join(DEBOVERRIDEDIR, PACKAGE), """
# Not an official new Debian package, so ignore this one.
# If we did want to close a new-package ITP bug:
# http://www.debian.org/doc/manuals/developers-reference/pkgs.html#upload-bugfix  # noqa
{PACKAGE} binary: new-package-should-close-itp-bug
""".format(
    PACKAGE=PACKAGE,
))

# =============================================================================
log.info("Creating copyright file. Will be installed as " +
         join(DSTDOCDIR, 'copyright'))
# =============================================================================
write_text(join(WRKDOCDIR, 'copyright'), """{PACKAGE}

CAMCOPS

    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

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

    On Debian systems, see /usr/share/common-licenses/GPL-3

ADDITIONAL LIBRARY COMPONENTS

    Public domain or copyright (C) their respective authors (for details,
    see attribution in the source code and other license terms packaged with
    the source).

TEXT FOR SPECIFIC ASSESSMENT SCALES

    Public domain or copyright (C) their respective authors; see details in
    source code/string files distributed with this software.
""".format(
    PACKAGE=PACKAGE,
    # DSTSTRINGFILE=DSTSTRINGFILE,
))


# =============================================================================
log.info("Creating supervisor conf file. Will be " + DST_SUPERVISOR_CONF_FILE)
# =============================================================================
write_text(WRK_SUPERVISOR_CONF_FILE, string.Template("""

# IF YOU EDIT THIS FILE, run:
#       sudo service supervisor restart
# TO MONITOR SUPERVISOR, run:
#       sudo supervisorctl status
# TO ADD MORE CAMCOPS INSTANCES, make a copy of the [program:camcops-gunicorn]
#   section, renaming the copy, and change the following:
#   - the CAMCOPS_CONFIG_FILE environment variable;
#   - the port or socket;
#   - the log files.
# Then make the main web server point to the copy as well.
# NOTES:
# - You can't put quotes around the directory variable
#   http://stackoverflow.com/questions/10653590
# - Programs like celery and gunicorn that are installed within a virtual
#   environment use the virtualenv's python via their shebang.
# - The "environment" setting sets the OS environment. The "--env" parameter
#   to gunicorn sets the WSGI environment.

# As RPM reinstalls this file (inconveniently), everything is commented out
# so it doesn't cause disruption in its starting state.
#
# Uncomment and edit what you need.

# [program:camcops-gunicorn]
#
# command = $DSTPYTHONVENV/bin/gunicorn camcops_server:camcops:application
#     --workers 4
#     --bind=unix:$DEFAULT_GUNICORN_SOCKET
#     --env CAMCOPS_CONFIG_FILE=$DSTCONFIGFILE
#
# # Alternative methods (port and socket respectively):
# #   --bind=127.0.0.1:$DEFAULT_GUNICORN_PORT
# #   --bind=unix:$DEFAULT_GUNICORN_SOCKET
# directory = $DSTSERVERDIR
# environment = MPLCONFIGDIR="$DSTMPLCONFIGDIR"
# user = www-data
# # ... Ubuntu: typically www-data
# # ... CentOS: typically apache
# stdout_logfile = /var/log/supervisor/${PACKAGE}_gunicorn.log
# stderr_logfile = /var/log/supervisor/${PACKAGE}_gunicorn_err.log
# autostart = true
# autorestart = true
# startsecs = 10
# stopwaitsecs = 60

""").substitute(  # noqa
    DSTPYTHONVENV=DSTPYTHONVENV,
    DEFAULT_GUNICORN_PORT=DEFAULT_GUNICORN_PORT,
    DEFAULT_GUNICORN_SOCKET=DEFAULT_GUNICORN_SOCKET,
    DSTMPLCONFIGDIR=DSTMPLCONFIGDIR,
    DSTSERVERDIR=DSTSERVERDIR,
    # DSTPYTHONPATH=DSTPYTHONPATH,
    DSTCONFIGFILE=DSTCONFIGFILE,
    PACKAGE=PACKAGE,
))
webify_file(WRK_SUPERVISOR_CONF_FILE, WEBDOC_SUPERVISOR_CONF_FILE)

# =============================================================================
log.info("Creating instructions. Will be installed within " + DSTBASEDIR)
# =============================================================================

# CONSIDER: MULTIPLE INSTANCES
# - http://stackoverflow.com/questions/1553165/multiple-django-sites-with-apache-mod-wsgi  # noqa
# - http://mediacore.com/blog/hosting-multiple-wsgi-applications-with-apache
# - http://stackoverflow.com/questions/9581197/two-django-projects-running-simultaneously-and-mod-wsgi-acting-werid  # noqa

write_text(WRKINSTRUCTIONS, string.Template(r"""
===============================================================================
Your system's CamCOPS configuration
===============================================================================
- Default CamCOPS config is:
    $DSTCONFIGFILE
  This must be edited before it will run properly.

- Gunicorn/Celery are being supervised as per:
    $DST_SUPERVISOR_CONF_FILE
  This this should be edited to point to the correct CamCOPS config.
  (And copied, changing the CAMCOPS_CONFIG_FILE environment variable, should
  you want to run >1 instance.)

- Gunicorn default port is:
    $DEFAULT_GUNICORN_PORT
  To change this, edit
    $DST_SUPERVISOR_CONF_FILE
  (or copy and edit the copy). Duplicate entries in this script to run another
  instance on another port/socket.

- Static file root to serve:
    $DSTSTATICDIR
  See instructions below re Apache.

===============================================================================
Running CamCOPS tools within its virtual environment
===============================================================================

The principle is to use the venv's python executable to run the script.

For example, to run the camcops_meta.py tool to make all tables for all
databases, assuming all relevant config files are described by
"/etc/camcops/camcops_*.conf", with sudo prepended to allow access:

    sudo $DSTBASEDIR/venv/bin/python $DSTBASEDIR/server/tools/camcops_meta.py --verbose --filespecs /etc/camcops/camcops_*.conf --ccargs maketables

To test all configs, with the same filespec:

    sudo $DSTBASEDIR/venv/bin/python $DSTBASEDIR/server/tools/camcops_meta.py --verbose --filespecs /etc/camcops/camcops_*.conf --ccargs test

(An alternative method is to use "source $DSTBASEDIR/venv/bin/activate",
and then run things interactively, but this will not work so easily via sudo.)

But a shortcut for all these things is:

    sudo $DSTMETACONSOLEFILE --verbose --filespecs /etc/camcops/camcops_*.conf --ccargs test

===============================================================================
Full stack
===============================================================================

- Gunicorn serves CamCOPS via WSGI
  ... serving via an internal port (in the default configuration, $DEFAULT_GUNICORN_PORT).
  ... or an internal socket (such as $DEFAULT_GUNICORN_SOCKET)

- supervisord keeps Gunicorn running

- You should use a proper web server like Apache or nginx to:

    (a) serve static files

    (b) proxy requests to the WSGI app via Gunicorn

===============================================================================
Monitoring with supervisord
===============================================================================

    sudo supervisorctl  # assuming it's running as root

===============================================================================
Advanced configuration
===============================================================================

CamCOPS uses operating system environment variables (os.environ, from a Python
perspective) for things that influence early startup, such as module loading.
This is because it's often convenient to load all relevant modules before
reading the configuration file. These govern low-level settings and are not
typically needed, or are typically set up for you as part of the default
CamCOPS installation.

Essential environment variables
-------------------------------

CAMCOPS_CONFIG_FILE
    Points to the configuration file itself (e.g. /etc/camcops.conf).

Common environment variables
----------------------------

MPLCONFIGDIR
    A temporary cache directory for matplotlib to store information (e.g. font
    lists). Specifying this dramatically reduces matplotlib's startup time
    (from e.g. 3 seconds the first time, to a fraction of that subsequently).
    If you don't specify it, CamCOPS uses a fresh temporary directory, so you
    don't get the speedup. The default is
        {DSTMPLCONFIGDIR}
    The directory must be writable by the user running CamCOPS.

Debugging environment variables
-------------------------------

CAMCOPS_DEBUG_TO_HTTP_CLIENT
    Boolean string (e.g. 'True', 'Y', '1' / 'False', 'N', '0').
    Enables exception reporting to the HTTP client. Should be DISABLED for
    production systems. Default is False.

CAMCOPS_PROFILE
    Boolean string.
    Enable a profiling layer on HTTP requests. The output goes to the system
    console. Default is False.

CAMCOPS_SERVE_STATIC_FILES
    Boolean string.
    The CamCOPS program will itself serve static files. Default is True.
    In a production server, you can ignore this setting, but you should serve
    static files from a proper web server (e.g. Apache) instead, for
    performance.

Note regarding environment variables
------------------------------------

Operating system environment variables are read at PROGRAM LOAD TIME, not WSGI
call time. They are distinct from WSGI environment variables (which are passed
from the WSGI web server to CamCOPS at run-time and contain per-request
information).

===============================================================================
Testing with just gunicorn
===============================================================================

- Assuming your www-data has the necessary access, then configure gunicorn
  for a test port on 8000:

    sudo -u www-data \
        CAMCOPS_CONFIG_FILE="$DSTCONFIGFILE" \
        $DSTPYTHONVENV/bin/gunicorn camcops_server:camcops:application \
        --workers 4 \
        --bind=127.0.0.1:8000

===============================================================================
Apache
===============================================================================
-------------------------------------------------------------------------------
OPTIMAL: proxy Apache through to Gunicorn
-------------------------------------------------------------------------------
(a) Add Ubuntu/Apache prerequisites

    [Ubuntu]
        sudo apt-get install apache2 libapache2-mod-wsgi libapache2-mod-proxy-html libapache2-mod-xsendfile
        sudo a2enmod proxy_http  # may be unnecessary
        sudo apt-get install mysql-client mysql-server
    [CentOS]
        yum install httpd mod_wsgi mod_proxy mod_xsendfile
        yum install mysql55 mysql55-server libmysqlclient-dev

(b) Configure Apache for CamCOPS.
    Use a section like this in the Apache config file:

<VirtualHost *:443>
    # ...

    # =========================================================================
    # CamCOPS
    # =========================================================================

        # ---------------------------------------------------------------------
        # 1. Proxy requests to the Gunicorn server and back, and allow access
        # ---------------------------------------------------------------------
        #    ... either via port $DEFAULT_GUNICORN_PORT
        #    ... or, better, via socket $DEFAULT_GUNICORN_SOCKET
        # NOTES
        # - When you ProxyPass /$URLBASE, you should browse to
        #       https://YOURSITE/$URLBASE/webview
        #   and point your tablets to
        #       https://YOURSITE/$URLBASE/database
        # - Don't specify trailing slashes.
        #   If you do, http://host/$URLBASE will fail though;
        #              http://host/$URLBASE/ will succeed.
        # - Using a socket
        #   - this requires Apache 2.4.9, and passes after the '|' character a
        #     URL that determines the Host: value of the request; see
        #       https://httpd.apache.org/docs/trunk/mod/mod_proxy.html#proxypass
        #   - The Django debug toolbar will then require the bizarre entry in
        #     the Django settings: INTERNAL_IPS = ("b''", ) -- i.e. the string
        #     value of "b''", not an empty bytestring.
        # - Ensure that you put the CORRECT PROTOCOL (e.g. https) in the rules
        #   below.
        # - For ProxyPass options, see https://httpd.apache.org/docs/2.2/mod/mod_proxy.html#proxypass
        #   ... including "retry=0" to stop Apache disabling the connection for
        #       a while on failure.

        # Don't ProxyPass the static files; we'll serve them via Apache.
    ProxyPassMatch ^/$URLBASE/static/ !

        # Port
        # Note the use of "http" (reflecting the backend), not https (like the
        # front end).

    # ProxyPass /$URLBASE http://127.0.0.1:$DEFAULT_GUNICORN_PORT retry=0
    # ProxyPassReverse /$URLBASE http://127.0.0.1:$DEFAULT_GUNICORN_PORT

        # Socket (Apache 2.4.9 and higher)
        #
        # The general syntax is:
        #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|PROTOCOL://HOST/EXTRA_URL_FOR_BACKEND retry=0
        # Note that:
        #   - the protocol should be http, not https (Apache deals with the
        #     HTTPS part and passes HTTP on)
        #   - the EXTRA_URL_FOR_BACKEND needs to be (a) unique for each
        #     instance or Apache will use a single worker for multiple
        #     instances, and (b) blank for the backend's benefit. Since those
        #     two conflict when there's >1 instance, there's a problem.
        #   - Normally, HOST is given as localhost. It may be that this problem
        #     is solved by using a dummy unique value for HOST:
        #     https://bz.apache.org/bugzilla/show_bug.cgi?id=54101#c1
        #
        # If your Apache version is too old, you will get the error
        #   "AH00526: Syntax error on line 56 of /etc/apache2/sites-enabled/SOMETHING:
        #    ProxyPass URL must be absolute!"
        # On Ubuntu, if your Apache is too old, you could use
        #   sudo add-apt-repository ppa:ondrej/apache2
        # ... details at https://launchpad.net/~ondrej/+archive/ubuntu/apache2
        #
        # If you get this error:
        #   AH01146: Ignoring parameter 'retry=0' for worker 'unix:/tmp/.camcops_gunicorn.sock|https://localhost' because of worker sharing
        #   https://wiki.apache.org/httpd/ListOfErrors
        # ... then your URLs are overlapping and should be redone or sorted:
        #   http://httpd.apache.org/docs/2.4/mod/mod_proxy.html#workers
        # The part that must be unique for each instance, with no part a
        # leading substring of any other, is THIS_BIT in:
        #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|https://localhost/THIS_BIT retry=0
        #
        # If you get an error like this:
        #   AH01144: No protocol handler was valid for the URL /SOMEWHERE. If you are using a DSO version of mod_proxy, make sure the proxy submodules are included in the configuration using LoadModule.
        # Then do this:
        #   sudo a2enmod proxy proxy_http
        #   sudo apache2ctl restart
        #
        # If you get an error like this:
        #   ... [proxy_http:error] [pid 32747] (103)Software caused connection abort: [client 109.151.49.173:56898] AH01102: error reading status line from remote server httpd-UDS:0
        #       [proxy:error] [pid 32747] [client 109.151.49.173:56898] AH00898: Error reading from remote server returned by /camcops_bruhl/webview
        # then check you are specifying http://, not https://, in the ProxyPass
        #
        # Other information sources:
        #   https://emptyhammock.com/projects/info/pyweb/webconfig.html

    ProxyPass /$URLBASE unix:$DEFAULT_GUNICORN_SOCKET|http://dummy1/ retry=0
    ProxyPassReverse /$URLBASE unix:$DEFAULT_GUNICORN_SOCKET|http://dummy1/

        # Allow proxy over SSL.
        # Without this, you will get errors like:
        #   ... SSL Proxy requested for wombat:443 but not enabled [Hint: SSLProxyEngine]
        #   ... failed to enable ssl support for 0.0.0.0:0 (httpd-UDS)

    SSLProxyEngine on

        # Allow access

    <Location /$URLBASE>
        Require all granted
    </Location>

        # ---------------------------------------------------------------------
        # 2. Serve static files
        # ---------------------------------------------------------------------
        # a) offer them at the appropriate URL
        # b) provide permission

    #   Change this: aim the alias at your own institutional logo.
    Alias /$URLBASE/static/logo_local.png $DSTSTATICDIR/logo_local.png

    #   The rest
    Alias /$URLBASE/static/ $DSTSTATICDIR/

    <Directory $DSTSTATICDIR>
        Require all granted
    </Directory>

        # ---------------------------------------------------------------------
        # 3. For additional instances
        # ---------------------------------------------------------------------
        # (a) duplicate section 1 above, editing the base URL and Gunicorn
        #     connection (socket/port);
        # (b) you will also need to create an additional Gunicorn instance,
        #     as above;
        # (c) add additional static aliases (in section 2 above).
        # Example (using sockets):

    # ProxyPassMatch ^/camcops_instance2/static/ !
    # ProxyPass /camcops_instance2 unix:/tmp/.camcops_gunicorn_instance2.sock|http://dummy2/ retry=0
    # ProxyPassReverse /camcops_instance2 unix:/tmp/.camcops_gunicorn_instance2.sock|http://dummy2/
    # <Location /camcops_instance2>
    #     Require all granted
    # </Location>
    # Alias /camcops_instance2/static/logo_local.png $DSTSTATICDIR/logo_local.png
    # Alias /camcops_instance2/static/ $DSTSTATICDIR/


    #==========================================================================
    # SSL security (for HTTPS)
    #==========================================================================

    # You will also need to install your SSL certificate; see the instructions
    # that came with it. You get a certificate by creating a certificate
    # signing request (CSR). You enter some details about your site, and a
    # software tool makes (1) a private key, which you keep utterly private,
    # and (2) a CSR, which you send to a Certificate Authority (CA) for
    # signing. They send back a signed certificate, and a chain of certificates
    # leading from yours to a trusted root CA.

    # You can create your own (a 'snake-oil' certificate), but your tablets
    # and browsers will not trust it, so this is a bad idea.

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

    #==========================================================================
    # GZIP COMPRESSION FOR APPROPRIATE CONTENT TYPES (OPTIONAL)
    # Run "sudo a2enmod deflate" from the command line if not already enabled.
    #==========================================================================
    # http://stackoverflow.com/questions/12367858/how-can-i-get-apache-gzip-compression-to-work
    # testing it: curl -I --compress http://mysite.mydomain/index.html
    # http://serverfault.com/questions/81609/how-to-check-if-apache-compression-is-working
    SetOutputFilter DEFLATE
    AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml application/x-javascript application/x-httpd-php
    BrowserMatch ^Mozilla/4 gzip-only-text/html
    BrowserMatch ^Mozilla/4\.0[678] no-gzip
    BrowserMatch \bMSIE !no-gzip !gzip-only-text/html
    BrowserMatch \bMSI[E] !no-gzip !gzip-only-text/html
    SetEnvIfNoCase Request_URI \.(?:gif|jpe?g|png)$$ no-gzip
    Header append Vary User-Agent env=!dont-vary

""").substitute(  # noqa
    DEFAULT_GUNICORN_PORT=DEFAULT_GUNICORN_PORT,
    DEFAULT_GUNICORN_SOCKET=DEFAULT_GUNICORN_SOCKET,
    DSTBASEDIR=DSTBASEDIR,
    DSTCONFIGDIR=DSTCONFIGDIR,
    DSTCONFIGFILE=DSTCONFIGFILE,
    DSTMETACONSOLEFILE=DSTMETACONSOLEFILE,
    DSTMPLCONFIGDIR=DSTMPLCONFIGDIR,
    # DSTPYTHONPATH=DSTPYTHONPATH,
    DSTPYTHONVENV=DSTPYTHONVENV,
    DSTSERVERDIR=DSTSERVERDIR,
    DSTSTATICDIR=DSTSTATICDIR,
    DST_SUPERVISOR_CONF_FILE=DST_SUPERVISOR_CONF_FILE,
    MAINSCRIPTNAME=MAINSCRIPTNAME,
    TABLETSCRIPT=TABLETSCRIPT,
    URLBASE=URLBASE,
    WEBVIEWSCRIPT=WEBVIEWSCRIPT,
))
webify_file(WRKINSTRUCTIONS, WEBDOCINSTRUCTIONS)

# In <Files "$DBSCRIPTNAME"> section, we did have:
#   # The next line prevents XMLHttpRequest Access-Control-Allow-Origin errors.
#   # Also need headers.load as a module:
#   # http://harthur.wordpress.com/2009/10/15/configure-apache-to-accept-cross-site-xmlhttprequests-on-ubuntu/  # noqa
#   # ln -s /etc/apache2/mods-available/headers.load /etc/apache2/mods-enabled/headers.load  # noqa

#   # Header set Access-Control-Allow-Origin "*"

# =============================================================================
log.info("Creating demonstration MySQL database creation commands. Will be "
         "installed within " + DSTBASEDIR)
# =============================================================================
write_text(WRKMYSQLCREATION, """
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
))
webify_file(WRKMYSQLCREATION, WEBDOCSMYSQLCREATION)

# =============================================================================
log.info("Creating demonstration backup script. Will be installed within " +
         DSTBASEDIR)
# =============================================================================
write_text(WRKDBDUMPFILE, """#!/bin/bash

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
""")  # noqa
webify_file(WRKDBDUMPFILE, WEBDOCDBDUMPFILE)

# =============================================================================
log.info("Setting ownership and permissions")
# =============================================================================
# sudo chown -R $USER:$USER $WRKDIR
subprocess.check_call(
    ['find', WRKDIR, '-type', 'd', '-exec', 'chmod', '755', '{}', ';'])
# ... make directories executabe: must do that first, or all the subsequent
# recursions fail
subprocess.check_call(
    ['find', WRKDIR, '-type', 'f', '-exec', 'chmod', '644', '{}', ';'])
subprocess.check_call([
    "chmod",
    "a+x",
    WRKCONSOLEFILE,
    WRKMETACONSOLEFILE,
    WRKDBDUMPFILE,
    join(DEBDIR, 'prerm'),
    join(DEBDIR, 'postrm'),
    join(DEBDIR, 'preinst'),
    join(DEBDIR, 'postinst'),
])
subprocess.check_call(
    ['find', WRKDIR, '-iname', '*.py', '-exec', 'chmod', 'a+x', '{}', ';'])
subprocess.check_call(
    ['find', WRKDIR, '-iname', '*.pl', '-exec', 'chmod', 'a+x', '{}', ';'])

# =============================================================================
log.info("Removing junk")
# =============================================================================
subprocess.check_call(
    ['find', WRKDIR, '-name', '*.svn', '-exec', 'rm', '-rf', '{}', ';'])
subprocess.check_call(
    ['find', WRKDIR, '-name', '.git', '-exec', 'rm', '-rf', '{}', ';'])
subprocess.check_call(
    ['find', WRKDOCDIR, '-name', 'LICENSE', '-exec', 'rm', '-rf', '{}', ';'])

# =============================================================================
log.info("Building package")
# =============================================================================
subprocess.check_call(['fakeroot', 'dpkg-deb', '--build', WRKDIR, PACKAGENAME])
# ... "fakeroot" prefix makes all files installed as root:root

# =============================================================================
log.info("Checking with Lintian")
# =============================================================================
subprocess.check_call(['lintian', PACKAGENAME])

# =============================================================================
log.info("Converting to RPM")
# =============================================================================
subprocess.check_call(
    ['fakeroot', 'alien', '--to-rpm', '--scripts', PACKAGENAME],
    cwd=PACKAGEDIR)
# see "man alien"/NOTES: needs to be run as root for correct final permissions
EXPECTED_MAIN_RPM_NAME = "{PACKAGE}-{MAINVERSION}-2.noarch.rpm".format(
    PACKAGE=PACKAGE,
    MAINVERSION=MAINVERSION,
)
FULL_RPM_PATH = join(PACKAGEDIR, EXPECTED_MAIN_RPM_NAME)
myuser = getpass.getuser()
shutil.chown(FULL_RPM_PATH, myuser, myuser)

# =============================================================================
log.info("Changing dependencies within RPM")
# =============================================================================
# Alien does not successfully translate the dependencies, and anyway the names
# for packages are different on CentOS. A dummy prerequisite package works
# (below) but is inelegant.
# The rpmbuild commands are filters (text in via stdin, text out to stdout),
# so replacement just needs the echo command.

subprocess.check_call([
    'rpmrebuild',
    '--define', '_topdir ' + RPMTOPDIR,
    '--package',
    '--change-spec-requires=/bin/echo Requires: {}'.format(
        " ".join(DEPENDS_RPM)),
    FULL_RPM_PATH,
])
# ... add "--edit-whole" as the last option before the RPM name to see what
#     you're getting
# ... define topdir, or it builds in ~/rpmbuild/...
# ... --package, or it looks for an installed RPM rather than a package file

shutil.move(join(RPMTOPDIR, 'RPMS', 'noarch', EXPECTED_MAIN_RPM_NAME),
            join(PACKAGEDIR, EXPECTED_MAIN_RPM_NAME))
# ... will overwrite its predecessor

# =============================================================================
log.info("Deleting temporary workspace")
# =============================================================================
shutil.rmtree(TMPDIR, ignore_errors=True)  # CAUTION!

# =============================================================================
log.info("=" * 79)
log.info("Debian package should be: " + PACKAGENAME)
log.info("RPM should be: " + FULL_RPM_PATH)
# =============================================================================
