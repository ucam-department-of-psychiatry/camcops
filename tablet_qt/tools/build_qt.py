#!/usr/bin/env python3.5

"""
===============================================================================
Overview
===============================================================================

This script is design to download and build the prerequisites for building
the CamCOPS client, including:

    Qt          C++ cross-platform library
    OpenSSL     Encryption
    Eigen       Matrix algebra
    SQLCipher   Encrypted SQLite

This script is intended to run on PYTHON 2 as well as Python 3, and to have
dependencies except the system libraries. That's why it's a bit bare-bones.

===============================================================================
Why?
===============================================================================

When is it NECESSARY to compile OpenSSL from source?
    - OpenSSL for Android
      http://doc.qt.io/qt-5/opensslsupport.html
      ... so: necessary.

When is it NECESSARY to compile Qt from source?
    - Static linking of OpenSSL (non-critical)
    - SQLite support (critical)
      http://doc.qt.io/qt-5/sql-driver.html
      ... so: necessary.
      
===============================================================================
Windows
===============================================================================

Several compilers are possible, in principle.

-   Cygwin
    Very nice installation and cross-operation with native Windows.
    May be useful for toolchains.
    However, software that its compilers produce run under POSIX, so require an
    intermediate Cygwin DLL layer to run; we don't want that.
    
-   Microsoft Visual Studio (free or paid)
    An obvious potential candidate, but not open-source.
    
-   MinGW
    Runs under Windows and produces native code.
    Qt supports it.
    Provides the MSYS bash environment to assist for compilation.
    Can also run under Linux and cross-compile to Windows.

    -   More specifically: mingw-w64, which is GCC for 32- and 64-bit Windows
        http://mingw-w64.org/
        ... i686-w64-mingw32 for 32-bit executables
        ... x86_64-w64-mingw32 for 64-bits executables

    -   Within this option, there is MXE, which is a cross-compilation
        environment.

    -   Upshot: I tried hard. As of 2017-11-19:
        -   MinGW itself is the old version and has been superseded by
            mingw-w64 (a.k.a. mingw64).
        -   attempts to use MinGW-W64 to build 32-bit Windows code (via the MXE
            build of mingw-w64) lead to a GCC compiler crash; this is because
            the version of mingw-w64 that MXE supports uses an old GCC.
        -   getting Qt happy is very hard
        -   For the 64-bit compilation, I ended up with a "make" process that
            reaches this error:

/home/rudolf/dev/qt_local_build/src/qt5/qtwebglplugin/src/plugins/platforms/webgl/qwebglwindow_p.h:64:48: error: field 'defaults' has incomplete type 'std::promise<QMap<unsigned int, QVariant> >'
     std::promise<QMap<unsigned int, QVariant>> defaults;

        -   Not clear that it's worth the effort to use a manual build of
            mingw-w64 as well.
        -   And none of this reached the stage of actually testing on Windows.

DECISION:

-   Use Microsoft Visual Studio and native compilation under Windows.

THEREFORE:

    build OS                target OS
    ===========================================================
    Linux, x86, 64-bit      Linux, x86, 32-bit
                            Linux, x86, 64-bit
                            Android, x86, 32-bit (for emulator)
                            Android, ARM, 32-bit (for Android devices)

    OS/X, x86, 64-bit       OS/X, x86, 64-bit
                            iOS, x86 (for emulator)
                            iOS, ARM, 32-bit (for iPad etc.)
                            iOS, ARM, 64-bit (for iPad etc.)

    Windows, x86, 64-bit    Windows, x86, 64-bit
                            Windows, x86, 32-bit


... reflected in the build_all option.

-------------------------------------------------------------------------------
IGNORE FOR NOW - moving towards MinGW under Windows
-------------------------------------------------------------------------------

FROM SCRATCH:
    - install Git
      ... allow it to add to the PATH
    - install Python 3.5 or higher (e.g. Python 3.6, 64-bit, for a 64-bit OS)
      ... allow it to add to the PATH
    - clone the CamCOPS repository: git clone https://.../camcops
    - python camcops/tablet_qt/tools/build_qt.py

-------------------------------------------------------------------------------
IGNORE - deprecated - Cygwin
-------------------------------------------------------------------------------

We'll try with Cygwin.

1.  INSTALL CYGWIN

    From https://www.cygwin.com/, download the installer (e.g.
    setup-x86_64.exe) and run it. If you want to add more packages later, run
    it again. The screens you'll see, in order (at least for a standard
    installation from the Internet), are:
    
        - saying hello
        - choose a download source
        - select root install directory / install for whom?
        - select local package directory
        - select your internet connection
        - choose a download site
        - ... progress...
        - SELECT PACKAGES -- the interesting bit.
        - ... progress...
        - done; create icons on desktop?
    
2.  If you accept its default, it'll install to C:\cygwin64 (on 64-bit
    systems).
    
3.  At the package selector, make sure you include:

        binutils                GNU assembler, linker, and similar utilities
        colorgcc                Colorizer for GCC warning/error messages (*)
        gcc-core                GNU Compiler Collection (C, OpenMP)
        gcc-g++                 GNU Compiler Collection (C++)
        gccmakedep              X Makefile dependency tool for GCC
        mingw64-x86_64-gcc-g++  GCC for Win64 toolchain (C++)
        
            (*) Not necessary, but nice.
        
    If you can't see a package at the Cygwin installer's "Select Packages"
    screen, make sure "View" shows "Full" or "Category". You can type package
    names into the "Search" box to restrict the list. To install a package,
    click on "skip" and it'll change to the version number. When you've chosen
    everything, click "next".

    # Under Windows: Cygwin or MinGW? Need MinGW, for direct Windows API code
    # (rather than a compatibility layer via Cygwin). We want to build a
    # maximally portable executable.


===============================================================================
Notes
===============================================================================

OTHER NOTES:
# configure: http://doc.qt.io/qt-5/configure-options.html
# sqlite: http://doc.qt.io/qt-5/sql-driver.html
# build for Android: http://wiki.qt.io/Qt5ForAndroidBuilding
# multi-core builds: http://stackoverflow.com/questions/9420825/how-to-compile-on-multiple-cores-using-mingw-inside-qtcreator  # noqa

"""

import argparse
from collections import OrderedDict
from contextlib import contextmanager
import itertools
import logging
import multiprocessing
import os
from os.path import abspath, expanduser, isdir, isfile, join, split
import platform
from pprint import pformat
import shlex
import shutil
import ssl
import stat
import subprocess
import sys
import traceback
from typing import Any, Callable, Dict, Generator, List, Tuple, Union
import urllib.request

try:
    from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
except ImportError:
    main_only_quicksetup_rootlogger = None
try:
    import distro  # http://distro.readthedocs.io/en/latest/
except ImportError:
    distro = None
    if platform.system() in ["Linux"]:
        print("Please install 'distro' first, using:\n\n"
              "pip install distro")
        raise

log = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# -----------------------------------------------------------------------------
# Configure the build process
# -----------------------------------------------------------------------------

USE_MLPACK = False  # mlpack provides matrix algebra but requires Armadillo/Boost  # noqa
USE_ARMADILLO = USE_MLPACK  # Armadillo needs cross-compilation but tries to use system LAPACK/BLAS  # noqa
USE_BOOST = USE_MLPACK

USE_EIGEN = True  # Better matrix system than mlpack in that Eigen is headers-only  # noqa

CAN_CROSS_COMPILE_LINUX_TO_WINDOWS = False  # see above
USE_CYGWIN = False  # Cygwin compiles to binaries requiring a POSIX layer
USE_MINGW = False  # MinGW compiles to pure native Windows code and cross-compiles  # noqa
USE_MXE = False  # A cross-compilation environment
USE_VS = True  # Microsoft Visual Studio / Visual C++

# -----------------------------------------------------------------------------
# Internal constants
# -----------------------------------------------------------------------------

USER_DIR = expanduser("~")
HEAD = "HEAD"  # git commit meaning "the most recent"

ENVVAR_QT_BASE = "CAMCOPS_QT_BASE_DIR"

# -----------------------------------------------------------------------------
# Downloading and versions
# -----------------------------------------------------------------------------

# Android
DEFAULT_ANDROID_API_NUM = 23
DEFAULT_ROOT_DIR = join(USER_DIR, "dev", "qt_local_build")
DEFAULT_ANDROID_SDK = join(USER_DIR, "dev", "android-sdk-linux")
DEFAULT_ANDROID_NDK = join(USER_DIR, "dev", "android-ndk-r11c")
DEFAULT_NDK_HOST = "linux-x86_64"
DEFAULT_TOOLCHAIN_VERSION = "4.9"

# Qt
DEFAULT_QT_SRC_DIRNAME = "qt5"
DEFAULT_QT_GIT_URL = "git://code.qt.io/qt/qt5.git"
DEFAULT_QT_GIT_BRANCH = "5.10"
# previously "5.7.0", "5.9", "5.10"
# ... to find out which are available: go into the local git directory and run
# "git remote show origin"
DEFAULT_QT_GIT_COMMIT = HEAD
DEFAULT_QT_USE_OPENSSL_STATICALLY = True
FIX_QT_5_7_0_ANDROID_MAKE_INSTALL_BUG = False  # was necessary for v5.7.0
FIX_QT_5_9_2_CROSS_COMPILE_TOP_LEVEL_BUILD_BUG = True
FIX_QT_5_9_2_CROSS_COMPILE_EXECVP_MISSING_COMPILER_BUG = True
FIX_QT_5_9_2_W64_HOST_TOOL_WANTS_WINDOWS_H = True
ADD_SO_VERSION_OF_LIBQTFORANDROID = False

# OpenSSL
DEFAULT_OPENSSL_VERSION = "1.1.0g"
OPENSSL_AT_LEAST_1_1 = True
# ... formerly "1.0.2h", but Windows 64 builds break
# ... as of 2017-11-21, stable series is 1.1 and LTS series is 1.0.2
# ... but Qt 5.9.3 doesn't support OpenSSL 1.1.0g; errors relating to
#     "undefined type 'x509_st'"
# ... requires Qt 5.10.0 alpha: https://bugreports.qt.io/browse/QTBUG-52905
OPENSSL_FAILS_OWN_TESTS = True
# https://bugs.launchpad.net/ubuntu/+source/openssl/+bug/1581084
DEFAULT_OPENSSL_SRC_URL = (
    "https://www.openssl.org/source/openssl-{}.tar.gz".format(
        DEFAULT_OPENSSL_VERSION))
DEFAULT_OPENSSL_ANDROID_SCRIPT_URL = \
    "https://wiki.openssl.org/images/7/70/Setenv-android.sh"

# SQLCipher; https://www.zetetic.net/sqlcipher/open-source/
DEFAULT_SQLCIPHER_GIT_URL = "https://github.com/sqlcipher/sqlcipher.git"
DEFAULT_SQLCIPHER_GIT_COMMIT = HEAD
# ... note that there's another URL for the Android binary packages
# ... SQLCipher supports OpenSSL 1.1.0 as of SQLCipher 3.4.1

# Boost
DEFAULT_BOOST_VERSION = "1.64.0"
DEFAULT_BOOST_SRC_URL = (
    "https://dl.bintray.com/boostorg/"
    "release/{vdot}/source/boost_{vund}.tar.gz".format(
        vdot=DEFAULT_BOOST_VERSION,
        vund=DEFAULT_BOOST_VERSION.replace(".", "_"),
    )
    # It looks like there's an extra ":" before the final "boost" in the
    # list at https://dl.bintray.com/boostorg/release/1.64.0/source/
    # but the URL only works if you remove it.
)

# Armadillo
DEFAULT_ARMA_VERSION = "7.950.0"
DEFAULT_ARMA_SRC_URL = (
    "http://sourceforge.net/projects/arma/files/"
    "armadillo-{}.tar.xz".format(
        DEFAULT_ARMA_VERSION))

# MLPACK; http://mlpack.org/
DEFAULT_MLPACK_GIT_URL = "https://github.com/mlpack/mlpack"
DEFAULT_MLPACK_GIT_COMMIT = HEAD

# Eigen
DEFAULT_EIGEN_VERSION = "3.3.3"

# jom
# DEFAULT_JOM_GIT_URL = "git://code.qt.io/qt-labs/jom.git"

# MXE
DEFAULT_MXE_GIT_URL = "https://github.com/mxe/mxe.git"
MXE_HAS_GCC_WITH_I386_BUG = True  # True as of 2017-11-19

# -----------------------------------------------------------------------------
# Building Qt
# -----------------------------------------------------------------------------
# TO MAKE MINOR CHANGES: delete ...installdir/bin/qmake, and rerun this script.
# (Can still take ages. Not sure it saves any time, in fact.)

QT_CONFIG_COMMON_ARGS = [
    # use "configure -help" to list all of them
    # http://doc.qt.io/qt-4.8/configure-options.html  # NB better docs than 5.7
    # http://doc.qt.io/qt-5.7/configure-options.html  # less helpful
    # http://doc.qt.io/qt-5.9/configure-options.html

    # -------------------------------------------------------------------------
    # Qt license, debug v. release,
    # -------------------------------------------------------------------------

    "-opensource", "-confirm-license",  # Choose our Qt edition.

    "-release",  # Make a release-mode library. (Default is release.)

    # "-debug-and-release",  # make a release library as well: MAC ONLY
    # ... debug was the default in 4.8, but not in 5.7
    # ... release is default in 5.7 (as per "configure -h")
    # ... check with "readelf --debug-dump=decodedline <LIBRARY.so>"
    # ... http://stackoverflow.com/questions/1999654

    # -------------------------------------------------------------------------
    # static v. shared
    # -------------------------------------------------------------------------
    # Now decided on a per-platform basis (2017-06-18)

    # -------------------------------------------------------------------------
    # Database support
    # -------------------------------------------------------------------------

    # v5.7.0 # "-qt-sql-sqlite",  # SQLite (v3) support built in to Qt
    "-sql-sqlite",  # v5.9: explicitly add SQLite support
    "-qt-sqlite",  # v5.9: "qt", rather than "system"

    "-no-sql-db2",  # disable other SQL drivers
    "-no-sql-ibase",
    "-no-sql-mysql",  # ... for future: maybe re-enable as a plugin
    "-no-sql-oci",
    "-no-sql-odbc",  # ... for future: maybe re-enable as a plugin
    "-no-sql-psql",  # ... for future: maybe re-enable as a plugin
    "-no-sql-sqlite2",  # this is an old SQLite version
    "-no-sql-tds",  # this one specifically was causing library problems

    # -------------------------------------------------------------------------
    # Libraries
    # -------------------------------------------------------------------------

    "-qt-doubleconversion",  # Use Qt version of double conversion library
    # NOT YET WORKING ("Qt no longer ships fonts") # "-qt-freetype",  # Qt, not system, version of Freetype  # noqa
    # NOT YET WORKING ("Qt no longer ships fonts") # "-qt-harfbuzz",  # Qt, not system, version of HarfBuzz-NG  # noqa
    "-qt-libjpeg",  # Qt, not host OS, version of JPEG library
    "-qt-libpng",  # Qt, not host OS, version of PNG library
    "-qt-zlib",  # Qt, not host OS, version of zlib

    # -------------------------------------------------------------------------
    # Compilation
    # -------------------------------------------------------------------------
    # Note: the default release build optimizes with -O2 -Os; there are
    # some 'configure' options to control this, but it's probably a good
    # default.

    "-no-warnings-are-errors",  # don't treat warnings as errors

    # -------------------------------------------------------------------------
    # Stuff to skip
    # -------------------------------------------------------------------------
    # CHANGE OF HEART: don't skip anything; it leads to trouble later!

    # not a valid "-nomake": # "-nomake", "docs",
    # not a valid "-nomake": # "-nomake", "demos",
    "-nomake", "examples",
    "-nomake", "tests",

    # "-skip", "qttranslations",

    # Don't need this on any platform, and unsupported on Android:
    "-skip", "qtserialport",

    # Except the webkit stuff, which ends up giving problems with Wayland-EGL:
    # "-skip", "qtwebkit",  # disabled 2017-10-22: "Project ERROR: -skip command line argument used with non-existent module 'qtwebkit'."  # noqa
    # "-skip", "qtwebkit-examples",  # disabled 2017-10-22: ditto
]

# -----------------------------------------------------------------------------
# Building OpenSSL
# -----------------------------------------------------------------------------

OPENSSL_COMMON_OPTIONS = [
    "shared",  # make .so files (needed by Qt sometimes) as well as .a
    # deprecated option as of 1.1.0g # "no-ssl2",  # SSL-2 is broken
    "no-ssl3",  # SSL-3 is broken. Is an SSL-3 build required for TLS 1.2?
    # "no-comp",  # disable compression independent of zlib
]

# -----------------------------------------------------------------------------
# External tools
# -----------------------------------------------------------------------------

ANT = "ant"  # for Android builds
BASH = "bash"
CL = "cl"  # Visual C++ compiler
CMAKE = "cmake"
DPKG_QUERY = "dpkg-query"
GIT = "git"
GOBJDUMP = "gobjdump"  # OS/X equivalent of readelf
JAVAC = "javac"  # for Android builds
LD = "ld"
MAKE = "make"
MAKEDEPEND = "makedepend"  # used by OpenSSL via "make"
NASM = "nasm.exe"  # Assembler for Windows (for OpenSSL); http://www.nasm.us/
NMAKE = "nmake.exe"  # Visual Studio make tool
OBJDUMP = "objdump"
PERL = "perl"
READELF = "readelf"  # read ELF-format library files
SED = "sed"  # stream editor
TAR = "tar"  # manipulate tar files
TCLSH = "tclsh"
VCVARSALL = "vcvarsall.bat"  # sets environment variables for VC++
XCODE_SELECT = "xcode-select"  # OS/X tool to find paths for XCode

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOG_FORMAT = '%(asctime)s.%(msecs)03d:%(levelname)s:%(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'

# -----------------------------------------------------------------------------
# Errors
# -----------------------------------------------------------------------------

BAD_WINDOWS_PATH_MSG = (
    "Something has put a unquoted ampersand (&) in the PATH environment "
    "variable. Whilst not technically illegal, this breaks quite a lot of "
    "software. (The usual culprit is MySQL; see "
    "https://stackoverflow.com/questions/34124636.) Please fix this (enclose "
    "that part in quotes), e.g. in your system or user environment variables "
    "via the Control Panel, and try again. The path is:\n\n"
)

# Take your pick:
CANNOT_CROSS_COMPILE_QT = (
    "Cannot, at present, cross-compile Qt from Linux to Windows.")
ERROR_COMPILE_FOR_WINDOWS_ON_LINUX = "Please use Linux to build for Windows."


# -----------------------------------------------------------------------------
# Classes to collect constants
# -----------------------------------------------------------------------------

class Os(object):
    """
    Operating system constants.
    These strings are cosmetic and should NOT be relied on for passing to
    external tools.
    """
    ANDROID = "Android"
    LINUX = "Linux"
    WINDOWS = "Windows"
    OSX = "OS/X"
    IOS = "iOS"


ALL_OSS = [getattr(Os, _) for _ in dir(Os) if not _.startswith("_")]


