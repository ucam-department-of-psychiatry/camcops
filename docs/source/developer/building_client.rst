..  docs/source/developer/building_client.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
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

.. _Android NDK: https://developer.android.com/ndk/
.. _Android SDK: https://developer.android.com/studio/
.. _CMake: https://cmake.org/
.. _Cygwin: https://www.cygwin.com/
.. _Debugging Tools for Windows: https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/
.. _Git: https://git-scm.com/
.. _ImageMagick: https://www.imagemagick.org/
.. _Inno Setup: http://www.jrsoftware.org/isinfo.php
.. _jom: https://wiki.qt.io/Jom
.. _NASM: http://www.nasm.us/
.. _Perl: https://www.activestate.com/activeperl
.. _Python: https://www.python.org/
.. _Qt: https://www.qt.io/
.. _TCL: https://www.activestate.com/activetcl
.. _Valgrind: http://valgrind.org/
.. _Visual Studio: https://visualstudio.microsoft.com/
.. _Windows SDK: https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk


.. _dev_building_client:

Building the CamCOPS client
===========================

The CamCOPS client is written in C++11 using the Qt_ cross-platform framework.

..  contents::
    :local:
    :depth: 3


Prerequisites
-------------

**Ensure the following prerequisites are met:**
https://wiki.qt.io/Building_Qt_5_from_Git


Linux
~~~~~

- Linux should come with Python and the necessary build tools.

- Tested in Aug 2018 with:

  .. code-block:: none

    Ubuntu 16.04
    Ubuntu 18.04 / gcc 7.3.0


Android (with a Linux build host)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- To build Android programs under Linux, you will also need a Java development
  kit (JDK), such as OpenJDK: ``sudo apt install openjdk-8-jdk``.

- Install the `Android SDK`_. This is an auto-updating set of software tools;
  run ``tools/android`` to update it.

  - Ensure SDK 26 is installed; this is the target version.

