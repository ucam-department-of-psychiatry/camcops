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

#pragma once
#include <QString>

namespace platform {

// Which platform are we on?
extern const bool PLATFORM_ANDROID;
extern const bool PLATFORM_IOS;
extern const bool PLATFORM_LINUX;
extern const bool PLATFORM_WINDOWS;
extern const bool PLATFORM_MACOS;
// Is it a tablet OS?
extern const bool PLATFORM_TABLET;

// Dialogs are full screen on iOS and on Android
// they don't position correctly when rotated.
// https://bugreports.qt.io/browse/QTBUG-91363
extern const bool PLATFORM_FULL_SCREEN_DIALOGS;

// What OS type (e.g. "Android", "Linux", "Windows", "iOS", "MacOS")?
extern const QString OS_CLASS;

// Is the host computer a 64-bit system?
bool isHost64Bit();

// Was the build computer a 64-bit system?
bool isBuild64Bit();

// Compiler
extern const QString COMPILER_NAME_VERSION;
extern const QString COMPILED_WHEN;

}  // namespace platform
