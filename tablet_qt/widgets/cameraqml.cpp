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


// #define DEBUG_CAMERA
// #define DEBUG_TEST_QML_ONLY

#define USE_FILE

#include "cameraqml.h"

#include <QFile>
#include <QFileInfo>
#include <QMimeDatabase>
#include <QMimeType>
#include <QtQml/QQmlEngine>
#include <QtQuick/QQuickItem>
#include <QVBoxLayout>

#include "lib/uifunc.h"

#ifdef DEBUG_TEST_QML_ONLY
const QString TEST_ANIMATION_QML("camcops/camera_qml/test_animation.qml");
#else
const QString CAMERA_QML("camcops/camera_qml/camera.qml");
#endif

/*

For examples see
- https://doc.qt.io/qt-6.5/qtmultimedia-multimediawidgets-camera-example.html
- qt5/qtmultimedia/examples/multimediawidgets/camera/camera.cpp
- qt5/qtmultimedia/examples/multimedia/declarative-camera/...

The "declarative-camera" example is the QML one.
- It's very responsive. It runs on Android properly.

The "multimediawidgets/camera" one is plain CPP.
- Its viewfinder is laggy in the default configuration.
- Its viewfinder doesn't work on Android.

Yet presumably all the QML stuff uses the same underlying CPP code?

Or maybe not?
- https://forum.qt.io/topic/59394/declarative-camera-vs-widget-based-camera-qml-to-c-breakout
- https://doc.qt.io/qt-6.5/qtqml-cppintegration-interactqmlfromcpp.html
- http://lists.qt-project.org/pipermail/android-development/2015-September/000734.html
- https://stackoverflow.com/questions/40153156/qt-qcamera-not-working-on-android
- https://bugreports.qt.io/browse/QTBUG-38233
- https://bugreports.qt.io/browse/QTBUG-41467
- http://omg-it.works/how-to-grab-video-frames-directly-from-qcamera/
- https://forum.qt.io/topic/47330/android-qcamera-5-4-beta
- https://www.ics.com/blog/combining-qt-widgets-and-qml-qwidgetcreatewindowcontainer

The actual error on Android is:
... warning: The video surface is not compatible with any format supported by
    the camera

*/


// ============================================================================
// Constructor/destructor
// ============================================================================

CameraQml::CameraQml(QWidget* parent) :
    OpenableWidget(parent)
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    /*

QWidget::createWindowContainer()
    - https://www.ics.com/blog/combining-qt-widgets-and-qml-qwidgetcreatewindowcontainer
    - https://doc.qt.io/qt-6.5/qquickview.html#details
    - http://blog.qt.io/blog/2013/02/19/introducing-qwidgetcreatewindowcontainer/

BUT:
    - doesn't work on Android, even for the test animation.
    - When it doesn't work, but the declarative-camera example does:
      These errors come from both, so are not a problem:
      (a) camcops
      - D libGLESv2: DTS_GLAPI : DTS is not allowed for Package :
        org.camcops.camcops
      - E libGLESv1: HWUI Protection: wrong call from hwui context
        F:ES1-glDeleteTexturesSEC
      (b) declarative_camera
      - D libGLESv2: DTS_GLAPI : DTS is not allowed for Package :
        org.qtproject.example.declarative_camera
      ...
      - E libGLESv1: HWUI Protection: wrong call from hwui context
        F:ES1-glDeleteTexturesSEC

    - http://lists.qt-project.org/pipermail/interest/2015-November/019657.html

... use QQuickWidget instead.

    */
    m_qml_view = new QQuickWidget();
    m_qml_view->setResizeMode(QQuickWidget::SizeRootObjectToView);
    connect(
        m_qml_view->engine(), &QQmlEngine::quit, this, &CameraQml::cancelled
    );
    // Just after calling setSource(), calling view->rootObject() can give a
    // nullptr, because it may be loading in the background. So:
    connect(
        m_qml_view,
        &QQuickWidget::statusChanged,
        this,
        &CameraQml::qmlStatusChanged
    );
    // ... and must set that signal before calling setSource().
#ifdef DEBUG_TEST_QML_ONLY
    m_qml_view->setSource(uifunc::resourceUrl(TEST_ANIMATION_QML));
    m_qml_view->resize(800, 480);
#else
    m_qml_view->setSource(uifunc::resourceUrl(CAMERA_QML));
#endif

    auto top_layout = new QVBoxLayout();
    top_layout->addWidget(m_qml_view);
    setLayout(top_layout);
}

// ============================================================================
// Public interface
// ============================================================================

void CameraQml::finish()
{
    emit finished();
}

// ============================================================================
// Internals
// ============================================================================

void CameraQml::qmlStatusChanged(const QQuickWidget::Status status)
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    if (status == QQuickWidget::Ready) {
        qmlFinishedLoading();
    } else {
        qWarning() << "QML status is unhappy:" << status;
    }
}

void CameraQml::qmlFinishedLoading()
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_qml_view);
    QQuickItem* root = m_qml_view->rootObject();
    Q_ASSERT(root);
    // It's possible to connect to non-root objects, but it's much cleaner to
    // route from QML child objects up to the QML root object, and then to C++.
    connect(
        root,
        SIGNAL(imageCaptured(const QVariant&)),
        this,
        SLOT(copyPreviewImage(const QVariant&))
    );
    connect(root, SIGNAL(previewSaved()), this, SLOT(savePreviewImage()));
    connect(
        root,
        SIGNAL(fileNoLongerNeeded(const QString&)),
        this,
        SLOT(deleteSuperfluousFile(const QString&))
    );
    // ... we have to use SIGNAL() and SLOT() since C++ has no idea of the
    // provenance of the signal (and whether or not it exists) -- the macros
    // map signals via strings, so this works, but you'll get an error like
    // "QObject::connect: No such signal
    //  PhotoPreview_QMLTYPE_2::imageCaptured(const QString&)"
    // if you get the type wrong.
}

void CameraQml::copyPreviewImage(const QVariant& preview)
{
    m_preview = preview.value<QImage>();
}

void CameraQml::savePreviewImage()
{
    emit imageCaptured(m_preview);
}

void CameraQml::deleteFile(const QString& filename) const
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    if (!filename.isEmpty()) {
        bool success = QFile::remove(filename);
        qDebug() << "Deleting temporary camera file " << filename
                 << (success ? "... success" : "... FAILED!");
    }
}

void CameraQml::deleteSuperfluousFile(const QString& filename) const
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    deleteFile(filename);
}
