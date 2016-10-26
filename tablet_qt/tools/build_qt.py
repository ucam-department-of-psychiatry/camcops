#!/usr/bin/env python3

"""
When is it NECESSARY to compile OpenSSL from source?
    - OpenSSL for Android
      http://doc.qt.io/qt-5/opensslsupport.html
      ... so: necessary.

When is it NECESSARY to compile Qt from source?
    - Static linking of OpenSSL (non-critical)
    - SQLite support (critical)
      http://doc.qt.io/qt-5/sql-driver.html
      ... so: necessary.

COMPILING OPENSSL:
    ...

OTHER NOTES:
# configure: http://doc.qt.io/qt-5/configure-options.html
# sqlite: http://doc.qt.io/qt-5/sql-driver.html
# build for Android: http://wiki.qt.io/Qt5ForAndroidBuilding
# multi-core builds: http://stackoverflow.com/questions/9420825/how-to-compile-on-multiple-cores-using-mingw-inside-qtcreator  # noqa

UPON QT CONFIGURE FAILURE:

-   gstreamer (used for Unix audio etc.)
    gstreamer version 1.0 version (for Unix) requires:
        sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
    ... NB some things try to remove it, it seems! (Maybe autoremove?)

-   Qt configure can't find make or gmake in PATH...

    If they are in the PATH, then check permissions on
          qtbase/config.tests/unix/which.test
    ... if not executable, permissions have been altered wrongly.

-   NB actual configure scripts are:
        /home/rudolf/dev/qt_local_build/src/qt5/configure
        /home/rudolf/dev/qt_local_build/src/qt5/configure/qtbase/configure

-   "recipe for target 'sub-plugins-make_first' failed", or similar:

    If configure fails, try more or less verbose (--verbose 0, --verbose 2) and
    also try "--nparallel 1" so you can see which point is failing more
    clearly. This is IMPORTANT or other error messages incorrectly distract
    you.

"""


import argparse
import logging
import multiprocessing
import os
from os.path import abspath, expanduser, isdir, isfile, join, split
import shutil
import subprocess
import sys
import urllib.request

log = logging.getLogger(__name__)

QT_CONFIG_COMMON_ARGS = [
    # use "configure -help" to list all of them
    # http://doc.qt.io/qt-4.8/configure-options.html  # NB better docs than 5.7
    # http://doc.qt.io/qt-5.7/configure-options.html  # less helpful

    # -------------------------------------------------------------------------
    # Qt license, debug v. release, static v. shared
    # -------------------------------------------------------------------------

    "-opensource", "-confirm-license",

    "-release",  # default is release

    # "-debug-and-release",  # make a release library as well: MAC ONLY
        # ... debug was the default in 4.8, but not in 5.7
        # ... release is default in 5.7 (as per "configure -h")
        # ... check with "readelf --debug-dump=decodedline <LIBRARY.so>"
        # ... http://stackoverflow.com/questions/1999654

    "-static",  # makes a static Qt library (cf. default of "-shared")
    # ... NB ALSO NEEDS "CONFIG += static" in the .pro file

    # -------------------------------------------------------------------------
    # Database support
    # -------------------------------------------------------------------------
    "-qt-sql-sqlite",  # SQLite (v3) support built in to Qt

    "-no-sql-db2",  # disable other SQL drivers
    "-no-sql-ibase",
    "-no-sql-mysql",  # ... for future: maybe re-enable as a plugin
    "-no-sql-oci",
    "-no-sql-odbc",  # ... for future: maybe re-enable as a plugin
    "-no-sql-psql",  # ... for future: maybe re-enable as a plugin
    "-no-sql-sqlite2",  # this is an old SQLite version
    "-no-sql-tds",  # this one specifically was causing library problems

    # -------------------------------------------------------------------------
    # Third-party libraries
    # -------------------------------------------------------------------------
    "-qt-zlib",  # Qt, not host OS, version of zlib
    "-qt-libpng",  # Qt, not host OS, version of PNG library
    "-qt-libjpeg",  # Qt, not host OS, version of JPEG library
    "-qt-doubleconversion",


    # -------------------------------------------------------------------------
    # Compilation
    # -------------------------------------------------------------------------
    "-no-warnings-are-errors",

    # -------------------------------------------------------------------------
    # Stuff to skip
    # -------------------------------------------------------------------------
    "-nomake", "tests",
    "-nomake", "examples",
    "-skip", "qttranslations",
    "-skip", "qtwebkit",
    "-skip", "qtserialport",
    "-skip", "qtwebkit-examples",
]
OPENSSL_COMMON_OPTIONS = [
    "shared",  # make .so files (needed by Qt sometimes) as well as .a
    "no-ssl2",  # SSL-2 is broken
    "no-ssl3",  # SSL-3 is broken. Is an SSL-3 build required for TLS 1.2?
    # "no-comp",  # disable compression independent of zlib
]