class Cpu(object):
    """
    CPU constants.
    These strings are cosmetic and should NOT be relied on for passing to
    external tools.
    """
    X86_32 = "Intel x86 (32-bit)"  # usually: "x86", "i386"
    X86_64 = "Intel x86 (64-bit)"
    AMD_64 = "AMD (64-bit)"
    ARM_V5 = "ARM v5 (32-bit)"  # 32-bit; https://en.wikipedia.org/wiki/ARM_architecture  # noqa
    ARM_V7 = "ARM v7 (32-bit)"  # 32-bit; https://en.wikipedia.org/wiki/ARM_architecture  # noqa
    ARM_V8_64 = "ARM v8 (64-bit)"


ALL_CPUS = [getattr(Cpu, _) for _ in dir(Cpu) if not _.startswith("_")]


# =============================================================================
# Information about the target system
# =============================================================================

class Platform(object):
    """
    Represents the build or target platform, defined by OS+CPU.
    """
    # noinspection PyShadowingNames
    def __init__(self, os_: str, cpu: str, distro_id: str = "") -> None:
        self.os = os_
        self.cpu = cpu
        self.distro_id = distro_id
        if os_ not in ALL_OSS:
            raise NotImplementedError("Unknown target OS: {!r}".format(os_))
        if cpu not in ALL_CPUS:
            raise NotImplementedError("Unknown target CPU: {!r}".format(cpu))

        # 64-bit support only (thus far)?
        if os_ in [Os.LINUX, Os.OSX] and not self.cpu_x86_64bit_family:
            raise NotImplementedError("Don't know how to build for CPU " +
                                      cpu + " on system " + os_)

    # -------------------------------------------------------------------------
    # Descriptives
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        return self.description

    def __eq__(self, other: "Platform") -> bool:
        return (
            self.os == other.os and
            self.cpu == other.cpu and
            self.distro_id == other.distro_id
        )

    @property
    def description(self) -> str:
        return "{}/{}".format(self.os, self.cpu)

    @property
    def os_shortname(self) -> str:
        if self.os == Os.ANDROID:
            return "android"
        elif self.os == Os.LINUX:
            return "linux"
        elif self.os == Os.WINDOWS:
            return "windows"
        elif self.os == Os.OSX:
            return "osx"
        elif self.os == Os.IOS:
            return "ios"
        else:
            raise ValueError("Unknown OS: {!r}".format(self.os))

    @property
    def cpu_shortname(self) -> str:
        if self.cpu == Cpu.X86_32:
            return "x86_32"
        elif self.cpu_x86_64bit_family:
            return "x86_64"
        elif self.cpu == Cpu.ARM_V5:
            return "armv5"
        elif self.cpu == Cpu.ARM_V7:
            return "armv7"
        elif self.cpu == Cpu.ARM_V8_64:
            return "armv8_64"
        else:
            raise ValueError("Unknown CPU: {!r}".format(self.cpu))

    @property
    def dirpart(self) -> str:
        """
        Used to name our build directories.
        """
        return "{}_{}".format(self.os_shortname, self.cpu_shortname)

    # -------------------------------------------------------------------------
    # OS/CPU information
    # -------------------------------------------------------------------------

    @property
    def linux(self) -> bool:
        return self.os == Os.LINUX

    @property
    def debian(self) -> bool:
        # http://distro.readthedocs.io/en/latest/#distro.id
        return self.distro_id in ["ubuntu", "debian"]

    @property
    def osx(self) -> bool:
        return self.os == Os.OSX

    @property
    def unix(self) -> bool:
        return self.linux or self.osx

    @property
    def android(self) -> bool:
        return self.os == Os.ANDROID

    @property
    def ios(self) -> bool:
        return self.os == Os.IOS

    @property
    def windows(self) -> bool:
        return self.os == Os.WINDOWS

    @property
    def mobile(self) -> bool:
        return self.os in [Os.ANDROID, Os.IOS]

    @property
    def desktop(self) -> bool:
        return not self.mobile

    @property
    def cpu_x86_family(self) -> bool:
        return self.cpu in [Cpu.X86_32, Cpu.X86_64, Cpu.AMD_64]
    
    @property
    def cpu_64bit(self) -> bool:
        return self.cpu in [Cpu.X86_64, Cpu.AMD_64, Cpu.ARM_V8_64]
    
    @property
    def cpu_x86_64bit_family(self) -> bool:
        return self.cpu_x86_family and self.cpu_64bit

    @property
    def cpu_x86_32bit_family(self) -> bool:
        return self.cpu_x86_family and not self.cpu_64bit

    @property
    def cpu_arm_family(self) -> bool:
        return self.cpu in [Cpu.ARM_V5, Cpu.ARM_V7, Cpu.ARM_V8_64]

    # -------------------------------------------------------------------------
    # Library (e.g. .so, DLL) verification
    # -------------------------------------------------------------------------

    @property
    def dynamic_lib_ext(self) -> str:
        """
        What DYNAMIC/SHARED library filename extension is in use?
        """
        # I think this depends on the build system, not the target.
        # ... no; on the target.
        if self.osx or self.ios:
            return ".dylib"
            # ... sometimes also ".so" or ".bundle"
        elif self.windows:
            return ".dll"
        else:
            return ".so"

    @property
    def static_lib_ext(self) -> str:
        """
        What STATIC library filename extension is in use?
        """
        if self.osx or self.ios:
            return ".a"
        elif self.windows:
            return ".lib"
        else:
            return ".a"
        
    @property
    def obj_ext(self):
        """
        What OBJECT file extension is in use?
        """
        if self.windows:
            return ".obj"
        else:
            return ".o"

    def ensure_elf_reader(self) -> None:
        """Only to be called for the build platform."""
        if self.linux:
            require(READELF)
            require(OBJDUMP)  # for Windows DLL files
        elif self.osx:
            require(GOBJDUMP)
        elif self.windows:
            pass
        else:
            raise NotImplementedError("Don't know ELF reader for {}".format(
                BUILD_PLATFORM))

    def verify_lib(self, filename: str) -> None:
        """
        Check an ELF or DLL file matches our architecture.
        """
        log.info("Verifying type of library file: {!r}".format(filename))
        if BUILD_PLATFORM.linux:
            if self.windows:
                dumpcmd = [OBJDUMP, "-f", filename]
                dumpresult, _ = run(dumpcmd, get_output=True)
                pe32_tag = "file format pe-i386"
                pe64_tag = "file format pe-x86-64"
                if self.cpu_64bit and pe64_tag not in dumpresult:
                    raise ValueError("File {!r} is not a Win64 "
                                     "DLL".format(filename))
                if not self.cpu_64bit and pe32_tag not in dumpresult:
                    raise ValueError("File {!r} is not a Win32 "
                                     "DLL".format(filename))
            else:
                elf_arm_tag = "Tag_ARM_ISA_use: Yes"
                elfcmd = [READELF, "-A", filename]
                elfresult, _ = run(elfcmd, get_output=True)
                arm_tag_present = elf_arm_tag in elfresult
                if self.cpu_arm_family and not arm_tag_present:
                    raise ValueError(
                            "File {} was not built for ARM".format(filename))
                elif not self.cpu_arm_family and arm_tag_present:
                    raise ValueError(
                            "File {} was built for ARM".format(filename))
        elif BUILD_PLATFORM.osx:
            # https://lowlevelbits.org/parsing-mach-o-files/
            # https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
            # gobjdump --help
            dumpcmd = [GOBJDUMP, "-f", filename]
            dumpresult, _ = run(dumpcmd, get_output=True)
            arm64tag = "file format mach-o-arm64"
            arm64tag_present = arm64tag in dumpresult
            if self.cpu == Cpu.ARM_V8_64 and not arm64tag_present:
                raise ValueError(
                    "File {} was not built for ARM64".format(filename))
            elif self.cpu != Cpu.ARM_V8_64 and arm64tag_present:
                raise ValueError(
                    "File {} was built for ARM64".format(filename))
        else:
            log.warning("Don't know how to verify library under build "
                        "platform {}".format(BUILD_PLATFORM))
            return
        log.info("Library file is good: {!r}".format(filename))

    # -------------------------------------------------------------------------
    # Android
    # -------------------------------------------------------------------------

    @property
    def android_cpu(self) -> str:
        """
        CPU name for Android builds.
        """
        if not self.android:
            raise ValueError("Platform is not Android")
        if self.cpu_x86_64bit_family:
            return "x86_64"
        elif self.cpu_x86_32bit_family:
            return "x86"
        elif self.cpu == Cpu.ARM_V7:
            return "arm"
        elif self.cpu == Cpu.ARM_V5:
            return "armv5"
        else:
            raise NotImplementedError("Don't know how to build Android for "
                                      "CPU " + self.cpu)

    @property
    def android_arch_short(self) -> str:
        return self.android_cpu

    @property
    def android_arch_full(self) -> str:
        # e.g. arch-x86
        return "arch-{}".format(self.android_arch_short)

    # -------------------------------------------------------------------------
    # iOS
    # -------------------------------------------------------------------------

    @property
    def ios_platform_name(self) -> str:
        if not self.ios:
            raise ValueError("ios_platform_name requested but not using iOS")
        if self.cpu_x86_family:
            return "iPhoneSimulator"
        elif self.cpu_arm_family:
            return "iPhoneOS"
        else:
            raise ValueError("Unknown combination for ios_platform_name")

    @property
    def ios_arch(self) -> str:
        if self.cpu_x86_64bit_family:
            return "x86_64"
        elif self.cpu == Cpu.X86_32:
            return "i386"
        elif self.cpu == Cpu.ARM_V7:
            return "armv7"
        elif self.cpu == Cpu.ARM_V8_64:
            return "arm64"
        else:
            raise ValueError("Unknown architecture for iOS")

    # -------------------------------------------------------------------------
    # Windows
    # -------------------------------------------------------------------------

    @property
    def mxe_target(self) -> str:
        assert self.windows, "mxe_target is for cross-compilation to Windows"
        assert BUILD_PLATFORM.linux, "mxe_target is for cross-compilation from Linux"  # noqa
        if self.cpu_64bit:
            return "x86_64-w64-mingw32.static"
        else:
            return "i686-w64-mingw32.static"

    # -------------------------------------------------------------------------
    # Other cross-compilation details
    # -------------------------------------------------------------------------

    def gcc(self, fullpath: bool, cfg: "Config") -> str:
        if not fullpath:
            return "gcc"
        if self.android:
            if self.cpu_x86_32bit_family:
                return join(cfg.android_toolchain(self),
                            "i686-linux-android-gcc")
            elif self.cpu_arm_family:
                return join(cfg.android_toolchain(self),
                            "arm-linux-androideabi-gcc")
            else:
                raise NotImplementedError("Don't know gcc name")
        return shutil.which("gcc")

    def ar(self, fullpath: bool, cfg: "Config") -> str:
        if not fullpath:
            return "gcc-ar"
        if self.android:
            return join(cfg.android_toolchain(self),
                        "i686-linux-android-gcc-ar")
        return shutil.which("ar")

    @property
    def cross_compile_prefix(self) -> str:
        if BUILD_PLATFORM.unix:
            if self.android:
                if self.cpu == Cpu.X86_32:
                    return "i686-linux-android-"
                elif self.cpu == Cpu.ARM_V7:
                    return "arm-linux-androideabi-"
            elif self.windows:
                # https://superuser.com/questions/238112/what-is-the-difference-between-i686-and-x86-64  # noqa
                if self.cpu_64bit:
                    return "x86_64-w64-mingw32.static-"
                else:
                    return "i686-w64-mingw32.static-"
        raise NotImplementedError("Don't know CROSS_COMPILE prefix for " +
                                  str(self))

    def make_args(self, cfg: "Config", extra_args: List[str] = None,
                  command: str = "", makefile: str = "") -> List[str]:
        extra_args = extra_args or []  # type: List[str]
        if self.windows:
            if shutil.which(cfg.jom_executable):
                make = cfg.jom_executable
                supports_parallel = True
            else:
                make = NMAKE
                supports_parallel = False
            makefile_switch = "/F"
            parallel_switch = "/J"
        else:
            make = MAKE
            supports_parallel = True
            makefile_switch = "-f"  # Unix standard
            parallel_switch = "-j"
        # require(make)
        # ... not necessarily visible now; may be on a PATH yet to be set
        args = [make]
        if supports_parallel:
            args += [parallel_switch, str(cfg.nparallel)]
        if extra_args:
            args += extra_args
        if makefile:
            args += [makefile_switch, makefile]
        if command:
            args.append(command)
        return args

    @property
    def qmake_executable(self) -> str:
        """
        Used to calculate the name of the qmake file we'll be building (so we
        can check if it's been compiled).
        """
        if self.windows:
            return "qmake.exe"
        else:
            return "qmake"

    # -------------------------------------------------------------------------
    # SQLCipher
    # -------------------------------------------------------------------------

    @property
    def sqlcipher_platform(self) -> str:
        # See config.guess in SQLCipher source.
        # (You can run or source it to see its answer.)
        if self.linux:
            if self.cpu_x86_64bit_family:
                return "x86_64-unknown-linux"
            elif self.cpu_x86_32bit_family:
                return "i686-unknown-linux"
        elif self.android:
            if self.cpu == Cpu.ARM_V7:
                # arm? [1]
                # arm-linux? [2]
                return "arm-linux"
            elif self.cpu_x86_32bit_family:
                return "i686-unknown-linux"  # ?
        elif self.osx:
            # e.g. empirically: "i386-apple-darwin15.6.0"
            # "uname -m" tells you whether you're 32 or 64 bit
            # "uname -r" gives you the release
            return "i386-apple-darwin"
        elif self.windows:
            if self.cpu_x86_64bit_family:
                return "x86_64-unknown-windows"  # untested *** try running config.guess
            elif self.cpu_x86_32bit_family:
                return "i686-unknown-windows"  # untested *** try running config.guess
        raise NotImplementedError("Don't know how to support SQLCipher for "
                                  "{}".format(self))


def get_build_platform() -> Platform:
    """Find the architecture this script is running on."""
    s = platform.system()
    if s == "Linux":
        os_ = Os.LINUX
    elif s == "Darwin":
        os_ = Os.OSX
    elif s == "Windows":
        os_ = Os.WINDOWS
    else:
        raise NotImplementedError("Don't know host (build) OS {!r}".format(s))
    m = platform.machine()
    if m == "i386":
        cpu = Cpu.X86_32
    elif m == "x86_64":
        cpu = Cpu.X86_64
    elif m == "AMD64":
        cpu = Cpu.AMD_64
    else:
        raise NotImplementedError("Don't know host (build) CPU {!r}".format(m))
    distro_id = distro.id() if distro else ""
    return Platform(os_, cpu, distro_id)


BUILD_PLATFORM = get_build_platform()


# =============================================================================
# Config class, just to make sure we check the argument namespace properly
# =============================================================================
# https://stackoverflow.com/questions/42279063/python-typehints-for-argparse-namespace-objects  # noqa

