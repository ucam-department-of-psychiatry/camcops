#!/usr/bin/env python
# camcops/server/tools/MAKE_LINUX_PACKAGES.py

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
import shutil
import subprocess
import sys
import tempfile

from cardinal_pythonlib.file_io import (
    get_lines_without_comments,
    remove_gzip_timestamp,
    write_text,
    write_gzipped_text,
)
from cardinal_pythonlib.fileops import copyglob, mkdir_p
from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

from camcops_server.cc_modules.cc_baseconstants import (
    LINUX_DEFAULT_CAMCOPS_CONFIG_DIR,
    LINUX_DEFAULT_CAMCOPS_DIR,
    LINUX_DEFAULT_LOCK_DIR,
    LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR,
)
from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
    CAMCOPS_CHANGEDATE,
)

log = logging.getLogger(__name__)

# =============================================================================
# Python version requirements
# =============================================================================

if sys.version_info[0] < 3:
    raise AssertionError("Need Python 3 or higher")
if sys.version_info[1] < 5:
    raise AssertionError("Need Python 3.5 or higher")


# =============================================================================
# URL defaults and other constants
# =============================================================================

PACKAGE = "camcops"
DSTSYSTEMPYTHON = 'python3'
# ... must be present on the path on the destination system


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
# Directory constants
# =============================================================================

THIS_DIR = os.path.dirname(os.path.abspath(__file__))  # tools
SETUP_PY_DIR = os.path.abspath(join(THIS_DIR, os.pardir))
PROJECT_BASE_DIR = os.path.abspath(join(THIS_DIR, os.pardir, os.pardir))

DSTBASEDIR = LINUX_DEFAULT_CAMCOPS_DIR

TMPDIR = tempfile.mkdtemp()
log.info("Temporary working directory: " + TMPDIR)
WRKDIR = join(TMPDIR, 'debian')
RPMTOPDIR = join(TMPDIR, 'rpmbuild')

SRCSERVERDIR = join(PROJECT_BASE_DIR, 'server')
DOCROOTDIR = join(PROJECT_BASE_DIR, 'documentation')
PACKAGEDIR = join(SRCSERVERDIR, 'packagebuild')

DSTDOCDIR = join('/usr/share/doc', PACKAGE)
WRKDOCDIR = workpath(WRKDIR, DSTDOCDIR)

WRKBASEDIR = workpath(WRKDIR, DSTBASEDIR)

DEBDIR = join(WRKDIR, 'DEBIAN')
# ... where Debian package control information lives
DEBOVERRIDEDIR = workpath(WRKDIR, '/usr/share/lintian/overrides')

DSTCONSOLEFILEDIR = '/usr/bin'
SETUPSCRIPTNAME = PACKAGE
WRKCONSOLEFILEDIR = workpath(WRKDIR, DSTCONSOLEFILEDIR)

DSTTEMPDIR = join(DSTBASEDIR, 'tmp')

SRCTOOLDIR = join(SRCSERVERDIR, 'tools')
WRKTOOLDIR = join(WRKBASEDIR, 'tools')
DSTTOOLDIR = join(DSTBASEDIR, 'tools')
VENVSCRIPT = 'install_virtualenv.py'
WKHTMLTOPDFSCRIPT = 'install_wkhtmltopdf.py'
METASCRIPT = 'camcops_meta.py'
DSTVENVSCRIPT = join(DSTTOOLDIR, VENVSCRIPT)
DSTWKHTMLTOPDFSCRIPT = join(DSTTOOLDIR, WKHTMLTOPDFSCRIPT)

MAINSCRIPTNAME = 'camcops.py'

METASCRIPTNAME = '{}_meta'.format(PACKAGE)

DSTMANDIR = '/usr/share/man/man1'  # section 1 for user commands
WRKMANDIR = workpath(WRKDIR, DSTMANDIR)

DSTCONFIGDIR = join('/etc', PACKAGE)
WRKCONFIGDIR = workpath(WRKDIR, DSTCONFIGDIR)

DSTDPKGDIR = '/var/lib/dpkg/info'

DSTLOCKDIR = LINUX_DEFAULT_LOCK_DIR
DSTPYTHONVENV = join(DSTBASEDIR, 'venv')
DSTVENVBIN = join(DSTPYTHONVENV, 'bin')
DSTPYTHONCACHE = join(DSTBASEDIR, '.cache')

DSTMPLCONFIGDIR = LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR
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
                                            DEBVERSION=DEBVERSION)
)
# upstream_version-debian_revision --
# see http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version