# =============================================================================
# Ancillary
# =============================================================================

def run(args, env=None):
    log.info("Running external command: {}".format(args))
    if env is not None:
        log.info("Using environment: {}".format(env))
    subprocess.check_call(args, env=env)


def replace(filename, text_from, text_to):
    log.info("Amending {} from {} to {}".format(
        filename, repr(text_from), repr(text_to)))
    with open(filename) as infile:
        contents = infile.read()
    contents = contents.replace(text_from, text_to)
    with open(filename, 'w') as outfile:
        outfile.write(contents)


def require(command):
    if not shutil.which(command):
        raise ValueError("Missing OS command: {}".format(command))


def replace_multiple(filename, replacements):
    with open(filename) as infile:
        contents = infile.read()
    for text_from, text_to in replacements:
        log.info("Amending {} from {} to {}".format(
            filename, repr(text_from), repr(text_to)))
        contents = contents.replace(text_from, text_to)
    with open(filename, 'w') as outfile:
        outfile.write(contents)


def mkdir_p(path):
    log.info("mkdir -p {}".format(path))
    os.makedirs(path, exist_ok=True)


def download_if_not_exists(url, filename):
    if isfile(filename):
        log.info("Already have: {}".format(filename))
        return
    dir, basename = split(abspath(filename))
    mkdir_p(dir)
    log.info("Downloading from {} to {}".format(url, filename))
    urllib.request.urlretrieve(url, filename)


def fetch_qt(args):
    if isdir(args.qt_src_gitdir):
        log.info("Using Qt source in {}".format(args.qt_src_gitdir))
        return
    log.info("Fetching Qt source from {} (branch {}) into {}".format(
        args.qt_git_url, args.qt_git_branch, args.qt_src_gitdir))
    os.chdir(args.src_rootdir)
    run(["git", "clone", "--branch", args.qt_git_branch, args.qt_git_url])
    os.chdir(args.qt_src_gitdir)
    run(["perl", "init-repository"])


def fetch_openssl(args):
    download_if_not_exists(args.openssl_src_url, args.openssl_src_fullpath)
    #download_if_not_exists(args.openssl_android_script_url,
    #                       args.openssl_android_script_fullpath)


def get_openssl_rootdir_workdir(args, system):
    rootdir = join(args.root_dir, "openssl_{}_build".format(system))
    workdir = join(rootdir, args.openssl_version)
    return rootdir, workdir


def root_path():
    # http://stackoverflow.com/questions/12041525
    return os.path.abspath(os.sep)


# =============================================================================
# Building OpenSSL
# =============================================================================

