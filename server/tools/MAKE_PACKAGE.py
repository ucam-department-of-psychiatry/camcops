#!/usr/bin/env python3

"""
For CentOS, you need to get Python 3 installed. For Centos 6, 64-bit:

    # http://stackoverflow.com/questions/8087184/installing-python3-on-rhel

    sudo yum install https://centos6.iuscommunity.org/ius-release.rpm
    sudo yum install python34u

Note that you can get CentOS version/architecture with:

    cat /etc/centos-release
    uname -a
"""

# We could use a temporary directory for the Debian build,
# but it's helpful to be able to see what it's doing as well.
# ... actually, let's do that, using mkdtemp(), so it'll linger if the build
# fails.

import getpass
import glob
import gzip
import os
from os.path import join
import re
import shutil
import string
import subprocess
import sys
import tempfile

if sys.version_info[0] < 3:
    raise AssertionError("Need Python 3")

# =============================================================================
# URL defaults and other constants
# =============================================================================

PACKAGE = "camcops"

DSTSYSTEMPYTHON = 'python3'
# ... must be present on the path on the destination system

INSTITUTIONURL = 'http://www.mydomain/'
CAMCOPSHOSTNAME = 'mycomputer.mydomain'
URLBASE = 'camcops'
WEBVIEWSCRIPT = 'webview'
TABLETSCRIPT = 'database'
DEFAULT_DB_NAME = 'camcops'
DEFAULT_DB_USER = 'YYYYYY_REPLACE_ME'
DEFAULT_DB_PASSWORD = 'ZZZZZZ_REPLACE_ME'
DEFAULT_DB_READONLY_USER = 'QQQQQQ_REPLACE_ME'
DEFAULT_DB_READONLY_PASSWORD = 'PPPPPP_REPLACE_ME'
DEFAULT_ANONSTAG_DB_NAME = 'anon_staging_camcops'
DEFAULT_ANONSTAG_DB_USER = 'UUUUUU_REPLACE_ME'
DEFAULT_ANONSTAG_DB_PASSWORD = 'WWWWWW_REPLACE_ME'

DEFAULT_GUNICORN_PORT = 8006
DEFAULT_GUNICORN_SOCKET = '/tmp/.camcops_gunicorn.sock'
# ... must be writable by the relevant user

# =============================================================================
# Helper functions
# =============================================================================

FG_RED = '\033[0;31m'
BG_GREY = '\033[2;47m'
NO_COLOUR = '\033[0m'


def error(msg):
    print(FG_RED, BG_GREY, msg, NO_COLOUR, sep="")


def workpath(workdir, destpath):
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


def mkdirp(path):
    os.makedirs(path, exist_ok=True)


def copyglob(src, dest, allow_nothing=False):
    something = False
    for file in glob.glob(src):
        shutil.copy(file, dest)
        something = True
    if something or allow_nothing:
        return
    raise ValueError("No files found matching: {}".format(src))


def chown_r(path, user, group):
    # http://stackoverflow.com/questions/2853723
    for root, dirs, files in os.walk(path):
        for x in dirs:
            shutil.chown(os.path.join(root, x), user, group)
        for x in files:
            shutil.chown(os.path.join(root, x), user, group)


def get_lines_without_comments(filename):
    lines = []
    with open(filename) as f:
        for line in f:
            line = line.partition('#')[0]
            line = line.rstrip()
            line = line.lstrip()
            if line:
                lines.append(line)
    return lines


# =============================================================================
# Check prerequisites
# =============================================================================
# http://stackoverflow.com/questions/2806897
if os.geteuid() == 0:
    exit("This script should not be run using sudo or as the root user")

print("Checking prerequisites")
PREREQUISITES = (
    "alien dpkg-deb fakeroot find git gzip lintian rpmrebuild".split())
