#include "platform.h"
#include <QtGlobal>

#ifdef Q_OS_ANDROID
const bool Platform::PLATFORM_ANDROID = true;
#else
const bool Platform::PLATFORM_ANDROID = false;
#endif

#ifdef Q_OS_IOS
const bool Platform::PLATFORM_IOS = true;
#else
const bool Platform::PLATFORM_IOS = false;
#endif

#ifdef Q_OS_LINUX
const bool Platform::PLATFORM_LINUX = true;
#else
const bool Platform::PLATFORM_LINUX = false;
#endif

#ifdef Q_OS_WIN
const bool Platform::PLATFORM_WINDOWS = true;
#else
const bool Platform::PLATFORM_WINDOWS = false;
#endif

#if defined(Q_OS_ANDROID) || defined(Q_OS_IOS)
const bool Platform::PLATFORM_TABLET = true;
#else
const bool Platform::PLATFORM_TABLET = false;
#endif
