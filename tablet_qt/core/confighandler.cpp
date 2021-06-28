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

#include <jni.h>

#include "core/confighandler.h"

ConfigHandler* ConfigHandler::m_instance = NULL;

ConfigHandler::ConfigHandler()
{
    m_instance = this;
}


ConfigHandler* ConfigHandler::getInstance()
{
    if (!m_instance)
        m_instance = new ConfigHandler;
    return m_instance;
}

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