def build_openssl_android(args, cpu):
    rootdir, workdir = get_openssl_rootdir_workdir(args, "android_" + cpu)
    targets = [join(workdir, "libssl.so"),
               join(workdir, "libcrypto.so")]
    if not args.force and all(isfile(x) for x in targets):
        log.info("OpenSSL: All targets exist already: {}".format(targets))
        return

    # https://wiki.openssl.org/index.php/Android
    # We're not using the Setenv-android.sh script, but replicating its
    # functions.
    android_arch_short = cpu
    android_arch_full = "arch-{}".format(android_arch_short)  # e.g. arch-x86
    if cpu == "x86":
        android_eabi = "{}-{}".format(android_arch_short,
                                      args.android_toolchain_version)  # e.g. x86-4.9
        # For toolchain version: ls $ANDROID_NDK_ROOT/toolchains
        # ... "-android-arch" and "-android-toolchain-version" get
        # concatenated, I think; for example, this gives the toolchain
        # "x86_64-4.9"
    else:
        # but ARM ones look like "arm-linux-androideabi-4.9"
        android_eabi = "{}-linux-androideabi-{}".format(android_arch_short,
                                                        args.android_toolchain_version)
    android_sysroot = join(args.android_ndk_root, "platforms",
                           args.android_api, android_arch_full)
    android_toolchain = join(args.android_ndk_root, "toolchains", android_eabi,
                             "prebuilt", args.android_ndk_host, "bin")

    # http://doc.qt.io/qt-5/opensslsupport.html
    if cpu == "armv5":
        target_os = "android"
    elif cpu == "arm":
        target_os = "android-armv7"
    else:
        target_os = "android-{}".format(cpu)

    # env = os.environ.copy()
    env = {  # clean environment
        'PATH': os.environ['PATH'],
    }
    mkdir_p(rootdir)
    run(["tar", "-xvf", args.openssl_src_fullpath, "-C", rootdir])

    # https://wiki.openssl.org/index.php/Android
    makefile_org = join(workdir, "Makefile.org")
    replace(makefile_org,
            "install: all install_docs install_sw",
            "install: install_docs install_sw")

    os.chdir(workdir)

    # The OpenSSL "config" sh script guesses the OS, then passes details
    # to its "Configure" Perl script.
    # For Android, OpenSSL suggest using their Setenv-android.sh script, then
    # running "config".
    # However, it does seem to be screwing up. Let's try Configure instead.

    common_ssl_config_options = OPENSSL_COMMON_OPTIONS + [
        "no-hw",  # disable hardware support ("useful on mobile devices")
        "no-engine",  # disable hardware support ("useful on mobile devices")
    ]

    env["ANDROID_API"] = args.android_api
    env["ANDROID_ARCH"] = android_arch_full
    env["ANDROID_DEV"] = join(android_sysroot, "usr")
    env["ANDROID_EABI"] = android_eabi
    env["ANDROID_NDK_ROOT"] = args.android_ndk_root
    env["ANDROID_SDK_ROOT"] = args.android_sdk_root
    env["ANDROID_SYSROOT"] = android_sysroot
    env["ANDROID_TOOLCHAIN"] = android_toolchain
    env["ARCH"] = cpu
    # env["CROSS_COMPILE"] = "i686-linux-android-"
    env["FIPS_SIG"] = ""  # OK to leave blank if not building FIPS
    env["HOSTCC"] = "gcc"
    env["MACHINE"] = "i686"
    env["NDK_SYSROOT"] = android_sysroot
    env["PATH"] = "{}{}{}".format(android_toolchain, os.pathsep, env["PATH"])
    env["RELEASE"] = "2.6.37"  # ??
    env["SYSROOT"] = android_sysroot
    env["SYSTEM"] = target_os  # ... NB "android" means ARMv5

    use_configure = True
    if use_configure:
        # ---------------------------------------------------------------------
        # Configure
        # ---------------------------------------------------------------------
        # http://doc.qt.io/qt-5/opensslsupport.html
        env["ANDROID_DEV"] = join(android_sysroot, "usr")
        if cpu == "x86":
            cc_prefix = "i686"
        else:
            cc_prefix = "arm"
        if cpu == "x86":
            env["CC"] = join(
                android_toolchain,
                "i686-linux-android-gcc-{}".format(
                    args.android_toolchain_version)
            )
            env["AR"] = join(android_toolchain, "i686-linux-android-gcc-ar")
        else:
            env["CC"] = join(
                android_toolchain,
                "arm-linux-androideabi-gcc-{}".format(
                    args.android_toolchain_version)
            )
            env["AR"] = join(android_toolchain, "arm-linux-androideabi-gcc-ar")
        configure_args = [
            target_os,
        ] + common_ssl_config_options  # was OPENSSL_COMMON_OPTIONS, check ***
        # print(env)
        # sys.exit(1)
        run(["perl", join(workdir, "Configure")] + configure_args, env)

    else:
        # ---------------------------------------------------------------------
        # config
        # ---------------------------------------------------------------------
        # https://wiki.openssl.org/index.php/Android
        # and "If in doubt, on Unix-ish systems use './config'."

        # https://wiki.openssl.org/index.php/Compilation_and_Installation
        config_args = [
            target_os,
        ] + common_ssl_config_options
        run([join(workdir, "config")] + config_args, env)

    # Have to remove version numbers from final library filenames:
    # http://doc.qt.io/qt-5/opensslsupport.html
    makefile = join(workdir, "Makefile")
    replace_multiple(makefile, [
        ('LIBNAME=$$i LIBVERSION=$(SHLIB_MAJOR).$(SHLIB_MINOR)',
            'LIBNAME=$$i'),
        ('LIBCOMPATVERSIONS=";$(SHLIB_VERSION_HISTORY)"', ''),
    ])
    run(["make", "depend"], env)
    run(["make", "build_libs"], env)

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


