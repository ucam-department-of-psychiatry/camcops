..  documentation/source/developer/development_command_line.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

.. _OpenSSL: https://www.openssl.org/
.. _Qt: https://www.qt.io/
.. _SQLCipher: https://www.zetetic.net/sqlcipher/
.. _SQLite: https://www.sqlite.org/
.. _WAV: https://en.wikipedia.org/wiki/WAV


.. _development_command_line_tools:

Development command-line tools
==============================

If you are developing tasks for CamCOPS, be aware of these additional
development tools.

.. _build_qt:

build_qt.py
-----------

This program runs on a variety of platforms (including Linux, Windows, OS/X)
and has the surprisingly tricky job of building the following libraries, from
source:

- OpenSSL_
- SQLCipher_
- Qt_

for the following platforms, using a variety of CPUs:

- Android (ARM, x86 emulator) (compile under Linux)
- iOS (ARM, x86 simulators) (compile under OS/X)
- Linux (x86)
- OS/X
- Windows

It will fetch source code and do all the work. Once built, you should have a Qt
environment that you can point Qt Creator to, and you should be able to compile
CamCOPS with little extra work. (Though probably not none.)

The ``--build_all`` option is generally a good one; this builds for all
architectures supported on the host you're using.

Here's its help as of 2018-06-09:

