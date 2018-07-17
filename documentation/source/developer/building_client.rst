..  documentation/source/developer/building_client.rst

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

.. _Qt: https://www.qt.io/
.. _Valgrind: http://valgrind.org/

Building the CamCOPS client
===========================

Prerequisites
-------------

You will need Qt_ (with Qt Creator) and you will need to build a copy of Qt
from source using the CamCOPS :ref:`build_qt` tool.

Qt versions
-----------

Assuming you set your qt_local_build directory to ``~/dev/qt_local_build``, the
``build_qt.py`` script should generate a series of ``qmake`` (or, under
Windows, ``qmake.exe``) files within that directory:

    ==================  ==============================================
    Operating system    qmake
    ==================  ==============================================
    Linux 64-bit        qt_linux_x86_64_install/bin/qmake
    Android (ARM)       qt_android_armv7_install/bin/qmake
    Android emulator    qt_android_x86_32_install/bin/qmake
    Mac OS/X 64-bit     qt_osx_x86_64_install/bin/qmake
    iOS (ARM)           qt_ios_armv8_64_install/bin/qmake
    iOS Simulator       qt_ios_x86_64_install/bin/qmake
    Windows 32-bit      qt_windows_x86_32_install/bin/qmake
    Windows 64-bit      qt_windows_x86_64_install/bin/qmake
    ==================  ==============================================


Qt kits
-------

Options last checked against Qt Creator 4.6.2 (built June 2018).

**Custom_Linux_x86_64**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - ``Custom_Linux_x86_64``
        * - File system name
          -
        * - Device type
          - Desktop
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
          - [not editable]
        * - Additional Qbs Profile Settings
          -

**Custom_Android_ARM**

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - ``Custom_Android_ARM``
        * - File system name
          -
        * - Device type
          - Android Device
        * - Device
          - Run on Android (default for Android)
        * - Sysroot
          -
        * - Compiler: C
          - <No compiler>
        * - Compiler: C++
          - Android GCC (arm-4.9)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Android Debugger for Android GCC (arm-4.9)
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

**Custom_Android_x86** -- NOT FULLY TESTED

    .. list-table::
        :header-rows: 1
        :stub-columns: 1

        * - Option
          - Setting
        * - Name
          - ``Custom_Android_x86``
        * - File system name
          -
        * - Device type
          - Android Device
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
          - ``Custom_Windows_x86_64``
        * - File system name
          -
        * - Device type
          - Desktop
        * - Device
          - Local PC (default for Desktop)
        * - Sysroot
          - ``[...]\qt_local_build\qt_windows_x86_64_install\bin``
        * - Compiler: C
          - Microsoft Visual C++ Compiler 14.0 (amd64)
        * - Compiler: C++
          - Microsoft Visual C++ Compiler 14.0 (amd64)
        * - Environment
          - [not editable: "No changes to apply."]
        * - Debugger
          - Auto-detected CDB at ``C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe``
        * - Qt version
          - **THE "WINDOWS 64-BIT" ONE FROM QT VERSIONS, ABOVE**
        * - Qt mkspec
          -
        * - CMake Tool
          - System CMake at ``C:\Program Files (x86)\CMake\bin\cmake.exe``
        * - CMake Generator
          - CodeBlocks - MinGW Makefiles, Platform: <none>, Toolset: <none>
        * - CMake Configuration
          - ``CMAKE_CXX_COMPILER:STRING=%{Compiler:Executable:Cxx}``
            ``CMAKE_C_COMPILER:STRING=%{Compiler:Executable:C}``
            ``CMAKE_PREFIX_PATH:STRING=%{Qt:QT_INSTALL_PREFIX}``
            ``QT_QMAKE_EXECUTABLE:STRING=%{Qt:qmakeExecutable}``
        * - Additional Qbs Profile Settings
          -

Build settings
--------------