class Config(object):
    # noinspection PyUnresolvedReferences
    def __init__(self, args: argparse.Namespace) -> None:
        # Architectures
        self.build_all = args.build_all  # type: bool
        self.build_android_x86_32 = args.build_android_x86_32  # type: bool
        self.build_android_arm_v7_32 = args.build_android_arm_v7_32  # type: bool  # noqa
        self.build_linux_x86_64 = args.build_linux_x86_64  # type: bool
        self.build_osx_x86_64 = args.build_osx_x86_64  # type: bool
        self.build_windows_x86_64 = args.build_windows_x86_64  # type: bool
        self.build_windows_x86_32 = args.build_windows_x86_32  # type: bool
        self.build_ios = args.build_ios  # type: bool
        self.build_ios_simulator = args.build_ios_simulator  # type: bool

        if self.build_all:
            if BUILD_PLATFORM.linux:
                self.build_android_arm_v7_32 = True
                # rarely used, emulator only # self.build_android_x86_32 = True
                self.build_linux_x86_64 = True
                if CAN_CROSS_COMPILE_LINUX_TO_WINDOWS:
                    if not MXE_HAS_GCC_WITH_I386_BUG:
                        self.build_windows_x86_32 = True
                    self.build_windows_x86_64 = True
            elif BUILD_PLATFORM.osx:
                self.build_osx_x86_64 = True
                self.build_ios = True
                self.build_ios_simulator = True
            elif BUILD_PLATFORM.windows:
                self.build_windows_x86_32 = True
                self.build_windows_x86_64 = True

        # General
        self.show_config_only = args.show_config_only  # type: bool
        self.root_dir = args.root_dir  # type: str
        self.nparallel = args.nparallel  # type: int
        self.force = args.force  # type: bool
        self.verbose = args.verbose  # type: int
        self.src_rootdir = join(self.root_dir, "src")  # type: str

        # Qt
        # - git repository in src/qt5
        # - build to multiple directories off root
        # - each is (1) built into the "*_build" directory, then installed
        #   (via "make install") to the "*_install" directory.
        # - One points Qt Creator to "*_install/bin/qmake" to give it a Qt
        #   architecture "kit".
        self.qt_git_url = args.qt_git_url  # type: str
        self.qt_git_branch = args.qt_git_branch  # type: str
        self.qt_git_commit = args.qt_git_commit  # type: str
        self.qt_openssl_static = args.qt_openssl_static  # type: bool
        self.qt_src_gitdir = join(self.src_rootdir,
                                  args.qt_src_dirname)  # type: str  # noqa

        # Android SDK/NDK
        # - installed independently by user
        # - used for cross-compilation to Android targets
        self.android_api_number = args.android_api_number  # type: int
        self.android_sdk_root = args.android_sdk_root  # type: str
        self.android_ndk_root = args.android_ndk_root  # type: str
        self.android_ndk_host = args.android_ndk_host  # type: str
        self.android_toolchain_version = args.android_toolchain_version  # type: str  # noqa
        self.android_api = "android-{}".format(self.android_api_number)
        # ... see $ANDROID_SDK_ROOT/platforms/

        # iOS
        self.ios_sdk = args.ios_sdk  # type: str

        # OpenSSL
        # - download tar file to src/openssl
        # - built to multiple directories off root
        self.openssl_version = args.openssl_version  # type: str
        self.openssl_src_url = args.openssl_src_url  # type: str
        self.openssl_android_script_url = args.openssl_android_script_url  # type: str  # noqa
        # ... derived:
        self.openssl_src_dir = join(self.src_rootdir, "openssl")
        self.openssl_src_filename = "openssl-{}.tar.gz".format(
            self.openssl_version)
        self.openssl_src_fullpath = join(self.openssl_src_dir,
                                         self.openssl_src_filename)
        self.openssl_android_script_fullpath = join(
            self.openssl_src_dir, "Setenv-android.sh")

        # SQLCipher
        # - git repository in "src"
        # - single build in situ; we make the amalgamation file "sqlite3.c",
        #   and as a bonus the "sqlcipher" executable for the host machine, but
        #   the latter isn't part of CamCOPS's use of SQLCipher (CamCOPS just
        #   uses the amalgamation file, which is platform-independent).
        self.sqlcipher_git_url = args.sqlcipher_git_url  # type: str
        self.sqlcipher_git_commit = args.sqlcipher_git_commit  # type: str
        self.sqlcipher_src_gitdir = join(self.src_rootdir, "sqlcipher")  # type: str  # noqa

        if USE_BOOST:
            # Boost
            # - download tar file to src/boost
            # - unpack to boost/...
            self.boost_version = args.boost_version  # type: str
            self.boost_src_url = args.boost_src_url  # type: str
            # ... derived:
            boost_version_underscores = self.boost_version.replace(".", "_")
            self.boost_src_dir = join(self.src_rootdir, "boost")
            self.boost_src_filename = "boost_{}.tar.xz".format(
                boost_version_underscores)
            self.boost_src_fullpath = join(self.boost_src_dir,
                                           self.boost_src_filename)
            self.boost_dest_dir = join(self.root_dir, "boost")
            self.boost_root = join(self.boost_dest_dir,
                                   "boost_" + boost_version_underscores)
            self.boost_include_dir = self.boost_root
            self.boost_library_dir = join(self.boost_root, "libs")

        # Armadillo
        # - download tar file to src/armadillo
        # - unpack to armadillo/...
        # - build -- ABANDONED, lots of dependencies
        if USE_ARMADILLO:
            self.arma_version = args.arma_version  # type: str
            self.arma_src_url = args.arma_src_url  # type: str
            # ... derived:
            arma_w_version = "armadillo-{}".format(self.arma_version)
            self.arma_src_dir = join(self.src_rootdir, "armadillo")
            self.arma_src_filename = arma_w_version + ".tar.xz"
            self.arma_src_fullpath = join(self.arma_src_dir,
                                          self.arma_src_filename)
            self.arma_dest_dir = join(self.root_dir, "armadillo")
            self.arma_working_dir = join(self.arma_dest_dir, arma_w_version)
            self.arma_include_dir = join(self.arma_working_dir, "include")
            self.arma_lib = join(self.arma_working_dir, "libarmadillo.so")

        if USE_MLPACK:
            # MLPACK
            # - git repository in src/mlpack
            # - CMake to build BUT needs compilation (+ cross-compilation)
            self.mlpack_git_url = args.mlpack_git_url  # type: str
            self.mlpack_git_commit = args.mlpack_git_commit  # type: str
            self.mlpack_src_gitdir = join(self.src_rootdir, "mlpack")  # type: str  # noqa
            self.build_mlpack = args.build_mlpack  # type: bool

        if USE_EIGEN:
            self.eigen_version = args.eigen_version  # type: str
            self.eigen_src_url = (
                "http://bitbucket.org/eigen/eigen/get/{}.tar.gz".format(
                    self.eigen_version)
            )
            self.eigen_src_dir = join(self.src_rootdir, "eigen")
            self.eigen_src_fullpath = join(
                self.eigen_src_dir,
                "eigen-{}.tar.gz".format(self.eigen_version))
            self.eigen_unpacked_dir = join(self.root_dir, "eigen")

        # jom: comes with QtCreator
        # self.jom_git_url = args.jom_git_url  # type: str
        # self.jom_src_gitdir = join(self.src_rootdir, "jom")  # type: str
        # self.jom_executable = join(self.jom_src_gitdir, "bin", "jom.exe") # type: str  # noqa
        self.jom_executable = args.jom_executable  # type: str

        # Windows
        self.windows_prebuilt_qt_root = args.windows_prebuilt_qt_root  # type: str  # noqa
        self.windows_sdk_version = args.windows_sdk_version  # type: str

        if USE_MXE:
            self.mxe_git_url = args.mxe_git_url  # type: str
            self.mxe_src_gitdir = join(self.src_rootdir, "mxe")  # type: str
            self.mxe_usr_dir = join(self.mxe_src_gitdir, "usr")  # type: str
            self.mxe_bin_dir = join(self.mxe_usr_dir, "bin")  # type: str  # noqa

    def __repr__(self) -> str:
        elements = ["    {}={}".format(k, repr(v))
                    for k, v in self.__dict__.items()]
        elements.sort()
        return "{q}(\n{e}\n)".format(q=self.__class__.__qualname__,
                                     e=",\n".join(elements))

    # -------------------------------------------------------------------------
    # Directories
    # -------------------------------------------------------------------------

    def qt_build_dir(self, target_platform: Platform) -> str:
        return join(self.root_dir, "qt_{}_build".format(
            target_platform.dirpart))

    def qt_install_dir(self, target_platform: Platform) -> str:
        return join(self.root_dir, "qt_{}_install".format(
            target_platform.dirpart))

    def get_openssl_rootdir_workdir(
            self, target_platform: Platform) -> Tuple[str, str]:
        """
        Calculates local OpenSSL directories.
        """
        rootdir = join(self.root_dir,
                       "openssl_{}_build".format(target_platform.dirpart))
        workdir = join(rootdir, "openssl-{}".format(self.openssl_version))
        return rootdir, workdir

    # -------------------------------------------------------------------------
    # Compile/make tools
    # -------------------------------------------------------------------------

    def make_args(self, extra_args: List[str] = None, command: str = "",
                  makefile: str = "") -> List[str]:
        return BUILD_PLATFORM.make_args(cfg=self,
                                        extra_args=extra_args,
                                        command=command,
                                        makefile=makefile)

    # -------------------------------------------------------------------------
    # Environment variables
    # -------------------------------------------------------------------------

    def set_compile_env(self, env: Dict[str, str],
                        target_platform: Platform,
                        use_cross_compile_var: bool = True) -> None:
        """
        Adds variables to the environment for compilation or cross-compilation.
        Modifies env.
        """
        if target_platform.android:
            self._set_android_env(env, target_platform=target_platform,
                                  use_cross_compile_var=use_cross_compile_var)
        elif target_platform.ios:
            self._set_ios_env(env, target_platform=target_platform)
        elif target_platform.linux:
            self._set_linux_env(env,
                                use_cross_compile_var=use_cross_compile_var)
        elif target_platform.windows:
            self._set_windows_env(env, target_platform=target_platform,
                                  use_cross_compile_var=use_cross_compile_var)
        elif target_platform.osx:
            self._set_osx_env(env)
        else:
            raise NotImplementedError(
                "Don't know how to set compilation environment for "
                "{}".format(target_platform))

    def _set_linux_env(self,
                       env: Dict[str, str],
                       use_cross_compile_var: bool) -> None:
        env["AR"] = BUILD_PLATFORM.ar(fullpath=not use_cross_compile_var,
                                      cfg=self)
        env["CC"] = BUILD_PLATFORM.gcc(fullpath=not use_cross_compile_var,
                                       cfg=self)

    def _set_osx_env(self, env: Dict[str, str]) -> None:
        pass

    def _set_android_env(self,
                         env: Dict[str, str],
                         target_platform: Platform,
                         use_cross_compile_var: bool) -> None:
        android_sysroot = self.android_sysroot(target_platform)
        android_toolchain = self.android_toolchain(target_platform)

        env["ANDROID_API"] = self.android_api
        env["ANDROID_API_VERSION"] = self.android_api
        env["ANDROID_ARCH"] = target_platform.android_arch_full
        env["ANDROID_DEV"] = join(android_sysroot, "usr")
        env["ANDROID_EABI"] = self.android_eabi(target_platform)
        env["ANDROID_NDK_ROOT"] = self.android_ndk_root
        env["ANDROID_SDK_ROOT"] = self.android_sdk_root
        env["ANDROID_SYSROOT"] = android_sysroot
        env["ANDROID_TOOLCHAIN"] = android_toolchain
        env["AR"] = target_platform.ar(fullpath=not use_cross_compile_var,
                                       cfg=self)
        env["ARCH"] = target_platform.android_arch_short
        env["CC"] = self.android_cc(target_platform,
                                    fullpath=not use_cross_compile_var)
        if use_cross_compile_var:
            env["CROSS_COMPILE"] = target_platform.cross_compile_prefix
            # ... unnecessary as we are specifying AR, CC directly
        env["HOSTCC"] = BUILD_PLATFORM.gcc(fullpath=not use_cross_compile_var,
                                           cfg=self)
        env["PATH"] = "{}{}{}".format(android_toolchain, os.pathsep,
                                      env["PATH"])
        env["SYSROOT"] = android_sysroot
        env["NDK_SYSROOT"] = android_sysroot

    def _set_ios_env(self, env: Dict[str, str],
                     target_platform: Platform) -> None:
        # https://gist.github.com/foozmeat/5154962
        encoding = sys.getdefaultencoding()
        developer = (
            subprocess.check_output([XCODE_SELECT, "-print-path"])
            .decode(encoding)
            .strip()
        )

        env["BUILD_TOOLS"] = developer
        env["CC"] = "{cc} -arch {arch}".format(
            cc=os.path.join(developer, 'usr', 'bin', 'gcc'),
            arch=target_platform.ios_arch
        )
        env["CROSS_TOP"] = os.path.join(
            developer,
            "Platforms",
            "{}.platform".format(target_platform.ios_platform_name),
            "Developer"
        )
        env["CROSS_SDK"] = "{plt}{sdkv}.sdk".format(
            plt=target_platform.ios_platform_name,
            sdkv=self.ios_sdk,
            # ... can be blank; e.g. iPhoneOS9.3.sdk symlinks to iPhoneOS.sdk
        )
        env["PLATFORM"] = target_platform.ios_platform_name

    def _set_windows_env(self, env: Dict[str, str],
                         target_platform: Platform,
                         use_cross_compile_var: bool) -> None:
        if BUILD_PLATFORM.linux:
            if CAN_CROSS_COMPILE_LINUX_TO_WINDOWS:
                if not USE_MINGW or not USE_MXE:
                    raise NotImplementedError(
                        "Only know how to use MinGW + MXE")
                crosscomp = target_platform.cross_compile_prefix
                mxe_target_root = join(self.mxe_usr_dir,
                                       target_platform.mxe_target)
                pkgconfig_sysroot = self.mxe_src_gitdir

                env["CC"] = target_platform.gcc(
                    fullpath=not use_cross_compile_var, cfg=self)
                if use_cross_compile_var:
                    env["CROSS_COMPILE"] = crosscomp
                env["HOSTCC"] = BUILD_PLATFORM.gcc(
                    fullpath=not use_cross_compile_var, cfg=self)
                env["PATH"] += os.pathsep + self.mxe_bin_dir
                # As per MXE:
                env["PKG_CONFIG"] = "{}pkg-config".format(crosscomp)
                env["PKG_CONFIG_DIR"] = ""
                # ... https://autotools.io/pkgconfig/cross-compiling.html
                env["PKG_CONFIG_SYSROOT_DIR"] = pkgconfig_sysroot  # proper
                env["PKG_CONFIG_SYSROOT"] = pkgconfig_sysroot  # occasional mistake  # noqa

                # http://ilgthegeek.old.livius.net/2015/02/05/pkg-config-search-path/  # noqa
                env["PKG_CONFIG_PATH"] = self.mxe_bin_dir
                env["PKG_CONFIG_LIBDIR"] = join(mxe_target_root,
                                                "lib", "pkgconfig")

                # Then to find windows.h:
                # https://stackoverflow.com/questions/2497344/what-is-the-environment-variable-for-gcc-g-to-look-for-h-files-during-compila  # noqa
                # env["CPATH"] = join(mxe_target_root, "include")
                # ... breaks compilation using host g++
                # ... instead:
                # env["SYSROOT"] = mxe_target_root

                # Now...
            else:
                raise NotImplementedError(CANNOT_CROSS_COMPILE_QT)

        elif BUILD_PLATFORM.windows:
            # http://doc.qt.io/qt-5/windows-building.html
            if contains_unquoted_ampersand_dangerous_to_windows(env["PATH"]):
                fail(BAD_WINDOWS_PATH_MSG + env["PATH"])
            # PATH
            env["PATH"] = os.pathsep.join([
                join(self.qt_src_gitdir, "qtrepotools", "bin"),
                join(self.qt_src_gitdir, "qtbase", "bin"),
                join(self.qt_src_gitdir, "gnuwin32", "bin"),
                env["PATH"],
            ])
            # VCVARSALL.BAT
            # We can't CALL a batch file and have it change our environment,
            # so we must implement the functionality of VCVARSALL.BAT <arch>
            if target_platform.cpu_x86_32bit_family:
                # "x86" in VC\vcvarsall.bat
                arch = "x86"
            elif target_platform.cpu_x86_64bit_family:
                # "amd64" in VC\vcvarsall.bat
                arch = "amd64"
            else:
                raise NotImplementedError(
                    "Don't know how to compile for Windows for target "
                    "platform {}".format(target_platform))
            # Now read the result from vcvarsall.bat directly
            args = [VCVARSALL, arch]
            fetched_env = windows_get_environment_from_batch_command(
                env_cmd=args, initial_env=env
            )
            env.update(**fetched_env)
            # Other
            env["CC"] = CL  # Visual C++
            # ... for SQLCipher "configure": if we try gcc, it will fail to
            # match the object format of OpenSSL that we previously created
            # using cl, so the configuration step will fail. We have to use cl
            # throughout.
            
            # Sanity checks
            if contains_unquoted_ampersand_dangerous_to_windows(env["PATH"]):
                fail(BAD_WINDOWS_PATH_MSG + env["PATH"])

        else:
            raise NotImplementedError(
                "Don't know how to compile for Windows on build platform "
                "{}".format(BUILD_PLATFORM))

    def android_eabi(self, target_platform: Platform) -> str:
        if target_platform.cpu_x86_family:
            return "{}-{}".format(
                target_platform.android_arch_short,
                self.android_toolchain_version)  # e.g. x86-4.9
            # For toolchain version: ls $ANDROID_NDK_ROOT/toolchains
            # ... "-android-arch" and "-android-toolchain-version" get
            # concatenated, I think; for example, this gives the toolchain
            # "x86_64-4.9"
        elif target_platform.cpu_arm_family:
            # but ARM ones look like "arm-linux-androideabi-4.9"
            return "{}-linux-androideabi-{}".format(
                target_platform.android_arch_short,
                self.android_toolchain_version)
        else:
            raise NotImplementedError("Unknown CPU family for Android")

    def android_sysroot(self, target_platform: Platform) -> str:
        return join(self.android_ndk_root, "platforms",
                    self.android_api, target_platform.android_arch_full)

    def target_toolchain(self, target_platform) -> str:
        """Directory of the target toolchain, or '' to assume the PATH."""
        if target_platform.android:
            return self.android_toolchain(target_platform)
        else:
            # Assumed to be on the PATH
            return ""

    def android_toolchain(self, target_platform: Platform) -> str:
        """Directory of the Android toolchain."""
        return join(self.android_ndk_root, "toolchains",
                    self.android_eabi(target_platform),
                    "prebuilt", self.android_ndk_host, "bin")

    @staticmethod
    def cross_compile_prefix(target_platform: Platform) -> str:
        if target_platform.android:
            if target_platform.cpu == Cpu.X86_32:
                return "i686-linux-android-"
            elif target_platform.cpu == Cpu.ARM_V7:
                return "arm-linux-androideabi-"
        raise NotImplementedError("Don't know CROSS_COMPILE prefix for " +
                                  str(target_platform))

    def android_cc(self, target_platform: Platform,
                   fullpath: bool) -> str:
        # Don't apply the CROSS_COMPILE prefix; that'll be prefixed
        # automatically.
        return (
            target_platform.gcc(fullpath, cfg=self) + "-" +
            self.android_toolchain_version
        )

    # -------------------------------------------------------------------------
    # Conversion functions
    # -------------------------------------------------------------------------

    def convert_android_lib_a_to_so(self, lib_a_fullpath: str,
                                    target_platform: Platform) -> str:
        # https://stackoverflow.com/questions/3919902/method-of-converting-a-static-library-into-a-dynamically-linked-library  # noqa
        libprefix = "lib"
        directory, filename = split(lib_a_fullpath)
        basename, ext = os.path.splitext(filename)
        if not basename.startswith(libprefix):
            raise ValueError("Don't know how to convert library: " +
                             lib_a_fullpath)
        libname = basename[len(libprefix):]
        newlibbasename = libprefix + libname + ".so"
        newlibfilename = join(directory, newlibbasename)
        compiler = self.android_cc(target_platform, fullpath=True)
        run([
            compiler,
            "-o", newlibfilename,
            "-shared",
            "-Wl,--whole-archive",
            "-Wl,-soname," + newlibbasename,
            lib_a_fullpath,
            "-Wl,--no-whole-archive",
            # "-L{}".format(directory),
            # "-l{}".format(libname),
            "--sysroot={}".format(self.android_sysroot(target_platform)),
        ])
        target_platform.verify_lib(newlibfilename)
        return newlibfilename


# =============================================================================
# Ancillary
# =============================================================================

def chdir(directory: str) -> None:
    """
    Change directory and say so.
    """
    log.debug("Entering directory: {}".format(directory))
    os.chdir(directory)


@contextmanager
def pushd(directory: str) -> None:
    """
    Context manager to change directory and preserve original on exit.
    """
    previous_dir = os.getcwd()
    chdir(directory)
    yield
    chdir(previous_dir)
    
    
def which_with_envpath(executable: str, env: Dict[str, str]) -> None:
    """
    Reason: when you use run([executable, ...], env) and therefore
    subprocess.run([executable, ...], env=env), the PATH that's searched for
    "executable" is the parent's, not the new one -- so you have to find the
    executable manually.
    """
    oldpath = os.environ.get("PATH", "")
    os.environ["PATH"] = env.get("PATH")
    which = shutil.which(executable)
    os.environ["PATH"] = oldpath
    return which
    
    
def quote_for_command_line(x: str) -> str:
    if BUILD_PLATFORM.windows:
        return x  # suboptimal but better than shlex.quote()!
    else:
        return shlex.quote(x)


def make_copy_paste_cmd(args: List[str]) -> str:
    """
    Convert a series of arguments to a command string that can be copied/
    pasted.
    """
    return subprocess.list2cmdline(args)
    # return " ".join(
    #     quote_for_command_line(x) for x in args
    # ).replace("\n", r"\n")


def make_copy_paste_env(env: Dict[str, str]) -> str:
    """
    Convert an environment into a set of commands to recreate that environment.
    """
    cmd = "set" if BUILD_PLATFORM.windows else "export"
    return (
        "\n".join("{cmd} {k}={v}".format(
            cmd=cmd,
            k=k,
            v=(env[k] if BUILD_PLATFORM.windows else
               subprocess.list2cmdline([env[k]]))
        ) for k in sorted(env.keys())))
    # Note that even subprocess.list2cmdline() will put needless quotes in
    # here, whereas SET is happy with e.g. SET x=C:\Program Files\somewhere;
    # subprocess.list2cmdline() will also mess up trailing backslashes (e.g.
    # for the VS140COMNTOOLS environment variable).
    
    
