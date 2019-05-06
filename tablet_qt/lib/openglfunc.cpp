/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

// See:
// - https://raw.githubusercontent.com/mltframework/shotcut/master/src/widgets/gltestwidget.h
// - https://raw.githubusercontent.com/mltframework/shotcut/master/src/widgets/gltestwidget.cpp
// - https://forum.qt.io/topic/68217/qopenglwidget-how-to-get-opengl-version-from-os


#include "openglfunc.h"
#include <QDebug>
#include <QtGui/QOffscreenSurface>
#include <QtGui/QOpenGLContext>
#include <QtGui/QOpenGLFunctions>
#include <QtGui/QSurface>
#include <QtGui/QSurfaceFormat>
#include <QtOpenGL/QGLFormat>
#include <QtWidgets/QOpenGLWidget>

static bool s_opengl_initialized = false;
static bool s_opengl_present = false;


namespace openglfunc {


bool isOpenGLPresent()
{
    if (!s_opengl_initialized) {
        s_opengl_initialized = true;
        s_opengl_present = false;

        QOffscreenSurface surf;
        surf.create();
        QSurfaceFormat fmt = surf.format();
        qInfo() << "OpenGL surface format:" << fmt;

        QOpenGLContext ctx;
        if (!ctx.create()) {
            qCritical() << "Unable to create OpenGL context";
            return false;
        }
        ctx.makeCurrent(&surf);

        QOpenGLFunctions* glfuncs = ctx.functions();

        glfuncs->initializeOpenGLFunctions();

        const bool opengl_v2 = QGLFormat::openGLVersionFlags() & QGLFormat::OpenGL_Version_2_0;
        const bool npot_textures = glfuncs->hasOpenGLFeature(QOpenGLFunctions::NPOTTextures);
        const bool shaders = glfuncs->hasOpenGLFeature(QOpenGLFunctions::Shaders);
        const bool framebuffers = glfuncs->hasOpenGLFeature(QOpenGLFunctions::Framebuffers);

        s_opengl_present = opengl_v2 && npot_textures && shaders && framebuffers;

        if (s_opengl_present) {
            qInfo() << "OpenGL v2.0 is present and satisfactory";
        } else {
            qWarning() << "OpenGL v2.0 present:" << opengl_v2;
            qWarning() << "OpenGL has NPOTTextures:" << npot_textures;
            qWarning() << "OpenGL has Shaders:" << shaders;
            qWarning() << "OpenGL has Framebuffers:" << framebuffers;
            qCritical() << "Error: This program requires OpenGL version 2.0 with the framebuffer object extension.";
        }
    }
    return s_opengl_present;
}


}  // namespace openglfunc