for cmd in PREREQUISITES:
    if shutil.which(cmd) is None:
        print("""
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
        error("{} command not found; stopping".format(cmd))
        sys.exit(1)


# RPM issues
# 1. A dummy camcops-prerequisites package works but is inelegant.
# 2. Alien seems to strip dependencies.
# 3. rpmrebuild does the job albeit not wholly intuitive documentation!
#    It also allows you to see what Alien was doing.

# =============================================================================
# Directory constants
# =============================================================================

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_BASE_DIR = os.path.abspath(join(THIS_DIR, os.pardir, os.pardir))

DSTBASEDIR = join('/usr/share', PACKAGE)
# Lintian dislikes files/subdirectories in: /usr/bin/X, /usr/local/X, /opt/X
# It dislikes images in /usr/lib

TMPDIR = tempfile.mkdtemp()
print("Temporary working directory: " + TMPDIR)
WRKDIR = join(TMPDIR, 'debian')
RPMTOPDIR = join(TMPDIR, 'rpmbuild')

SRCSERVERDIR = join(PROJECT_BASE_DIR, 'server')
SRCTABLETDIR = join(PROJECT_BASE_DIR, 'tablet')
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
DSTCONSOLEFILE = join(DSTCONSOLEFILEDIR, SETUPSCRIPTNAME)
WRKCONSOLEFILE = join(WRKCONSOLEFILEDIR, SETUPSCRIPTNAME)

WRKSERVERDIR = join(WRKBASEDIR, 'server')
DSTSERVERDIR = join(DSTBASEDIR, 'server')

SRCEXTRASTRINGS = join(SRCSERVERDIR, 'extra_strings')
WRKEXTRASTRINGS = join(WRKSERVERDIR, 'extra_strings')
DSTEXTRASTRINGS = join(DSTSERVERDIR, 'extra_strings')
SRCEXTRASTRINGTEMPLATES = join(SRCSERVERDIR, 'extra_string_templates')
WRKEXTRASTRINGTEMPLATES = join(WRKSERVERDIR, 'extra_string_templates')

SRCPYTHONLIBDIR = join(SRCSERVERDIR, 'pythonlib')
WRKPYTHONLIBDIR = join(WRKSERVERDIR, 'pythonlib')

SRCMODULEDIR = join(SRCSERVERDIR, 'cc_modules')
WRKMODULEDIR = join(WRKSERVERDIR, 'cc_modules')

SRCTASKDIR = join(SRCSERVERDIR, 'tasks')
WRKTASKDIR = join(WRKSERVERDIR, 'tasks')

DSTTEMPDIR = join(DSTBASEDIR, 'tmp')

SRCTASKDISCARDEDDIR = join(SRCSERVERDIR, 'tasks_discarded')
WRKTASKDISCARDEDDIR = join(WRKSERVERDIR, 'tasks_discarded')
DSTTASKDISCARDEDDIR = join(DSTSERVERDIR, 'tasks_discarded')

SRCTOOLDIR = join(SRCSERVERDIR, 'tools')
WRKTOOLDIR = join(WRKSERVERDIR, 'tools')
DSTTOOLDIR = join(DSTSERVERDIR, 'tools')
VENVSCRIPT = 'install_virtualenv.py'
WKHTMLTOPDFSCRIPT = 'install_wkhtmltopdf.py'
METASCRIPT = 'camcops_meta.py'
DSTVENVSCRIPT = join(DSTTOOLDIR, VENVSCRIPT)
DSTWKHTMLTOPDFSCRIPT = join(DSTTOOLDIR, WKHTMLTOPDFSCRIPT)

WRKTABLETDIR = join(WRKBASEDIR, 'tablet')
DSTTABLETDIR = join(DSTBASEDIR, 'tablet')

MAINSCRIPTNAME = 'camcops.py'

DSTPYTHONPATH = DSTSERVERDIR
# ... others are referenced via the package system from this base directory
WRKMAINSCRIPT = join(WRKSERVERDIR, MAINSCRIPTNAME)
DSTMAINSCRIPT = join(DSTSERVERDIR, MAINSCRIPTNAME)

METASCRIPTNAME = '{}_meta'.format(PACKAGE)
DSTMETASCRIPT = join(DSTTOOLDIR, METASCRIPT)
WRKMETACONSOLEFILE = join(WRKCONSOLEFILEDIR, METASCRIPTNAME)
DSTMETACONSOLEFILE = join(DSTCONSOLEFILEDIR, METASCRIPTNAME)

DSTMANDIR = '/usr/share/man/man1'  # section 1 for user commands
WRKMANDIR = workpath(WRKDIR, DSTMANDIR)
WRKMANFILE = join(WRKMANDIR, SETUPSCRIPTNAME + '.1.gz')
DSTMANFILE = join(DSTMANDIR, SETUPSCRIPTNAME + '.1.gz')
WRKMETAMANFILE = join(WRKMANDIR, METASCRIPTNAME + '.1.gz')
DSTMETAMANFILE = join(DSTMANDIR, METASCRIPTNAME + '.1.gz')

WRKDBDUMPFILE = join(WRKBASEDIR, 'demo_mysql_dump_script')
WEBDOCDBDUMPFILE = join(WEBDOCSDIR, 'demo_mysql_dump_script')
WRKMYSQLCREATION = join(WRKBASEDIR, 'demo_mysql_database_creation')
WEBDOCSMYSQLCREATION = join(WEBDOCSDIR, 'demo_mysql_database_creation')
WRKINSTRUCTIONS = os.path.join(WRKBASEDIR, 'instructions.txt')
DSTINSTRUCTIONS = os.path.join(DSTBASEDIR, 'instructions.txt')
WEBDOCINSTRUCTIONS = os.path.join(WEBDOCSDIR, 'instructions.txt')

DSTSUPERVISORCONFDIR = '/etc/supervisor/conf.d'
WRKSUPERVISORCONFDIR = workpath(WRKDIR, DSTSUPERVISORCONFDIR)
DST_SUPERVISOR_CONF_FILE = os.path.join(DSTSUPERVISORCONFDIR,
                                        PACKAGE + '.conf')
WRK_SUPERVISOR_CONF_FILE = workpath(WRKDIR, DST_SUPERVISOR_CONF_FILE)

DSTCONFIGDIR = join('/etc', PACKAGE)
WRKCONFIGDIR = workpath(WRKDIR, DSTCONFIGDIR)
DSTCONFIGFILE = join(DSTCONFIGDIR, PACKAGE + '.conf')
WRKCONFIGFILE = join(WRKCONFIGDIR, PACKAGE + '.conf')
WEBDOCSCONFIGFILE = join(WEBDOCSDIR, PACKAGE + '.conf')

DSTDPKGDIR = '/var/lib/dpkg/info'

DSTLOCKDIR = join('/var/lock', PACKAGE)
DSTHL7LOCKFILESTEM = join(DSTLOCKDIR, PACKAGE + '.hl7')
DSTSUMMARYTABLELOCKFILESTEM = join(DSTLOCKDIR, PACKAGE + '.summarytables')
# http://www.debian.org/doc/debian-policy/ch-opersys.html#s-writing-init

DSTREADME = join(DSTDOCDIR, 'README.txt')
WRKREADME = join(WRKDOCDIR, 'README.txt')

DEB_REQ_FILE = os.path.join(SRCSERVERDIR, 'requirements-deb.txt')
RPM_REQ_FILE = os.path.join(SRCSERVERDIR, 'requirements-rpm.txt')

DSTPYTHONVENV = join(DSTBASEDIR, 'venv')
DSTVENVPYTHON = join(DSTPYTHONVENV, 'bin', 'python')
DSTPYTHONCACHE = join(DSTBASEDIR, '.cache')

SRCSTATICDIR = join(SRCSERVERDIR, 'static')
WRKSTATICDIR = join(WRKSERVERDIR, 'static')
DSTSTATICDIR = join(DSTSERVERDIR, 'static')

DSTMPLCONFIGDIR = '/var/cache/{}/matplotlib'.format(PACKAGE)
# Lintian dislikes using /var/local
WRKMPLCONFIGDIR = workpath(WRKDIR, DSTMPLCONFIGDIR)

# =============================================================================
# Version number and conditionals
# =============================================================================
VERSIONFILE = join(SRCSERVERDIR, 'cc_modules', 'cc_version.py')
version_regex = re.compile(r'^CAMCOPS_SERVER_VERSION\s*=\s*([\d\.]*)')
changedate_regex = re.compile(r'CAMCOPS_CHANGEDATE\s*=\s*\"(\S*)\"')
for i, line in enumerate(open(VERSIONFILE)):
    m = version_regex.match(line)
    if m:
        MAINVERSION = m.group(1)
    m = changedate_regex.match(line)
    if m:
        CHANGEDATE = m.group(1)
DEBVERSION = MAINVERSION + '-1'
PACKAGENAME = join(
    PACKAGEDIR,
    '{PACKAGE}_{DEBVERSION}_all.deb'.format(PACKAGE=PACKAGE,
                                            DEBVERSION=DEBVERSION))
# upstream_version-debian_revision --
# see http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version

print("mainversion:", MAINVERSION)
print("changedate:", CHANGEDATE)


# =============================================================================
# Directories, files
# =============================================================================
# print("Deleting old workspace")
# shutil.rmtree(WRKDIR, ignore_errors=True)  # CAUTION!

print("Making directories")
mkdirp(DEBDIR)
mkdirp(DEBOVERRIDEDIR)
mkdirp(PACKAGEDIR)
mkdirp(RPMTOPDIR)
mkdirp(WRKCONFIGDIR)
mkdirp(WRKCONSOLEFILEDIR)
mkdirp(WRKDIR)
mkdirp(WRKDOCDIR)
mkdirp(WRKEXTRASTRINGS)
mkdirp(WRKEXTRASTRINGTEMPLATES)
mkdirp(WRKMANDIR)
mkdirp(WRKMODULEDIR)
mkdirp(WRKMPLCONFIGDIR)
mkdirp(WRKPYTHONLIBDIR)
mkdirp(WRKSERVERDIR)
mkdirp(WRKSTATICDIR)
mkdirp(WRKSUPERVISORCONFDIR)
mkdirp(WRKTABLETDIR)
mkdirp(WRKTASKDIR)
mkdirp(WRKTASKDISCARDEDDIR)
mkdirp(WRKTOOLDIR)
for d in "BUILD,BUILDROOT,RPMS,RPMS/noarch,SOURCES,SPECS,SRPMS".split(","):
    mkdirp(join(RPMTOPDIR, d))

print("Copying files")
copyglob(join(SRCSERVERDIR, '*.py'), WRKSERVERDIR)
copyglob(join(SRCSERVERDIR, '*.txt'), WRKSERVERDIR)
copyglob(join(SRCPYTHONLIBDIR, '*.py'), WRKPYTHONLIBDIR)
copyglob(join(SRCSTATICDIR, '*'), WRKSTATICDIR)
copyglob(join(SRCSERVERDIR, 'changelog.Debian'), WRKDOCDIR)
subprocess.check_call(['gzip', '-9', join(WRKDOCDIR, 'changelog.Debian')])
copyglob(join(SRCSERVERDIR, 'changelog.Debian'), WEB_VERSION_FILES_DIR)
# ... for the web site
copyglob(join(SRCMODULEDIR, '*.py'), WRKMODULEDIR)
copyglob(join(SRCTASKDIR, '*.py'), WRKTASKDIR)
copyglob(join(SRCTASKDISCARDEDDIR, '*.py'), WRKTASKDISCARDEDDIR)
copyglob(join(SRCEXTRASTRINGS, '*'), WRKEXTRASTRINGS, allow_nothing=True)
copyglob(join(SRCEXTRASTRINGTEMPLATES, '*'), WRKEXTRASTRINGTEMPLATES,
         allow_nothing=True)
copyglob(join(SRCTOOLDIR, VENVSCRIPT), WRKTOOLDIR)
copyglob(join(SRCTOOLDIR, WKHTMLTOPDFSCRIPT), WRKTOOLDIR)
copyglob(join(SRCTOOLDIR, METASCRIPT), WRKTOOLDIR)

print("Copying tablet code")
TABLETSUBDIRS = [
    "i18n/en",
    "Resources/common",
    "Resources/html",
    "Resources/lib",
    "Resources/menu",
    "Resources/menulib",
    "Resources/questionnaire",
    "Resources/questionnairelib",
    "Resources/screen",
    "Resources/table",
    "Resources/task",
    "Resources/task_html",
]
for d in TABLETSUBDIRS:
    destdir = join(WRKTABLETDIR, d)
    mkdirp(destdir)
    copyglob(join(SRCTABLETDIR, d, '*'), destdir)

DSTSTRINGFILE = join(DSTTABLETDIR, 'i18n/en/strings.xml')

# =============================================================================
print("Creating man page. Will be installed as " + DSTMANFILE)
# =============================================================================
# http://www.fnal.gov/docs/products/ups/ReferenceManual/html/manpages.html

with gzip.open(WRKMANFILE, 'wt') as outfile:
    print(r""".\" Manpage for {SETUPSCRIPTNAME}.
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
    ), file=outfile)