def contains_unquoted_target(x: str,
                             quote: str = '"', target: str = '&') -> bool:
    """
    See https://stackoverflow.com/questions/34124636.
    Under Windows, if an ampersand is in a path and is not quoted, it'll break
    lots of things.
    Simple example:
        set RUBBISH=a & b           # 'b' is not recognizable as a... command
        set RUBBISH='a & b'         # 'b'' is not recognizable as a... command
        set RUBBISH="a & b"         # OK
    
    ... and you get similar knock-on effects, e.g. if you set RUBBISH using the
    Control Panel to the literal
        a & dir
    
    and then do
        echo %RUBBISH%
    it will (1) print "a" and then (2) print a directory listing as it RUNS
    "dir"! That's pretty dreadful.
    
    See also
        https://www.thesecurityfactory.be/command-injection-windows.html
    
    Anyway, this is a sanity check for that sort of thing.
    """
    in_quote = False
    for c in x:
        if c == quote:
            in_quote = not in_quote
        elif c == target:
            if not in_quote:
                return True
    return False


def contains_unquoted_ampersand_dangerous_to_windows(x: str) -> bool:
    return contains_unquoted_target(x, quote='"', target='&')


# def chmod_recursive(root: str, permission: int) -> None:
#     # Untested
#     # Permission: e.g. stat.S_IWUSR
#     os.chmod(root, permission)
#     for dirpath, dirnames, filenames in os.walk(root):
#         for d in dirnames:
#             os.chmod(join(dirpath, d), permission)
#         for f in filenames:
#             os.chmod(join(dirpath, f), permission)


def shutil_rmtree_onerror(func: Callable[[str], None],
                          path: str,
                          exc_info: Tuple) -> None:
    # https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied  # noqa
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def rmtree(directory: str) -> None:
    log.debug("Deleting directory {}".format(directory))
    shutil.rmtree(directory, onerror=shutil_rmtree_onerror)
    

def run(args: List[str],
        env: Dict[str, str] = None,
        get_output: bool = False,
        debug_show_env: bool = True,
        encoding: str = sys.getdefaultencoding(),
        allow_failure: bool = False) -> Tuple[str, str]:
    """
    Runs an external process, announcing it.
    """
    cwd = os.getcwd()
    # log.debug("External command Python form: {}".format(args))
    copy_paste_cmd = make_copy_paste_cmd(args)
    csep = "=" * 79
    esep = "-" * 79
    if debug_show_env:
        effective_env = env or os.environ
        log.debug(
            "Environment for the command that follows:\n"
            "{esep}\n"
            "{env}\n"
            "{esep}".format(esep=esep, env=make_copy_paste_env(effective_env))
        )
    log.info(
        "Launching external command:\n"
        "{csep}\n"
        "WORKING DIRECTORY: {cwd}\n"
        "COMMAND: {cmd}\n"
        "{csep}".format(csep=csep, cwd=cwd, cmd=copy_paste_cmd)
    )
    try:
        if get_output:
            p = subprocess.run(args, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=not allow_failure)
            stdout, stderr = (
                p.stdout.decode(encoding), p.stderr.decode(encoding)
            )
        else:
            subprocess.check_call(args, env=env)
            stdout, stderr = "", ""
        log.debug("\n{csep}\nFINISHED SUCCESSFULLY: {cmd}\n{csep}".format(
            cmd=copy_paste_cmd, csep=csep))
        return stdout, stderr
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.critical(
            "Command that failed:\n"
            "[ENVIRONMENT]\n"
            "{env}\n"
            "\n"
            "[DIRECTORY] {cwd}\n"
            "[PYTHON ARGS] {args}\n"
            "[COMMAND] {cmd}".format(
                cwd=cwd,
                env=make_copy_paste_env(effective_env),
                cmd=copy_paste_cmd,
                args=args
            )
        )
        raise


def replace_in_file(filename: str, text_from: str, text_to: str) -> None:
    """
    Replaces text in a file.
    """
    log.info("Amending {}: {} -> {}".format(
        filename, repr(text_from), repr(text_to)))
    with open(filename) as infile:
        contents = infile.read()
    contents = contents.replace(text_from, text_to)
    with open(filename, 'w') as outfile:
        outfile.write(contents)


def require(command: str) -> None:
    """
    Checks that an external command is available, or raises an exception.
    """
    if shutil.which(command):
        return
    # Failure, so offer some help
    missing_msg = "Missing OS command: {}".format(command)
    helpmsg = "If core commands are missing:\n"

    if BUILD_PLATFORM.linux:
        helpmsg += """
Linux (Ubuntu)
-------------------------------------------------------------------------------
ar          } Should be pre-installed!
cmake       }
gcc         }
gobjdump    }
readelf     }

ant         sudo apt install ant
javac       sudo apt install openjdk-8-jdk

"""  # noqa
    _ = """
Linux (Ubuntu) (DEFUNCT)
-------------------------------------------------------------------------------
*mingw*     } sudo apt install mingw-w64
*windres    }
    """

    if BUILD_PLATFORM.osx:
        helpmsg += """
OS/X
-------------------------------------------------------------------------------
cmake       brew update && brew install cmake
gobjdump    brew update && brew install binutils
"""

    if BUILD_PLATFORM.windows:
        helpmsg += r"""
Windows                                                                 Cygwin
                                                                        package
-------------------------------------------------------------------------------
bash        Install Cygwin; part of the default installation            -
cmake       Install the Cygwin package "cmake"                          cmake
ld          Install the Cygwin package "gcc-g++"                        gcc-g++
make        Install the Cygwin package "make"                           make
tar         Install Cygwin; part of the default installation            -
tclsh       Install the Cygwin package "tcl" AND ALSO:                  tcl
                C:\> bash
                $ cp /bin/tclsh8.6.exe /bin/tclsh.exe
            ... because the built-in "tclsh" (no .exe) isn't found by Windows.

git         Install from https://git-scm.com/
nasm        Install from http://www.nasm.us/
vcvarsall.bat    Install Microsoft Visual Studio/VC++, e.g. the free Community
            edition from https://www.visualstudio.com/; download and run the
            installer; tick at least "Desktop development with C++"
perl        Install from https://www.activestate.com/activeperl

Don't forget to add the tools to your PATH, such as:
    C:\Perl64\bin
    C:\cygwin64\bin
    C:\Program Files\NASM
    C:\Program Files\Git\cmd
    
and for vcvarsall.bat, something like one of:
    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC
    C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build
... depending on your version of Visual Studio.

If you install Cygwin Perl (package "perl"), make sure the native Windows
version of Perl PRECEDES IT in the PATH; you don't want the Cygwin one to be
the default.

"""
    _ = r"""
Windows (DEFUNCT)
-------------------------------------------------------------------------------
makedepend  Install the Cygwin (*) package "makedepend"
readelf     Install the Cygwin (*) package "binutils"
            
    """

    log.critical(missing_msg)
    log.info(helpmsg)
    raise ValueError(missing_msg)


def are_debian_packages_installed(packages: List[str]) -> Dict[str, bool]:
    assert len(packages) >= 1
    require(DPKG_QUERY)
    args = [
        DPKG_QUERY,
        "-W",  # --show
        # "-f='${Package} ${Status} ${Version}\n'",
        "-f=${Package} ${Status}\n",  # --showformat
    ] + packages
    stdout, stderr = run(args, get_output=True, allow_failure=True)
    present = OrderedDict()
    for line in stdout.split("\n"):
        if line:  # e.g. "autoconf install ok installed"
            words = line.split()
            assert len(words) >= 2
            package = words[0]
            present[package] = "installed" in words[1:]
    for line in stderr.split("\n"):
        if line:  # e.g. "dpkg-query: no packages found matching XXX"
            words = line.split()
            assert len(words) >= 2
            package = words[-1]
            present[package] = False
    log.debug("Debian package presence: {}".format(present))
    return present


def require_debian_packages(packages: List[str]) -> None:
    """
    Ensure specific packages are installed under Debian.
    Args:
        packages:

    Returns:

    """
    present = are_debian_packages_installed(packages)
    missing_packages = [k for k, v in present.items() if not v]
    if missing_packages:
        missing_packages.sort()
        msg = (
            "Debian packages are missing, as follows. Suggest:\n\n"
            "sudo apt install {}".format(" ".join(missing_packages))
        )
        fail(msg)


def replace_multiple_in_file(filename: str,
                             replacements: List[Tuple[str, str]]) -> None:
    """
    Replaces multiple from/to string pairs within a single file.
    """
    with open(filename) as infile:
        contents = infile.read()
    for text_from, text_to in replacements:
        log.info("Amending {}: {} -> {}".format(
            filename, repr(text_from), repr(text_to)))
        contents = contents.replace(text_from, text_to)
    with open(filename, 'w') as outfile:
        outfile.write(contents)


def mkdir_p(path: str) -> None:
    """
    Makes a directory, and any other necessary directories (mkdir -p).
    """
    log.info("mkdir -p {}".format(path))
    os.makedirs(path, exist_ok=True)


def download_if_not_exists(url: str, filename: str,
                           skip_cert_verify: bool = True) -> None:
    """
    Downloads a URL to a file, unless the file already exists.
    """
    if isfile(filename):
        log.info("No need to download, already have: {}".format(filename))
        return
    directory, basename = split(abspath(filename))
    mkdir_p(directory)
    log.info("Downloading from {} to {}".format(url, filename))
        
    # urllib.request.urlretrieve(url, filename)
    # ... sometimes fails (e.g. downloading
    # https://www.openssl.org/source/openssl-1.1.0g.tar.gz under Windows) with:
    # ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777)  # noqa
    # ... due to this certificate root problem (probably because OpenSSL
    #     [used by Python] doesn't play entirely by the same rules as others?):
    # https://stackoverflow.com/questions/27804710
    # So:

    ctx = ssl.create_default_context()  # type: ssl.SSLContext
    if skip_cert_verify:
        log.debug("Skipping SSL certificate check for " + url)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, context=ctx) as u, open(filename, 'wb') as f:  # noqa
        f.write(u.read())


def root_path() -> str:
    """
    Returns the system root directory.
    """
    # http://stackoverflow.com/questions/12041525
    return abspath(os.sep)


def git_clone(prettyname: str, url: str, directory: str,
              branch: str = None,
              commit: str = None,
              clone_options: List[str] = None) -> bool:
    """
    Fetches a Git repository, unless we have it already.
    Returns: did we need to do anything?
    """
    clone_options = clone_options or []  # type: List[str]
    if isdir(directory):
        log.info("Not re-cloning {} Git repository: using existing source "
                 "in {}".format(prettyname, directory))
        return False
    log.info("Fetching {} source from {} into {}".format(
        prettyname, url, directory))
    gitargs = [GIT, "clone"] + clone_options
    if branch:
        gitargs += ["--branch", branch]
    gitargs += [url, directory]
    run(gitargs)
    if commit:
        log.info("Resetting {} local Git repository to commit {}".format(
            prettyname, commit))
        run([GIT,
             "-C", directory,
             "reset", "--hard", commit])
        # Using a Git repository that's not in the working directory:
        # https://stackoverflow.com/questions/1386291/git-git-dir-not-working-as-expected  # noqa
    return True


# def fix_git_repo_for_windows(directory: str):
#     # https://github.com/openssl/openssl/issues/174
#     log.info("Fixing repository {!r} for Windows line endings".format(
#         directory))
#     with pushd(directory):
#         run([GIT, "config", "--local", "core.autocrlf", "false"])
#         run([GIT, "config", "--local", "core.eol", "lf"])
#         run([GIT, "rm", "--cached", "-r", "."])
#         run([GIT, "reset", "--hard"])


def untar_to_directory(tarfile: str, directory: str,
                       verbose: bool = False,
                       gzipped: bool = False,
                       skip_if_dir_exists: bool = True) -> None:
    """
    Unpacks a TAR file into a specified directory.
    """
    if skip_if_dir_exists and isdir(directory):
        log.info("Skipping extraction of {} as directory {} exists".format(
            tarfile, directory))
        return
    log.info("Extracting {} -> {}".format(tarfile, directory))
    mkdir_p(directory)
    args = [TAR, "-x"]  # -x: extract
    if verbose:
        args.append("-v")  # -v: verbose
    if gzipped:
        args.append("-z")  # -z: decompress using gzip
    if not BUILD_PLATFORM.osx:  # OS/X tar doesn't support --force-local
        args.append("--force-local")  # allows filenames with colons in (Windows!)  # noqa
    args.extend(["-f", tarfile])  # -f: filename follows
    args.extend(["-C", directory])  # -C: change to directory
    run(args)


def delete_files_within_dir(filename: str, directory: str) -> None:
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            if f == filename:
                fullpath = join(dirpath, f)
                log.debug("Deleting {!r}".format(fullpath))
                os.remove(fullpath)


def delete_cmake_cache(directory: str) -> None:
    """
    Removes the CMake cache file from a directory.
    """
    log.info("Deleting CMake cache files within: {!r}".format(directory))
    delete_files_within_dir("CMakeCache.txt", directory)


# def delete_qmake_cache(directory: str) -> None:
#     log.info("Deleting qmake cache files within: {!r}".format(directory))
#     delete_files_within_dir(".qmake.cache", directory)
#     delete_files_within_dir(".qmake.stash", directory)
#     delete_files_within_dir(".qmake.super", directory)


# Nope! These are important.
# def delete_qmake_conf(directory: str) -> None:
#     log.info("Deleting qmake config files within: {!r}".format(directory))
#     delete_files_within_dir(".qmake.conf", directory)


def copytree(srcdir: str, destdir: str, destroy: bool = False) -> None:
    """
    Recursive copy.
    """
    log.info("Copying directory {} -> {}".format(srcdir, destdir))
    if os.path.exists(destdir):
        if not destroy:
            raise ValueError("Destination exists!")
        if not os.path.isdir(destdir):
            raise ValueError("Destination exists but isn't a directory!")
        log.debug("... removing old contents")
        rmtree(destdir)
        log.debug("... now copying")
    shutil.copytree(srcdir, destdir)


def convert_line_endings(filename: str, to_unix: bool = False,
                         to_windows: bool = False) -> None:
    """
    Converts a file from UNIX -> Windows line endings, or the reverse.
    """
    assert to_unix != to_windows
    with open(filename, "rb") as f:
        contents = f.read()
    windows_eol = b"\r\n"  # CR LF
    unix_eol = b"\n"  # LF
    if to_unix:
        log.info("Converting from Windows to UNIX line endings: {!r}".format(
            filename))
        src = windows_eol
        dst = unix_eol
    else:  # to_windows
        log.info("Converting from UNIX to Windows line endings: {!r}".format(
            filename))
        src = unix_eol
        dst = windows_eol
        if windows_eol in contents:
            log.info("... already contains at least one Windows line ending; "
                     "probably converted before; skipping")
            return
    contents = contents.replace(src, dst)
    with open(filename, "wb") as f:
        f.write(contents)


def get_starting_env(plain: bool = None) -> Dict[str, str]:
    if plain is None:
        plain = not BUILD_PLATFORM.windows
    if plain:
        # Beware under Windows. Some other parent environment variables needed
        # for Visual C++ compiler, or you get "cannot create temporary il file"
        # errors. Not sure which, though; APPDATA, TEMP and TMP are not
        # sufficient.
        env = {}  # type: Dict[str, str]
        keys = ["PATH"]
        # if BUILD_PLATFORM.windows:
        #     keys += ["APPDATA", "TEMP", "TMP"]
        for k in keys:
            if k in os.environ:
                env[k] = os.environ[k]
        return env
    else:
        return os.environ.copy()


def fail(msg: str) -> None:
    log.critical(msg)
    raise ValueError(msg)


def is_line_in_file(filename: str, line: str) -> bool:
    assert "\n" not in line
    with open(filename, "r") as file:
        for fileline in file:
            if fileline == line:
                return True
        return False


def add_line_if_absent(filename: str, line: str) -> None:
    assert "\n" not in line
    if not is_line_in_file(filename, line):
        log.info("Appending line {!r} to file {!r}".format(line, filename))
        with open(filename, "a") as file:
            file.writelines([line])
            
            
def validate_pair(ob: Any) -> bool:
    try:
        if len(ob) != 2:
            log.warning("Unexpected result: {!r}".format(ob))
            raise ValueError()
    except ValueError:
        return False
    return True


def consume(iterator) -> None:
    try:
        while True:
            next(iterator)
    except StopIteration:
        pass