def build_openssl_common_unix(args, cosmetic_osname, target_os, shared_lib_suffix):
    """
    The target_os parameter is paseed to OpenSSL's Configure script.
    Use "./Configure LIST" for all possibilities.

        https://wiki.openssl.org/index.php/Compilation_and_Installation
    """
    rootdir, workdir = get_openssl_rootdir_workdir(args, cosmetic_osname)
    targets = [join(workdir, "libssl{}".format(shared_lib_suffix)),
               join(workdir, "libcrypto{}".format(shared_lib_suffix))]
    if not args.force and all(isfile(x) for x in targets):
        log.info("OpenSSL: All targets exist already: {}".format(targets))
        return

    env = {  # clean environment
        'PATH': os.environ['PATH'],
    }
    mkdir_p(rootdir)
    run(["tar", "-xvf", args.openssl_src_fullpath, "-C", rootdir])

    makefile_org = join(workdir, "Makefile.org")
    replace(makefile_org,
            "install: all install_docs install_sw",
            "install: install_docs install_sw")

    os.chdir(workdir)

    configure_args = [
        target_os,
    ] + OPENSSL_COMMON_OPTIONS
    run(["perl", join(workdir, "Configure")] + configure_args, env)

    # Have to remove version numbers from final library filenames:
    # http://doc.qt.io/qt-5/opensslsupport.html
    makefile = join(workdir, "Makefile")
    replace_multiple(makefile, [
        ('LIBNAME=$$i LIBVERSION=$(SHLIB_MAJOR).$(SHLIB_MINOR)',
            'LIBNAME=$$i'),
        ('LIBCOMPATVERSIONS=";$(SHLIB_VERSION_HISTORY)"', ''),
    ])
    run(["make", "depend", "-j", str(args.nparallel)], env)
    run(["make", "build_libs", "-j", str(args.nparallel)], env)


def build_openssl_linux(args):
    build_openssl_common_unix(args,
                              cosmetic_osname="linux",
                              target_os="linux-x86_64",
                              shared_lib_suffix=".so")



def build_openssl_osx(args):
    build_openssl_common_unix(args,
                              cosmetic_osname="osx",
                              target_os="darwin64-x86_64-cc",
                              shared_lib_suffix=".dylib")
    # https://gist.github.com/tmiz/1441111


# =============================================================================
# Building Qt
# =============================================================================

def add_generic_qt_config_args(qt_config_args, args):
    qt_config_args.extend(QT_CONFIG_COMMON_ARGS)

    # For testing a new OpenSSL build, have args.static_openssl=False, or you
    # have to rebuild Qt every time... extremely slow.
    if args.static_openssl:
        qt_config_args.append("-openssl-linked")  # OpenSSL
        # http://doc.qt.io/qt-4.8/ssl.html
        # http://stackoverflow.com/questions/20843180
    else:
        qt_config_args.append("-openssl")  # OpenSSL

    if args.verbose >= 1:
        qt_config_args.append("-v")  # verbose
    if args.verbose >= 2:
        qt_config_args.append("-v")  # more verbose