.. code-block:: none

    usage: build_qt.py [-h] [--show_config_only] [--root_dir ROOT_DIR]
                       [--nparallel NPARALLEL] [--force] [--tee TEE]
                       [--verbose {0,1,2}] [--build_all] [--build_android_x86_32]
                       [--build_android_arm_v7_32] [--build_linux_x86_64]
                       [--build_osx_x86_64] [--build_windows_x86_64]
                       [--build_windows_x86_32] [--build_ios_arm_v7_32]
                       [--build_ios_arm_v8_64] [--build_ios_simulator_x86_32]
                       [--build_ios_simulator_x86_64]
                       [--qt_build_type {debug,release,release_w_symbols}]
                       [--qt_src_dirname QT_SRC_DIRNAME] [--qt_git_url QT_GIT_URL]
                       [--qt_git_branch QT_GIT_BRANCH]
                       [--qt_git_commit QT_GIT_COMMIT] [--qt_openssl_static]
                       [--qt_openssl_linked]
                       [--android_api_number ANDROID_API_NUMBER]
                       [--android_sdk_root ANDROID_SDK_ROOT]
                       [--android_ndk_root ANDROID_NDK_ROOT]
                       [--android_ndk_host ANDROID_NDK_HOST]
                       [--android_toolchain_version ANDROID_TOOLCHAIN_VERSION]
                       [--ios_sdk IOS_SDK] [--ios_min_version IOS_MIN_VERSION]
                       [--osx_min_version OSX_MIN_VERSION]
                       [--openssl_version OPENSSL_VERSION]
                       [--openssl_src_url OPENSSL_SRC_URL]
                       [--openssl_android_script_url OPENSSL_ANDROID_SCRIPT_URL]
                       [--sqlcipher_git_url SQLCIPHER_GIT_URL]
                       [--sqlcipher_git_commit SQLCIPHER_GIT_COMMIT]
                       [--eigen_version EIGEN_VERSION]
                       [--jom_executable JOM_EXECUTABLE]
                       [--mxe_git_url MXE_GIT_URL]

    Build Qt and other libraries for CamCOPS

    optional arguments:
      -h, --help            show this help message and exit

    General:
      General options

      --show_config_only    Show config, then quit (default: False)
      --root_dir ROOT_DIR   Root directory for source and builds (default taken
                            from environment variable CAMCOPS_QT_BASE_DIR if
                            present) (default: /home/rudolf/dev/qt_local_build)
      --nparallel NPARALLEL
                            Number of parallel processes to run (default: 8)
      --force               Force build (default: False)
      --tee TEE             Copy stdout/stderr to this named file (default: None)
      --verbose {0,1,2}, -v {0,1,2}
                            Verbosity level (default: 0)

    Architecture:
      Choose architecture for which to build

      --build_all           Build for all architectures supported on this host
                            (Linux/Intel x86 (64-bit)) (default: False)
      --build_android_x86_32
                            An architecture target (Android under an Intel x86
                            32-bit emulator) (default: False)
      --build_android_arm_v7_32
                            An architecture target (Android under a ARM processor
                            tablet) (default: False)
      --build_linux_x86_64  An architecture target (native Linux with a 64-bit
                            Intel/AMD CPU; check with 'lscpu' and 'uname -a'
                            (default: False)
      --build_osx_x86_64    An architecture target (Mac OS/X under an Intel 64-bit
                            CPU; check with 'sysctl -a|grep cpu', and see
                            https://support.apple.com/en-gb/HT201948 ) (default:
                            False)
      --build_windows_x86_64
                            An architecture target (Windows with an Intel/AMD
                            64-bit CPU) (default: False)
      --build_windows_x86_32
                            An architecture target (Windows with an Intel/AMD
                            32-bit CPU) (default: False)
      --build_ios_arm_v7_32
                            An architecture target (iOS with a 32-bit ARM
                            processor) (default: False)
      --build_ios_arm_v8_64
                            An architecture target (iOS with a 64-bit ARM
                            processor) (default: False)
      --build_ios_simulator_x86_32
                            An architecture target (iOS with an Intel 32-bit CPU,
                            for the iOS simulator) (default: False)
      --build_ios_simulator_x86_64
                            An architecture target (iOS with an Intel 64-bit CPU,
                            for the iOS simulator) (default: False)

    Qt:
      Qt options [Qt must be built from source for SQLite support, and also if
      static OpenSSL linkage is desired; note that static OpenSSL linkage
      requires a Qt rebuild (slow!) if you rebuild OpenSSL]

      --qt_build_type {debug,release,release_w_symbols}
                            Qt build type (release = small and quick) (default:
                            release)
      --qt_src_dirname QT_SRC_DIRNAME
                            Qt source directory (default: qt5)
      --qt_git_url QT_GIT_URL
                            Qt Git URL (default: git://code.qt.io/qt/qt5.git)
      --qt_git_branch QT_GIT_BRANCH
                            Qt Git branch (default: 5.10.0)
      --qt_git_commit QT_GIT_COMMIT
                            Qt Git commit (default: HEAD)
      --qt_openssl_static   Link OpenSSL statically (ONLY if Qt is statically
                            linked) [True=static, False=dynamic] (default: True)
      --qt_openssl_linked   Link OpenSSL dynamically [True=static, False=dynamic]
                            (default: True)

    Android:
      Android options (NB you must install the Android SDK and NDK separately,
      BEFOREHAND)

      --android_api_number ANDROID_API_NUMBER
                            Android API number (default: 23)
      --android_sdk_root ANDROID_SDK_ROOT
                            Android SDK root directory (default:
                            /home/rudolf/dev/android-sdk-linux)
      --android_ndk_root ANDROID_NDK_ROOT
                            Android NDK root directory (default:
                            /home/rudolf/dev/android-ndk-r11c)
      --android_ndk_host ANDROID_NDK_HOST
                            Android NDK host architecture (default: linux-x86_64)
      --android_toolchain_version ANDROID_TOOLCHAIN_VERSION
                            Android toolchain version (default: 4.9)

    iOS:
      iOS options

      --ios_sdk IOS_SDK     iOS SDK to use (leave blank for system default)
                            (default: )
      --ios_min_version IOS_MIN_VERSION
                            Minimum target iOS version (default: 7.0)

    OS/X:
      OS/X options

      --osx_min_version OSX_MIN_VERSION
                            Minimum target OS/X version (default: 10.7)

    OpenSSL:
      OpenSSL options [OpenSSL must be built from source to use it on Android;
      Qt needs OpenSSL somehow; CamCOPS uses OpenSSL]

      --openssl_version OPENSSL_VERSION
                            OpenSSL version (default: 1.1.0g)
      --openssl_src_url OPENSSL_SRC_URL
                            OpenSSL source URL (default:
                            https://www.openssl.org/source/openssl-1.1.0g.tar.gz)
      --openssl_android_script_url OPENSSL_ANDROID_SCRIPT_URL
                            OpenSSL Android script source (URL) (not really
                            unused) (default:
                            https://wiki.openssl.org/images/7/70/Setenv-
                            android.sh)

    SQLCipher:
      SQLCipher options [CamCOPS uses SQLCipher]

      --sqlcipher_git_url SQLCIPHER_GIT_URL
                            SQLCipher Git URL (default:
                            https://github.com/sqlcipher/sqlcipher.git)
      --sqlcipher_git_commit SQLCIPHER_GIT_COMMIT
                            SQLCipher Git commit (default: HEAD)

    Eigen:
      Eigen C++ template library [CamCOPS uses Eigen]

      --eigen_version EIGEN_VERSION
                            Eigen version (default: 3.3.3)

    jom:
      'jom' parallel make tool for Windows

      --jom_executable JOM_EXECUTABLE
                            jom executable (typically installed with QtCreator)
                            (default: C:\Qt\Tools\QtCreator\bin\jom.exe)

    MXE:
      MXE cross-compilation environment for Linux hosts

      --mxe_git_url MXE_GIT_URL
                            MXE Git URL (default: https://github.com/mxe/mxe.git)


chord.py
--------

This generates musical chords as WAV_ files. It's not very generic but it
generates specific sounds used by the CamCOPS client.

decrypt_sqlcipher.py
--------------------

This tool requires an installed copy of SQLCipher_. It creates a decrypted
SQLite_ database from an encrypted SQLCipher_ database, given the password.

Here's its help as of 2018-06-09:

.. code-block:: none

    usage: decrypt_sqlcipher.py [-h] [--password PASSWORD] [--sqlcipher SQLCIPHER]
                                [--encoding ENCODING]
                                encrypted decrypted

    Use SQLCipher to make a decrypted copy of a database

    positional arguments:
      encrypted             Filename of the existing encrypted database
      decrypted             Filename of the decrypted database to be created

    optional arguments:
      -h, --help            show this help message and exit
      --password PASSWORD   Password (if blank, environment variable
                            DECRYPT_SQLCIPHER_PASSWORD will be used, or you will
                            be prompted) (default: None)
      --sqlcipher SQLCIPHER
                            SQLCipher executable file (if blank, environment
                            variable SQLCIPHER will be used, or the default of
                            'sqlcipher') (default: None)
      --encoding ENCODING   Encoding to use (default: utf-8)