def windows_get_environment_from_batch_command(
        env_cmd: Union[str, List[str]],
        initial_env: Dict[str, str] = None) -> Dict[str, str]:
    # https://stackoverflow.com/questions/1214496/how-to-get-environment-from-a-subprocess-in-python  # noqa
    # ... with decoding bug fixed for Python 3
    """
    Take a command (either a single command or list of arguments)
    and return the environment created after running that command.
    Note that the command must be a batch file or .cmd file, or the
    changes to the environment will not be captured.

    If initial_env is supplied, it is used as the initial environment passed
    to the child process. (Otherwise, this process's os.environ() will be
    used by default.)
    """
    if not isinstance(env_cmd, (list, tuple)):
        env_cmd = [env_cmd]
    # construct the command that will alter the environment
    env_cmd = subprocess.list2cmdline(env_cmd)
    # create a tag so we can tell in the output when the proc is done
    tag = '+/!+/!+/! Finished command to set/print env +/!+/!+/!'  # RNC
    # construct a cmd.exe command to do accomplish this
    cmd = 'cmd.exe /s /c "{env_cmd} && echo "{tag}" && set"'.format(
        env_cmd=env_cmd, tag=tag)
    # launch the process
    log.info("Fetching environment using command: {}".format(env_cmd))
    log.debug("Full command: {}".format(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=initial_env)
    # parse the output sent to stdout
    encoding = sys.getdefaultencoding()

    def gen_lines() -> Generator[str, None, None]:  # RNC: fix decode problem
        for line in proc.stdout:
            yield line.decode(encoding)

    # define a way to handle each KEY=VALUE line
    def handle_line(line: str) -> List[str]:  # RNC: as function
        return line.rstrip().split('=', 1)
    
    lines = gen_lines()  # RNC
    # consume whatever output occurs until the tag is reached
    consume(itertools.takewhile(lambda l: tag not in l, lines))
    # ... RNC: note that itertools.takewhile() generates values not matching
    #     the condition, but then consumes the condition value itself. So the
    #     tag's already gone. Example:
    #
    #   def gen():
    #       mylist = [1, 2, 3, 4, 5]
    #       for x in mylist:
    #           yield x
    #
    #   g = gen()
    #   list(itertools.takewhile(lambda x: x != 3, g))  # [1, 2]
    #   next(g)  # 4, not 3
    #
    # parse key/values into pairs
    pairs = map(handle_line, lines)
    # make sure the pairs are valid (this also eliminates the tag)
    valid_pairs = filter(validate_pair, pairs)
    # construct a dictionary of the pairs
    result = dict(valid_pairs)  # consumes generator
    # let the process finish
    proc.communicate()
    log.debug("Fetched environment:\n" + pformat(result))
    return result


def ensure_first_perl_is_not_cygwin() -> None:
    require(PERL)
    which = shutil.which(PERL)
    if "cygwin" in which.lower():
        fail("The first instance of Perl on your path ({}) is from Cygwin. "
             "This will fail when building OpenSSL. Please re-order your PATH "
             "so that a Windows version, e.g. ActiveState Perl, comes "
             "first.".format(which))

_WHY_ENSURE_FIRST_PERL_IS_NOT_CYGWIN = r"""
===============================================================================
WORKING DIRECTORY: C:\Users\Rudolf\dev\qt_local_build\openssl_windows_x86_64_build\openssl-1.1.0g
COMMAND: perl C:\Users\Rudolf\dev\qt_local_build\openssl_windows_x86_64_build\openssl-1.1.0g\Configure VC-WIN64A shared no-ssl3
===============================================================================
File::Glob::glob() will disappear in perl 5.30. Use File::Glob::bsd_glob() instead. at C:\Users\Rudolf\dev\qt_local_build\openssl_windows_x86_64_build\openssl-1.1.0g\Configure line 270.
Configuring OpenSSL version 1.1.0g (0x1010007fL)
    no-asan         [default]  OPENSSL_NO_ASAN
    no-crypto-mdebug [default]  OPENSSL_NO_CRYPTO_MDEBUG
    no-crypto-mdebug-backtrace [default]  OPENSSL_NO_CRYPTO_MDEBUG_BACKTRACE
    no-ec_nistp_64_gcc_128 [default]  OPENSSL_NO_EC_NISTP_64_GCC_128
    no-egd          [default]  OPENSSL_NO_EGD
    no-fuzz-afl     [default]  OPENSSL_NO_FUZZ_AFL
    no-fuzz-libfuzzer [default]  OPENSSL_NO_FUZZ_LIBFUZZER
    no-heartbeats   [default]  OPENSSL_NO_HEARTBEATS
    no-md2          [default]  OPENSSL_NO_MD2 (skip dir)
    no-msan         [default]  OPENSSL_NO_MSAN
    no-rc5          [default]  OPENSSL_NO_RC5 (skip dir)
    no-sctp         [default]  OPENSSL_NO_SCTP
    no-ssl-trace    [default]  OPENSSL_NO_SSL_TRACE
    no-ssl3         [option]   OPENSSL_NO_SSL3
    no-ssl3-method  [default]  OPENSSL_NO_SSL3_METHOD
    no-ubsan        [default]  OPENSSL_NO_UBSAN
    no-unit-test    [default]  OPENSSL_NO_UNIT_TEST
    no-weak-ssl-ciphers [default]  OPENSSL_NO_WEAK_SSL_CIPHERS
    no-zlib         [default]
    no-zlib-dynamic [default]
Configuring for VC-WIN64A

******************************************************************************
This perl implementation doesn't produce Windows like paths (with backward
slash directory separators).  Please use an implementation that matches your
building platform.

This Perl version: 5.26.1 for x86_64-cygwin-threads-multi
******************************************************************************

$ which perl
/usr/bin/perl

>>> shutil.which("perl")
'C:\\cygwin64\\bin\\perl.EXE'

# Then after installing ActiveState Perl:

$ which perl
/cygdrive/c/Perl64/bin/perl

>>> shutil.which("perl")
'C:\\Perl64\\bin\\perl.EXE'

"""


# =============================================================================
# Building OpenSSL
# =============================================================================

def fetch_openssl(cfg: Config) -> None:
    """
    Downloads OpenSSL source code.
    """
    download_if_not_exists(cfg.openssl_src_url, cfg.openssl_src_fullpath)
    download_if_not_exists(cfg.openssl_android_script_url,
                           cfg.openssl_android_script_fullpath)


def build_openssl(cfg: Config, target_platform: Platform) -> None:
    """
    Builds OpenSSL.

    The target_os parameter is paseed to OpenSSL's Configure script.
    Use "./Configure LIST" for all possibilities.

        https://wiki.openssl.org/index.php/Compilation_and_Installation
    """
    # -------------------------------------------------------------------------
    # Prerequisites
    # -------------------------------------------------------------------------
    if BUILD_PLATFORM.windows:
        ensure_first_perl_is_not_cygwin()
        require(NASM)

    # -------------------------------------------------------------------------
    # Set up filenames we expect to be generated
    # -------------------------------------------------------------------------
    rootdir, workdir = cfg.get_openssl_rootdir_workdir(target_platform)
    dynamic_lib_ext = target_platform.dynamic_lib_ext
    static_lib_ext = target_platform.static_lib_ext
    if BUILD_PLATFORM.windows:
        openssl_verparts = cfg.openssl_version.split(".")
        openssl_major = "-{}_{}".format(openssl_verparts[0],
                                        openssl_verparts[1])
        if target_platform.cpu_x86_64bit_family:
            fname_arch = "-x64"
        else:
            fname_arch = ""
        fname_extra = openssl_major + fname_arch  # e.g. "-1_1-x64"
    else:
        fname_extra = ""
    main_targets = [
        join(workdir, "libssl{}{}".format(fname_extra, dynamic_lib_ext)),
        join(workdir, "libssl{}".format(static_lib_ext)),
        join(workdir, "libcrypto{}{}".format(fname_extra, dynamic_lib_ext)),
        join(workdir, "libcrypto{}".format(static_lib_ext)),
    ]
    
    # Now, also: Linux likes to use "-lcrypto" and have that mean "look at
    # libcrypto.so", whereas under Windows we seem to have to use
    # "-llibcrypto" instead. However, some things, like SQLCipher,
    # hard-code the "-lcrypto" (in that example, in its test suite as it
    # compiles conftest.c). So we're best off using the Linux notation but
    # making additional copies of the libraries:
    shadow_targets = []  # type: List[str]
    libprefix = "lib"
    if BUILD_PLATFORM.windows:
        for t in main_targets:
            dirname, basename = os.path.split(t)
            assert basename.startswith(libprefix)
            shortbasename = basename[len(libprefix):]
            shadow_targets.append(join(dirname, shortbasename))

    targets = main_targets + shadow_targets
    if not cfg.force and all(isfile(x) for x in targets):
        log.info("OpenSSL: All targets exist already:\n{}".format(
            "\n".join("    " + str(x) for x in targets)))
        return

    # -------------------------------------------------------------------------
    # Unpack source
    # -------------------------------------------------------------------------
    untar_to_directory(cfg.openssl_src_fullpath, rootdir)

    # -------------------------------------------------------------------------
    # Configure options
    # -------------------------------------------------------------------------
    # The OpenSSL "config" sh script guesses the OS, then passes details
    # to its "Configure" Perl script.
    # For Android, OpenSSL suggest using their Setenv-android.sh script, then
    # running "config".
    # However, it does seem to be screwing up. Let's try Configure instead.

    # http://doc.qt.io/qt-5/opensslsupport.html
    target_os = ""

    if target_platform.android:
        if target_platform.cpu == Cpu.ARM_V5:
            target_os = "android"  # ... NB "android" means ARMv5
        elif target_platform.cpu == Cpu.ARM_V7:
            if OPENSSL_AT_LEAST_1_1:
                target_os = "android-armeabi"
            else:
                target_os = "android-armv7"
        elif target_platform.cpu_x86_family:
            target_os = "android-x86"
        else:
            pass  # will raise error below

    elif target_platform.linux and target_platform.cpu_x86_64bit_family:
        target_os = "linux-x86_64"

    elif target_platform.osx and target_platform.cpu_x86_64bit_family:
        # https://gist.github.com/tmiz/1441111
        target_os = "darwin64-x86_64-cc"

    elif target_platform.ios:
        # https://gist.github.com/foozmeat/5154962
        # https://gist.github.com/felix-schwarz/c61c0f7d9ab60f53ebb0
        # https://gist.github.com/armadsen/b30f352a8d6f6c87a146
        # If Bitcode is later required, see the other ones above and
        # https://stackoverflow.com/questions/30722606/what-does-enable-bitcode-do-in-xcode-7  # noqa
        if target_platform.cpu == Cpu.ARM_V8_64:
            target_os = "iphoneos-cross"
        elif target_platform.cpu_x86_64bit_family:
            target_os = "darwin64-x86_64-cc"
        # iOS specials
        run([
            SED,
            "-ie",
            "s!static volatile sig_atomic_t intr_signal;!static volatile intr_signal;!",  # noqa
            join(workdir, "crypto", "ui", "ui_openssl.c")
        ])
        # At some point (transiently!) we also got something like:
        #    ar  r ../../libcrypto.a o_names.o obj_dat.o obj_lib.o 
        #        obj_err.o obj_xref.
        # failing with:
        #     /usr/bin/ranlib: archive member: libcrypto.a(....o) size too 
        #         large (archive member extends past the end of the file)
        #     ar: internal ranlib command failed
        # ... not sure why.
    
    elif target_platform.windows:
        if BUILD_PLATFORM.windows:
            # if USE_CYGWIN:
            #     target_os = "Cygwin-x86_64"
            # elif USE_MINGW:
            #     if target_platform.cpu_64bit:
            #         target_os = "mingw64"
            #     else:
            #         target_os = "mingw"

            # http://p-nand-q.com/programming/windows/building_openssl_with_visual_studio_2013.html  # noqa
            if target_platform.cpu_x86_64bit_family:
                target_os = "VC-WIN64A"
                # I'm not sure what "VC-WIN64I" is. Intel vs AMD? Ah, no:
                # https://stackoverflow.com/questions/38151387/build-openssl-for-both-x64-and-x86-side-by-side-installation  # noqa
                # ... "WIN64I denotes IA-64 and WIN64A - AMD64"
                # ... where IA-64 means Intel Itanium: https://en.wikipedia.org/wiki/IA-64  # noqa
                # ... so we want "-A" for x86-64.
            elif target_platform.cpu_x86_32bit_family:
                target_os = "VC-WIN32"
            else:
                raise NotImplementedError(
                    "Don't know how to compile OpenSSL for "
                    "this processor: {}".format(target_platform))
        elif BUILD_PLATFORM.linux:
            if USE_MINGW:
                if target_platform.cpu_64bit:
                    target_os = "mingw64"
                else:
                    target_os = "mingw"
                    
    # For new platforms: if you're not sure, use target_os = "crashme" and
    # you'll get the list of permitted values, which as of 2017-11-12 is:
    
    _OPENSSL_1_0_2H_TARGETS = """
BC-32 BS2000-OSD BSD-generic32 BSD-generic64 BSD-ia64 BSD-sparc64 BSD-sparcv8
BSD-x86 BSD-x86-elf BSD-x86_64 Cygwin Cygwin-x86_64 DJGPP MPE/iX-gcc OS2-EMX
OS390-Unix QNX6 QNX6-i386 ReliantUNIX SINIX SINIX-N UWIN VC-CE VC-WIN32
VC-WIN64A VC-WIN64I aix-cc aix-gcc aix3-cc aix64-cc aix64-gcc android
android-armv7 android-mips android-x86 aux3-gcc beos-x86-bone beos-x86-r5
bsdi-elf-gcc cc cray-j90 cray-t3e darwin-i386-cc darwin-ppc-cc darwin64-ppc-cc
darwin64-x86_64-cc dgux-R3-gcc dgux-R4-gcc dgux-R4-x86-gcc dist gcc hpux-cc
hpux-gcc hpux-ia64-cc hpux-ia64-gcc hpux-parisc-cc hpux-parisc-cc-o4
hpux-parisc-gcc hpux-parisc1_1-cc hpux-parisc1_1-gcc hpux-parisc2-cc
hpux-parisc2-gcc hpux64-ia64-cc hpux64-ia64-gcc hpux64-parisc2-cc
hpux64-parisc2-gcc hurd-x86 iphoneos-cross irix-cc irix-gcc irix-mips3-cc
irix-mips3-gcc irix64-mips4-cc irix64-mips4-gcc linux-aarch64
linux-alpha+bwx-ccc linux-alpha+bwx-gcc linux-alpha-ccc linux-alpha-gcc
linux-aout linux-armv4 linux-elf linux-generic32 linux-generic64
linux-ia32-icc linux-ia64 linux-ia64-icc linux-mips32 linux-mips64 linux-ppc
linux-ppc64 linux-ppc64le linux-sparcv8 linux-sparcv9 linux-x32 linux-x86_64
linux-x86_64-clang linux-x86_64-icc linux32-s390x linux64-mips64 linux64-s390x
linux64-sparcv9 mingw mingw64 ncr-scde netware-clib netware-clib-bsdsock
netware-clib-bsdsock-gcc netware-clib-gcc netware-libc netware-libc-bsdsock
netware-libc-bsdsock-gcc netware-libc-gcc newsos4-gcc nextstep nextstep3.3
osf1-alpha-cc osf1-alpha-gcc purify qnx4 rhapsody-ppc-cc sco5-cc sco5-gcc
solaris-sparcv7-cc solaris-sparcv7-gcc solaris-sparcv8-cc solaris-sparcv8-gcc
solaris-sparcv9-cc solaris-sparcv9-gcc solaris-x86-cc solaris-x86-gcc
solaris64-sparcv9-cc solaris64-sparcv9-gcc solaris64-x86_64-cc
solaris64-x86_64-gcc sunos-gcc tandem-c89 tru64-alpha-cc uClinux-dist
uClinux-dist64 ultrix-cc ultrix-gcc unixware-2.0 unixware-2.1 unixware-7
unixware-7-gcc vos-gcc vxworks-mips vxworks-ppc405 vxworks-ppc60x
vxworks-ppc750 vxworks-ppc750-debug vxworks-ppc860 vxworks-ppcgen
vxworks-simlinux debug debug-BSD-x86-elf debug-VC-WIN32 debug-VC-WIN64A
debug-VC-WIN64I debug-ben debug-ben-darwin64 debug-ben-debug
debug-ben-debug-64 debug-ben-debug-64-clang debug-ben-macos
debug-ben-macos-gcc46 debug-ben-no-opt debug-ben-openbsd
debug-ben-openbsd-debug debug-ben-strict debug-bodo debug-darwin-i386-cc
debug-darwin-ppc-cc debug-darwin64-x86_64-cc debug-geoff32 debug-geoff64
debug-levitte-linux-elf debug-levitte-linux-elf-extreme
debug-levitte-linux-noasm debug-levitte-linux-noasm-extreme debug-linux-elf
debug-linux-elf-noefence debug-linux-generic32 debug-linux-generic64
debug-linux-ia32-aes debug-linux-pentium debug-linux-ppro debug-linux-x86_64
debug-linux-x86_64-clang debug-rse debug-solaris-sparcv8-cc
debug-solaris-sparcv8-gcc debug-solaris-sparcv9-cc debug-solaris-sparcv9-gcc
debug-steve-opt debug-steve32 debug-steve64 debug-vos-gcc
    """
    _OPENSSL_1_1_0G_TARGET = """
Usage: Configure [no-<cipher> ...] [enable-<cipher> ...] [-Dxxx] [-lxxx] [-Lxxx] [-fxxx] [-Kxxx] [no-hw-xxx|no-hw] [[no-]threads] [[no-]shared] [[no-]zlib|zlib-dynamic] [no-asm] [no-dso] [no-egd] [sctp] [386] [--prefix=DIR] [--openssldir=OPENSSLDIR] [--with-xxx[=vvv]] [--config=FILE] os/compiler[:flags]

pick os/compiler from:
BS2000-OSD BSD-generic32 BSD-generic64 BSD-ia64 BSD-sparc64 BSD-sparcv8 
BSD-x86 BSD-x86-elf BSD-x86_64 Cygwin Cygwin-i386 Cygwin-i486 Cygwin-i586 
Cygwin-i686 Cygwin-x86 Cygwin-x86_64 DJGPP MPE/iX-gcc OS390-Unix QNX6 
QNX6-i386 UEFI UWIN VC-CE VC-WIN32 VC-WIN64A VC-WIN64A-masm VC-WIN64I aix-cc 
aix-gcc aix64-cc aix64-gcc android android-armeabi android-mips android-x86 
android64 android64-aarch64 bsdi-elf-gcc cc darwin-i386-cc darwin-ppc-cc 
darwin64-debug-test-64-clang darwin64-ppc-cc darwin64-x86_64-cc dist gcc 
haiku-x86 haiku-x86_64 hpux-ia64-cc hpux-ia64-gcc hpux-parisc-cc 
hpux-parisc-gcc hpux-parisc1_1-cc hpux-parisc1_1-gcc hpux64-ia64-cc 
hpux64-ia64-gcc hpux64-parisc2-cc hpux64-parisc2-gcc hurd-x86 ios-cross 
ios64-cross iphoneos-cross irix-mips3-cc irix-mips3-gcc irix64-mips4-cc 
irix64-mips4-gcc linux-aarch64 linux-alpha-gcc linux-aout linux-arm64ilp32 
linux-armv4 linux-c64xplus linux-elf linux-generic32 linux-generic64 
linux-ia64 linux-mips32 linux-mips64 linux-ppc linux-ppc64 linux-ppc64le 
linux-sparcv8 linux-sparcv9 linux-x32 linux-x86 linux-x86-clang linux-x86_64 
linux-x86_64-clang linux32-s390x linux64-mips64 linux64-s390x linux64-sparcv9 
mingw mingw64 nextstep nextstep3.3 purify qnx4 sco5-cc sco5-gcc 
solaris-sparcv7-cc solaris-sparcv7-gcc solaris-sparcv8-cc solaris-sparcv8-gcc 
solaris-sparcv9-cc solaris-sparcv9-gcc solaris-x86-gcc solaris64-sparcv9-cc 
solaris64-sparcv9-gcc solaris64-x86_64-cc solaris64-x86_64-gcc tru64-alpha-cc 
tru64-alpha-gcc uClinux-dist uClinux-dist64 unixware-2.0 unixware-2.1 
unixware-7 unixware-7-gcc vms-alpha vms-alpha-p32 vms-alpha-p64 vms-ia64 
vms-ia64-p32 vms-ia64-p64 vos-gcc vxworks-mips vxworks-ppc405 vxworks-ppc60x 
vxworks-ppc750 vxworks-ppc750-debug vxworks-ppc860 vxworks-ppcgen 
vxworks-simlinux debug debug-erbridge debug-linux-ia32-aes debug-linux-pentium 
debug-linux-ppro debug-test-64-clang 

NOTE: If in doubt, on Unix-ish systems use './config'.
    """

    if not target_os:
        raise NotImplementedError("Don't know how to make OpenSSL for " +
                                  target_platform.description)

    configure_args = [target_os] + OPENSSL_COMMON_OPTIONS
    if target_platform.mobile:
        configure_args += [
            "no-hw",  # disable hardware support ("useful on mobile devices")
            "no-engine",  # disable hardware support ("useful on mobile devices")  # noqa
        ]
    # OpenSSL's Configure script applies optimizations by default.

    # -------------------------------------------------------------------------
    # Environment
    # -------------------------------------------------------------------------
    env = get_starting_env()
    cfg.set_compile_env(env, target_platform)
    if target_platform.android:
        # https://wiki.openssl.org/index.php/Android
        # We're not using the Setenv-android.sh script, but replicating its
        # functions; cfg.set_compile_env() does much of that.
        # Also:
        env["FIPS_SIG"] = ""  # OK to leave blank if not building FIPS
        env["MACHINE"] = "i686"
        env["RELEASE"] = "2.6.37"  # ??
        env["SYSTEM"] = target_os  # e.g. "android", "android-armv7"
        if OPENSSL_AT_LEAST_1_1:
            # https://github.com/openssl/openssl/issues/1681
            # or: "error: invalid 'asm': invalid operand for code 'w'"
            env["CROSS_SYSROOT"] = env["ANDROID_SYSROOT"]

    # -------------------------------------------------------------------------
    # Makefile tweaking
    # -------------------------------------------------------------------------
    # https://wiki.openssl.org/index.php/Android
    if not OPENSSL_AT_LEAST_1_1:
        makefile_org = join(workdir, "Makefile.org")
        replace_in_file(makefile_org,
                        "install: all install_docs install_sw",
                        "install: install_docs install_sw")
    
    # if BUILD_PLATFORM.windows:
    #     # https://github.com/openssl/openssl/issues/174
    #     convert_line_endings(join(workdir, "Makefile.org"), to_unix=True)
    #     # Without this, the Perl "Configure" script goes wrong and fails to
    #     # remove "md2" whilst copying Makefile.org to Makefile. This results
    #     # in the error "#error MD2 is disabled".
    #     # Here, we guarantee the error regardless of the distribution,
    #     # because we run a textfile replace on Makefile.org, thus ensuring
    #     # Windows line endings (which are what the Perl script chokes on).
    #     # So we have to manually convert it back.

    with pushd(workdir):
        # ---------------------------------------------------------------------
        # Configure (or config)
        # ---------------------------------------------------------------------
        use_configure = True  # Better!
        if use_configure or not target_platform.android:
            # http://doc.qt.io/qt-5/opensslsupport.html
            if BUILD_PLATFORM.windows:
                log.warning(
                    "The OpenSSL Configure script may warn about nmake.exe "
                    "being missing when it isn't. (Or when it is...)")
            run([PERL, join(workdir, "Configure")] + configure_args, env)
        else:
            # The "config" script guesses the OS then runs "Configure".
            # https://wiki.openssl.org/index.php/Android
            # and "If in doubt, on Unix-ish systems use './config'."
            # https://wiki.openssl.org/index.php/Compilation_and_Installation
            run([join(workdir, "config")] + configure_args, env)

        # ---------------------------------------------------------------------
        # Make
        # ---------------------------------------------------------------------
        if OPENSSL_AT_LEAST_1_1:
            # See INSTALL, INSTALL.WIN, etc. from the OpenSSL distribution
            run(cfg.make_args(), env)
            if not OPENSSL_FAILS_OWN_TESTS:
                if target_platform.os == BUILD_PLATFORM.os:
                    run(cfg.make_args(command="test"), env)
                    # can't really test e.g. Android code directly under Linux
                # run(cfg.make_args(command="install"), env)

        else:
            # Have to remove version numbers from final library filenames,
            # AFTER configure has run:
            # http://doc.qt.io/qt-5/opensslsupport.html

            makefile = join(workdir, "Makefile")
            replace_multiple_in_file(makefile, [
                ('LIBNAME=$$i LIBVERSION=$(SHLIB_MAJOR).$(SHLIB_MINOR)',
                    'LIBNAME=$$i'),
                ('LIBCOMPATVERSIONS=";$(SHLIB_VERSION_HISTORY)"', ''),
            ])
            run(cfg.make_args(command="depend"), env)
            run(cfg.make_args(command="build_libs"), env)

    # Testing:
    # - "Have I built for the right architecture?"
    #   http://stackoverflow.com/questions/267941
    #   http://stackoverflow.com/questions/1085137
    #
    #   file libssl.so
    #   objdump -a libssl.so  # or -x, or...
    #   readelf -h libssl.so
    #
    # - Compare to files on the Android emulator:
    #
    #   adb pull /system/lib/libz.so  # system
    #   adb pull /data/data/org.camcops.camcops/lib/  # ours
    #
    # ... looks OK

    for i, t in enumerate(main_targets):
        target_platform.verify_lib(t)
        if BUILD_PLATFORM.windows:
            assert len(shadow_targets) == len(main_targets)
            shutil.copyfile(t, shadow_targets[i])


# =============================================================================
# Building Qt
# =============================================================================

def fetch_qt(cfg: Config) -> None:
    """
    Downloads Qt source code.
    """
    if not git_clone(prettyname="Qt",
                     url=cfg.qt_git_url,
                     branch=cfg.qt_git_branch,
                     commit=cfg.qt_git_commit,
                     directory=cfg.qt_src_gitdir):
        return
    chdir(cfg.qt_src_gitdir)
    run([PERL, "init-repository"])


def build_qt(cfg: Config, target_platform: Platform) -> str:
    """
    1. Builds Qt.
    2. Returns the name of the "install" directory, where the installed qmake
       is.
    """
    # http://doc.qt.io/qt-5/opensslsupport.html
    # Android:
    #       example at http://wiki.qt.io/Qt5ForAndroidBuilding
    # Windows:
    #       https://stackoverflow.com/questions/14932315/how-to-compile-qt-5-under-windows-or-linux-32-or-64-bit-static-or-dynamic-on-v  # noqa
    #       ?also http://simpleit.us/2010/05/30/enabling-openssl-for-qt-c-on-windows/  # noqa
    #       http://doc.qt.io/qt-5/windows-building.html
    #       http://wiki.qt.io/Jom
    #       http://www.holoborodko.com/pavel/2011/02/01/how-to-compile-qt-4-7-with-visual-studio-2010/
    # iOS:
    #       http://doc.qt.io/qt-5/building-from-source-ios.html
    #       http://doc.qt.io/qt-5/ios-support.html
    # OS/X:
    #       http://doc.qt.io/qt-5/osx.html

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    # Linkage method of Qt itself?
    qt_linkage_static = target_platform.desktop
    # NOT Android; dynamic linkage then bundling into single-file APK.

    # Means by which Qt links to OpenSSL?
    qt_openssl_linkage_static = cfg.qt_openssl_static and qt_linkage_static
    # If Qt is linked dynamically, we do not let it link to OpenSSL
    # statically (it won't work).

    if target_platform.android:
        require(JAVAC)
        # ... will be called by the make process; better to know now, since the
        # relevant messages are easily lost in the torrent
        require(ANT)

    opensslrootdir, opensslworkdir = cfg.get_openssl_rootdir_workdir(target_platform)  # noqa
    openssl_include_root = join(opensslworkdir, "include")
    openssl_lib_root = opensslworkdir

    builddir = cfg.qt_build_dir(target_platform)
    installdir = cfg.qt_install_dir(target_platform)

    targets = [join(installdir, "bin", target_platform.qmake_executable)]
    if not cfg.force and all(isfile(x) for x in targets):
        log.info("Qt: All targets exist already:\n{}".format(
            "\n".join("    " + str(x) for x in targets)))
        return installdir

    # -------------------------------------------------------------------------
    # clean from old configure
    # -------------------------------------------------------------------------
    # No need to clean anything in the source directory, as long as you don't
    # build there.
    # https://stackoverflow.com/questions/24261974 (comments)
    
    # rmtree(builddir)
    # rmtree(installdir)
    # ... do this if something goes wrong, but it is slow; maybe not routinely
    # (unless you're developing this script)?

    # -------------------------------------------------------------------------
    # Environment
    # -------------------------------------------------------------------------
    env = get_starting_env()
    openssl_libs = "-L{} -lssl -lcrypto".format(openssl_lib_root)
    # See also https://bugreports.qt.io/browse/QTBUG-62016
    env['OPENSSL_LIBS'] = openssl_libs
    # Setting OPENSSL_LIBS as an *environment variable* may be unnecessary,
    # but is suggested by Qt; http://doc.qt.io/qt-4.8/ssl.html
    # However, it seems necessary to set it as an *option* to configure; see
    # below.
    cfg.set_compile_env(env, target_platform)

    # -------------------------------------------------------------------------
    # Directories
    # -------------------------------------------------------------------------
    log.info("Configuring {} build in {}".format(target_platform.description,
                                                 builddir))
    mkdir_p(builddir)
    mkdir_p(installdir)

    # -------------------------------------------------------------------------
    # Work out options to configure
    # -------------------------------------------------------------------------
    # -xplatform options are in src/qt5/qtbase/mkspecs/
    if BUILD_PLATFORM.windows:
        configure_prog_name = "configure.bat"
    else:
        configure_prog_name = "configure"
    qt_config_args = [
        join(cfg.qt_src_gitdir, configure_prog_name),
        # General options:
        "-I", openssl_include_root,  # OpenSSL
        "-L", openssl_lib_root,  # OpenSSL
        "-prefix", installdir,
        "-recheck-all",  # don't cache from previous configure runs
        "OPENSSL_LIBS=" + openssl_libs,
    ]
    if qt_linkage_static:
        qt_config_args.append("-static")
        # makes a static Qt library (cf. default of "-shared")
        # ... NB ALSO NEEDS "CONFIG += static" in the .pro file
        
    # In Qt 5.10 (as of 2017-11-21), "configure --list-features" does not
    # show "printing-and-pdf", unlike e.g. https://blog.basyskom.com/2017/qt-lite,  # noqa
    # but something in "configure" knows about it because it crashes when
    # creating qmake with "Project ERROR: Unknown feature object
    # printing-and-pdf in expression 'config.unix && features.printing-and-pdf'."  # noqa
    #
    # no, doesn't work: # qt_config_args += ["-no-feature-printing-and-pdf"]

    android_arch_short = "?"
    if target_platform.android:
        # We use a dynamic build of Qt (bundled into the APK), not a static
        # version; see android_compilation.txt
        if target_platform.cpu == Cpu.X86_32:
            android_arch_short = "x86"
        elif target_platform.cpu == Cpu.ARM_V7:
            android_arch_short = "armeabi-v7a"
        else:
            raise NotImplementedError("Don't know how to use CPU {!r} for "
                                      "Android".format(target_platform.cpu))
        qt_config_args += [
            "-android-sdk", cfg.android_sdk_root,
            "-android-ndk", cfg.android_ndk_root,
            "-android-ndk-host", cfg.android_ndk_host,
            "-android-arch", android_arch_short,
            "-android-toolchain-version", cfg.android_toolchain_version,
            "-xplatform", "android-g++",
        ]
    elif target_platform.linux:
        qt_config_args += [
            "-qt-xcb",  # use XCB source bundled with Qt?
            "-gstreamer", "1.0",  # gstreamer version; see troubleshooting below  # noqa
        ]
    elif target_platform.osx:
        pass
    elif target_platform.ios:
        # http://doc.qt.io/qt-5/building-from-source-ios.html
        # "A default build builds both the simulator and device libraries."
        qt_config_args += [
            "-xplatform", "macx-ios-clang"
        ]
    elif target_platform.windows:
        if BUILD_PLATFORM.linux:
            # Compare MXE's mxe/src/qt5.mk (for Qt 5.9.2), with # comments added  # noqa
            # ... NOT qt.mk, which is for Qt 4.x
            # See also qt5/qtbase/configure.json; e.g. search for "nomake" to see options  # noqa
            # https://stackoverflow.com/questions/22540239/what-would-be-a-pratical-example-of-sysroot-and-prefix-options-for-qt  # noqa
            _ = """
define $(PKG)_BUILD
    # ICU is buggy. See #653. TODO: reenable it some time in the future.
    cd '$(1)' && \
        OPENSSL_LIBS="`'$(TARGET)-pkg-config' --libs-only-l openssl`" \
        PSQL_LIBS="-lpq -lsecur32 `'$(TARGET)-pkg-config' --libs-only-l openssl pthreads` -lws2_32" \
        SYBASE_LIBS="-lsybdb `'$(TARGET)-pkg-config' --libs-only-l gnutls` -liconv -lws2_32" \
        PKG_CONFIG="${TARGET}-pkg-config" \
        PKG_CONFIG_SYSROOT_DIR="/" \
        PKG_CONFIG_LIBDIR="$(PREFIX)/$(TARGET)/lib/pkgconfig" \
        ./configure \
            -opensource \                                       # QT_CONFIG_COMMON_ARGS
            -confirm-license \                                  # QT_CONFIG_COMMON_ARGS
            -xplatform win32-g++ \                              # had already
            -device-option CROSS_COMPILE=${TARGET}- \           # had already
            -device-option PKG_CONFIG='${TARGET}-pkg-config' \  # added
            -pkg-config \                                       # added
            -force-pkg-config \                                 # added
            -no-use-gold-linker \                               # added
            -release \                                          # QT_CONFIG_COMMON_ARGS
            -static \                                           # see qt_linkage_static
            -prefix '$(PREFIX)/$(TARGET)/qt5' \
            -no-icu \                                           # added
            -opengl desktop \                                   # had already
            -no-glib \                                          # added
            -accessibility \                                    # is the default, but added anyway
            -nomake examples \                                  # QT_CONFIG_COMMON_ARGS
            -nomake tests \                                     # QT_CONFIG_COMMON_ARGS
            -plugin-sql-mysql \                                 # disabled in QT_CONFIG_COMMON_ARGS
            -mysql_config $(PREFIX)/$(TARGET)/bin/mysql_config \# plugin disabled in QT_CONFIG_COMMON_ARGS
            -plugin-sql-sqlite \
            -plugin-sql-odbc \                                  # disabled in QT_CONFIG_COMMON_ARGS
            -plugin-sql-psql \                                  # disabled in QT_CONFIG_COMMON_ARGS
            -plugin-sql-tds -D Q_USE_SYBASE \                   # disabled in QT_CONFIG_COMMON_ARGS
            -system-zlib \                                      # Qt version instead
            -system-libpng \                                    # Qt version instead
            -system-libjpeg \                                   # Qt version instead
            -system-sqlite \                                    # Qt version instead
            -fontconfig \                                       # added
            -system-freetype \                                  # added
            -system-harfbuzz \                                  # added
            -system-pcre \                                      # added
            -openssl-linked \                                   # see qt_openssl_linkage_static
            -dbus-linked \                                      # added
            -no-pch \                                           # added
            -v \                                                # see cfg.verbose
            $($(PKG)_CONFIGURE_OPTS)
            """  # noqa

            # https://stackoverflow.com/questions/10934683/how-do-i-configure-qt-for-cross-compilation-from-linux-to-windows-target  # noqa
            crosscomp = target_platform.cross_compile_prefix
            qt_config_args += [
                "-xplatform", "win32-g++",

                "-device-option", "CROSS_COMPILE=" + crosscomp,
                # ... the environment CROSS_COMPILE setting isn't enough

                # "-opengl", "dynamic",
                # ... or get: "fatal error: GLES2/gl2.h: No such file or directory"  # noqa
                "-opengl", "desktop",
                # ... or get: "fatal error: EGL/egl.h: No such file or directory"  # noqa

                # These as per MXE:
                "-device-option", "PKG_CONFIG={}pkg-config".format(crosscomp),
                "-pkg-config",
                "-force-pkg-config",
                "-no-use-gold-linker",
                "-no-icu",
                "-no-glib",
                "-accessibility",
                # "-fontconfig",
                "-qt-freetype",     # was system
                "-qt-harfbuzz",     # was system
                "-qt-pcre",         # was system
                "-no-dbus",         # don't need it
                "-no-pch",

                "-I", join(cfg.mxe_usr_dir, target_platform.mxe_target, "include")  # noqa
                # ... Qt translates this to "-isystem" rather than "-i" in the
                #     eventual call to the compiler
            ]
            # winsdk_basedir = "/home/rudolf/tmp/winsdk-10/Include/10.0.14393.0"
            # for d in ["km", "mmos", "shared", "ucrt", "um", "winrt"]:
            #     qt_config_args += ["-I", join(winsdk_basedir, d)]
            # Still not enough! Now needs vcruntime.h, etc...
            # raise NotImplementedError(CANNOT_CROSS_COMPILE_QT)

        elif BUILD_PLATFORM.windows:
            qt_config_args += []  # *** check

        else:
            raise NotImplementedError("Don't know how to compile Qt for "
                                      "Windows on {}".format(target_platform))

    else:
        raise NotImplementedError("Don't know how to compile Qt for " +
                                  str(target_platform))

    qt_config_args.extend(QT_CONFIG_COMMON_ARGS)

    # For testing a new OpenSSL build, have cfg.qt_openssl_static=False, or you
    # have to rebuild Qt every time... extremely slow.
    if qt_openssl_linkage_static:
        qt_config_args.append("-openssl-linked")  # OpenSSL
        # http://doc.qt.io/qt-4.8/ssl.html
        # http://stackoverflow.com/questions/20843180
    else:
        qt_config_args.append("-openssl")  # OpenSSL

    if cfg.verbose >= 1:
        qt_config_args.append("-v")  # verbose
    if cfg.verbose >= 2:
        qt_config_args.append("-v")  # more verbose

    # Fix other problems:

    if FIX_QT_5_9_2_CROSS_COMPILE_TOP_LEVEL_BUILD_BUG:
        # "You cannot configure qt separately within a top-level build."
        def check_bad_super_cache(bad_super_cache: str) -> None:
            if os.path.exists(bad_super_cache):
                fail(
                    "You must delete {!r} first, or Qt's 'configure' will "
                    "fail with the error 'Project ERROR: You cannot configure "
                    "qt separately within a top-level build.' (from "
                    "qtbase/mkspecs/features/qt_configure.prf, when it checks "
                    "_QMAKE_SUPER_CACHE_).".format(
                        bad_super_cache
                    )
                )

        check_bad_super_cache(os.path.expanduser("~/.qmake.super"))
        check_bad_super_cache(join(cfg.root_dir, ".qmake.super"))

    if target_platform.windows and BUILD_PLATFORM.linux:

        if FIX_QT_5_9_2_CROSS_COMPILE_EXECVP_MISSING_COMPILER_BUG:
            # "execvp: .obj/release/pcre2_auto_possess.o: Permission denied"
            # https://bugreports.qt.io/browse/QTBUG-63659
            # https://bugreports.qt.io/browse/QTBUG-63637
            win32_qmake_conf = join(cfg.qt_src_gitdir, "qtbase",
                                    "mkspecs", "win32-g++", "qmake.conf")
            add_line_if_absent(
                filename=win32_qmake_conf,
                line="QMAKE_LINK_OBJECT_MAX = 10"
            )
            add_line_if_absent(
                filename=win32_qmake_conf,
                line="QMAKE_LINK_OBJECT_SCRIPT = object_script"
            )
            # I think this bug also makes it use "g++" rather than
            # "x86_64-w64-mingw32.static-g++"!

            # Argh; much difficulty; probably this bug:
            # https://bugreports.qt.io/browse/QTBUG-62434
            # ... "configure/qmake fails when cross-compiling"
            # ... loses the CROSS_COMPILE variable
            # ... so solution: move to "5.10" Qt branch.

        if FIX_QT_5_9_2_W64_HOST_TOOL_WANTS_WINDOWS_H:
            # https://bugreports.qt.io/browse/QTBUG-38223
            _ = """
g++ -c -pipe -O2 -std=c++11 -fno-exceptions -Wall -W -D_REENTRANT -fPIC -DQT_NO_NARROWING_CONVERSIONS_IN_CONNECT -DQT_USE_QSTRINGBUILDER -DQT_NO_EXCEPTIONS -D_LARGEFILE64_SOURCE -D_LARGEFILE_SOURCE -DQT_NO_DEBUG -DQT_BOOTSTRAP_LIB -DQT_VERSION_STR='"5.10.0"' -DQT_VERSION_MAJOR=5 -DQT_VERSION_MINOR=10 -DQT_VERSION_PATCH=0 -DQT_BOOTSTRAPPED -DQT_NO_CAST_TO_ASCII -I/home/rudolf/dev/qt_local_build/src/qt5/qtactiveqt/src/tools/idc -I. -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtCore -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtCore/5.10.0 -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtCore/5.10.0/QtCore -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtXml -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtXml/5.10.0 -I/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtXml/5.10.0/QtXml -I/home/rudolf/dev/qt_local_build/src/qt5/qtbase/mkspecs/linux-g++ -o .obj/main.o /home/rudolf/dev/qt_local_build/src/qt5/qtactiveqt/src/tools/idc/main.cpp
In file included from /home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtCore/qt_windows.h:1:0,
                 from /home/rudolf/dev/qt_local_build/src/qt5/qtactiveqt/src/tools/idc/main.cpp:33:
/home/rudolf/dev/qt_local_build/qt_windows_x86_64_build/qtbase/include/QtCore/../../../../src/qt5/qtbase/src/corelib/global/qt_windows.h:64:21: fatal error: windows.h: No such file or directory
"""  # noqa
            qt_config_args += ["-skip", "qtactiveqt"]

    # -------------------------------------------------------------------------
    # configure
    # -------------------------------------------------------------------------
    with pushd(builddir):
        try:
            run(qt_config_args, env)  # The configure step takes a few seconds.
        except subprocess.CalledProcessError:
            log.critical("""
===============================================================================
Troubleshooting Qt 'configure' failures
===============================================================================

-   gstreamer (used for Unix audio etc.)
    gstreamer version 1.0 version (for Unix) requires:
        sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
    ... NB some things try to remove it, it seems! (Maybe autoremove?)

-   Qt configure can't find make or gmake in PATH...

    If they are in the PATH, then check permissions on
          qtbase/config.tests/unix/which.test
    ... if not executable, permissions have been altered wrongly.

-   NB actual configure scripts are, from local build directory:
        .../src/qt5/configure
        .../src/qt5/configure/qtbase/configure
        .../src/qt5/configure/qtbase/configure.json

-   "recipe for target 'sub-plugins-make_first' failed", or similar:

    If configure fails, try more or less verbose (--verbose 0, --verbose 2) and
    also try "--nparallel 1" so you can see which point is failing more
    clearly. This is IMPORTANT or other error messages incorrectly distract
    you.

""")
            raise

    # -------------------------------------------------------------------------
    # make (can take several hours)
    # -------------------------------------------------------------------------
    log.info("Making Qt {} build into {}".format(target_platform.description,
                                                 installdir))
    with pushd(builddir):
        # run(cfg.make_args(command="qmake_all"), env)
        try:
            run(cfg.make_args(), env)
        except subprocess.CalledProcessError:
            log.critical("""
===============================================================================
Troubleshooting Qt 'make' failures
===============================================================================

Q.  If this is the first time you've had this error...
A.  RE-RUN THE SCRIPT; sometimes Qt builds fail then pick themselves up the 
    next time.
""")  # noqa
            _ = """
Q.  fatal error: uiviewsettingsinterop.h: No such file or directory
A.  Looks tricky:
    https://forum.qt.io/topic/76092/unable-to-compile-qt5-8-with-mingw-64-bit-compiler/4

Q.  fatal error: vcruntime.h: No such file or directory
A.  !!! does MXE build, and if so, can we copy it?
    !!! https://stackoverflow.com/questions/14170590/building-qt-5-on-linux-for-windows
            """
            raise

    # -------------------------------------------------------------------------
    # make install
    # -------------------------------------------------------------------------
    if target_platform.android and FIX_QT_5_7_0_ANDROID_MAKE_INSTALL_BUG:
        # PROBLEM WITH "make install":
        #       mkdir: cannot create directory ‘/libs’: Permission denied
        # ... while processing qttools/src/qtplugininfo/Makefile
        # https://bugreports.qt.io/browse/QTBUG-45095
        # 1. Attempt to fix as follows:
        makefile = join(builddir, "qttools", "src", "qtplugininfo", "Makefile")
        baddir = join("$(INSTALL_ROOT)", "libs", android_arch_short, "")
        gooddir = join(installdir, "libs", android_arch_short, "")
        replace_in_file(makefile, " " + baddir, " " + gooddir)

    # 2. Using INSTALL_ROOT: bases the root of a filesystem off installdir
    # env["INSTALL_ROOT"] = installdir
    # http://stackoverflow.com/questions/8360609

    with pushd(builddir):
        run(cfg.make_args(command="install"), env)
    # ... installs to installdir because of -prefix earlier
    return installdir


def make_missing_libqtforandroid_so(cfg: Config,
                                    target_platform: Platform) -> None:
    qt_install_dir = cfg.qt_install_dir(target_platform)
    parent_dir = join(qt_install_dir, "plugins", "platforms")
    starting_lib_dir = join(parent_dir, "android")
    static_ext = target_platform.static_lib_ext
    starting_a_lib = join(starting_lib_dir, "libqtforandroid" + static_ext)
    newlib_path = cfg.convert_android_lib_a_to_so(starting_a_lib,
                                                  target_platform)
    _, newlib_basename = split(newlib_path)
    extra_copy_newlib = join(parent_dir, newlib_basename)
    shutil.copyfile(newlib_path, extra_copy_newlib)


# =============================================================================
# SQLCipher
# =============================================================================

def fetch_sqlcipher(cfg: Config) -> None:
    """
    Downloads SQLCipher source code.
    """
    git_clone(prettyname="SQLCipher",
              url=cfg.sqlcipher_git_url,
              commit=cfg.sqlcipher_git_commit,
              directory=cfg.sqlcipher_src_gitdir,
              clone_options=["--config", "core.autocrlf=false"])
    # We must have LF endings, not CR+LF, because we're going to use Unix tools
    # even under Windows.


def build_sqlcipher(cfg: Config, target_platform: Platform) -> None:
    """
    Builds SQLCipher, an open-source encrypted version of SQLite.
    Our source is the public version; our destination is an "amalgamation"
    .h and .c file (equivalent to the amalgamation sqlite3.h and sqlite3.c
    of SQLite itself). Actually, they have the same names, too.
    
    CROSS-COMPILATION OF SQLITE/SQLCIPHER:
    [1] https://vicente-hernando.appspot.com/sqlite3-cross-compile-arm-howto
    [2] https://discuss.zetetic.net/t/cross-compile-sqlicipher-for-arm/2104
    [3] https://github.com/sqlcipher/sqlcipher/issues/176
    """

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------
    destdir = join(cfg.root_dir,
                   "sqlcipher_" + target_platform.dirpart,
                   "sqlcipher")  # this allows #include <sqlcipher/sqlite3.h>

    target_h = join(destdir, "sqlite3.h")
    target_c = join(destdir, "sqlite3.c")
    target_o = join(destdir, "sqlite3" + target_platform.obj_ext)
    target_exe = join(destdir, "sqlcipher")

    want_exe = not target_platform.mobile and not BUILD_PLATFORM.windows

    all_targets = [target_c, target_h, target_o]
    if want_exe:
        all_targets.append(target_exe)
    if all(isfile(x) for x in all_targets):
        log.info("SQLCipher: all targets present; skipping ({})".format(
            all_targets))
        return

    log.info("Building SQLCipher...")
    copytree(cfg.sqlcipher_src_gitdir, destdir, destroy=True)

    # -------------------------------------------------------------------------
    # configure args
    # -------------------------------------------------------------------------
    _, openssl_workdir = cfg.get_openssl_rootdir_workdir(target_platform)
    openssl_include_dir = join(openssl_workdir, "include")
    
    # Compiler:
    cflags = [
        "-DSQLITE_HAS_CODEC",
        "-I{}".format(openssl_include_dir),
        # ... sqlite.c does e.g. "#include <openssl/rand.h>"
    ]
    if BUILD_PLATFORM.windows:
        # We have set our environment so CC points to cl, not gcc.
        gccflags = []  # type: List[str]
    else:
        gccflags = [
            "-Wfatal-errors",  # all errors are fatal
        ]
    clflags = []  # type: List[str]
    # if cfg.verbose >= 2:
    #     clflags.append("/showIncludes")
    
    # Linker:
    ldflags = ["-L{}".format(openssl_workdir)]

    link_openssl_statically = target_platform.desktop
    # ... try for dynamic linking on Android
    if link_openssl_statically:
        log.info("Linking OpenSSL into SQLCipher STATICALLY")
        static_ext = target_platform.static_lib_ext
        static_openssl_lib = join(openssl_workdir, "libcrypto" + static_ext)
        # Not working:
        # ldflags.append("-static")
        # ldflags.append("-l:libcrypto.a")
        # ... Note the colon! Search for ":filename" in "man ld"
        #
        # Try this:
        ldflags.append(static_openssl_lib)
        # ... https://github.com/sqlcipher/sqlcipher
    else:
        log.info("Linking OpenSSL into SQLCipher DYNAMICALLY")
        # make the executable load OpenSSL dynamically
        ldflags.append('-lcrypto')
    # Note that "--with-crypto-lib" isn't helpful here:
    # https://www.zetetic.net/blog/2013/6/27/sqlcipher-220-release.html

    trace_include = False
    if trace_include:
        cflags.append("-H")
    if target_platform.android:
        cflags.append("--sysroot={}".format(
            cfg.android_sysroot(target_platform)))
        # ... or configure will call ld which will say:
        # ld: error: cannot open crtbegin_dynamic.o: No such file or directory

    if BUILD_PLATFORM.windows:
        require(BASH)
        require(LD)
        config_args = [BASH]
        # if cfg.verbose >= 2:
        #     config_args.append("-x")  # echo each command
        # ... instead, check config.log; it's much clearer
    else:
        config_args = []  # type: List[str]
    config_args += [
        join(destdir, "configure"),
        "--enable-tempstore=yes",
        # ... see README.md; equivalent to SQLITE_TEMP_STORE=2
        # no quotes (they're fine on the command line but not here):
        'CFLAGS={}'.format(" ".join(cflags + gccflags)),
        'LDFLAGS={}'.format(" ".join(ldflags)),
    ]
    # By default, SQLCipher compiles with "-O2" optimizations under gcc; see
    # its "configure" script.

    # Platform-specific tweaks; cross-compilation.
    # The CROSS_COMPILE prefix doesn't appear in any files, so is presumably
    # not supported, but "--build" and "--host" are used (where "host" means
    # "target").

    env = get_starting_env()
    cfg.set_compile_env(env, target_platform, use_cross_compile_var=False)

    # env["LD_LIBRARY_PATH"] = openssl_workdir  # Linux
    # env["DYLD_LIBRARY_PATH"] = openssl_workdir  # OS/X
    # env["DYLD_FALLBACK_LIBRARY_PATH"] = openssl_workdir  # OS/X

    config_args.append("--build={}".format(
        BUILD_PLATFORM.sqlcipher_platform))
    config_args.append("--host={}".format(
        target_platform.sqlcipher_platform))

    # config_args.append("--prefix={}".format(cfg.android_sysroot(platform)))
    # if target_platform.android:
    #     config_args.append("CC=" + cfg.android_cc(target_platform))
    #     # ... or we won't be cross-compiling

    # -------------------------------------------------------------------------
    # configure
    # -------------------------------------------------------------------------
    with pushd(destdir):
        run(config_args, env)

    # -------------------------------------------------------------------------
    # make
    # -------------------------------------------------------------------------
    with pushd(destdir):
        # Don't use cfg.make_args(); we want "make" even under Windows (via
        # Cygwin).
        require(MAKE)
        require(TCLSH)
        if not isfile(target_c) or not isfile(target_h):
            # Under Windows, if we were to use cl rather than gcc, e.g. by
            # setting env["CC"], it fails because the make environment uses
            # Unix-style paths. So we let it use gcc.
            run([MAKE, "sqlite3.c"], env)  # the amalgamation target  # noqa
        if not isfile(target_exe) or not isfile(target_o):
            if BUILD_PLATFORM.windows:
                # If we run make, it'll now call gcc but all sorts of Windows-
                # specific stuff will be missing; see
                # https://github.com/sqlcipher/sqlcipher/issues/206
                cl_executable = which_with_envpath(CL, env)
                run([
                    cl_executable,
                    "/c",  # compile without linking
                    "sqlite3.c"
                ] + cflags + clflags, env)
            else:
                run([MAKE, "sqlite3.o"], env)  # for static linking
        if want_exe and not isfile(target_exe):
            run([MAKE, "sqlcipher"], env)  # the command-line executable

    # -------------------------------------------------------------------------
    # Check and report
    # -------------------------------------------------------------------------
    target_platform.verify_lib(target_o)

    log.info("If successful, you should have the amalgation files:\n"
             "- {}\n"
             "- {}\n"
             "and the library:\n"
             "- {}\n"
             "and, on non-mobile platforms, the executable:\n"
             "- {}".format(target_c, target_h, target_o, target_exe))


# =============================================================================
# Boost
# =============================================================================

def fetch_boost(cfg: Config) -> None:
    """
    Downloads Boost source code.
    """
    download_if_not_exists(cfg.boost_src_url, cfg.boost_src_fullpath)


def build_boost(cfg: Config) -> None:
    """
    Unpacks Boost from source.
    Try to avoid anything needing compilation; if we can keep this to
    "headers-only" Boost, it will be cross-platform without further effort.
    """
    untar_to_directory(cfg.boost_src_fullpath, cfg.boost_dest_dir)


# =============================================================================
# Armadillo
# =============================================================================

def fetch_armadillo(cfg: Config) -> None:
    """
    Downloads Armadillo source code.
    There's also a Git repository at
        https://github.com/conradsnicta/armadillo-code
    but the download is the verified static snapshot.
    """
    download_if_not_exists(cfg.arma_src_url, cfg.arma_src_fullpath)


def build_armadillo(cfg: Config) -> None:
    untar_to_directory(cfg.arma_src_fullpath, cfg.arma_dest_dir)
    # run([CMAKE,
    #      # "-D", "ARMADILLO_LIBRARY={}".format(cfg.arma_lib),
    #      "-D", "ARMADILLO_INCLUDE_DIR={}".format(cfg.arma_include_dir),
    #      cfg.arma_working_dir])
    # run([MAKE, "-C", cfg.arma_working_dir])


# =============================================================================
# MLPACK
# =============================================================================

def fetch_mlpack(cfg: Config) -> None:
    """
    Downloads MLPACK source code.
    """
    git_clone(prettyname="MLPACK",
              url=cfg.mlpack_git_url,
              commit=cfg.mlpack_git_commit,
              directory=cfg.mlpack_src_gitdir)


def build_mlpack(cfg: Config) -> None:
    """
    Without building, there is no <mlpack/mlpack_export.hpp>
    
    We run cmake for MLPACK, telling it where Armadillo lives.
    
    If you get this:
        CMake Error at CMake/NewCXX11.cmake:4 (target_compile_features):
        target_compile_features no known features for CXX compiler
        "GNU"
    ... update cmake from 3.5.1
        https://stackoverflow.com/questions/38027292/configure-a-qt5-5-7-application-for-android-with-cmake
        https://bugreports.qt.io/browse/QTBUG-54666
    ... note that CMake 3.7.0 is the first to support Android cross-
        compilation, too
    ... e.g. from https://launchpad.net/ubuntu/+source/cmake
        ... hard to install.
        ... first >=3.7.0 is Ubuntu zesty
        ... no backports to xenial
        ... "pinning"
        ... or just manually install .deb files:
        
        sudo dpkg --install \
            cmake_3.7.2-1_amd64.deb \
            cmake-data_3.7.2-1_all.deb \
            libjsoncpp1_1.7.4-3_amd64.deb

        from
            https://launchpad.net/ubuntu/+source/cmake
            https://packages.ubuntu.com/zesty/libjsoncpp1
            
    ... no, still get error; aha:
        https://github.com/mlpack/mlpack/issues/796
    ... see CMAKE_CXX_FLAGS below
        ... no, would need more hacking of the CMakeLists.txt
    ... aha! Define FORCE_CXX11=1

    """  # noqa
    delete_cmake_cache(cfg.mlpack_src_gitdir)
    cmakelists = join(cfg.mlpack_src_gitdir, "CMakeLists.txt")
    replacements = [
        # The supplied version hard-codes the Boost versions (as of 2017-06-06,
        # to versions 1.49.0 through 1.55.0), asking for 1.49.
        (
            '''set(Boost_ADDITIONAL_VERSIONS
  "1.49.0" "1.50.0" "1.51.0" "1.52.0" "1.53.0" "1.54.0" "1.55.0")''',
            'set(Boost_ADDITIONAL_VERSIONS "{}")'.format(cfg.boost_version)
        ),
        # Note that FindBoost.cmake looks for
        #       boost_program_options
        #       boost_unit_test_framework
        #       boost_serialization
        # as libraries (and they require Boost compilation)...
        # ... BECAUSE they are marked as REQUIRED by MLPACK's CMakeLists.txt
        # We shouldn't need them, so as well as changing the Boost version,
        # we can remove the requirement:
        (
            """find_package(Boost 1.49
    COMPONENTS
      program_options
      unit_test_framework
      serialization
    REQUIRED
)""",
            "find_package(Boost {})".format(cfg.boost_version)
        ),
    ]
    replace_multiple_in_file(cmakelists, replacements)
    log.info("CMake version:")
    with pushd(cfg.mlpack_src_gitdir):
        run([CMAKE, "--version"])
        run([
            CMAKE,
            #  "-D", "ARMADILLO_LIBRARY={}".format(cfg.arma_lib),
            "-D", "ARMADILLO_INCLUDE_DIR={}".format(cfg.arma_include_dir),
            "-D", "BOOST_ROOT={}".format(cfg.boost_root),
            "-D", "BOOST_INCLUDEDIR={}".format(cfg.boost_include_dir),
            "-D", "BOOST_LIBRARYDIR={}".format(cfg.boost_library_dir),
            # "-D", "CMAKE_CXX_FLAGS=-I/usr/local/opt/llvm/include -std=c++11",
            "-D", "FORCE_CXX11=1"
            # "-D", "Boost_DEBUG=ON",  # tell FindBoost.cmake to be verbose
            # "-L",  # list variables
            # "--debug-output",
            # "--trace-expand",  # very verbose
            "-Wno-dev",  # turn off some warnings
            cfg.mlpack_src_gitdir
        ])


# =============================================================================
# Eigen
# =============================================================================

def fetch_eigen(cfg: Config) -> None:
    """
    Downloads Eigen.
    http://eigen.tuxfamily.org
    """
    download_if_not_exists(cfg.eigen_src_url, cfg.eigen_src_fullpath)


def build_eigen(cfg: Config) -> None:
    """
    'Build' simply means 'unpack' -- header-only template library.
    """
    untar_to_directory(tarfile=cfg.eigen_src_fullpath,
                       directory=cfg.eigen_unpacked_dir,
                       gzipped=True)


# =============================================================================
# jom: parallel make tool for Windows
# =============================================================================

# def fetch_jom(cfg: Config) -> None:
#     """
#     Downloads jom
#     http://wiki.qt.io/Jom
#     """
#     git_clone(prettyname="jom",
#               url=cfg.jom_git_url,
#               directory=cfg.jom_src_gitdir)


# # noinspection PyUnusedLocal
# def build_jom(cfg: Config) -> None:
#     """
#     Builds jom, the parallel make tool for Windows.
#     See http://code.qt.io/cgit/qt-labs/jom.git/tree/README
#     """
#     if not BUILD_PLATFORM.windows:
#         log.critical("don't know how to build jom yet (NB it's a Qt program")
#         raise NotImplementedError()
#     if isfile(cfg.jom_executable):
#         log.info("Already have {!r}; no need to build jom".format(
#             cfg.jom_executable))
#         return
#     env = os.environ.copy()
#     cfg.set_compile_env(env, BUILD_PLATFORM)
#     with pushd(cfg.jom_src_gitdir):
#         qmake = BUILD_PLATFORM.prebuilt_qmake(cfg)
#         nmake = BUILD_PLATFORM.nmake(cfg)
#         require(qmake)
#         require(nmake)
#         run([qmake, "-r"], env)
#         run([nmake], env)


# =============================================================================
# MXE: cross-compilation environment for Linux hosts
# =============================================================================

def fetch_mxe(cfg: Config) -> None:
    """
    Downloads MXE
    http://mxe.cc/
    """
    git_clone(prettyname="MXE",
              url=cfg.mxe_git_url,
              directory=cfg.mxe_src_gitdir)


def build_mxe(cfg: Config, target_platform: Platform,
              debug_make: bool = False,
              build_qt_as_test: bool = False) -> None:
    """
    Builds MXE. (This is a prerequisite to using MXE to build something else!)
    """
    if BUILD_PLATFORM.debian:
        require_debian_packages(
            "autoconf automake autopoint bash bison bzip2 flex gettext "
            "git g++ gperf intltool libffi-dev libgdk-pixbuf2.0-dev "
            "libtool-bin libltdl-dev libssl-dev libxml-parser-perl make "
            "openssl p7zip-full patch perl pkg-config python ruby scons "
            "sed unzip wget xz-utils".split()
        )
        if BUILD_PLATFORM.cpu_64bit:
            require_debian_packages(
                "g++-multilib libc6-dev-i386".split()
            )
    cmdargs = [
        MAKE,
        "-j", str(cfg.nparallel),
    ]
    if debug_make:
        cmdargs.append("--debug=b")
    cmdargs += [
        "MXE_TARGETS=" + target_platform.mxe_target,
        # "qt5",
        # ... we're trying not to NEED that, so if you remove that
        # command, add in the qt5 dependencies (see qt5.mk in MXE):
        "gcc", "dbus", "freetds", "jpeg", "libmng", "libpng",
        "openssl", "postgresql", "sqlite", "tiff", "zlib",
    ]
    if build_qt_as_test:
        cmdargs.append("qt5")  # Qt 5 (all of it)
    with pushd(cfg.mxe_src_gitdir):
        try:
            run(cmdargs)
        except subprocess.CalledProcessError:
            log.critical(r"""
===============================================================================
Troubleshooting MXE 'make' failures
===============================================================================

Q.  "Missing requirements"
    OR "recipe for target '.../src/mxe/usr/i686-w64-mingw32.static/installed/
    fontconfig' failed"
A.  Debian:

        apt-get install \
            autoconf automake autopoint bash bison bzip2 flex gettext \
            git g++ gperf intltool libffi-dev libgdk-pixbuf2.0-dev \
            libtool-bin libltdl-dev libssl-dev libxml-parser-perl make \
            openssl p7zip-full patch perl pkg-config python ruby scons \
            sed unzip wget xz-utils
        
    Debian 64-bit:
    
        apt-get install g++-multilib libc6-dev-i386
        
    See http://mxe.cc/#requirements

""")
            raise


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """
    Main entry point.
    """
    # -------------------------------------------------------------------------
    # Command-line arguments
    # -------------------------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="Build Qt and other libraries for CamCOPS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # General
    general = parser.add_argument_group("General", "General options")
    default_root_dir = os.environ.get(ENVVAR_QT_BASE) or DEFAULT_ROOT_DIR
    general.add_argument(
        "--show_config_only", action="store_true",
        help="Show config, then quit")
    general.add_argument(
        "--root_dir", default=default_root_dir,
        help=(
            "Root directory for source and builds (default taken from "
            "environment variable {} if present)".format(ENVVAR_QT_BASE)
        )
    )
    general.add_argument(
        "--nparallel", type=int, default=multiprocessing.cpu_count(),
        help="Number of parallel processes to run")
    general.add_argument("--force", action="store_true", help="Force build")
    general.add_argument(
        "--verbose", "-v", type=int, default=0, choices=[0, 1, 2],
        help="Verbosity level")

    # Architectures
    archgroup = parser.add_argument_group(
        "Architecture",
        "Choose architecture for which to build")
    archgroup.add_argument(
        "--build_all", action="store_true",
        help="Build for all architectures supported on this host ({})".format(
            BUILD_PLATFORM)
    )
    archgroup.add_argument(
        "--build_android_x86_32", action="store_true",
        help="An architecture target (Android under an "
             "Intel x86 32-bit emulator)")
    archgroup.add_argument(
        "--build_android_arm_v7_32", action="store_true",
        help="An architecture target (Android under a ARM processor tablet)")
    archgroup.add_argument(
        "--build_linux_x86_64", action="store_true",
        help="An architecture target (native Linux with a 64-bit Intel/AMD "
             "CPU; check with 'lscpu' and 'uname -a'")
    archgroup.add_argument(
        "--build_osx_x86_64", action="store_true",
        help="An architecture target (Mac OS/X under an Intel 64-bit CPU; "
             "check with 'sysctl -a|grep cpu', and see "
             "https://support.apple.com/en-gb/HT201948 )")
    archgroup.add_argument(
        "--build_windows_x86_64", action="store_true",
        help="An architecture target (Windows with an Intel/AMD 64-bit CPU)"
    )
    archgroup.add_argument(
        "--build_windows_x86_32", action="store_true",
        help="An architecture target (Windows with an Intel/AMD 32-bit CPU)"
    )
    archgroup.add_argument(
        "--build_ios", action="store_true",
        help="An architecture target (iOS with a 64-bit ARM processor)"
    )
    archgroup.add_argument(
        "--build_ios_simulator", action="store_true",
        help="An architecture target (iOS with an Intel 64-bit CPU, for the "
             "iOS simulator)"
    )

    # Qt
    qt = parser.add_argument_group(
        "Qt",
        "Qt options [Qt must be built from source for SQLite support, and "
        "also if static OpenSSL linkage is desired; note that static OpenSSL "
        "linkage requires a Qt rebuild (slow!) if you rebuild OpenSSL]")
    qt.add_argument(
        "--qt_src_dirname", default=DEFAULT_QT_SRC_DIRNAME,
        help="Qt source directory")
    qt.add_argument(
        "--qt_git_url", default=DEFAULT_QT_GIT_URL,
        help="Qt Git URL")
    qt.add_argument(
        "--qt_git_branch", default=DEFAULT_QT_GIT_BRANCH,
        help="Qt Git branch")
    qt.add_argument(
        "--qt_git_commit", default=DEFAULT_QT_GIT_COMMIT,
        help="Qt Git commit")
    qt.add_argument(
        "--qt_openssl_static", dest="qt_openssl_static", action="store_true",
        help="Link OpenSSL statically (ONLY if Qt is statically linked) "
             "[True=static, False=dynamic]")
    qt.add_argument(
        "--qt_openssl_linked", dest="qt_openssl_static", action="store_false",
        help="Link OpenSSL dynamically [True=static, False=dynamic]")
    parser.set_defaults(qt_openssl_static=DEFAULT_QT_USE_OPENSSL_STATICALLY)

    # Android
    android = parser.add_argument_group(
        "Android",
        "Android options (NB you must install the Android SDK and NDK "
        "separately, BEFOREHAND)")
    android.add_argument(
        "--android_api_number", type=int, default=DEFAULT_ANDROID_API_NUM,
        help="Android API number")
    android.add_argument(
        "--android_sdk_root", default=DEFAULT_ANDROID_SDK,
        help="Android SDK root directory")
    android.add_argument(
        "--android_ndk_root", default=DEFAULT_ANDROID_NDK,
        help="Android NDK root directory")
    android.add_argument(
        "--android_ndk_host", default=DEFAULT_NDK_HOST,
        help="Android NDK host architecture")
    android.add_argument(
        "--android_toolchain_version", default=DEFAULT_TOOLCHAIN_VERSION,
        help="Android toolchain version")

    # iOS
    ios = parser.add_argument_group("iOS", "iOS options")
    ios.add_argument(
        "--ios_sdk", default="",
        help="iOS SDK to use (leave blank for system default)"
    )

    # OpenSSL
    openssl = parser.add_argument_group(
        "OpenSSL",
        "OpenSSL options [OpenSSL must be built from source to use it on "
        "Android; Qt needs OpenSSL somehow; CamCOPS uses OpenSSL]")
    openssl.add_argument(
        "--openssl_version", default=DEFAULT_OPENSSL_VERSION,
        help="OpenSSL version")
    openssl.add_argument(
        "--openssl_src_url", default=DEFAULT_OPENSSL_SRC_URL,
        help="OpenSSL source URL")
    openssl.add_argument(
        "--openssl_android_script_url",
        default=DEFAULT_OPENSSL_ANDROID_SCRIPT_URL,
        help="OpenSSL Android script source (URL) (not really unused)"
    )
    
    # SQLCipher
    sqlcipher = parser.add_argument_group(
        "SQLCipher",
        "SQLCipher options [CamCOPS uses SQLCipher]")
    sqlcipher.add_argument(
        "--sqlcipher_git_url", default=DEFAULT_SQLCIPHER_GIT_URL,
        help="SQLCipher Git URL")
    sqlcipher.add_argument(
        "--sqlcipher_git_commit", default=DEFAULT_SQLCIPHER_GIT_COMMIT,
        help="SQLCipher Git commit")

    # Boost (used by MLPACK)
    if USE_BOOST:
        boost = parser.add_argument_group(
            "Boost",
            "Boost C++ library options [MLPACK uses Boost]")
        boost.add_argument(
            "--boost_version", default=DEFAULT_BOOST_VERSION,
            help="Armadillo version")
        boost.add_argument(
            "--boost_src_url", default=DEFAULT_BOOST_SRC_URL,
            help="Armadillo source URL")

    # Armadillo (used by MLPACK)
    if USE_ARMADILLO:
        armadillo = parser.add_argument_group(
            "Armadillo",
            "Armadillo C++ library options [MLPACK uses Armadillo]")
        armadillo.add_argument(
            "--arma_version", default=DEFAULT_ARMA_VERSION,
            help="Armadillo version")
        armadillo.add_argument(
            "--arma_src_url", default=DEFAULT_ARMA_SRC_URL,
            help="Armadillo source URL")

    # MLPACK
    if USE_MLPACK:
        mlpack = parser.add_argument_group(
            "MLPACK",
            "MLPACK C++ library options [CamCOPS uses MLPACK]")
        mlpack.add_argument(
            "--mlpack_git_url", default=DEFAULT_MLPACK_GIT_URL,
            help="MLPACK Git URL")
        mlpack.add_argument(
            "--mlpack_git_commit", default=DEFAULT_MLPACK_GIT_COMMIT,
            help="MLPACK Git commit")
        mlpack.add_argument(
            "--build_mlpack", action="store_true",
            help="MLPACK: build (in isolation)")

    # Eigen
    if USE_EIGEN:
        eigen = parser.add_argument_group(
            "Eigen",
            "Eigen C++ template library [CamCOPS uses Eigen]")
        eigen.add_argument(
            "--eigen_version", default=DEFAULT_EIGEN_VERSION,
            help="Eigen version")

    # jom
    jom = parser.add_argument_group(
        "jom",
        "'jom' parallel make tool for Windows"
    )
    jom.add_argument(
        "--jom_executable", default=r"C:\Qt\Tools\QtCreator\bin\jom.exe",
        help="jom executable (typically installed with QtCreator)"
        
    )
    
    windows = parser.add_argument_group(
        "Windows",
        "Options for Windows"
    )
    windows.add_argument(
        "--windows_prebuilt_qt_root", default=r"C:\Qt\5.6",
        help="Root directory of pre-built Qt installation"
    )
    windows.add_argument(
        "--windows_sdk_version", default="8.1",
        help="Windows SDK version (e.g. '8.1', '10.0.10240.0')"
    )

    # MXE
    mxe = parser.add_argument_group(
        "MXE",
        "MXE cross-compilation environment for Linux hosts"
    )
    mxe.add_argument(
        "--mxe_git_url", default=DEFAULT_MXE_GIT_URL,
        help="MXE Git URL"
    )

    args = parser.parse_args()  # type: argparse.Namespace

    # Logging
    loglevel = logging.DEBUG if args.verbose >= 1 else logging.INFO
    if main_only_quicksetup_rootlogger:
        main_only_quicksetup_rootlogger(level=loglevel)
    else:
        logging.basicConfig(level=loglevel, format=LOG_FORMAT,
                            datefmt=LOG_DATEFMT)

    # Calculated args

    cfg = Config(args)
    log.debug("Args: {}".format(args))
    log.debug("Config: {}".format(cfg))
    log.info("Running on {}".format(BUILD_PLATFORM))

    if cfg.show_config_only:
        sys.exit(0)

    # =========================================================================
    # Test the environment passing
    # =========================================================================
    # run(["/usr/local/bin/shared/print_params_and_env_then_abort", "hello",
    #      "world"])  # full environment passed through
    # run(["/usr/local/bin/shared/print_params_and_env_then_abort", "hello",
    #      "world"], env={"SOMEVAR": "someval"})  # only what Bash added

    # =========================================================================
    # Common requirements
    # =========================================================================
    require(CMAKE)
    require(GIT)
    require(PERL)
    require(TAR)
    if BUILD_PLATFORM.windows:
        require(VCVARSALL)
    BUILD_PLATFORM.ensure_elf_reader()

    # =========================================================================
    # Fetch
    # =========================================================================
    fetch_qt(cfg)
    fetch_openssl(cfg)
    fetch_sqlcipher(cfg)
    if USE_BOOST:
        fetch_boost(cfg)
    if USE_ARMADILLO:
        fetch_armadillo(cfg)
    if USE_MLPACK:
        fetch_mlpack(cfg)
    if USE_EIGEN:
        fetch_eigen(cfg)
    # if BUILD_PLATFORM.windows:
    #     fetch_jom(cfg)
    if USE_MXE and BUILD_PLATFORM.linux:
        fetch_mxe(cfg)

    # =========================================================================
    # Build
    # =========================================================================

    if USE_BOOST:
        build_boost(cfg)
    if USE_ARMADILLO:
        build_armadillo(cfg)
    if USE_MLPACK:
        build_mlpack(cfg)
    if USE_EIGEN:
        build_eigen(cfg)
    # if BUILD_PLATFORM.windows:
    #     build_jom(cfg)

    installdirs = []
    done_extra = False

    # noinspection PyShadowingNames
    def build_for(os: str, cpu: str) -> None:
        target_platform = Platform(os, cpu)
        if USE_MXE and BUILD_PLATFORM.linux and target_platform.windows:
            build_mxe(cfg, target_platform)
        log.info("Building Qt [+SQLite/SQLCipher +OpenSSL] for {}".format(
            target_platform))
        build_openssl(cfg, target_platform)
        installdirs.append(
            build_qt(cfg, target_platform)
        )
        if target_platform.android and ADD_SO_VERSION_OF_LIBQTFORANDROID:
            make_missing_libqtforandroid_so(cfg, target_platform)
        build_sqlcipher(cfg, target_platform)
        
    if cfg.build_android_x86_32:  # for x86 Android emulator
        build_for(Os.ANDROID, Cpu.X86_32)

    if cfg.build_android_arm_v7_32:  # for native Android
        build_for(Os.ANDROID, Cpu.ARM_V7)

    if cfg.build_linux_x86_64:  # for 64-bit Linux
        build_for(Os.LINUX, Cpu.X86_64)

    if cfg.build_osx_x86_64:  # for 64-bit Intel Mac OS/X
        build_for(Os.OSX, Cpu.X86_64)
        
    if cfg.build_windows_x86_64:
        build_for(Os.WINDOWS, Cpu.X86_64)

    if cfg.build_windows_x86_32:
        if BUILD_PLATFORM.linux and MXE_HAS_GCC_WITH_I386_BUG:
            fail("""
Can't build for Win32. Error will be:
    internal compiler error: in ix86_compute_frame_layout, at config/i386/i386.c:10145

Compiler bug is:
    https://sourceforge.net/p/mingw-w64/bugs/544/
    ... due to: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=71864
    
... needs MXE to support a more recent version of mingw-w64 and in turn a more 
    recent version of gcc
""")  # noqa
        build_for(Os.WINDOWS, Cpu.X86_32)

    if cfg.build_ios:
        build_for(Os.IOS, Cpu.ARM_V8_64)

    if cfg.build_ios_simulator:
        build_for(Os.IOS, Cpu.X86_64)

    if not installdirs and not done_extra:
        log.warning("Nothing more to do. Run with --help argument for help.")
        sys.exit(1)

    log.info("""
===============================================================================
Now, in Qt Creator:
===============================================================================
1. Add Qt build
      Tools > Options > Build & Run > Qt Versions > Add
      ... browse to one of: {bindirs}
      ... and select "qmake".
2. Create kit
      Tools > Options > Build & Run > Kits > Add (manual)
      ... Qt version = the one you added in the preceding step
      ... compiler =
            for Android: Android GCC (i686-4.9)
      ... debugger =
            for Android: Android Debugger for GCC (i686-4.9)
Then for your project,
      - click on the "Projects" tab
      - Add Kit > choose the kit you created.
      - For Android:
        - Build Settings > Android APK > Details > Additional Libraries > Add

BUILD / RUNTIME REQUIREMENTS

- For Ubuntu, see compilation_linux.txt

- To build Android programs under Linux, also need:

    sudo apt install openjdk-8-jdk

- For debugging, consider:

    sudo apt install valgrind

    """.format(  # noqa
        bindirs=", ".join(join(x, "bin") for x in installdirs)
    ))
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        log.critical("External process failed:")
        traceback.print_exc()
        sys.exit(1)


CURRENTLY_WORKING_ON = """

- OS/X: check SQLCipher now builds
- Windows: 'make' for OpenSSL

... Google "compile sqlcipher visual studio"
... stackoverflow.com/questions/4353037
... might need MinGW/MSYS

"""