def build_qt_android(args, cpu):
    # Android example at http://wiki.qt.io/Qt5ForAndroidBuilding
    # http://doc.qt.io/qt-5/opensslsupport.html
    # Windows: ?also http://simpleit.us/2010/05/30/enabling-openssl-for-qt-c-on-windows/  # noqa

    require("javac")  # try: sudo apt install openjdk-8-jdk
    # ... will be called by the make process; better to know now, since the
    # relevant messages are easily lost in the torrent

    require("ant")  # will be needed later; try: sudo apt install ant

    opensslrootdir, opensslworkdir = get_openssl_rootdir_workdir(
        args, "android_" + cpu)
    openssl_include_root = join(opensslworkdir, "include")
    openssl_lib_root = opensslworkdir
    if cpu == "x86":
        android_arch_short = cpu
    elif cpu == "arm":
        android_arch_short = "armeabi-v7a"
    else:
        raise ValueError("Unknown cpu: {}".format(cpu))

    builddir = join(args.root_dir, "qt_android_{}_build".format(cpu))
    installdir = join(args.root_dir, "qt_android_{}_install".format(cpu))

    targets = [join(installdir, "bin", "qmake")]
    if not args.force and all(isfile(x) for x in targets):
        log.info("Qt: All targets exist already: {}".format(targets))
        return installdir

    # env = os.environ.copy()
    env = {  # clean environment
        'PATH': os.environ['PATH'],
    }
    env["OPENSSL_LIBS"] = "-L{} -lssl -lcrypto".format(openssl_lib_root)
    # ... unnecessary? But suggested by Qt.

    log.info("Configuring Android {} build in {}".format(cpu, builddir))
    mkdir_p(builddir)
    mkdir_p(installdir)
    os.chdir(builddir)
    qt_config_args = [
        join(args.qt_src_gitdir, "configure"),

        # General options:
        "-I", openssl_include_root,  # OpenSSL
        "-L", openssl_lib_root,  # OpenSSL
        "-prefix", installdir,

        # Android options:
        "-android-sdk", args.android_sdk_root,
        "-android-ndk", args.android_ndk_root,
        "-android-ndk-host", args.android_ndk_host,
        "-android-arch", android_arch_short,
        "-android-toolchain-version", args.android_toolchain_version,
        "-xplatform", "android-g++",
    ]

    add_generic_qt_config_args(qt_config_args, args)
    run(qt_config_args)  # The configure step takes a few seconds.

    log.info("Making Qt Android {} build into {}".format(cpu, installdir))
    os.chdir(builddir)
    env["ANDROID_API_VERSION"] = args.android_api
    env["ANDROID_NDK_ROOT"] = args.android_ndk_root
    env["ANDROID_SDK_ROOT"] = args.android_sdk_root
    run(["make", "-j", str(args.nparallel)], env)  # The make step takes a few hours.  # noqa

    # PROBLEM WITH "make install":
    #       mkdir: cannot create directory ‘/libs’: Permission denied
    # ... while processing qttools/src/qtplugininfo/Makefile
    # https://bugreports.qt.io/browse/QTBUG-45095
    # 1. Attempt to fix as follows:
    makefile = join(builddir, "qttools", "src", "qtplugininfo", "Makefile")
    baddir = join("$(INSTALL_ROOT)", "libs", android_arch_short, "")
    gooddir = join(installdir, "libs", android_arch_short, "")
    replace(makefile, " " + baddir, " " + gooddir)

    # 2. Using INSTALL_ROOT: bases the root of a filesystem off installdir
    # env["INSTALL_ROOT"] = installdir
    # http://stackoverflow.com/questions/8360609

    run(["make", "install"], env)
    # ... installs to installdir because of -prefix earlier
    return installdir