- Android SDK version constraints:

  - Qt requires Android API ≥16 (http://doc.qt.io/qt-5/android-support.html).

  - Qt 5.11.1 does not compile with the ``android-16`` toolchain (specifically
    its Bluetooth components). Qt looks for a Java package
    ``android.bluetooth.le``, which is the Bluetooth Low Energy component that
    comes with Android SDK 18. So let's try 18 as the minimum. That does
    compile.

  - For whatever reasons, CamCOPS (v2.2.3-2.2.4) doesn't run on Android 4.4.x
    (API 18) but does run on 6.0 (API 23); intermediates untested.

  - Google Play store requires ``targetSdkVersion`` to be at least 26 from
    2018-11-01
    (https://developer.android.com/distribute/best-practices/develop/target-sdk).

  - Above Android API 23, linking to non-public libraries is prohibited,
    possibly with exceptions for SSL/crypto.

    - https://android-developers.googleblog.com/2016/06/android-changes-for-ndk-developers.html
    - https://developer.android.com/about/versions/nougat/android-7.0-changes#ndk

    I think this caused fatal problems for CamCOPS in 2018-07; not sure, but
    this might explain it.

  - Android libraries should be compiled for the same SDK version as
    ``minSdkVersion`` in ``AndroidManifest.xml`` (see
    https://stackoverflow.com/questions/21888052/what-is-the-relation-between-app-platform-androidminsdkversion-and-androidtar/41079462#41079462,
    and https://developer.android.com/ndk/guides/stable_apis).

- Install the `Android NDK`_. Tested with:

  .. code-block:: none

    android-ndk-r11c  # doesn't support 64-bit ARM
    android-ndk-r20   # as of 2019-06-15

- Android NDK version constraints:

  - Qt favour Android NDK r10e (the May 2015 release)
    (http://doc.qt.io/qt-5/androidgs.html) but r11c also seems to work fine.

  - However, r11c doesn't support 64-bit ARM, which is required in the Google
    Play Store as of Aug 2019, so we're trying r20. See
    https://developer.android.com/distribute/best-practices/develop/64-bit.
    Note also that Qt wants the ``android-clang`` toolchain for Qt 5.12 or
    later and then supports the latest version (the GCC toolchain "requires
    Android NDK r10e" [or r11c!]). So from 2019-06-15 we move to r20 with
    clang, and add support for 64-bit ARM.


Windows
~~~~~~~

- Install a recent version of Python_. Make sure it's on your ``PATH``.

- Install a Microsoft Visual C++ compiler. A free one is `Visual Studio`_
  Community. As you install Visual Studio, don't forget to tick the C++
  options.

- Install these other tools:

  - CMake_. (We'll use this version of cmake to build CamCOPS.)

  - Cygwin_ and its packages ``cmake``, ``gcc-g++``, and ``make``. (If you missed
    them out during initial installation, just re-run the Cygwin setup program,
    such as ``setup-x86_64.exe``. SQLCipher requires ``make``.)

  - NASM_, the Netwide Assembler for x86-family processors.

  - ActiveState TCL_. (SQLCipher requires ``tclsh``.)

  - ActiveState Perl_. (OpenSSL requires ``perl``.)

  - Optionally, `Debugging Tools for Windows`_ (including CDB), such as from
    the `Windows SDK`_.

  - ImageMagick_; make sure you also install the C/C++ development headers
    (see
    http://docs.wand-py.org/en/latest/guide/install.html#install-imagemagick-on-windows).

- Add everything to the ``PATH``.

  - In Windows 10, persistent environment variable settings are accessible by
    searching the Start menu for "environment variables", or
    :menuselection:`Start --> Control Panel --> System and Security --> System
    --> Advanced System Settings --> Environment Variables`.

  - You can use either the User or the System settings, as you see fit.

  - PATH elements are separated with semicolons, if you edit the path manually.

  - For example, you may want these:

    .. code-block:: none

        C:\cygwin64\bin
        C:\Program Files\NASM
        C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build

        -- These are usually added automatically by installers:

        C:\Program Files\Git\cmd
        C:\ActiveTcl\bin
        C:\Perl64\bin

  - Do make sure that the ``PATH`` doesn't have an unquoted ampersand in; this
    is technically legal but it causes no end of trouble (see :ref:`build_qt`).
    (The usual culprit is MySQL.) The :ref:`build_qt` script will check this.

- Tested in July 2018 with:

  .. code-block:: none

    ActivePerl 5.24.3 build 2404 (64-bit)
    ActiveTcl 8.6.7 build 0 (64-bit)
    CMake 3.12.0 (64-bit)
    Cygwin Setup 2.889 (64-bit)
    Microsoft Visual Studio Community 2017
    NASM 2.13.03 (64-bit)
    Python 3.6
    Qt Creator 4.7.0
    Windows 10 (64-bit)


macOS (formerly OS X)
~~~~~~~~~~~~~~~~~~~~~

- See :ref:`Setting up an iMac for CamCOPS development <set_up_imac_for_dev>`.

- Tested in Apr 2019 with:

  .. code-block:: none

    # macOS Mojave 10.14.4
    # Xcode 10.2.1 (macOS SDK 10.14; iOS SDK 12.2)
    build_qt --build_all


All operating systems
~~~~~~~~~~~~~~~~~~~~~

- Install the open-source edition of Qt_, with Qt Creator. (You only really
  need the Tools component. We will fetch Qt separately.)

- Make sure you have Git_ installed.

- Set some environment variables, so we can be consistent in these
  instructions. Specimen values:

    .. list-table::
        :header-rows: 1

        * - Environment variable
          - Example value (Linux, MacOS)
          - Example value (Windows)
          - Notes

        * - CAMCOPS_QT_BASE_DIR
          - ``~/dev/qt_local_build``
          - ``%USERPROFILE%\dev\qt_local_build``
          - Read by :ref:`build_qt`.

        * - CAMCOPS_SOURCE_DIR
          - ``~/dev/camcops``
          - ``%USERPROFILE%\dev\camcops``
          - Used in these instructions and by the Windows Inno Setup script.

        * - CAMCOPS_VENV
          - ``~/dev/camcops_venv``
          - ``%USERPROFILE%\dev\camcops_venv``
          - Used in these instructions.

        * - CAMCOPS_VISUAL_STUDIO_REDIST_ROOT
          - N/A.
          - ``C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Redist\MSVC\14.14.26405``
          - Used by the Windows Inno Setup script.

- Fetch CamCOPS. For example, for the GitHub version:

  .. code-block:: bash

    # Linux
    git clone https://github.com/RudolfCardinal/camcops $CAMCOPS_SOURCE_DIR

  .. code-block:: bat

    REM Windows
    git clone https://github.com/RudolfCardinal/camcops %CAMCOPS_SOURCE_DIR%

- Create a virtual environment and install some Python tools:

  .. code-block:: bash

    # Linux
    python3 -m venv $CAMCOPS_VENV
    . $CAMCOPS_VENV/bin/activate
    pip install cardinal_pythonlib

  .. code-block:: bat

    REM Windows
    python -m venv %CAMCOPS_VENV%
    %CAMCOPS_VENV%\Scripts\activate
    pip install cardinal_pythonlib


Build OpenSSL, SQLCipher, Qt
----------------------------

Build a copy of Qt and supporting tools (OpenSSL, SQLCipher) from source using
the CamCOPS :ref:`build_qt` tool (q.v.). For example:

.. code-block:: bash

    # Linux
    $CAMCOPS_SOURCE_DIR/tablet_qt/tools/build_qt.py --build_all

.. code-block:: bat

    REM Windows
    python %CAMCOPS_SOURCE_DIR%/tablet_qt/tools/build_qt.py --build_all


Version constraints for OpenSSL and SQLCipher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- OpenSSL 1.0.x has long-term support and 1.1.x is the current release.

- OpenSSL 1.0.2h didn't compile under 64-bit Windows, whereas OpenSSL 1.1.x
  did.

- OpenSSL 1.1.x requires Qt 5.10 or higher
  (https://bugreports.qt.io/browse/QTBUG-52905).

- SQLCipher supports OpenSSL 1.1.0 as of SQLCipher 3.4.1
  (https://discuss.zetetic.net/t/sqlcipher-3-4-1-release/1962).

- The Android NDK has moved from gcc to clang, for all standalone toolchains
  from r18 (https://developer.android.com/ndk/guides/standalone_toolchain).
  To compile OpenSSL with clang requires OpenSSL 1.1.1
  (https://github.com/openssl/openssl/pull/2229;
  https://github.com/openssl/openssl/blob/master/NOTES.ANDROID).
  As of 2019-06-15, the current version is OpenSSL 1.1.1c
  (https://www.openssl.org/). SQLCipher 4 supports OpenSSL 1.1.1
  (https://www.zetetic.net/blog/2018/11/30/sqlcipher-400-release/).
  As of 2019-06-15, the current version is SQLCipher 4.2.0.


Troubleshooting build_qt
~~~~~~~~~~~~~~~~~~~~~~~~

Problem: tar fails to work under Windows
########################################

.. code-block:: none

    ===============================================================================
    WORKING DIRECTORY: C:\Users\rudol\dev\qt_local_build\src\qt5
    PYTHON ARGS: ['tar', '-x', '-z', '--force-local', '-f', 'C:\\Users\\rudol\\dev\\qt_local_build\\src\\eigen\\eigen-3.3.3.tar.gz', '-C', 'C:\\Users\\rudol\\dev\\qt_local_build\\eigen']
    COMMAND: tar -x -z --force-local -f C:\Users\rudol\dev\qt_local_build\src\eigen\eigen-3.3.3.tar.gz -C C:\Users\rudol\dev\qt_local_build\eigen
    ===============================================================================
    tar: C\:\\Users\rudol\\dev\\qt_local_build\\eigen: Cannot open: No such file or directory

"How stupid," you might think. And the command works without the ``-C C:\...``
option (i.e. the ``-f`` parameter is happy with a full Windows path, but
``-C`` or its equivalent ``-directory=...`` isn't). This is with GNU tar v1.29
via Cygwin.

**Fixed** by using ``cardinal_pythonlib==1.0.46`` and the
``chdir_via_python=True`` argument to ``untar_to_directory``.


Problem: CL.EXE cannot open program database
############################################

**Problem (Windows):** ``fatal error C1041: cannot open program database
'...\openssl-1.1.0g\app.pdb'; if multiple CL.EXE write to the same .PDB file,
please use /FS``

... even when ``-FS`` is in use via jom_.

**Solution:** just run :ref:`build_qt` again; this error usually goes away.
Presumably the Qt jom_ tool doesn't always get things quite right with Visual
C++, and this error reflects parallel compilation processes clashing
occasionally. It's definitely worth persisting, because Jom saves no end of
time.

If it fails repeatedly, add the ``--nparallel 1`` option. (It seems to be the
OpenSSL build that's prone to failing; you can always interrupt the program
after OpenSSL has finished, and use the full number of CPU cores for the much
longer Qt build.)


Problem: aarch64-linux-android-gcc-4.9: not found
#################################################

You might see this when compiling for Android/64-bit ARM. The relevant arm64
cross-compiler is missing. See
https://stackoverflow.com/questions/28565640/build-kernel-with-aarch64-linux-gnu-gcc
and try e.g. ``sudo apt-get install gcc-aarch64-linux-gnu``.

.. todo:: IN PROGRESS ARM64
   ``sudo apt-get install gcc-4.9-aarch64-linux-gnu``



Run and set up Qt Creator
-------------------------

- **Run Qt Creator.**

- If you are compiling for Android:

  - Configure your Android SDK/NDK and Java JDK at: :menuselection:`Tools -->
    Options --> Android`, or in newer versions of Qt Creator,
    :menuselection:`Tools --> Options --> Devices --> Android --> Android
    Settings`.

- Proceed with the instructions below.


Qt versions
-----------

See :menuselection:`Tools --> Options --> Kits --> Qt Versions`, or on MacOS,
see :menuselection:`Qt Creator --> Preferences --> Kits --> Qt Versions`.

Assuming you set your qt_local_build directory to ``~/dev/qt_local_build``, the
:ref:`build_qt` script should have generated a series of ``qmake`` (or, under
Windows, ``qmake.exe``) files within that directory:

    =============================== ===========================================
    Operating system                qmake
    =============================== ===========================================
    Linux, x86 64-bit               ``qt_linux_x86_64_install/bin/qmake``
    Android, ARM 32-bit             ``qt_android_armv7_install/bin/qmake``
    Android, ARM 64-bit             ``qt_android_armv8_64_install/bin/qmake``
    Android emulator, x86 32-bit    ``qt_android_x86_32_install/bin/qmake``
    Mac OS/X, x86 64-bit            ``qt_osx_x86_64_install/bin/qmake``
    iOS, ARM 32-bit                 ``qt_ios_armv7_install/bin/qmake``
    iOS, ARM 64-bit                 ``qt_ios_armv8_64_install/bin/qmake``
    iOS Simulator, x86 64-bit       ``qt_ios_x86_64_install/bin/qmake``
    Windows, x86 32-bit             ``qt_windows_x86_32_install/bin/qmake``
    Windows, x86 64-bit             ``qt_windows_x86_64_install/bin/qmake``
    =============================== ===========================================

Select the correct ``qmake`` and it will be added as a Qt version. You can
change its name (prefixing "Custom" may be helpful to recognize it).


Qt kits
-------

See :menuselection:`Tools --> Options --> Kits --> Kits`, or on MacOS, see
:menuselection:`Qt Creator --> Preferences --> Kits --> Kits`.

Options last checked against Qt Creator 4.6.2 (built June 2018), then 4.8.1
(built Jan 2019) under Linux/Windows and 4.9.0 (built 11 Apr 2019) under MacOS.

.. note::

    If you did not install a version of Qt with Qt Creator, pick one of your
    own kits and choose "Make Default". Otherwise you will get the error
    ``Could not find qmake spec 'default'.`` (e.g. in the General Messages tab
    when you open your application) and the ``.pro`` (project) file will not
    parse. See https://stackoverflow.com/questions/27524680.

Non-default options are marked in bold and/or as "[non-default]".

**Custom_Linux_x86_64**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Linux_x86_64``
        * - File system name
          -
        * - Device type
          - **Desktop**
        * - Device
          - Local PC (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - GCC (C, x86 64bit in ``/usr/bin``)
        * - Compiler: C++
          - GCC (x86 64bit in ``/usr/bin``)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System GDB at ``/usr/bin/gdb``
        * - Qt version
          - **THE "LINUX 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at ``/usr/bin/cmake``
        * - CMake Generator
          - CodeBlocks - Unix Makefiles
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

**OLD_Custom_Android_ARM: DEPRECATED 32-BIT CONFIGURATION FOR GCC**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``OLD_Custom_Android_ARM``
        * - File system name
          -
        * - Device type
          - **Android Device**
        * - Device
          - Run on Android (default for Android)
        * - Sysroot
          -
        * - Compiler: C
          - <No compiler>
        * - Compiler: C++
          - Android GCC (C++, arm-4.9) [#androidgcc]_
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Android Debugger for Android GCC (C++, arm-4.9) [#androidgcc]_
        * - Qt version
          - **THE "ANDROID" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at ``/usr/bin/cmake``
        * - CMake Generator
          - CodeBlocks - Unix Makefiles
        * - CMake Configuration
          - [not editable]
        * - Additional Qbs Profile Settings
          -


**Custom_Android_ARM32: current 32-BIT configuration for clang**

    .. note::

        If you have not set up your Android NDK (see above), the "Qt Versions"
        tab will report "No compiler can produce code for this Qt version.
        Please define one or more compilers for: arm-linux-android-elf-32bit".

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_ARM32``
        * - File system name
          -
        * - Device type
          - **Android Device**
        * - Device
          - Run on Android (default for Android)
        * - Sysroot
          -
        * - Compiler: C
          - **Android Clang (C, arm)**
        * - Compiler: C++
          - **Android Clang (C++, arm)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - **Android Debugger for Android Clang (C++, arm)**
        * - Qt version
          - **THE "ANDROID, ARM 32-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at ``/usr/bin/cmake``
        * - CMake Generator
          - CodeBlocks - Unix Makefiles
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -


**Custom_Android_ARM64**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_ARM64``
        * - File system name
          -
        * - Device type
          - **Android Device**
        * - Device
          - Run on Android (default for Android)
        * - Sysroot
          -
        * - Compiler: C
          - **Android Clang (C, aarch64)**
        * - Compiler: C++
          - **Android Clang (C++, aarch64)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - **Android Debugger for Android Clang (C++, arm)**
        * - Qt version
          - **THE "ANDROID, ARM 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at ``/usr/bin/cmake``
        * - CMake Generator
          - CodeBlocks - Unix Makefiles
        * - CMake Configuration
          - [not editable]
        * - Additional Qbs Profile Settings
          -


**Custom_Android_x86** -- NOT FULLY TESTED

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_x86``
        * - File system name
          -
        * - Device type
          - **Android Device**
        * - Device
          - Run on Android (default for Android)
        * - Sysroot
          -
        * - Compiler: C
          - <No compiler>
        * - Compiler: C++
          - Android GCC (i686-4.9)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Android Debugger for Android GCC (i686-4.9)
        * - Qt version
          - **THE "ANDROID EMULATOR" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at ``/usr/bin/cmake``
        * - CMake Generator
          - CodeBlocks - Unix Makefiles
        * - CMake Configuration
          - [not editable]
        * - Additional Qbs Profile Settings
          -

**Custom_Windows_x86_64**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Windows_x86_64``
        * - File system name
          -
        * - Device type
          - **Desktop**
        * - Device
          - Local PC (default for Desktop)
        * - Sysroot
          - **[non-default]**
            ``[...]\qt_local_build\qt_windows_x86_64_install\bin``
        * - Compiler: C
          - **Microsoft Visual C++ Compiler 14.0 (amd64)**
        * - Compiler: C++
          - **Microsoft Visual C++ Compiler 14.0 (amd64)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Auto-detected CDB at ``C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe``
        * - Qt version
          - **THE "WINDOWS 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - **System CMake at** ``C:\Program Files (x86)\CMake\bin\cmake.exe``
        * - CMake Generator
          - CodeBlocks - MinGW Makefiles, Platform: <none>, Toolset: <none>
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

*Also works with: CMake Generator = CodeBlocks - NMake Makefiles JOM, Platform:
<none>, Toolset: <none>.*

**Custom_Windows_x86_32**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **``Custom_Windows_x86_32``**
        * - File system name
          -
        * - Device type
          - **Desktop**
        * - Device
          - Local PC (default for Desktop)
        * - Sysroot
          - **[non-default]**
            ``[...]\qt_local_build\qt_windows_x86_32_install\bin``
        * - Compiler: C
          - **Microsoft Visual C++ Compiler 14.0 (amd64_x86)**
        * - Compiler: C++
          - **Microsoft Visual C++ Compiler 14.0 (amd64_x86)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - None
        * - Qt version
          - **THE "WINDOWS 32-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - **System CMake at** ``C:\Program Files (x86)\CMake\bin\cmake.exe``
        * - CMake Generator
          -
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

.. note::

    For the Microsoft Visual C++ compiler, ``amd64`` means 64-bit and ``x86``
    means 32-bit. Then the two-part options are cross-compilers, in which the
    first part is the type of the host machine (the one running the compiler)
    and the second part is the type of the destination machine (the one that
    will run the compiled executable). Therefore, in full, ``x86`` produces
    32-bit output using a 32-bit compiler; ``amd64`` produces 64-bit output
    using a 64-bit compiler (i.e. requiring a 64-bit computer to do the
    compiling); ``x86_amd64`` produces 64-bit output using a 32-bit compiler
    (so you can build for 64-bit machines using a 32-bit machine), and
    ``amd64_x86`` produces 32-bit output using a 64-bit compiler. So, if you
    have a 64-bit machine, you probably want to use ``amd64_x86`` and
    ``amd64``; if you have a 32-bit machine, you definitely want to use ``x86``
    and ``x86_amd64``.


**Custom_MacOS_x86_64**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_MacOS_x86_64``
        * - File system name
          -
        * - Device type
          - **Desktop**
        * - Device
          - Local PC (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - GCC (C, x86 64bit in /usr/bin)
        * - Compiler: C++
          - Clang (C++, x86 64bit in /usr/bin)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System LLDB at /usr/bin/ldb
        * - Qt version
          - **THE "MACOS 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at /usr/local/bin/cmake
        * - CMake Generator
          - CodeBlocks - Unix Makefiles, Platform: <none>, Toolset: <none>
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

**Custom_iOS_armv8_64**

*BEING TESTED*

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_iOS_armv8_64``
        * - File system name
          -
        * - Device type
          - **iOS device**
        * - Device
          -
        * - Sysroot
          - **[non-default]**
            ``/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk``
        * - Compiler: C
          - **Apple Clang (arm64)**
        * - Compiler: C++
          - **Apple Clang (arm64)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System LLDB at /usr/bin/ldb
        * - Qt version
          - **THE "iOS 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at /usr/local/bin/cmake
        * - CMake Generator
          - CodeBlocks - Unix Makefiles, Platform: <none>, Toolset: <none>
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

If Qt accept the settings, a section marked "iOS Settings" will appear in the
"Build Settings" part of your project when configured for this kit.

**Custom_iOS_Simulator_x86_64**

*BEING TESTED*

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_iOS_Simulator_x86_64``
        * - File system name
          -
        * - Device type
          - **iOS Simulator**
        * - Device
          - iOS Simulator (default for iOS Simulator)
        * - Sysroot
          - **[non-default]**
            ``/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator.sdk``
        * - Compiler: C
          - GCC (C, x86 64bit in /usr/bin)
        * - Compiler: C++
          - Clang (C++, x86 64bit in /usr/bin)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System LLDB at /usr/bin/ldb
        * - Qt version
          - **THE "iOS SIMULATOR 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at /usr/local/bin/cmake
        * - CMake Generator
          - CodeBlocks - Unix Makefiles, Platform: <none>, Toolset: <none>
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

If Qt accept the settings, a section marked "iOS Settings" will appear in the
"Build Settings" part of your project when configured for this kit.


Build settings
--------------

Android
~~~~~~~

Under :menuselection:`Project --> Build Settings --> Build Steps --> Build
Android APK`:

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - :menuselection:`Application --> Android build SDK`
          - **PREVIOUSLY:** android-23 [= default].
            **NOW:** android-28 [= default].
        * - :menuselection:`Sign package --> Keystore`
          - ``~/Documents/CamCOPS/android_keystore/CAMCOPS_ANDROID_KEYSTORE.keystore``
            [NB not part of published code, obviously!]
        * - :menuselection:`Sign package --> Sign package`
          - Yes (at least for release versions)
        * - :menuselection:`Advanced actions --> Use Ministro service to
            install Qt`
          - Do NOT tick. (Formerly, before 2018-06-25, this was
            :menuselection:`Qt deployment --> Bundle Qt libraries in APK`. The
            objective remains to bundle Qt, not to install it via Ministro.)
        * - Additional libraries
          - ``~/dev/qt_local_build/openssl_android_armv7_build/openssl-1.1.0g/libcrypto.so``
            ``~/dev/qt_local_build/openssl_android_armv7_build/openssl-1.1.0g/libssl.so``


Then in the file ``AndroidManifest.xml`` (which Qt Creator has a custom editor
for):

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Package name
          - org.camcops.camcops
        * - Version code
          - [integer; may as well use consecutive]
        * - Version name
          - [string]
        * - Minimum required SDK
          - API 23 (Android 6) (see :ref:`changelog 2018 <changelog_2018>`)
        * - Target SDK
          - API 28 (Android 9) = minimum required by Google Play Store as of
            2019-11-01.
        * - Application name
          - CamCOPS
        * - Activity name
          - CamCOPS
        * - Run
          - camcops
        * - Application icon
          - [icon]
        * - Include default permissions for Qt modules
          - [tick]
        * - Include default features for Qt modules
          - [tick]
        * - Boxes for other permissions
          - [no other specific permission requested]

    But then you must also edit ``AndroidManifest.xml`` manually to include the
    line:

      .. code-block:: none

            <meta-data android:name="android.app.load_local_libs" android:value="-- %%INSERT_LOCAL_LIBS%% --:lib/libssl.so:lib/libcrypto.so"/>
            Note this bit:                                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For versions, see:

- https://developer.android.com/guide/topics/manifest/manifest-element.html
- https://developer.android.com/studio/publish/versioning.html

If you run this without a keystore, it produces a debug build (e.g.
``QtApp-debug.apk``). If you run it with a keystore/signature, it produces
``android-build-release-signed.apk`` (formerly ``QtApp-release-signed.apk``).
The APK filename is fixed at this point
(https://forum.qt.io/topic/43329/qt-5-3-1-qtcreator-rename-qtapp-debug-apk-to-myapp).
We can rename the APK if we want, or just upload to Google Play, distribute,
etc.

Qt will forget your "sign package" choice from time to time; get back to it via
:menuselection:`Projects --> [Custom Android ARM or whatever you called it] -->
Build Android APK --> Sign package`.


Linux
~~~~~

Under :menuselection:`Run Settings --> Run Environment`, set
``LD_LIBRARY_PATH`` to point to the OpenSSL libraries we've built, e.g.
``LD_LIBRARY_PATH=/home/rudolf/dev/qt_local_build/openssl_linux_x86_64_build/openssl-1.1.1c/``

You can also set this under :menuselection:`Build Settings --> Build
Environment`, because the default behaviour is for the run environment to
inherit the build environment.


iOS
~~~

*TO BE ADDED.*

See:

- https://doc.qt.io/qt-5/ios.html
- https://doc.qt.io/qtcreator/creator-developing-ios.html
- https://doc.qt.io/qt-5/ios-platform-notes.html

.. todo:: custom ios/Info.plist as per https://doc.qt.io/qt-5/ios-platform-notes.html

.. todo:: iOS appicons as per https://doc.qt.io/qt-5/ios-platform-notes.html

General
~~~~~~~

(I'd like to put general settings in a ``camcops.pro.shared`` file, as per
http://doc.qt.io/qtcreator/creator-sharing-project-settings.html, but this
isn't working well at present.)

- Open the ``camcops.pro`` project file in Qt Creator.

- Add your chosen kit(s) to the CamCOPS project.

- Use defaults, except everywhere you see :menuselection:`Build Settings -->
  Build Steps --> Make --> Make arguments`, add ``-j 8`` for an
  8-CPU machine to get it compiling in parallel.

  - To save this effort, set ``MAKEFLAGS="-j8"`` in your user environment (e.g.
    in ``~/.bashrc``, or ``~/.profile``); see
    https://stackoverflow.com/questions/8860712/setting-default-make-options-for-qt-creator.
    HOWEVER, Qt Creator doesn't seem to read that environment variable for me.
    Not sure why!

- Build.


Once built, see :ref:`Releasing CamCOPS <dev_releasing>`.


Notes
-----

Debugging
~~~~~~~~~

- DON'T FORGET to set up both Debug and Release (+/- Profile) builds.

- Phone USB debugging negotiation sometimes takes a while. On the Samsung
  Galaxy phone, the alert light goes red when in Debug mode.

- If a USB Android device appears not to connect (via ``adb devices``), appears
  then disappears as you connect it (via ``lsusb | wc``), and gives the
  ``dmesg`` error ``device descriptor read/64, error -71`` or similar, try a
  different cable (see
  https://stackoverflow.com/questions/9544557/debian-device-descriptor-read-64-error-71);
  try also plugging it directly into the computer's USB ports rather than
  through a hub.

- If you lose the debugger windows in Qt Creator midway through a debug
  session, press Ctrl-4.

- This error (with a variety of compiler names):

  .. code-block:: none

    .../mkspecs/features/toolchain.prf(50): system(execute) requires one or two arguments.
    Project ERROR: Cannot run compiler 'g++'. Maybe you forgot to setup the environment?

  means that you need to re-run qmake manually. It usually occurs if you delete
  your build* directories.

- For debugging, consider install Valgrind_: ``sudo apt install valgrind``


Android debugging
~~~~~~~~~~~~~~~~~

- Android logs

  - The default Android log format from ``adb logcat`` is  explained at
    https://developer.android.com/studio/debug/am-logcat.html. That format is

    .. code-block:: none

        date time PID-TID/package priority/tag: message
        e.g.
        12-10 13:02:50.071 1901-4229/com.google.android.gms V/AuthZen: Handling delegate intent.

        but actually looks like

        06-18 23:47:48.731 28303 28344 E         : dlsym failed: undefined symbol: main
        06-18 23:47:48.731 28303 28344 E         : Could not find main method

  - So do:

  - Search for "Force finishing activity".

- Better, though, is to launch from Qt Creator, which automatically filters
  (and does so very well).


Troubleshooting qmake/compilation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Sometimes you have to restart Qt creator after creating new build settings;
  it loses its .pro file and won't show the project, or complains of a missing
  .pro file when you try to build.

- The first build can be very slow as it compiles all the resources; this
  usually looks like a process stuck compiling qrc_camcops.cpp to qrc_camcops.o

- If builds are very slow, you may have forgotten to use all your CPU cores;
  try e.g. ``-j 8`` (for 8 cores) as an argument to make, as above.

- If an Android build fails for a bizarre reason (like garbage in a .java file
  that looks like it's been pre-supplied), delete the whole build directory,
  which is not always removed by cleaning.

- ``Error: "unsupported_android_version" is not translated``: see
  https://bugreports.qt.io/browse/QTBUG-63952. This error does not prevent you
  from continuing.

- This error whilst building CamCOPS:

  .. code-block:: none

    /home/rudolf/dev/qt_local_build/qt_linux_x86_64_install/bin/qmlimportscanner: error while loading shared libraries: libicui18n.so.55: cannot open shared object file: No such file or directory
    /home/rudolf/dev/qt_local_build/qt_linux_x86_64_install/mkspecs/features/qt.prf:312: Error parsing JSON at 1:1: illegal value
    Project ERROR: Failed to parse qmlimportscanner output.

  ... occurred after an upgrade from Ubuntu 16.04 to 18.04; the problem relates
  to missing OS libraries (``libicu``); the easiest thing is to rebuild Qt.

- This error whilst building CamCOPS:

  .. code-block:: none

    /usr/bin/x86_64-linux-gnu-ld: cannot find -ludev
    Makefile:2433: recipe for target 'camcops' failed
    collect2: error: ld returned 1 exit status

  ... use ``sudo apt install libudev-dev``.

- This error whilst building CamCOPS under Windows 10:

  .. code-block:: none

    :-1: error: dependent 'C:\Users\rudol\dev\qt_local_build\qt_windows_x86_64_install\lib\Qt5MultimediaWidgetsd.lib' does not exist.

  Try switching from "debug" to "release" build.


Troubleshooting running CamCOPS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Runtime error, failing to find ``libssl.so`` or ``libcrypto.so``:

  .. code-block:: none

    Starting /.../camcops...
    /.../camcops: error while loading shared libraries: libssl.so: cannot open shared object file: No such file or directory
    /.../camcops exited with code 127

  CamCOPS needs the ``libssl.so`` and ``libcrypto.so`` that was built by
  :ref:`build_qt`. Until we have a proper Linux client distribution, do this:

  .. code-block:: bash

    $ export LD_LIBRARY_PATH=~/dev/qt_local_build/openssl_linux_x86_64_build/openssl-1.1.0g/

  ... or wherever you built those ``.so`` libraries. Then re-run the CamCOPS
  .client.


- This error whilst running CamCOPS (Ubuntu 18.04):

  .. code-block:: none

    Starting /.../camcops...
    /.../camcops: error while loading shared libraries: libOpenVG.so.1: cannot open shared object file: No such file or directory
    /.../camcops exited with code 127

  Thoughts:

  .. code-block:: bash

    # Which files have similar names?

    $ find -L / -type f -name "libOpenVG.so*" 2>/dev/null
    /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so.1       # symlink to libOpenVG.so.1.0.0
    /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so.1.0.0   # actual file
    /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so         # symlink to libOpenVG.so.1.0.0
    /usr/lib/x86_64-linux-gnu/libOpenVG.so                  # symlink to mesa-egl/libOpenVG.so

    # Which packages provide these files?

    $ dpkg --search libOpenVG
    libopenvg1-mesa:amd64: /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so.1.0.0
    libopenvg1-mesa-dev: /usr/lib/x86_64-linux-gnu/libOpenVG.so
    libopenvg1-mesa-dev: /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so
    libopenvg1-mesa:amd64: /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so.1

    # Ergo, the problem can be solved with:

    $ sudo ln -s /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so.1 /usr/lib/x86_64-linux-gnu/libOpenVG.so.1

    # Yup, that fixes it.

  Solution:

  .. code-block:: bash

    sudo ln -s /usr/lib/x86_64-linux-gnu/mesa-egl/libOpenVG.so.1 /usr/lib/x86_64-linux-gnu/libOpenVG.so.1

.. That symlink implemented manually on wombat, osprey


===============================================================================

.. rubric:: Footnotes

.. [#androidgcc]
    Prior to Qt 5.12.0, the compiler was "Android GCC (arm-4.9)", and the
    debugger was "Android Debugger for Android GCC (arm-4.9)".
