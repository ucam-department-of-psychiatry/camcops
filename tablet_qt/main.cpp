/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
*/

// #define TEST_BASIC_QT_ONLY  // Disables CamCOPS! Just says hello.
#define FULL_LOG_FORMAT
#define DISABLE_ANDROID_NATIVE_DIALOGS

#include <QApplication>
#include <QDebug>
#include <QPushButton>
#include <QStyleFactory>
#include "core/camcopsapp.h"
#include "crypto/cryptofunc.h"

#ifdef FULL_LOG_FORMAT
    #ifdef QT_DEBUG
        const QString message_pattern(
            "camcops[%{threadid}]: %{time yyyy-MM-ddTHH:mm:ss.zzz}"
            ": %{type}: %{file}(%{line}): %{message}");
    #else
        const QString message_pattern(
            "camcops[%{threadid}]: %{time yyyy-MM-ddTHH:mm:ss.zzz}"
            ": %{type}: %{message}");
    #endif
#else
    const QString message_pattern("camcops: %{type}: %{message}");
#endif


#ifdef TEST_BASIC_QT_ONLY
int runMinimalQtApp(int& argc, char* argv[])
{
    QApplication app(argc, argv);
    QPushButton button("Hello, world!");
    button.show();
    return app.exec();
}
#endif


int main(int argc, char* argv[])
{
    /*
    NOTE: argc must be passed to the QApplication as a REFERENCE to int, or the
    app will crash. See
    - https://bugreports.qt.io/browse/QTBUG-5637
    - http://doc.qt.io/qt-5/qapplication.html
    */

#ifdef TEST_BASIC_QT_ONLY
    // For when it all breaks!
    return runMinimalQtApp(argc, argv);
#else
    /*
    -   The VERY FIRST THING we do is to create a QApplication, and that
        requires one bit of preamble.
        http://stackoverflow.com/questions/27963697
    -   Prevent native styling, which makes (for example) QListWidget colours
        not work from the stylsheet. This must be done before the app is
        created. See https://bugreports.qt.io/browse/QTBUG-45517
    */

    QStyle* style = QStyleFactory::create("Fusion");
    // QProxyStyle* proxy_style = new TreeViewProxyStyle(style);
    QApplication::setStyle(style);
    // ... https://stackoverflow.com/questions/41184723/i-want-qt-app-to-look-like-qt-app-rather-than-android-native

#ifdef DISABLE_ANDROID_NATIVE_DIALOGS
    // To fix a message box bug: https://bugreports.qt.io/browse/QTBUG-35313
    qputenv("QT_USE_ANDROID_NATIVE_DIALOGS", "0");
    // ... read by QAndroidPlatformTheme::usePlatformNativeDialog in qandroidplatformtheme.cpp
#endif

    qSetMessagePattern(message_pattern);
    // See also http://stackoverflow.com/questions/4954140/how-to-redirect-qdebug-qwarning-qcritical-etc-output

    CamcopsApp app(argc, argv);
#ifdef OPENSSL_VIA_QLIBRARY
    cryptofunc::ensureAllCryptoFunctionsLoaded();
#endif
    return app.run();
#endif
}