def build_qt_generic_unix(args, cosmetic_osname, extra_qt_config_args=None):
    extra_qt_config_args = extra_qt_config_args or []
    opensslrootdir, opensslworkdir = get_openssl_rootdir_workdir(
        args, cosmetic_osname)
    openssl_include_root = join(opensslworkdir, "include")
    openssl_lib_root = opensslworkdir
    builddir = join(args.root_dir, "qt_{}_build".format(cosmetic_osname))
    installdir = join(args.root_dir, "qt_{}_install".format(cosmetic_osname))

    targets = [join(installdir, "bin", "qmake")]
    if all(isfile(x) for x in targets):
        log.info("Qt: All targets exist already: {}".format(targets))
        return installdir

    env = {  # clean environment
        'PATH': os.environ['PATH'],
    }
    env["OPENSSL_LIBS"] = "-L{} -lssl -lcrypto".format(openssl_lib_root)
    # ... unnecessary? But suggested by Qt.

    log.info("Configuring {} build in {}".format(cosmetic_osname, builddir))
    mkdir_p(builddir)
    mkdir_p(installdir)
    os.chdir(builddir)
    qt_config_args = [
        join(args.qt_src_gitdir, "configure"),

        # General options:
        "-I", openssl_include_root,  # OpenSSL
        "-L", openssl_lib_root,  # OpenSSL
        "-prefix", installdir,
    ] + extra_qt_config_args

    add_generic_qt_config_args(qt_config_args, args)
    run(qt_config_args)  # The configure step takes a few seconds.

    log.info("Making Qt {} build into {}".format(cosmetic_osname, installdir))
    os.chdir(builddir)
    run(["make", "-j", str(args.nparallel)], env)  # The make step takes a few hours.  # noqa

    # makefile = join(builddir, "qttools", "src", "qtplugininfo", "Makefile")
    # baddir = join("$(INSTALL_ROOT)", "libs", android_arch_short, "")
    # gooddir = join(installdir, "libs", android_arch_short, "")
    # replace(makefile, " " + baddir, " " + gooddir)

    run(["make", "install"], env)
    # ... installs to installdir because of -prefix earlier
    return installdir


def build_qt_linux(args):
    return build_qt_generic_unix(
        args,
        cosmetic_osname="linux",
        extra_qt_config_args=[
            # Linux options:
            "-qt-xcb",  # use XCB source bundled with Qt?
            "-gstreamer", "1.0",  # gstreamer version; see notes at top of file
        ]
    )


def build_qt_osx(args):
    # http://stackoverflow.com/questions/20604093/qt5-install-on-osx-qt-xcb
    # os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    return build_qt_generic_unix(
        args,
        cosmetic_osname="osx",
        extra_qt_config_args=None
    )


# =============================================================================
# Main
# =============================================================================

