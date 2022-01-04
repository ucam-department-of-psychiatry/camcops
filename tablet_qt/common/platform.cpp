/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "platform.h"
#include <QString>
#include <QSysInfo>
#include <QtGlobal>
#include "common/preprocessor_aid.h"

namespace platform {

#ifdef Q_OS_ANDROID
    const bool PLATFORM_ANDROID = true;
    const QString OS_CLASS("Android");
#else
    const bool PLATFORM_ANDROID = false;
#endif

#ifdef Q_OS_IOS
    const bool PLATFORM_IOS = true;
    const QString OS_CLASS("iOS");
#else
    const bool PLATFORM_IOS = false;
#endif

#ifdef Q_OS_LINUX
    const bool PLATFORM_LINUX = true;
    #ifndef Q_OS_ANDROID
        const QString OS_CLASS("Linux");
    #endif
#else
    const bool PLATFORM_LINUX = false;
#endif

#ifdef Q_OS_WIN
    const bool PLATFORM_WINDOWS = true;
    const QString OS_CLASS("Windows");
#else
    const bool PLATFORM_WINDOWS = false;
#endif

#ifdef Q_OS_MACOS
    const bool PLATFORM_MACOS = true;
    const QString OS_CLASS("MacOS");
#else
    const bool PLATFORM_MACOS = false;
#endif

#if defined(Q_OS_ANDROID) || defined(Q_OS_IOS)
    const bool PLATFORM_TABLET = true;
    const bool PLATFORM_FULL_SCREEN_DIALOGS = true;
#else
    const bool PLATFORM_TABLET = false;
    const bool PLATFORM_FULL_SCREEN_DIALOGS = false;
#endif

// https://stackoverflow.com/questions/36649393/qt-check-if-current-process-is-32-or-64-bit/41863992

bool isHost64Bit()
{
    static const bool h = QSysInfo::currentCpuArchitecture().contains(QLatin1String("64"));
    return h;
}


bool isBuild64Bit()
{
    static const bool b = QSysInfo::buildCpuArchitecture().contains(QLatin1String("64"));
    return b;
}


// COMPILER_NAME_VERSION
#if defined COMPILER_IS_GCC
    const QString COMPILER_NAME_VERSION = QString(
            "GNU C++ compiler (GCC) version %1.%2.%3").arg(
            QString::number(__GNUC__),
            QString::number(__GNUC_MINOR__),
            QString::number(__GNUC_PATCHLEVEL__));
#elif defined COMPILER_IS_CLANG
    const QString COMPILER_NAME_VERSION = QString(
            "clang version %1.%2.%3").arg(
            QString::number(__clang_major__),
            QString::number(__clang_minor__),
            QString::number(__clang_patchlevel__));
#elif defined COMPILER_IS_VISUAL_CPP
    const QString COMPILER_NAME_VERSION = QString(
            "Microsoft Visual C++ version %").arg(
            QString::number(_MSC_FULL_VER));
#else
    const QString COMPILER_NAME_VERSION("Unknown");
#endif


// COMPILED_WHEN
#ifdef DISABLE_GCC_DATE_TIME_MACRO_WARNING
    #pragma GCC diagnostic push
    #pragma GCC diagnostic ignored "-Wdate-time"
#endif
#ifdef DISABLE_CLANG_DATE_TIME_MACRO_WARNING
    #pragma clang diagnostic push
    #pragma clang diagnostic ignored "-Wdate-time"
#endif
const QString COMPILED_WHEN = QString("%1 %2").arg(__DATE__, __TIME__);
#ifdef DISABLE_GCC_DATE_TIME_MACRO_WARNING
    #pragma GCC diagnostic pop
#endif
#ifdef DISABLE_CLANG_DATE_TIME_MACRO_WARNING
    #pragma clang diagnostic pop
#endif


}  // namespace platform