# =============================================================================
# Check prerequisites
# =============================================================================
# http://stackoverflow.com/questions/2806897
if os.geteuid() == 0:
    log.critical("This script should not be run using sudo or as the root user")
    sys.exit(1)

log.info("Checking prerequisites")
PREREQUISITES = ("alien dpkg-deb fakeroot find git gzip lintian "
                 "rpmrebuild".split())
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
# Check command-line arguments +/- provide help
# =============================================================================

parser = argparse.ArgumentParser(
    description="""
- Creates a Debian (.deb) and RPM (.rpm) distribution file for the CamCOPS 
  server, for distribution under Linux.

- In brief, the following sequence is followed as the package is built:

  * The CamCOPS server is packaged up from source using
        python setup.py sdist --extras
            # ... where "--extras" is a special custom option that copies the 
            # tablet source code and packages that, plus all static files 
    and zipped in a Debian-safe way.
    
  * The principle is that the Python package should do all the work, not the
    Debian framework. This also means that a user who elects to install via pip
    gets exactly the same functional file structure.

  * A Debian package is built, containing all the usual Debian goodies (man
    packages, the preinst/postinst/prerm/postrm files, cataloguing and control
    files, etc.).

  * The package is checked with Lintian.

  * An RPM is built from the .deb package.

- The user then installs the DEB or RPM file. In addition to installing 
  standard things like man pages, this then:

  * attempts to stop supervisord for the duration of the installation (because
    that's the usual way to run a CamCOPS server);

  * creates a few standard directories (e.g. for CamCOPS configuration and 
    lock files), including
        {LINUX_DEFAULT_CAMCOPS_CONFIG_DIR}
        {LINUX_DEFAULT_CAMCOPS_DIR}
        {LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR}
        {LINUX_DEFAULT_LOCK_DIR}

  * checks that Python 3.5 is available on the system;

  * uses the system Python to create a Python virtual environment within 
    {LINUX_DEFAULT_CAMCOPS_DIR};

  * uses the virtual environment's "pip" command to install the distributed
    CamCOPS Python package within that virtual environment;
    ... which also appears to compile .py to .pyc files automatically;

  * creates master executable scripts (which call corresponding Python 
    scripts):
        {DSTCONSOLEFILE}
        {DSTMETACONSOLEFILE}

  * sets some permissions (to default users such as "www-data" on Ubuntu, or
    "apache" on CentOS);

  * restarts supervisord.

    """.format(
        DSTCONSOLEFILE=DSTCONSOLEFILE,
        DSTMETACONSOLEFILE=DSTMETACONSOLEFILE,
        LINUX_DEFAULT_CAMCOPS_CONFIG_DIR=LINUX_DEFAULT_CAMCOPS_CONFIG_DIR,
        LINUX_DEFAULT_CAMCOPS_DIR=LINUX_DEFAULT_CAMCOPS_DIR,
        LINUX_DEFAULT_LOCK_DIR=LINUX_DEFAULT_LOCK_DIR,
        LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR=LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR,
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('--verbose', '-v', action='store_true')
args = parser.parse_args()
main_only_quicksetup_rootlogger(level=logging.DEBUG if args.verbose
                                else logging.INFO)

log.info("mainversion: {}".format(MAINVERSION))
log.info("changedate: {}".format(CHANGEDATE))


# =============================================================================
log.info("Building Python package")
# =============================================================================

SETUP_PY = join(SRCSERVERDIR, 'setup.py')
SDIST_BASEFILENAME = ('camcops_server-{}.tar.gz'.format(MAINVERSION))
SRC_SDIST_FILE = join(SRCSERVERDIR, 'dist', SDIST_BASEFILENAME)
WRK_SDIST_FILE = join(WRKBASEDIR, SDIST_BASEFILENAME)
DST_SDIST_FILE = join(DSTBASEDIR, SDIST_BASEFILENAME)

try:
    log.info("Deleting old {} if it exists".format(SRC_SDIST_FILE))
    os.remove(SRC_SDIST_FILE)
except OSError:
    pass
os.chdir(SETUP_PY_DIR)  # or setup.py looks in wrong places?
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
mkdir_p(WRKMANDIR)
mkdir_p(WRKMPLCONFIGDIR)
mkdir_p(WRKBASEDIR)
mkdir_p(WRKTOOLDIR)
for d in "BUILD,BUILDROOT,RPMS,RPMS/noarch,SOURCES,SPECS,SRPMS".split(","):
    mkdir_p(join(RPMTOPDIR, d))


# =============================================================================
log.info("Copying files")
# =============================================================================
# copyglob(join(SRCSERVERDIR, 'requirements*.txt'), WRKBASEDIR)
copyglob(join(SRCSERVERDIR, 'changelog.Debian'), WRKDOCDIR)
subprocess.check_call(['gzip', '-n', '-9',
                       join(WRKDOCDIR, 'changelog.Debian')])
# copyglob(join(SRCSERVERDIR, 'changelog.Debian'), WEB_VERSION_FILES_DIR)
# ... for the web site

copyglob(join(SRCTOOLDIR, VENVSCRIPT), WRKTOOLDIR)
copyglob(join(SRCTOOLDIR, WKHTMLTOPDFSCRIPT), WRKTOOLDIR)

shutil.copyfile(SRC_SDIST_FILE, WRK_SDIST_FILE)


# =============================================================================
log.info("Creating man page for camcops. Will be installed as " + DSTMANFILE)
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

There are prerequisites, such as setting up a database. See
http://www.camcops.org/ and the manual (use: 'camcops docs').

For help, use

    camcops --help
    camcops docs

To create a demonstration config file, run

    camcops demo_camcops_config

Typically one would put the real configuration file in /etc/camcops/, and make
it readable only by the Apache user (typically www-data on Debian/Ubuntu
and apache on CentOS).
    
To create demonstration configuration files for support programs such as
supervisord and Apache, try

    camcops demo_supervisor_config
    camcops demo_apache_config

You will also need to point your web server (e.g. Apache) at the CamCOPS
program itself; see http://www.camcops.org/ and the manual.

.SH FOR DETAILS
.IP "camcops --help"
show all options

.SH SEE ALSO
http://www.camcops.org/

.SH AUTHOR
Rudolf Cardinal (rudolf@pobox.com)
""".format(
    SETUPSCRIPTNAME=SETUPSCRIPTNAME,
    CHANGEDATE=CHANGEDATE,
    MAINVERSION=MAINVERSION,
))


# =============================================================================
log.info("Creating man page for camcops_meta. Will be installed as " +
         DSTMETAMANFILE)
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
))


# =============================================================================
log.info("Creating links to documentation. Will be installed as " + DSTREADME)
# =============================================================================
write_text(WRKREADME, """
CamCOPS: the Cambridge Cognitive and Psychiatric Test Kit

See http://www.camcops.org for documentation, or the manual (for which, use 
'camcops docs').
""")


# =============================================================================
log.info("Creating camcops launch script. Will be installed as " +
         DSTCONSOLEFILE)
# =============================================================================
write_text(WRKCONSOLEFILE, """#!/bin/bash
# Launch script for CamCOPS command-line tool.

echo 'Launching CamCOPS command-line tool...' >&2

{DST_CAMCOPS_LAUNCHER} "$@"

""".format(
    DST_CAMCOPS_LAUNCHER=DST_CAMCOPS_LAUNCHER,
))


# =============================================================================
log.info("Creating camcops_meta launch script. Will be installed as {}".format(
    DSTMETACONSOLEFILE))
# =============================================================================
write_text(WRKMETACONSOLEFILE, """#!/bin/bash
# Launch script for CamCOPS meta-command tool tool.

echo 'Launching CamCOPS meta-command tool...' >&2

{DST_CAMCOPS_META_LAUNCHER} "$@"

""".format(
    DST_CAMCOPS_META_LAUNCHER=DST_CAMCOPS_META_LAUNCHER,
))


# =============================================================================
log.info("Creating Debian control file")
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
 information from the CamCOPS tablet applications (desktop, Android, iOS).
 .
 For more details, see http://www.camcops.org/
""".format(
    PACKAGE=PACKAGE,
    DEBVERSION=DEBVERSION,
    DEPENDENCIES=", ".join(DEPENDS_DEB),
))


# =============================================================================
# log.info("Creating conffiles file. Will be installed as " +
#          join(DSTDPKGDIR, PACKAGE + '.conffiles'))
# =============================================================================
# configfiles = [DSTCONFIGFILE,
#                DST_SUPERVISOR_CONF_FILE]
# write_text(join(DEBDIR, 'conffiles'), "\n".join(configfiles))
#
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
# environment (otherwise it'll be busy). So:

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
if [[ ! -z "$APACHEUSER" ]]; then
    chown $APACHEUSER:$APACHEUSER {DSTLOCKDIR}
    chown $APACHEUSER:$APACHEUSER {DSTMPLCONFIGDIR}
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
===============================================================================
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
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
subprocess.check_call(['lintian', '--fail-on-warnings', PACKAGENAME])


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