# =============================================================================
print("Creating man page. Will be installed as " + DSTMETAMANFILE)
# =============================================================================
# http://www.fnal.gov/docs/products/ups/ReferenceManual/html/manpages.html

with gzip.open(WRKMETAMANFILE, 'wt') as outfile:
    print(r""".\" Manpage for {METASCRIPTNAME}.
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
    ), file=outfile)

# =============================================================================
print("Creating links to documentation. Will be installed as " + DSTREADME)
# =============================================================================
with open(WRKREADME, 'w') as outfile:
    print("""
CamCOPS: the Cambridge Cognitive and Psychiatric Test Kit

See http://www.camcops.org for documentation.
See also {DSTINSTRUCTIONS}
    """.format(
        DSTINSTRUCTIONS=DSTINSTRUCTIONS,
    ), file=outfile)

# =============================================================================
print("Creating config file. Will be installed as " + DSTCONFIGFILE)
# =============================================================================
with open(WRKCONFIGFILE, 'w') as outfile:
    print(string.Template("""
# =============================================================================
# Format of the CamCOPS configuration file
# =============================================================================
# COMMENTS. Hashes (#) and semicolons (;) mark out comments.
# SECTIONS. Sections are indicated with: [section]
# NAME/VALUE (KEY/VALUE) PAIRS.
# - The parser used is ConfigParser (Python).
# - It allows "name=value" or "name:value".
# - BOOLEAN OPTIONS. For Boolean options, TRUE values are any of: 1, yes, true,
#   on (case-insensitive). FALSE values are any of: 0, no, false, off.
# - UTF-8 encoding. Use this. For ConfigParser, the file is explicitly opened
#   in UTF-8 mode.
# - Avoid indentation.

# =============================================================================
# Main section: [server]
# =============================================================================

[server]

# -----------------------------------------------------------------------------
# Database connection/tools
# -----------------------------------------------------------------------------

# DB_NAME: MySQL database name.
# If you didn't call the database 'DEFAULT_DB_NAME}', edit the next line:

DB_NAME = $DEFAULT_DB_NAME

# DB_USER: MySQL database username.
# DB_PASSWORD: MySQL database password.
# Edit the next two lines:

DB_USER = $DEFAULT_DB_USER
DB_PASSWORD = $DEFAULT_DB_PASSWORD

# DB_SERVER: MySQL database server (default: localhost).
# DB_PORT: MySQL database port (default: 3306).
# These values are unlikely to need modification:

DB_SERVER = localhost
DB_PORT = 3306

# MYSQL: Specify the full path to the mysql executable, by default
# /usr/bin/mysql (used for data dumps for privileged users).

MYSQL = /usr/bin/mysql

# MYSQLDUMP: Specify the full path to the mysqldump executable, by default
# /usr/bin/mysqldump (used for data dumps for privileged users).

MYSQLDUMP = /usr/bin/mysqldump

# -----------------------------------------------------------------------------
# Database title and ID descriptions
# -----------------------------------------------------------------------------
# NOTE: WHENEVER YOU CHANGE THESE, YOU MUST USE THE CAMCOPS COMMAND-LINE TOOL
# TO REWRITE THEM INTO THE DATABASE.

# DATABASE_TITLE: the friendly title of your database (as Unicode UTF-8).

DATABASE_TITLE = My First CamCOPS Database

# IDDESC_1 to IDDESC_8: full descriptions of each of the possible ID numbers.
# IDSHORTDESC_1 to IDSHORTDESC_8: short versions of the same descriptions.
# All are Unicode UTF-8.

IDDESC_1 = NHS number
IDSHORTDESC_1 = NHS
IDDESC_2 = CPFT RiO number
IDSHORTDESC_2 = RiO
IDDESC_3 = CPFT M number
IDSHORTDESC_3 = M
IDDESC_4 = Addenbrooke’s number
IDSHORTDESC_4 = Add
IDDESC_5 = Papworth number
IDSHORTDESC_5 = Pap
IDDESC_6 = Hinchingbrooke number
IDSHORTDESC_6 = Hinch
IDDESC_7 = Peterborough City Hosp number
IDSHORTDESC_7 = PCH
IDDESC_8 = Spare_8_idnum
IDSHORTDESC_8 = Spare8

# -----------------------------------------------------------------------------
# ID policies
# -----------------------------------------------------------------------------
# NOTE: WHENEVER YOU CHANGE THESE, YOU MUST USE THE CAMCOPS COMMAND-LINE TOOL
# TO REWRITE THEM INTO THE DATABASE.

# UPLOAD_POLICY and FINALIZE_POLICY define two ID policies. The upload policy
# is the looser policy, allowing upload from tablets to the server. The
# finalize policy is typically the same or stricter, and allows records to
# be deleted from the tablets. See documentation.
#
# Case-insensitive. Valid tokens are:
#   (
#   )
#   AND
#   OR
#   forename
#   surname
#   dob
#   sex
#   idnum1 ... idnum8
#
# Liaison psychiatry upload example, allowing upload with any of multiple
# institutional IDs, but finalizing only with the institution's core ID:
#
# UPLOAD_POLICY = forename AND surname AND dob AND sex AND (idnum1 OR idnum2 OR idnum3 OR idnum4 OR idnum5 OR idnum6 OR idnum7 OR idnum8)
# FINALIZE_POLICY = forename AND surname AND dob AND sex AND idnum1
#
# Research pseudonym example, in which a single number is used and no
# patient-identifying information:
#
# UPLOAD_POLICY = sex AND idnum1
# FINALIZE_POLICY = sex AND idnum1

UPLOAD_POLICY = forename AND surname AND dob AND sex AND (idnum1 OR idnum2 OR idnum3 OR idnum4 OR idnum5 OR idnum6 OR idnum7 OR idnum8)
FINALIZE_POLICY = forename AND surname AND dob AND sex AND idnum1

# -----------------------------------------------------------------------------
# URLs and paths
# -----------------------------------------------------------------------------

# =============================================================================
# Site URL configuration
# =============================================================================

# A quick note on absolute and relative URLs, and how CamCOPS is mounted.
#
# Suppose your CamCOPS site is visible at
#       https://www.somewhere.ac.uk/camcops_smith_lab/webview
#       ^      ^^                 ^^                ^^      ^
#       +------++-----------------++----------------++------+
#       |       |                  |                 |
#       1       2                  3                 4
#
# Part 1 is the protocol, and part 2 the machine name.
# Part 3 is the mount point. The main server (e.g. Apache) knows where the
# CamCOPS script is mounted (in this case /camcops_smith_lab). It does NOT
# tell the script via the script's WSGI environment. Therefore, if the script
# sends HTML including links, the script can operate only in relative mode.
# For it to operate in absolute mode, it would need to know (3).
# Part 4 is visible to the CamCOPS script.
#
# If CamCOPS used URLs starting with '/', it would need to be told at least
# part (3). To use absolute URLs, it would need to know all of (1), (2), (3).
# We will follow others (e.g. http://stackoverflow.com/questions/2005079) and
# use only relative URLs.

# LOCAL_INSTITUTION_URL: Clicking on your institution's logo in the CamCOPS
# menu will take you to this URL.
# Edit the next line to point to your institution:

LOCAL_INSTITUTION_URL = $INSTITUTIONURL

# LOCAL_LOGO_FILE_ABSOLUTE: Specify the full path to your institution's logo
# file, e.g. /var/www/logo_local_myinstitution.png . It's used for PDF
# generation; HTML views use the fixed string "static/logo_local.png", aliased
# to your file via the Apache configuration file).
# Edit the next line to point to your local institution's logo file:

LOCAL_LOGO_FILE_ABSOLUTE = $DSTSTATICDIR/logo_local.png

# CAMCOPS_LOGO_FILE_ABSOLUTE: similarly, but for the CamCOPS logo.
# It's fine not to specify this.

# CAMCOPS_LOGO_FILE_ABSOLUTE = $DSTSTATICDIR/logo_camcops.png

# MAIN_STRING_FILE: Main strings.xml file to be used by the server.
# file and other resources (set by the installation script;
# default $DSTSTRINGFILE).

MAIN_STRING_FILE = $DSTSTRINGFILE

# EXTRA_STRING_FILES: multiline list of filenames (with absolute paths), read
# by the server, and used as EXTRA STRING FILES (in addition to the main
# strings.xml file specified by MAIN_STRING_FILE above). Optional.
# However, if you specify it, don't remove the default of
#   $DSTEXTRASTRINGS
# or you will lose some functionality of some core tasks.
# May use "glob" pattern-matching (see
# https://docs.python.org/3.5/library/glob.html).

EXTRA_STRING_FILES = $DSTEXTRASTRINGS/*

# INTROSPECTION: permits the offering of CamCOPS source code files to the user,
# allowing inspection of tasks' internal calculating algorithms. Default is
# true.

INTROSPECTION = true

# HL7_LOCKFILE: filename stem used for process locking for HL7 message
# transmission. Default is $DSTHL7LOCKFILESTEM
# The actual lockfile will, in this case, be called
#     $DSTHL7LOCKFILESTEM.lock
# and other process-specific files will be created in the same directory (so
# the CamCOPS script must have permission from the operating system to do so).
# The installation script will create the directory $DSTLOCKDIR

HL7_LOCKFILE = $DSTHL7LOCKFILESTEM

# SUMMARY_TABLES_LOCKFILE: file stem used for process locking for summary table
# generation. Default is $DSTSUMMARYTABLELOCKFILESTEM.
# The lockfile will, in this case, be called
#     $DSTSUMMARYTABLELOCKFILESTEM.lock
# and other process-specific files will be created in the same directory (so
# the CamCOPS script must have permission from the operating system to do so).
# The installation script will create the directory $DSTLOCKDIR

SUMMARY_TABLES_LOCKFILE = $DSTSUMMARYTABLELOCKFILESTEM

# WKHTMLTOPDF_FILENAME: for the pdfkit PDF engine, specify a filename for
# wkhtmltopdf that incorporates any need for an X Server (not the default
# /usr/bin/wkhtmltopdf). See http://stackoverflow.com/questions/9604625/ .
# A suitable one is bundled with CamCOPS, so you shouldn't have to alter this
# default. Default is None, which usually ends up calling /usr/bin/wkhtmltopdf

WKHTMLTOPDF_FILENAME =

# -----------------------------------------------------------------------------
# Login and session configuration
# -----------------------------------------------------------------------------

# SESSION_TIMEOUT_MINUTES: Time after which a session will expire (default 30).

SESSION_TIMEOUT_MINUTES = 30

# PASSWORD_CHANGE_FREQUENCY_DAYS: Force password changes (at webview login)
# with this frequency (0 for never). Note that password expiry will not prevent
# uploads from tablets, but when the user next logs on, a password change will
# be forced before they can do anything else.

PASSWORD_CHANGE_FREQUENCY_DAYS = 0

# LOCKOUT_THRESHOLD: Lock user accounts after every n login failures (default
# 10).

LOCKOUT_THRESHOLD = 10

# LOCKOUT_DURATION_INCREMENT_MINUTES: Account lockout time increment (default
# 10).
# Suppose LOCKOUT_THRESHOLD = 10 and LOCKOUT_DURATION_INCREMENT_MINUTES = 20.
# After the first 10 failures, the account will be locked for 20 minutes.
# After the next 10 failures, the account will be locked for 40 minutes.
# After the next 10 failures, the account will be locked for 60 minutes, and so
# on. Time and administrators can unlock accounts.

LOCKOUT_DURATION_INCREMENT_MINUTES = 10

# DISABLE_PASSWORD_AUTOCOMPLETE: if true, asks browsers not to autocomplete the
# password field on the main login page. The correct setting for maximum
# security is debated (don't cache passwords, versus allow a password manager
# so that users can use better/unique passwords). Default: true.
# Note that some browsers (e.g. Chrome v34 and up) may ignore this.

DISABLE_PASSWORD_AUTOCOMPLETE = true

# -----------------------------------------------------------------------------
# Suggested filenames for saving PDFs from the web view
# -----------------------------------------------------------------------------
# Try with Chrome, Firefox. Internet Explorer may be less obliging.

# PATIENT_SPEC_IF_ANONYMOUS: for anonymous tasks, this string is used as the
# patient descriptor (see also PATIENT_SPEC, SUGGESTED_PDF_FILENAME below).
# Typically "anonymous".

PATIENT_SPEC_IF_ANONYMOUS = anonymous

# PATIENT_SPEC: string, into which substitutions will be made, that defines the
# {patient} element available for substitution into the *_FILENAME_SPEC
# variables (see below). Possible substitutions:
#
#   {surname}      : patient's surname in upper case
#   {forename}     : patient's forename in upper case
#   {dob}          : patient's date of birth (format "%Y-%m-%d", e.g.
#                    2013-07-24)
#   {sex}          : patient's sex (M, F, X)
#
#   {idshortdesc1} : short description of the relevant ID number, if that ID
#   ...              number is not blank; otherwise blank
#   {idshortdesc8}
#
#   {idnum1}       : ID numbers
#   ...
#   {idnum8}
#
#   {allidnums}    : all available ID numbers in "shortdesc-value" pairs joined
#                    by "_". For example, if ID numbers 1, 4, and 5 are
#                    non-blank, this would have the format
#                    idshortdesc1-idval1_idshortdesc4-idval4_idshortdesc5-idval5

PATIENT_SPEC = {surname}_{forename}_{allidnums}

# TASK_FILENAME_SPEC:
# TRACKER_FILENAME_SPEC:
# CTV_FILENAME_SPEC:
# Strings used for suggested filenames to save from the webview, for tasks,
# trackers, and clinical text views. Substitutions will be made to determine
# the filename to be used for each file. Possible substitutions:
#
#   {patient}   : Patient string. If the task is anonymous, this is
#                 PATIENT_SPEC_IF_ANONYMOUS; otherwise, it is defined by
#                 PATIENT_SPEC above.
#   {created}   : Date/time of task creation.  Dates/times are of the format
#                 "%Y-%m-%dT%H%M", e.g. 2013-07-24T2004. They are expressed in
#                 the timezone of creation (but without the timezone
#                 information for filename brevity).
#   {now}       : Time of access/download (i.e. time now), in local timezone.
#   {tasktype}  : Base table name of the task (e.g. "phq9"). May contain an
#                 underscore. Blank for to trackers/CTVs.
#   {serverpk}  : Server's primary key. (In combination with tasktype, this
#                 uniquely identifies not just a task but a version of that
#                 task.) Blank for trackers/CTVs.
#   {filetype}  : e.g. "pdf", "html", "xml" (lower case)
#   {anonymous} : evaluates to PATIENT_SPEC_IF_ANONYMOUS if anonymous,
#                 otherwise ""
#   ... plus all those substitutions applicable to PATIENT_SPEC
#
# After these substitutions have been made, the entire filename is then
# processed to ensure that only characters generally acceptable to filenames
# are used (see convert_string_for_filename() in the CamCOPS source code).
# Specifically:
#
#   - Unicode converted to 7-bit ASCII (will mangle, e.g. removing accents)
#   - spaces converted to underscores
#   - characters are removed unless they are one of the following: all
#     alphanumeric characters (0-9, A-Z, a-z); '-'; '_'; '.'; and the
#     operating-system-specific directory separator (Python's os.sep, a forward
#     slash '/' on UNIX or a backslash '\' under Windows).

TASK_FILENAME_SPEC = CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}
TRACKER_FILENAME_SPEC = CamCOPS_{patient}_{now}_tracker.{filetype}
CTV_FILENAME_SPEC = CamCOPS_{patient}_{now}_clinicaltextview.{filetype}

# -----------------------------------------------------------------------------
# Debugging options
# -----------------------------------------------------------------------------
# Possible log levels are (case-insensitive): "debug", "info", "warn"
# (equivalent: "warning"), "error", and "critical" (equivalent: "fatal").

# WEBVIEW_LOGLEVEL: Set the level of detail provided from the webview to the
# Apache server log. (Loglevel option; see above.)

WEBVIEW_LOGLEVEL = info

# DBENGINE_LOGLEVEL: Set the level of detail provided from the underlying
# database transaction handler to the Apache server log. More of a security
# risk than WEBVIEW_DEBUG_OUTPUT. (Loglevel option; see above.)

DBENGINE_LOGLEVEL = info

# DBCLIENT_LOGLEVEL: Set the log level for the tablet client database access
# script. (Loglevel option; see above.)

DBCLIENT_LOGLEVEL = info

# ALLOW_INSECURE_COOKIES: DANGEROUS option that removes the requirement that
# cookies be HTTPS (SSL) only.

ALLOW_INSECURE_COOKIES = false

# -----------------------------------------------------------------------------
# Analytics
# -----------------------------------------------------------------------------

# SEND_ANALYTICS: Send analytics to the CamCOPS base in Cambridge? (Boolean
# option; default true.) We'd be very grateful if you would leave this on, as
# it helps us to know how many users of CamCOPS there are and what tasks are
# popular. NO PATIENT-IDENTIFIABLE INFORMATION, PER-PATIENT INFORMATION, OR
# TASK DETAILS ARE SENT. If enabled, the following information is sent weekly
# to the CamCOPS base computer:
# - the date/time, including timezone (allowing us to get a rough idea of its
#   geographical distribution)
# - IP address (allowing us to get a rough idea of geographical/institutional
#   distribution)
# - the CamCOPS version number (so we know if old versions are still in use, or
#   if we can break them in an upgrade)
# - the total number of records in each table (allowing us to get an idea of
#   which tasks are popular)

SEND_ANALYTICS = true

# -----------------------------------------------------------------------------
# Export to a staging database for CRIS, CRATE, or similar anonymisation
# software (anonymisation staging database; ANONSTAG)
# -----------------------------------------------------------------------------

ANONSTAG_DB_SERVER = localhost
ANONSTAG_DB_PORT = 3306
ANONSTAG_DB_NAME = $DEFAULT_ANONSTAG_DB_NAME
ANONSTAG_DB_USER = $DEFAULT_ANONSTAG_DB_USER
ANONSTAG_DB_PASSWORD = $DEFAULT_ANONSTAG_DB_PASSWORD
EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE = /tmp/camcops_cris_dd_draft.tsv

# -----------------------------------------------------------------------------
# In development
# -----------------------------------------------------------------------------

# ALLOW_MOBILEWEB: Enable the mobileweb client? (Boolean.)
# FEATURE IN DEVELOPMENT; SWITCH THIS OFF FOR NOW.
# The Mobile Web app is not yet fully operational.
# Also, enabling Mobile Web allows authorized users to retrieve (their own)
# patient information from the server, so disable it unless you need it.

ALLOW_MOBILEWEB = false

# =============================================================================
# List of HL7/file recipients, and then details for each one
# =============================================================================
# This section defines a list of recipients to which Health Level Seven (HL7)
# messages or raw files will be sent. Typically, you will send them by calling
# "camcops -7 CONFIGFILE" regularly from the system's /etc/crontab or other
# scheduling system. For example, a conventional /etc/crontab file has these
# fields:
#
#   minutes, hours, day_of_month, month, day_of_week, user, command
#
# so you could add a line like this to /etc/crontab:
#
#   * * * * *  root  camcops -7 /etc/camcops/MYCONFIG.conf
#
# ... and CamCOPS would run its exports once per minute. See "man 5 crontab"
# or http://en.wikipedia.org/wiki/Cron for more options.
#
# In this section, keys are ignored; values are section headings (one per
# recipient).

[recipients]

# Examples (commented out):

# recipient=recipient_A
# recipient=recipient_B

# =============================================================================
# Individual HL7/file recipient configurations
# =============================================================================
# Dates are YYYY-MM-DD, e.g. 2013-12-31, or blank

# Example (disabled because it's not in the list above)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# First example
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[recipient_A]

# TYPE: one of the following methods.
#   hl7
#       Sends HL7 messages across a TCP/IP network.
#   file
#       Writes files to a local filesystem.

TYPE = hl7

# -----------------------------------------------------------------------------
# Options applicable to HL7 messages and file transfers
# -----------------------------------------------------------------------------

# PRIMARY_IDNUM: which ID number (1-8) should be considered the "internal"
# (primary) ID number? Must be specified for HL7 messages. May be blank for
# file transmission.

PRIMARY_IDNUM = 1

# REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY: defines behaviour relating to the
# primary ID number (as defined by PRIMARY_IDNUM).
# - If true, no message sending will be attempted unless the PRIMARY_IDNUM is a
#   mandatory part of the finalizing policy (and if FINALIZED_ONLY is false,
#   also of the upload policy).
# - If false, messages will be sent, but ONLY FROM TASKS FOR WHICH THE
#   PRIMARY_IDNUM IS PRESENT; others will be ignored.
# - For file sending only, this will be ignored if PRIMARY_IDNUM is blank.
# - For file sending only, this setting does not apply to anonymous tasks,
#   whose behaviour is controlled by INCLUDE_ANONYMOUS (see below).

REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = true

# START_DATE: earliest date for which tasks will be sent. Assessed against the
# task's "when_created" field, converted to Universal Coordinated Time (UTC) --
# that is, this date is in UTC (beware if you are in a very different time
# zone). Blank to apply no start date restriction.

START_DATE =

# END_DATE: latest date for which tasks will be sent. In UTC. Assessed against
# the task's "when_created" field (converted to UTC). Blank to apply no end
# date restriction.

END_DATE =

# FINALIZED_ONLY: if true, only send tasks that are finalized (moved off their
# originating tablet and not susceptible to later modification). If false, also
# send tasks that are uploaded but not yet finalized (they will then be sent
# again if they are modified later).

FINALIZED_ONLY = true

# TASK_FORMAT: one of: pdf, html, xml

TASK_FORMAT = pdf

# XML_FIELD_COMMENTS: if TASK_FORMAT is xml, then XML_FIELD_COMMENTS determines
# whether field comments are included. These describe the meaning of each field
# so add to space requirements but provide more information for human readers.
# (Default true.)

XML_FIELD_COMMENTS = true

# -----------------------------------------------------------------------------
# Options applicable to HL7 only (TYPE = hl7)
# -----------------------------------------------------------------------------

# HOST: HL7 hostname or IP address

HOST = myhl7server.mydomain

# PORT: HL7 port (default 2575)

PORT = 2575

# PING_FIRST: if true, requires a successful ping to the server prior to
# sending HL7 messages. (Note: this is a TCP/IP ping, and tests that the
# machine is up, not that it is running an HL7 server.) Default: true.

PING_FIRST = true

# NETWORK_TIMEOUT_MS: network time (in milliseconds). Default: 10000.

NETWORK_TIMEOUT_MS = 10000

# IDNUM_TYPE_1 ... IDNUM_TYPE_8: strings used as the HL7 identifier type code
# in the PID segment, field 3 (internal ID) list of identifiers. If one is
# blank, its information will not be sent. (If the PRIMARY_IDNUM's type is
# blank, the system will not process messages.)

IDNUM_TYPE_1 = NHS
IDNUM_TYPE_2 = RiO
IDNUM_TYPE_3 = M
IDNUM_TYPE_4 = Add
IDNUM_TYPE_5 = Pap
IDNUM_TYPE_6 = Hinch
IDNUM_TYPE_7 = PCH
IDNUM_TYPE_8 =

# IDNUM_AA_1 ... IDNUM_AA_8: strings used as the Assigning Authority in the PID
# segment, field 3 (internal ID) list of identifiers. Optional.

IDNUM_AA_1 = NHS
IDNUM_AA_2 = CPFT
IDNUM_AA_3 = CPFT
IDNUM_AA_4 = CUH
IDNUM_AA_5 = CUH
IDNUM_AA_6 = HHC
IDNUM_AA_7 = PSH
IDNUM_AA_8 =

# KEEP_MESSAGE: keep a copy of the entire message in the databaase. Default is
# false. WARNING: may consume significant space in the database.

KEEP_MESSAGE = false

# KEEP_REPLY: keep a copy of the reply (e.g. acknowledgement) message received
# from the server. Default is false. WARNING: may consume significant space.

KEEP_REPLY = false

# DIVERT_TO_FILE: Override HOST/PORT options and send HL7 messages to this
# (single) file instead. Each messages is appended to the file. Default is
# blank (meaning network transmission will be used). This is a debugging
# option, allowing you to redirect HL7 messages to a file and inspect them.

DIVERT_TO_FILE =

# TREAT_DIVERTED_AS_SENT: Any messages that are diverted to a file (using
# DIVERT_TO_FILE) are treated as having been sent (thus allowing the file to
# mimic an HL7-receiving server that's accepting messages happily). If set to
# false (the default), a diversion will allow you to preview messages for
# debugging purposes without "swallowing" them. BEWARE, though: if you have
# an automatically scheduled job (for example, to send messages every minute)
# and you divert with this flag set to false, you will end up with a great many
# message attempts!

TREAT_DIVERTED_AS_SENT = false

# -----------------------------------------------------------------------------
# Options applicable to file transfers only (TYPE = file)
# -----------------------------------------------------------------------------

# INCLUDE_ANONYMOUS: include anonymous tasks.
# - Note that anonymous tasks cannot be sent via HL7; the HL7 specification is
#   heavily tied to identification.
# - Note also that this setting operates independently of the
#   REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY setting.

INCLUDE_ANONYMOUS = true

# PATIENT_SPEC_IF_ANONYMOUS: for anonymous tasks, this string is used as the
# patient descriptor (see also PATIENT_SPEC, FILENAME_SPEC below). Typically
# "anonymous".

PATIENT_SPEC_IF_ANONYMOUS = anonymous

# PATIENT_SPEC: string, into which substitutions will be made, that defines the
# {patient} element available for substitution into the FILENAME_SPEC (see
# below). Possible substitutions: as for PATIENT_SPEC in the main "[server]"
# section of the configuration file (see above).

PATIENT_SPEC = {surname}_{forename}_{idshortdesc1}{idnum1}

# FILENAME_SPEC: string into which substitutions will be made to determine the
# filename to be used for each file. Possible substitutions: as for
# SUGGESTED_PDF_FILENAME in the main "[server]" section of the configuration
# file (see above).

FILENAME_SPEC = /my_nfs_mount/mypath/CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}

# MAKE_DIRECTORY: make the directory if it doesn't already exist. Default is
# false.

MAKE_DIRECTORY = true

# OVERWRITE_FILES: whether or not to attempt overwriting existing files of the
# same name (default false). There is a DANGER of inadvertent data loss if you
# set this to true. (Needing to overwrite a file suggests that your filenames
# are not task-unique; try ensuring that both the {tasktype} and {serverpk}
# attributes are used in the filename.)

OVERWRITE_FILES = false

# RIO_METADATA: whether or not to export a metadata file for Servelec's RiO
# (default false).
# Details of this file format are in cc_task.py / Task.get_rio_metadata().
# The metadata filename is that of its associated file, but with the extension
# replaced by ".metadata" (e.g. X.pdf is accompanied by X.metadata).
# If RIO_METADATA is true, the following options also apply:
#   RIO_IDNUM: which of the ID numbers (as above) is the RiO ID?
#   RIO_UPLOADING_USER: username for the uploading user (maximum of 10
#       characters)
#   RIO_DOCUMENT_TYPE: document type as defined in the receiving RiO system.
#       This is a code that maps to a human-readable document type; for
#       example, the code "APT" might map to "Appointment Letter". Typically we
#       might want a code that maps to "Clinical Correspondence", but the code
#       will be defined within the local RiO system configuration.

RIO_METADATA = false
RIO_IDNUM = 2
RIO_UPLOADING_USER = CamCOPS
RIO_DOCUMENT_TYPE = CC

# SCRIPT_AFTER_FILE_EXPORT: filename of a shell script or other executable to
# run after file export is complete. You might use this script, for example, to
# move the files to a different location (such as across a network). If the
# parameter is blank, no script will be run. If no files are exported, the
# script will not be run.
# - Parameters passed to the script: a list of all the filenames exported.
#   (This includes any RiO metadata filenames.)
# - WARNING: the script will execute with the same permissions as the instance
#   of CamCOPS that's doing the export (so, for example, if you run CamCOPS
#   from your /etc/crontab as root, then this script will be run as root; that
#   can pose a risk!).
# - The script executes while the export lock is still held by CamCOPS (i.e.
#   further HL7/file transfers won't be started until the script(s) is/are
#   complete).
# - If the script fails, an error message is recorded, but the file transfer is
#   still considered to have been made (CamCOPS has done all it can and the
#   responsibility now lies elsewhere).
# - Example test script: suppose this is /usr/local/bin/print_arguments:
#       #!/bin/bash
#       for f in $$@
#       do
#           echo "CamCOPS has just exported this file: $$f"
#       done
#   ... then you could set:
#       SCRIPT_AFTER_FILE_EXPORT = /usr/local/bin/print_arguments

SCRIPT_AFTER_FILE_EXPORT =

    """).substitute(  # noqa
        DEFAULT_ANONSTAG_DB_NAME=DEFAULT_ANONSTAG_DB_NAME,
        DEFAULT_ANONSTAG_DB_PASSWORD=DEFAULT_ANONSTAG_DB_PASSWORD,
        DEFAULT_ANONSTAG_DB_USER=DEFAULT_ANONSTAG_DB_USER,
        DEFAULT_DB_NAME=DEFAULT_DB_NAME,
        DEFAULT_DB_PASSWORD=DEFAULT_DB_PASSWORD,
        DEFAULT_DB_USER=DEFAULT_DB_USER,
        DSTBASEDIR=DSTBASEDIR,
        DSTEXTRASTRINGS=DSTEXTRASTRINGS,
        DSTHL7LOCKFILESTEM=DSTHL7LOCKFILESTEM,
        DSTLOCKDIR=DSTLOCKDIR,
        DSTSERVERDIR=DSTSERVERDIR,
        DSTSTATICDIR=DSTSTATICDIR,
        DSTSTRINGFILE=DSTSTRINGFILE,
        DSTSUMMARYTABLELOCKFILESTEM=DSTSUMMARYTABLELOCKFILESTEM,
        INSTITUTIONURL=INSTITUTIONURL,
    ), file=outfile)
shutil.copy(WRKCONFIGFILE, WEBDOCSCONFIGFILE)

# =============================================================================
print("Creating launch script. Will be installed as " + DSTCONSOLEFILE)
# =============================================================================
with open(WRKCONSOLEFILE, 'w') as outfile:
    print("""#!/bin/sh
# Launch script for CamCOPS command-line tool.

echo 'Launching CamCOPS command-line tool...' >&2

export PYTHONPATH={DSTPYTHONPATH}

{DSTVENVPYTHON} {DSTMAINSCRIPT} "$@"
    """.format(
        DSTPYTHONPATH=DSTPYTHONPATH,
        DSTVENVPYTHON=DSTVENVPYTHON,
        DSTMAINSCRIPT=DSTMAINSCRIPT,
    ), file=outfile)


# =============================================================================
print("Creating {} launch script. Will be installed as {}".format(
    METASCRIPTNAME, DSTMETACONSOLEFILE))
# =============================================================================
with open(WRKMETACONSOLEFILE, 'w') as outfile:
    print("""#!/bin/sh
# Launch script for CamCOPS meta-command tool tool.

echo 'Launching CamCOPS meta-command tool...' >&2

export PYTHONPATH={DSTPYTHONPATH}

{DSTVENVPYTHON} {DSTMETASCRIPT} "$@"
    """.format(
        DSTPYTHONPATH=DSTPYTHONPATH,
        DSTVENVPYTHON=DSTVENVPYTHON,
        DSTMETASCRIPT=DSTMETASCRIPT,
    ), file=outfile)


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
print("Creating control file")
# =============================================================================

DEPENDS_DEB = get_lines_without_comments(DEB_REQ_FILE)
DEPENDS_RPM = get_lines_without_comments(RPM_REQ_FILE)

with open(join(DEBDIR, 'control'), 'w') as outfile:
    print("""Package: {PACKAGE}
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
    ), file=outfile)

# =============================================================================
print("Creating conffiles file. Will be installed as "
      + join(DSTDPKGDIR, PACKAGE + '.conffiles'))
# =============================================================================
configfiles = [DSTCONFIGFILE,
               DST_SUPERVISOR_CONF_FILE]
with open(join(DEBDIR, 'conffiles'), 'w') as outfile:
    print("\n".join(configfiles), file=outfile)
# If a configuration file is removed by the user, it won't be reinstalled:
#   http://www.debian.org/doc/debian-policy/ap-pkg-conffiles.html
# In this situation, do "sudo aptitude purge camcops" then reinstall.

# =============================================================================
print("Creating preinst file. Will be installed as "
      + join(DSTDPKGDIR, PACKAGE + '.preinst'))
# =============================================================================
with open(join(DEBDIR, 'preinst'), 'w') as outfile:
    print("""#!/bin/bash
# Exit on any errors? (Lintian strongly advises this.)
set -e

echo '{PACKAGE}: preinst file executing'

# Would be nice just to shut down camcops processes. But there can be
# several, on live systems, and it's hard to predict what they're called. We
# need them shut down if we're going to check/reinstall the virtual
# environment (otherwise it'll be busy). So although we tried this:

# echo "If available, stopping supervisor process: {PACKAGE}-gunicorn"
# which supervisorctl >/dev/null && supervisorctl stop {PACKAGE}-gunicorn
# supervisorctl seems not to emit an error exit status whatever it does

# ... in practice we should perhaps just stop the whole thing:

echo "If available, stopping supervisor service"
service supervisor stop || echo "no supervisor service or unable to stop"

echo '{PACKAGE}: preinst file finished'

    """.format(
        PACKAGE=PACKAGE,
    ), file=outfile)

# =============================================================================
print("Creating postinst file. Will be installed as "
      + join(DSTDPKGDIR, PACKAGE + '.postinst'))
# =============================================================================

with open(join(DEBDIR, 'postinst'), 'w') as outfile:
    print("""#!/bin/bash
# Exit on any errors? (Lintian strongly advises this.)
set -e

echo '{PACKAGE}: postinst file executing'

#------------------------------------------------------------------------------
# Helper functions
#------------------------------------------------------------------------------

command_exists()
{{
    # arguments: $1 is the command to test
    # returns 0 (true) for found, 1 (false) for not found
    if command -v $1 >/dev/null; then return 0; else return 1; fi
}}

# running_centos()
# {{
#     if [ -f /etc/system-release ] ; then
#         SYSTEM=`cat /etc/system-release | cut -d' ' -f1`
#         # VERSION=`cat /etc/system-release | cut -d' ' -f3`
#         # SYSTEM_ID=\$SYSTEM-\$VERSION
#         if ["$SYSTEM" == "CentOS"] ; then
#             return 0 # true
#         fi
#     fi
#     return 1 # false
# }}

#------------------------------------------------------------------------------
# Install Python virtual environment with packages
#------------------------------------------------------------------------------

echo 'About to install virtual environment'
export XDG_CACHE_HOME={DSTPYTHONCACHE}
{DSTSYSTEMPYTHON} {DSTVENVSCRIPT} {DSTPYTHONVENV} --skippackagechecks

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

# As before, we tried doing it selectively, but that was tricky, so we
# do all:

# echo "If available, starting supervisor process: {PACKAGE}-gunicorn"
# which supervisorctl >/dev/null && supervisorctl start {PACKAGE}-gunicorn

echo "If available, starting supervisor service"
service supervisor stop || echo "no supervisor service or unable to stop"

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
echo "        yum install httpd mod_proxy mod_xsendfile"
# mod_wsgi
echo "        yum install mysql55 mysql55-server libmysqlclient-dev"
echo
echo "2.  Can't install wkhtmltopdf right now (dpkg database will be locked)."
echo "    Later, run this once:"
echo "    {DSTSYSTEMPYTHON} {DSTWKHTMLTOPDFSCRIPT}"
echo "========================================================================"

echo '{PACKAGE}: postinst file finished'

    """.format(  # noqa
        PACKAGE=PACKAGE,
        DSTPYTHONCACHE=DSTPYTHONCACHE,
        DSTSYSTEMPYTHON=DSTSYSTEMPYTHON,
        DSTWKHTMLTOPDFSCRIPT=DSTWKHTMLTOPDFSCRIPT,
        DSTMPLCONFIGDIR=DSTMPLCONFIGDIR,
        DSTVENVSCRIPT=DSTVENVSCRIPT,
        DSTPYTHONVENV=DSTPYTHONVENV,
        DSTLOCKDIR=DSTLOCKDIR,
        DSTCONFIGFILE=DSTCONFIGFILE,
        DST_SUPERVISOR_CONF_FILE=DST_SUPERVISOR_CONF_FILE,
    ), file=outfile)


# =============================================================================
print("Creating prerm file. Will be installed as "
      + join(DSTDPKGDIR, PACKAGE + '.prerm'))
# =============================================================================
with open(join(DEBDIR, 'prerm'), 'w') as outfile:
    print("""#!/bin/sh
set -e

echo '{PACKAGE}: prerm file executing'

# echo "If available, stopping supervisor process: {PACKAGE}-gunicorn"
# which supervisorctl >/dev/null && supervisorctl stop {PACKAGE}-gunicorn

echo "If available, stopping supervisor service"
service supervisor stop || echo "no supervisor service or unable to stop"

# Must use -f or an error will cause the prerm (and package removal) to fail
# See /var/lib/dpkg/info/MYPACKAGE.prerm for manual removal!
find {DSTBASEDIR} -name '*.pyc' -delete
find {DSTBASEDIR} -name '*.pyo' -delete

echo '{PACKAGE}: prerm file finished'

    """.format(
        PACKAGE=PACKAGE,
        DSTBASEDIR=DSTBASEDIR,
    ), file=outfile)

# =============================================================================
print("Creating Lintian override file")
# =============================================================================
with open(join(DEBOVERRIDEDIR, PACKAGE), 'w') as outfile:
    print("""
# Not an official new Debian package, so ignore this one.
# If we did want to close a new-package ITP bug:
# http://www.debian.org/doc/manuals/developers-reference/pkgs.html#upload-bugfix  # noqa
{PACKAGE} binary: new-package-should-close-itp-bug
    """.format(
        PACKAGE=PACKAGE,
    ), file=outfile)

# =============================================================================
print("Creating copyright file. Will be installed as "
      + join(DSTDOCDIR, 'copyright'))
# =============================================================================
with open(join(WRKDOCDIR, 'copyright'), 'w') as outfile:
    print("""{PACKAGE}

CAMCOPS

    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    Licensed under the Apache License, Version 2.0 (the 'License');
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an 'AS IS' BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

ADDITIONAL LIBRARY COMPONENTS

    Public domain or copyright (C) their respective authors (for details,
    see attribution in the source code and other license terms packaged with
    the source).

TEXT FOR SPECIFIC ASSESSMENT SCALES

    Public domain or copyright (C) their respective authors; see details in
    {DSTSTRINGFILE}.
    """.format(
        PACKAGE=PACKAGE,
        DSTSTRINGFILE=DSTSTRINGFILE,
    ), file=outfile)


# =============================================================================
print("Creating supervisor conf file. Will be " + DST_SUPERVISOR_CONF_FILE)
# =============================================================================
with open(WRK_SUPERVISOR_CONF_FILE, 'w') as outfile:
    print(string.Template("""

; IF YOU EDIT THIS FILE, run:
;       sudo service supervisor restart
; TO MONITOR SUPERVISOR, run:
;       sudo supervisorctl status
; TO ADD MORE CAMCOPS INSTANCES, make a copy of the [program:camcops-gunicorn]
;   section, renaming the copy, and change the following:
;   - the CAMCOPS_CONFIG_FILE environment variable;
;   - the port or socket;
;   - the log files.
; Then make the main web server point to the copy as well.
; NOTES:
; - You can't put quotes around the directory variable
;   http://stackoverflow.com/questions/10653590
; - Programs like celery and gunicorn that are installed within a virtual
;   environment use the virtualenv's python via their shebang.
; - The "environment" setting sets the OS environment. The "--env" parameter
;   to gunicorn sets the WSGI environment.

[program:camcops-gunicorn]

command = $DSTPYTHONVENV/bin/gunicorn camcops:application
    --workers 4
    --bind=unix:$DEFAULT_GUNICORN_SOCKET
    --env CAMCOPS_CONFIG_FILE=$DSTCONFIGFILE

; Alternative methods (port and socket respectively):
;   --bind=127.0.0.1:$DEFAULT_GUNICORN_PORT
;   --bind=unix:$DEFAULT_GUNICORN_SOCKET
directory = $DSTSERVERDIR
environment = PYTHONPATH="$DSTPYTHONPATH",MPLCONFIGDIR="$DSTMPLCONFIGDIR"
user = www-data
; ... Ubuntu: typically www-data
; ... CentOS: typically apache
stdout_logfile = /var/log/supervisor/${PACKAGE}_gunicorn.log
stderr_logfile = /var/log/supervisor/${PACKAGE}_gunicorn_err.log
autostart = true
autorestart = true
startsecs = 10
stopwaitsecs = 60

    """).substitute(  # noqa
        DSTPYTHONVENV=DSTPYTHONVENV,
        DEFAULT_GUNICORN_PORT=DEFAULT_GUNICORN_PORT,
        DEFAULT_GUNICORN_SOCKET=DEFAULT_GUNICORN_SOCKET,
        DSTMPLCONFIGDIR=DSTMPLCONFIGDIR,
        DSTSERVERDIR=DSTSERVERDIR,
        DSTPYTHONPATH=DSTPYTHONPATH,
        DSTCONFIGFILE=DSTCONFIGFILE,
        PACKAGE=PACKAGE,
    ), file=outfile)

# =============================================================================
print("Creating instructions. Will be installed within " + DSTBASEDIR)
# =============================================================================

# CONSIDER: MULTIPLE INSTANCES
# - http://stackoverflow.com/questions/1553165/multiple-django-sites-with-apache-mod-wsgi  # noqa
# - http://mediacore.com/blog/hosting-multiple-wsgi-applications-with-apache
# - http://stackoverflow.com/questions/9581197/two-django-projects-running-simultaneously-and-mod-wsgi-acting-werid  # noqa

with open(WRKINSTRUCTIONS, 'w') as outfile:
    print(string.Template("""
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
  Copy this script to run another instance on another port/socket.

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

    sudo -u www-data \\
        PYTHONPATH="$DSTPYTHONPATH" \\
        CAMCOPS_CONFIG_FILE="$DSTCONFIGFILE" \\
        $DSTPYTHONVENV/bin/gunicorn camcops:application \\
        --workers 4 \\
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
        DSTPYTHONPATH=DSTPYTHONPATH,
        DSTPYTHONVENV=DSTPYTHONVENV,
        DSTSERVERDIR=DSTSERVERDIR,
        DSTSTATICDIR=DSTSTATICDIR,
        DST_SUPERVISOR_CONF_FILE=DST_SUPERVISOR_CONF_FILE,
        MAINSCRIPTNAME=MAINSCRIPTNAME,
        TABLETSCRIPT=TABLETSCRIPT,
        URLBASE=URLBASE,
        WEBVIEWSCRIPT=WEBVIEWSCRIPT,
    ), file=outfile)
shutil.copy(WRKINSTRUCTIONS, WEBDOCINSTRUCTIONS)

# In <Files "$DBSCRIPTNAME"> section, we did have:
    # The next line prevents XMLHttpRequest Access-Control-Allow-Origin errors.
    # Also need headers.load as a module:
    # http://harthur.wordpress.com/2009/10/15/configure-apache-to-accept-cross-site-xmlhttprequests-on-ubuntu/  # noqa
    # ln -s /etc/apache2/mods-available/headers.load /etc/apache2/mods-enabled/headers.load  # noqa

    # Header set Access-Control-Allow-Origin "*"

# =============================================================================
print("Creating demonstration MySQL database creation commands. Will be "
      "installed within " + DSTBASEDIR)
# =============================================================================
with open(WRKMYSQLCREATION, 'w') as outfile:
    print("""
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
    ), file=outfile)
shutil.copy(WRKMYSQLCREATION, WEBDOCSMYSQLCREATION)

# =============================================================================
print("Creating demonstration backup script. Will be installed within "
      + DSTBASEDIR)
# =============================================================================
with open(WRKDBDUMPFILE, 'w') as outfile:
    print("""#!/bin/sh

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
    """,  # noqa
    file=outfile)
shutil.copy(WRKDBDUMPFILE, WEBDOCDBDUMPFILE)

# =============================================================================
print("Setting ownership and permissions")
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
    WRKMAINSCRIPT,
    WRKMETACONSOLEFILE,
    WRKDBDUMPFILE,
    join(DEBDIR, 'prerm'),
    join(DEBDIR, 'preinst'),
    join(DEBDIR, 'postinst'),
])
subprocess.check_call(
    ['find', WRKDIR, '-iname', '*.py', '-exec', 'chmod', 'a+x', '{}', ';'])
subprocess.check_call(
    ['find', WRKDIR, '-iname', '*.pl', '-exec', 'chmod', 'a+x', '{}', ';'])

# =============================================================================
print("Removing junk")
# =============================================================================
subprocess.check_call(
    ['find', WRKDIR, '-name', '*.svn', '-exec', 'rm', '-rf', '{}', ';'])
subprocess.check_call(
    ['find', WRKDIR, '-name', '.git', '-exec', 'rm', '-rf', '{}', ';'])
subprocess.check_call(
    ['find', WRKDOCDIR, '-name', 'LICENSE', '-exec', 'rm', '-rf', '{}', ';'])

# =============================================================================
print("Building package")
# =============================================================================
subprocess.check_call(['fakeroot', 'dpkg-deb', '--build', WRKDIR, PACKAGENAME])
# ... "fakeroot" prefix makes all files installed as root:root

# =============================================================================
print("Checking with Lintian")
# =============================================================================
subprocess.check_call(['lintian', PACKAGENAME])

# =============================================================================
print("Converting to RPM")
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
print("Changing dependencies within RPM")
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
print("Deleting temporary workspace")
# =============================================================================
shutil.rmtree(TMPDIR, ignore_errors=True)  # CAUTION!

# =============================================================================
print("=" * 79)
print("Debian package should be: " + PACKAGENAME)
print("RPM should be: " + FULL_RPM_PATH)
# =============================================================================
