/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include <QDebug>
#include <QDesktopServices>
#include <QSysInfo>
#include <QUrl>
#include <QUrlQuery>

#ifdef Q_OS_ANDROID
#include <jni.h>
#endif

#include "core/confighandler.h"

ConfigHandler* ConfigHandler::m_instance = NULL;

ConfigHandler::ConfigHandler()
{
    m_instance = this;

    // QDesktopServices::setUrlHandler() doesn't work on Android
    // https://bugreports.qt.io/browse/QTBUG-70170
    // So this is handled in:
    // tablet_qt/android/src/org/camcops/camcops/CamcopsActivity.java

    // We use 'camcops' scheme instead of 'http' (with 'camcops' domain)
    // on Android:
    // https://doc.qt.io/qt-5/qdesktopservices.html#setUrlHandler says
    // "It is not possible to claim support for some well known URL schemes,
    // including http and https."
    // Unfortunately some mail clients such as GMail don't display URLs with
    // unknown schemes as hyperlinks, even with <a href="camcops://..."></a> in
    // HTML email
    // See also CFBundleURLSchemes in tablet_qt/ios/Info.plist
    QDesktopServices::setUrlHandler("camcops", this, "handleUrl");
}

void ConfigHandler::handleUrl(const QUrl url)
{
    qDebug() << Q_FUNC_INFO << url;

    auto query = QUrlQuery(url);
    auto default_single_user_mode = query.queryItemValue("default_single_user_mode");
    qDebug() << default_single_user_mode;
    if (!default_single_user_mode.isEmpty()) {
        emit defaultSingleUserModeSet(default_single_user_mode);
    }

    auto default_server_location = query.queryItemValue("default_server_location",
                                                        QUrl::FullyDecoded);
    qDebug() << default_server_location;
    if (!default_server_location.isEmpty()) {
        emit defaultServerLocationSet(default_server_location);
    }

    auto default_access_key = query.queryItemValue("default_access_key");
    qDebug() << default_access_key;
    if (!default_access_key.isEmpty()) {
        emit defaultAccessKeySet(default_access_key);
    }
}


ConfigHandler* ConfigHandler::getInstance()
{
    if (!m_instance)
        m_instance = new ConfigHandler;
    return m_instance;
}

#ifdef Q_OS_ANDROID
// Called from android/src/org/camcops/camcops/CamcopsActivity.java
#ifdef __cplusplus
extern "C" {
#endif

JNIEXPORT void JNICALL
  Java_org_camcops_camcops_CamcopsActivity_setDefaultSingleUserMode(
      JNIEnv *env,
      jobject obj,
      jstring value)
{
    Q_UNUSED(obj)

    const char *value_str = env->GetStringUTFChars(value, NULL);

    emit ConfigHandler::getInstance()->defaultSingleUserModeSet(value_str);

    env->ReleaseStringUTFChars(value, value_str);
}

JNIEXPORT void JNICALL
  Java_org_camcops_camcops_CamcopsActivity_setDefaultServerLocation(
      JNIEnv *env,
      jobject obj,
      jstring value)
{
    Q_UNUSED(obj)

    const char *value_str = env->GetStringUTFChars(value, NULL);

    emit ConfigHandler::getInstance()->defaultServerLocationSet(value_str);

    env->ReleaseStringUTFChars(value, value_str);
}

    JNIEXPORT void JNICALL
  Java_org_camcops_camcops_CamcopsActivity_setDefaultAccessKey(
      JNIEnv *env,
      jobject obj,
      jstring value)
{
    Q_UNUSED(obj)

    const char *value_str = env->GetStringUTFChars(value, NULL);

    emit ConfigHandler::getInstance()->defaultAccessKeySet(value_str);

    env->ReleaseStringUTFChars(value, value_str);
}


#ifdef __cplusplus
}
#endif

#endif