... let's put them in a ``camcops.pro.shared`` file:
http://doc.qt.io/qtcreator/creator-sharing-project-settings.html

General
~~~~~~~

- Use defaults, except everywhere you see :menuselection:`Build Settings -->
  Build Steps --> Make --> Make arguments`, add ``-j 8`` for an
  8-CPU machine to get it compiling in parallel.

  - To save this effort, set ``MAKEFLAGS="-j8"`` in your user environment (e.g.
    in ``~/.bashrc``, or ``~/.profile``); see
    https://stackoverflow.com/questions/8860712/setting-default-make-options-for-qt-creator.
    HOWEVER, Qt Creator doesn't seem to read that environment variable for me.
    Not sure why!

Android
~~~~~~~

Under :menuselection:`Build Settings --> Build Steps --> Build Android APK`:

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
          - API 16: Android 4.1, 4.1.1 [default]
        * - Target SDK
          - **WAS:** API 23: Android 6.0 [default].
            **AS OF 2018-06-25:** API 26: Android 8.0 [Google Play Store
            requires this soon].
            **DOWNGRADED AGAIN 2018-07-16: OpenSSL problems.** Probably because
            you have to rebuild OpenSSL for Android (see
            ``DEFAULT_ANDROID_API_NUM`` in ``build_qt.py``).
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
The APK name is fixed at this point
(https://forum.qt.io/topic/43329/qt-5-3-1-qtcreator-rename-qtapp-debug-apk-to-myapp).
We can rename the APK if we want, or just upload to Google Play, distribute,
etc.

Linux
~~~~~

Under :menuselection:`Build Settings --> Build Environment``, set e.g.
``LD_LIBRARY_PATH=/home/rudolf/dev/qt_local_build/openssl_linux_x86_64_build/openssl-1.1.0g/``

===============================================================================
Google Play Store settings
===============================================================================

- Developer URL is https://play.google.com/apps/publish
  --> pick your application
  --> e.g. Release management / App releases

- App category: "Utility/other".

- Content rating: by Google's definitions, CamCOPS hits criteria for references
  to illegal drugs (e.g. Deakin1HealthReview, and when strings are available,
  the various drug abuse scoring scales). Did not meet Google Play's criteria
  for sex, violence, etc.

- Note that "Pending publication" means you're waiting for Google Play to sort
  itself out, not that you have to do anything.

- Note re versions:

  - As above, the AndroidManifest.xml has an INTEGER version, so we may as
    well use consecutive numbers. See the release history below.

  The Google Developer site will check the version codes.
  Failed uploads can sometimes block that version number.

- You upload a new version with "App releases" / "Create Release".

- Note also that if you try to install the .apk directly to a device that's
  had an installation from Google Play Store, you'll get the error
  INSTALL_FAILED_UPDATE_INCOMPATIBLE (I think). Or if you mix debug/release
  versions.

- Finally, note that there can be a significant delay between uploading a new
  release and client devices seeing it on Google Play (or even being able to
  see it at https://play.google.com/store, or via the direct link at
  https://play.google.com/store/apps/details?id=org.camcops.camcops). Perhaps
  10 minutes to the main web site?

Google Play Store release history
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===============  ===================  ===================  ================  ===========  ==========
Google Play      AndroidManifest.xml  AndroidManifest.xml  To Play Store on  Minimum API  Target
Store release    version code         name                                   Android      Android
name                                                                         API          API
===============  ===================  ===================  ================  ===========  ==========
2.0.1 (beta)     2                    2.0.1                2017-08-04        16           23
2.0.4 (beta)     3                    2.0.4                2017-10-22        16           23
2.2.3 (beta)     5                    2.2.3                2018-06-25        16           26
2.2.4 (beta)     6                    2.2.4                2018-07-18        23           26
===============  ===================  ===================  ================  ===========  ==========


Notes
-----

Version constraints for third-party software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- OpenSSL 1.0.x has long-term support and 1.1.x is the current release.

- OpenSSL 1.0.2h didn't compile under 64-bit Windows, whereas OpenSSL 1.1.x
  did.

- OpenSSL 1.1.x requires Qt 5.10 or higher
  (https://bugreports.qt.io/browse/QTBUG-52905).

- SQLCipher supports OpenSSL 1.1.0 as of SQLCipher 3.4.1
  (https://discuss.zetetic.net/t/sqlcipher-3-4-1-release/1962).

- Qt requires Android API ≥16 (http://doc.qt.io/qt-5/android-support.html).

- Qt 5.11.1 does not compile with the ``android-16`` toolchain (specifically
  its Bluetooth components). Qt looks for a Java package
  ``android.bluetooth.le``, which is the Bluetooth Low Energy component that
  comes with Android SDK 18. So let's try 18 as the minimum. That does compile.

- Android libraries should be compiled for the same SDK version as
  ``minSdkVersion`` in ``AndroidManifest.xml`` (see
  https://stackoverflow.com/questions/21888052/what-is-the-relation-between-app-platform-androidminsdkversion-and-androidtar/41079462#41079462,
  and https://developer.android.com/ndk/guides/stable_apis).

- For whatever reasons, CamCOPS (v2.2.3-2.2.4) doesn't run on Android 4.4.x
  (API 18) but does run on 6.0 (API 23); intermediates untested.

- Google Play store will require ``targetSdkVersion`` to be at least 26 from
  2018-11-01
  (https://developer.android.com/distribute/best-practices/develop/target-sdk).

- Qt favour Android NDK r10e (the May 2015 release)
  (http://doc.qt.io/qt-5/androidgs.html) but r11c also seems to work fine.

Android
~~~~~~~

- To build Android programs under Linux, also need:
  ``sudo apt install openjdk-8-jdk``

- Configure your Android SDK/NDK and Java JDK at: :menuselection:`Tools -->
  Options --> Android`, or in newer versions of Qt Creator,
  :menuselection:`Tools --> Options --> Devices --> Android --> Android
  Settings`.

- Above Android API 23, linking to non-public libraries is prohibited, possibly
  with exceptions for SSL/crypto.

  - https://android-developers.googleblog.com/2016/06/android-changes-for-ndk-developers.html
  - https://developer.android.com/about/versions/nougat/android-7.0-changes#ndk

  I think this caused fatal problems for CamCOPS in 2018-07; not sure, but this
  might explain it.

- ``Error: "unsupported_android_version" is not translated``: see
  https://bugreports.qt.io/browse/QTBUG-63952. This error does not prevent you
  from continuing.

Debugging
~~~~~~~~~

- DON'T FORGET to set up both Debug and Release (+/- Profile) builds.

- Phone USB debugging negotiation sometimes takes a while. On the Samsung
  Galaxy phone, the alert light goes red when in Debug mode.

- If you lose the debugger windows in Qt Creator midway through a debug
  session, press Ctrl-4.

- This error (with a variety of compiler names):

  .. code-block:: none

    .../mkspecs/features/toolchain.prf(50): system(execute) requires one or two arguments.
    Project ERROR: Cannot run compiler 'g++'. Maybe you forgot to setup the environment?

  means that you need to re-run qmake manually. It usually occurs if you delete
  your build* directories.

- For debugging, consider install Valgrind_: ``sudo apt install valgrind``

Oddities
~~~~~~~~

- Sometimes you have to restart Qt creator after creating new build settings;
  it loses its .pro file and won't show the project, or complains of a missing
  .pro file when you try to build.

- The first build can be very slow as it compiles all the resources; this
  usually looks like a process stuck compiling qrc_camcops.cpp to qrc_camcops.o

- If an Android build fails for a bizarre reason (like garbage in a .java file
  that looks like it's been pre-supplied), delete the whole build directory,
  which is not always removed by cleaning.
