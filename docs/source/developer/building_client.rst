..  docs/source/developer/building_client.rst

..  Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).
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
.. _Android SDK: https://developer.android.com/tools/releases/platform-tools
.. _Chocolatey: https://chocolatey.org/
.. _CMake: https://cmake.org/
.. _Debugging Tools for Windows: https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/
.. _Git: https://git-scm.com/
.. _ImageMagick: https://www.imagemagick.org/
.. _Inno Setup: http://www.jrsoftware.org/isinfo.php
.. _MSYS2: https://www.msys2.org/
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

The CamCOPS client is written in C++11 using the Qt_ cross-platform
framework. We provide a custom python script to build Qt from source, along with
its dependencies (OpenSSL, SQLCipher and FFmpeg). CamCOPS can then be compiled
and linked with this custom version of Qt. This can be done within Qt Creator,
which confusingly is bundled with a second, official distribution of Qt.

..  contents::
    :local:
    :depth: 3


Prerequisites
-------------

**Ensure the following prerequisites are met:**
https://wiki.qt.io/Building_Qt_6_from_Git


Linux
~~~~~

- Linux should come with Python and the necessary build tools. The build script
  should warn about any missing ones, which should all be installable with
  your package manager.

- See
  https://github.com/ucam-department-of-psychiatry/camcops/blob/master/.github/workflows/build-qt.yml
  for the installation requirements on Ubuntu 20.04 and 22.04 (GitHub hosted
  runners).


Android (with a Linux build host)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- To build Android programs under Linux, you will also need a Java development
  kit (JDK), such as OpenJDK: ``sudo apt install openjdk-17-jdk``. If you are
  switching between different versions of Java, you can set up a symbolic link
  to /usr/lib/jvm/default-java:

  .. code-block:: bash

    ln -s /usr/lib/jvm/java-17-openjdk-amd64 /usr/lib/jvm/default-java

- You will also need to install `Android SDK_`.
  **The current Android SDK target version** is shown in
  ``AndroidManifest.xml``. **This is the version you need to install.**

- Set up a script file with variables like these:

  .. code-block:: bash

    export JAVA_HOME=/usr/lib/jvm/default-java
    export ANDROID_SDK_ROOT="/path/to/your/android-sdk"
    export ANDROID_NDK_ROOT="${ANDROID_SDK_ROOT}/ndk"
    export ANDROID_NDK_HOME="${ANDROID_NDK_ROOT}"
    export PATH="$PATH:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/cmdline-tools/tools/bin"

  Source it when you want to use Android tools. Alternatively add these line to
  your ``.profile`` (or similar) so they are set up automatically whenever you
  log in.

- In Qt Creator, under ``Preferences --> Devices --> Android`` set ``JDK
  location:`` to ``/usr/lib/jvm/default-java``. Select the currently supported
  NDK version in Android NDK list and make it the default. See
  https://doc.qt.io/qt-6.5/android-getting-started.html.

- If Qt complains about e.g. ``failed to find Build Tools revision 19.1.0``,
  then you can use ``sdkmanager --list`` and then install with e.g.
  ``sdkmanager "build-tools;19.1.0"``, or in Qt Creator's ``Tools --> Options
  --> Devices --> Android --> SDK Manager``..