def main():
    logging.basicConfig(level=logging.DEBUG)
    user_dir = expanduser("~")

    # Android
    default_android_api_num = 23
    default_root_dir = join(user_dir, "dev", "qt_local_build")
    default_android_sdk = join(user_dir, "dev", "android-sdk-linux")
    default_android_ndk = join(user_dir, "dev", "android-ndk-r11c")
    default_ndk_host = "linux-x86_64"
    default_toolchain_version = "4.9"

    # Qt
    default_qt_src_dirname = "qt5"
    default_qt_git_url = "git://code.qt.io/qt/qt5.git"
    default_qt_git_branch = "5.7.0"

    # OpenSSL
    default_openssl_version = "openssl-1.0.2h"
    default_openssl_src_url = (
        "https://www.openssl.org/source/{}.tar.gz".format(
            default_openssl_version))

    parser = argparse.ArgumentParser(
        description="Build Qt for CamCOPS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Architectures
    parser.add_argument(
        "--android_x86", action="store_true",
        help="An architecture target (Android under an Intel x86 emulator)")
    parser.add_argument(
        "--android_arm", action="store_true",
        help="An architecture target (Android under a ARM processor tablet)")
    parser.add_argument(
        "--linux_x86_64", action="store_true",
        help="An architecture target (native Linux with a 64-bit Intel CPU; "
             "check with 'lscpu' and 'uname -a'")
    parser.add_argument(
        "--osx_x86_64", action="store_true",
        help="An architecture target (Mac OS/X under an Intel 64-bit CPU; "
             "check with 'sysctl -a|grep cpu', and see "
             "https://support.apple.com/en-gb/HT201948 )")

    # General
    parser.add_argument(
        "--nparallel", type=int, default=multiprocessing.cpu_count(),
        help="Number of parallel processes to run")
    parser.add_argument("--force", action="store_true", help="Force build")
    parser.add_argument(
        "--verbose", type=int, default=1,
        help="Verbosity level")

    # Qt
    parser.add_argument(
        "--root_dir", default=default_root_dir,
        help="Root directory for source and builds")
    parser.add_argument(
        "--qt_src_dirname", default=default_qt_src_dirname,
        help="Qt source directory")
    parser.add_argument(
        "--qt_git_url", default=default_qt_git_url,
        help="Qt Git URL")
    parser.add_argument(
        "--qt_git_branch", default=default_qt_git_branch,
        help="Qt Git branch")

    parser.add_argument(
        "--qt_openssl_static", dest="static_openssl", action="store_true",
        help="Link OpenSSL statically")
    parser.add_argument(
        "--qt_openssl_linked", dest="static_openssl", action="store_false",
        help="Link OpenSSL dynamically")
    parser.set_defaults(static_openssl=True)

    # Android
    parser.add_argument(
        "--android_api_number", type=int, default=default_android_api_num,
        help="Android API number")
    parser.add_argument(
        "--android_sdk_root", default=default_android_sdk,
        help="Android SDK root directory")
    parser.add_argument(
        "--android_ndk_root", default=default_android_ndk,
        help="Android NDK root directory")
    parser.add_argument(
        "--android_ndk_host", default=default_ndk_host,
        help="Android NDK host architecture")
    parser.add_argument(
        "--android_toolchain_version", default=default_toolchain_version,
        help="Android toolchain version")

    # OpenSSL
    parser.add_argument(
        "--openssl_version", default=default_openssl_version,
        help="OpenSSL version")
    parser.add_argument(
        "--openssl_src_url", default=default_openssl_src_url,
        help="OpenSSL source URL")

    args = parser.parse_args()

    # Calculated args

    args.src_rootdir = join(args.root_dir, "src")
    args.qt_src_gitdir = join(args.src_rootdir, args.qt_src_dirname)

    args.android_api = "android-{}".format(args.android_api_number)
    # see $ANDROID_SDK_ROOT/platforms/

    args.openssl_tar_dir = join(args.src_rootdir, "openssl")
    args.openssl_src_dir = join(args.src_rootdir, args.openssl_version)
    args.openssl_src_filename = "{}.tar.gz".format(args.openssl_version)
    args.openssl_src_fullpath = join(args.openssl_src_dir,
                                     args.openssl_src_filename)

    log.info(args)

    # =========================================================================
    # Fetch
    # =========================================================================
    fetch_qt(args)
    fetch_openssl(args)

    # =========================================================================
    # Build
    # =========================================================================
    installdirs = []

    if args.android_x86:  # for x86 Android emulator
        log.info("Qt build: Android x86 +SQLite +OpenSSL")
        build_openssl_android(args, "x86")
        installdir = build_qt_android(args, "x86")
        installdirs.append(installdir)

    if args.android_arm:  # for native Android
        log.info("Qt build: Android ARM +SQLite +OpenSSL")
        build_openssl_android(args, "arm")
        installdir = build_qt_android(args, "arm")
        installdirs.append(installdir)

    if args.linux_x86_64:  # for 64-bit Linux
        log.info("Qt build: Linux x86 64-bit +SQLite +OpenSSL")
        build_openssl_linux(args)
        installdir = build_qt_linux(args)
        installdirs.append(installdir)

    if args.osx_x86_64:  # for 64-bit Intel Mac OS/X
        # http://doc.qt.io/qt-5/osx.html
        log.info("Qt build: Mac OS/X x86 64-bit +SQLite +OpenSSL")
        build_openssl_osx(args)
        installdir = build_qt_osx(args)
        installdirs.append(installdir)

    # *** args.ios*  # for iOS (iPad, etc.)
    #     http://doc.qt.io/qt-5/building-from-source-ios.html
    #     http://doc.qt.io/qt-5/ios-support.html
    #     https://gist.github.com/foozmeat/5154962

    # *** args.windows*  # for Windows
    #     http://www.holoborodko.com/pavel/2011/02/01/how-to-compile-qt-4-7-with-visual-studio-2010/

    if not installdirs:
        log.warning("Nothing to do. Run with --help argument for help.")
        sys.exit(1)

    print("""
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

LINUX
- Also need:
    sudo apt-get install mesa-common-dev libgl1-mesa-dev libglu1-mesa-dev  # for gl.h (OpenGL)

    """.format(  # noqa
        bindirs=", ".join(join(x, "bin") for x in installdirs)
    ))


if __name__ == '__main__':
    main()