- Note some Android SDK version constraints:

  - Google Play store requires ``targetSdkVersion`` to be at least 33 from
    2023-08-31
    (https://developer.android.com/google/play/requirements/target-sdk).

  - Above Android API 23, linking to non-public libraries is prohibited,
    possibly with exceptions for SSL/crypto.

    - https://android-developers.googleblog.com/2016/06/android-changes-for-ndk-developers.html
    - https://developer.android.com/about/versions/nougat/android-7.0-changes#ndk

  - Android libraries should be compiled for the same SDK version as
    ``minSdkVersion`` in ``AndroidManifest.xml`` (see
    https://stackoverflow.com/questions/21888052/what-is-the-relation-between-app-platform-androidminsdkversion-and-androidtar/41079462#41079462,
    and https://developer.android.com/ndk/guides/stable_apis).

.. todo:: Maybe "Include prebuilt OpenSSL libraries" will simplify things?


Windows
~~~~~~~

- Install a recent version of Python_. Make sure it's on your ``PATH``.

- Install a Microsoft Visual C++ compiler. A free one is `Visual Studio`_
  Community. As you install Visual Studio, don't forget to tick the C++
  options.

- Install these other tools. Many are available with Chocolatey_.

  - CMake_. (We'll use this version of cmake to build CamCOPS.)

  - MSYS2_. Use this to install other build tools.
    ``C:\tools\msys64\usr\bin\bash`` then ``$ pacman -S make yasm diffutils``.

  - NASM_, the Netwide Assembler for x86-family processors.

  - ActiveState TCL_. (SQLCipher requires ``tclsh``.)

  - ActiveState Perl_. or Strawberry Perl. (OpenSSL requires ``perl``.)

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

        C:\tools\msys64
        C:\tools\msys64\usr\bin
        C:\Program Files\NASM
        C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build

        -- These are usually added automatically by installers:

        C:\Program Files\Git\cmd
        C:\ActiveTcl\bin
        C:\Perl64\bin

  - Do make sure that the ``PATH`` doesn't have an unquoted ampersand in; this
    is technically legal but it causes no end of trouble (see :ref:`build_qt`).
    (The usual culprit is MySQL.) The :ref:`build_qt` script will check this.

- Tested and as part of our continuous integration process on GitHub (see
  https://github.com/ucam-department-of-psychiatry/camcops/blob/master/.github/workflows/build-qt.yml )
  and as of 2023-12-21:
  .. code-block:: none

    ActivePerl 5.28.1 build 2801 (64-bit)
    ActiveTcl 8.6.7 build 0 (64-bit)
    CCache 3.7.12
    CMake 3.25.1 (64-bit)
    Microsoft Visual Studio Community 2019
    MSYS2 20231026.0.0
    NASM 2.14.02 (64-bit)
    Python 3.9.13
    Qt Creator 4.10.1
    Windows 10 (64-bit)
    Yasm 1.2.0


macOS (formerly OS X)
~~~~~~~~~~~~~~~~~~~~~

- See :ref:`Setting up an iMac for CamCOPS development <set_up_imac_for_dev>`.

- Tested in Feb 2021 with:

  .. code-block:: none

    # macOS Catalina 10.15.7
    # Xcode 12.4 (macOS SDK 11.1; iOS SDK 14.4)
    build_qt --build_macos_x86_64


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

        * - CAMCOPS_QT6_BASE_DIR
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
          - ``C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Redist\MSVC\14.29.30133``
          - Used by the Windows Inno Setup script.

- Fetch CamCOPS. For example, for the GitHub version:

  .. code-block:: bash

    # Linux
    git clone https://github.com/ucam-department-of-psychiatry/camcops $CAMCOPS_SOURCE_DIR

  .. code-block:: bat

    REM Windows
    git clone https://github.com/ucam-department-of-psychiatry/camcops %CAMCOPS_SOURCE_DIR%

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

Build a copy of Qt and supporting tools (OpenSSL, SQLCipher, FFmpeg) from source using
the CamCOPS :ref:`build_qt` tool (q.v.). For example:

.. code-block:: bash

    # Linux
    $CAMCOPS_SOURCE_DIR/tablet_qt/tools/build_qt.py --build_all

.. code-block:: bat

    REM Windows
    python %CAMCOPS_SOURCE_DIR%/tablet_qt/tools/build_qt.py --build_all


Version constraints for OpenSSL and SQLCipher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Qt 6.5 supports OpenSSL 3.0.x

- OpenSSL 3.0.x is the current LTS version, supported until 2026-09-07.
  https://www.openssl.org/policies/releasestrat.html

- SQLCipher 4.4.5 supports OpenSSL 3.0.x



Troubleshooting build_qt
~~~~~~~~~~~~~~~~~~~~~~~~

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


.. note::

    If you did not install a version of Qt with Qt Creator, pick one of your
    own kits and choose "Make Default". Otherwise you will get the error
    ``Could not find qmake spec 'default'.`` (e.g. in the General Messages tab
    when you open your application) and the ``.pro`` (project) file will not
    parse. See https://stackoverflow.com/questions/27524680.

Non-default options are marked in bold and/or as "[non-default]".

**Custom_Linux_x86_64**

- Last checked against Qt Creator 11.0.2 (built Aug 2023).

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Linux_x86_64``
        * - File system name
          -
        * - Run device type
          - Desktop
        * - Run device
          - Desktop (default for Desktop)
        * - Build device
          - Desktop (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - GCC (C, x86 64bit in ``/usr/bin``)
        * - Compiler: C++
          - GCC (C++, x86 64bit in ``/usr/bin``)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System GDB at ``/usr/bin/gdb``
        * - Qt version
          - **THE "LINUX 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - System CMake at ``/usr/bin/cmake``
        * - CMake generator
          - [not editable: "Ninja"]
        * - CMake Configuration
          - ``-DQT_QMAKE_EXECUTABLE:FILEPATH=%{Qt:qmakeExecutable}``
            ``-DCMAKE_PREFIX_PATH:PATH=%{Qt:QT_INSTALL_PREFIX}``
            ``-DCMAKE_C_COMPILER:FILEPATH=%{Compiler:Executable:C}``
            ``-DCMAKE_CXX_COMPILER:FILEPATH=%{Compiler:Executable:Cxx}``

**Custom_Android_ARM32: 32-BIT configuration for clang**

- Last checked against Qt Creator 11.0.2 (built 12 Aug 2023) under Linux.

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_ARM32``
        * - File system name
          -
        * - Run device type
          - Android Device
        * - Run device
          - **YOUR DEVICE**
        * - Build device
          - Desktop (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - **Android Clang (C, arm, NDK 25.1.8937393)**
        * - Compiler: C++
          - **Android Clang (C++, arm, NDK 25.1.8937393)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - **Android Debugger (armeabi-v7a, NDK 25.1.8937393)**
        * - Qt version
          - **THE "ANDROID, ARM 32-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - CMake 3.24.2 (Qt)
        * - CMake Generator
          - Ninja
        * - CMake Configuration
          - ``-DQT_QMAKE_EXECUTABLE:FILEPATH=%{Qt:qmakeExecutable}``
            ``-DCMAKE_PREFIX_PATH:PATH=%{Qt:QT_INSTALL_PREFIX}``
            ``-DCMAKE_C_COMPILER:FILEPATH=%{Compiler:Executable:C}``
            ``-DCMAKE_CXX_COMPILER:FILEPATH=%{Compiler:Executable:Cxx}``


**Custom_Android_ARM64**

- Last checked against Qt Creator 11.0.2 (built 12 Aug 2023) under Linux.

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_ARM64``
        * - File system name
          -
        * - Run device type
          - Android Device
        * - Run device
          - **YOUR DEVICE**
        * - Build device
          - Desktop (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - **Android Clang (C, aarch64, NDK 25.1.8937393)**
        * - Compiler: C++
          - **Android Clang (C++, aarch64, NDK 25.1.8937393)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - **Android Debugger (arm64-v8a, NDK 25.1.8937393)**
        * - Qt version
          - **THE "ANDROID, ARM 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - CMake 3.24.2 (Qt)
        * - CMake Generator
          - Ninja
        * - CMake Configuration
          - ``-DQT_QMAKE_EXECUTABLE:FILEPATH=%{Qt:qmakeExecutable}``
            ``-DCMAKE_PREFIX_PATH:PATH=%{Qt:QT_INSTALL_PREFIX}``
            ``-DCMAKE_C_COMPILER:FILEPATH=%{Compiler:Executable:C}``
            ``-DCMAKE_CXX_COMPILER:FILEPATH=%{Compiler:Executable:Cxx}``

**Custom_Android_x86**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_x86``
        * - File system name
          -
        * - Run device type
          - Android Device
        * - Run device
          - Pixel_3a_API_30_x86
        * - Build device
          - Desktop (default for Desktop)
        * - Compiler: C
          - Android Clang (C, i686, NDK 25.1.8937393)
        * - Compiler: C++
          - Android Clang (C++, i686, NDK 25.1.8937393)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Android Debugger (Multi-Abi, NDK 25.1.8937393)
        * - Sysroot
          -
        * - Qt version
          - **THE "ANDROID EMULATOR" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - CMake 3.24.2 (Qt)
        * - CMake Generator
          - Ninja
        * - CMake Configuration
          - [not editable]
        * - Python
          - None

**Custom_Android_x86_64**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_Android_x86_64``
        * - File system name
          -
        * - Run device type
          - Android Device
        * - Run device
          - Pixel_3a_API_34
        * - Build device
          - Desktop (default for Desktop)
        * - Compiler: C
          - Android Clang (C, x86_64, NDK 25.1.8937393)
        * - Compiler: C++
          - Android Clang (C++, x86_64, NDK 25.1.8937393)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Android Debugger (Multi-Abi, NDK 25.1.8937393)
        * - Sysroot
          -
        * - Qt version
          - **THE "ANDROID EMULATOR" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - CMake 3.24.2 (Qt)
        * - CMake Generator
          - Ninja
        * - CMake Configuration
          - [not editable]
        * - Python
          - None


**Custom_Windows_x86_64**

- Last checked against Qt Creator 4.8.1 (built Jan 2019).

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

- Last checked against Qt Creator 4.8.1 (built Jan 2019).

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

- Last checked against Qt Creator 11.0.3 (built 27 Sep 2023).

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_MacOS_x86_64``
        * - File system name
          -
        * - Run device type
          - Desktop
        * - Run device
          - Desktop (default for Desktop)
        * - Build device
          - Desktop (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - Clang (C, x86 64bit in /usr/bin)
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
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - System CMake at /usr/local/bin/cmake
        * - CMake Generator
          - Ninja
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``

**Custom_iOS_armv8_64**

- Last checked against Qt Creator 11.0.3 (built 27 Sep 2023).

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - **[non-default]** ``Custom_iOS_armv8_64``
        * - File system name
          -
        * - Run device type
          - iOS device
        * - Run device
          - **YOUR DEVICE**
        * - Build device
          - Desktop (default for Desktop)
        * - Sysroot
          -
        * - Compiler: C
          - **Apple Clang (arm64)**
        * - Compiler: C++
          - **Apple Clang (arm64)**
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System LLDB at /usr/bin/lldb
        * - Qt version
          - **THE "iOS 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
          -
        * - CMake Tool
          - System CMake at /usr/local/bin/cmake
        * - CMake Generator
          - Xcode
        * - CMake Configuration
          - ``-DQT_QMAKE_EXECUTABLE:FILEPATH=%{Qt:qmakeExecutable}``
            ``-DCMAKE_PREFIX_PATH:PATH=%{Qt:QT_INSTALL_PREFIX}``
            ``-DCMAKE_C_COMPILER:FILEPATH=%{Compiler:Executable:C}``
            ``-DCMAKE_CXX_COMPILER:FILEPATH=%{Compiler:Executable:Cxx}``

If Qt accept the settings, a section marked "iOS Settings" will appear in the
"Build Settings" part of your project when configured for this kit.

**Custom_iOS_Simulator_x86_64**

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
          - Apple Clang (x86_64)
        * - Compiler: C++
          - Apple Clang (x86_64)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - System LLDB at /Applications/Xcode.app/Contents/Developer/usr/bin/lldb
        * - Qt version
          - **THE "iOS SIMULATOR 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - Additional Qbs Profile Settings
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
        * - :menuselection:`Application --> Android build platform SDK`
          - android-33 [= default].
        * - :menuselection:`Sign package --> Keystore`
          - ``~/Documents/CamCOPS/android_keystore/CAMCOPS_ANDROID_KEYSTORE.keystore``
            [NB not part of published code, obviously!]
        * - :menuselection:`Sign package --> Sign package`
          - Yes (at least for release versions)
        * - Additional libraries
          - ``~/dev/qt6_local_build/openssl_android_armv8_64_build/openssl-3.0.12/libcrypto_3.so``
            ``~/dev/qt6_local_build/openssl_android_armv7_build/openssl-3.0.12/libssl_3.so``


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


iOS
~~~

See:

- https://doc.qt.io/qt-6.5/ios.html
- https://doc.qt.io/qtcreator/creator-developing-ios.html
- https://doc.qt.io/qt-6.5/ios-platform-notes.html

It is possible to deploy to an actual device via USB or the iOS simulator using
a development provisioning profile associated with an Apple developer ID. You
need to enable developer mode on the device.

Some build/deploy problems can be solved by restarting Qt Creator, XCode and
any running iOS simulator but check the error messages in Qt Creator first.


MacOS
-----

See:

- https://doc.qt.io/qt-6.5/macos.html


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

  - That includes the Java error "duplicate class", e.g. ``error: duplicate
    class: org.qtproject.qt5.android.bindings.QtLoader``
    (https://stackoverflow.com/questions/43774714).

- ``Error: "unsupported_android_version" is not translated``: see
  https://bugreports.qt.io/browse/QTBUG-63952. This error does not prevent you
  from continuing.

- This error whilst building CamCOPS:

  .. code-block:: none

    /home/rudolf/dev/qt_local_build/qt_linux_x86_64_install/bin/qmlimportscanner:
    error while loading shared libraries: libicui18n.so.55: cannot open shared
    object file: No such file or directory
    /home/rudolf/dev/qt_local_build/qt_linux_x86_64_install/mkspecs/features/qt.prf:312:
    Error parsing JSON at 1:1: illegal value
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

    :-1: error: dependent
    'C:\Users\rudol\dev\qt_local_build\qt_windows_x86_64_install\lib\Qt5MultimediaWidgetsd.lib'
    does not exist.

  Try switching from "debug" to "release" build.

- Missing header files or libraries under Ubuntu/Debian Linux:

  - For example, for the error "cannot find -lgstphotography-1.0", try
    ``apt-file search gstphotography``, or ``apt-file search
    gstphotography-1.0.so`` if you get too many results. Prefer packages with a
    ``-dev`` suffix as these have development headers.

  - Likewise, for the error "GL/gl.h: No such file or directory", try
    ``apt-file search GL/gl.h``. (Here the missing package is ``libgl-dev``.)


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
