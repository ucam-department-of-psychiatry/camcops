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

// MODIFIED FROM:
// https://doc.qt.io/qt-6.5/qtmultimedia-multimediawidgets-camera-camera-cpp.html

/*
**
** Copyright (C) 2015 The Qt Company Ltd.
** Contact: http://www.qt.io/licensing/
**
** This file is part of the examples of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** You may use this file under the terms of the BSD license as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
*/

// #define DEBUG_CAMERA

#include "cameraqcamera.h"

#include <QCameraDevice>
#include <QCloseEvent>
#include <QFile>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QLabel>
#include <QMediaDevices>
#include <QPixmap>
#include <QPushButton>
#include <QStatusBar>
#include <QTimer>
#include <QtQml/QQmlEngine>
#include <QtQuick/QQuickItem>
#include <QVBoxLayout>
#include <QVideoFrame>
#include <QVideoWidget>

#include "common/cssconst.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "dialogs/scrollmessagebox.h"
#include "lib/uifunc.h"

/*
    NOT IMPLEMENTED (see CameraQml instead):
    - choose camera front/back
    - set preview resolution (from those supported)
    - set main resolution (from those supported)
*/

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

CameraQCamera::CameraQCamera(const QString& stylesheet, QWidget* parent) :
    CameraQCamera(QMediaDevices::defaultVideoInput(), stylesheet, parent)
{
}

CameraQCamera::CameraQCamera(
    const QCameraDevice& camera_device,
    const QString& stylesheet,
    QWidget* parent
) :
    OpenableWidget(parent)
{
    setStyleSheet(stylesheet);

    m_camera.clear();
    m_capture.clear();
    m_ready = false;
    m_capturing_image = false;
    m_exiting = false;
#ifndef CAMERA_LOAD_FROM_DISK_PROMPTLY
    m_captured_state = CapturedState::Nothing;
#endif

    Qt::Alignment align_top_left = Qt::AlignLeft | Qt::AlignTop;

    m_button_take = new QPushButton(tr("Take"));
    connect(
        m_button_take,
        &QAbstractButton::clicked,
        this,
        &CameraQCamera::takeImage
    );

    m_button_cancel = new QPushButton(TextConst::cancel());
    connect(
        m_button_cancel,
        &QAbstractButton::clicked,
        this,
        &CameraQCamera::cancelled
    );

    auto button_layout = new QVBoxLayout();
    button_layout->addWidget(m_button_take, 0, align_top_left);
    button_layout->addWidget(m_button_cancel, 0, align_top_left);
    button_layout->addStretch();
    auto button_widget = new QWidget();
    button_widget->setLayout(button_layout);

    m_viewfinder = new QVideoWidget();
    m_viewfinder->setSizePolicy(
        QSizePolicy::Expanding, QSizePolicy::Expanding
    );

    auto middle_layout = new QHBoxLayout();
    middle_layout->addWidget(button_widget);
    middle_layout->addWidget(m_viewfinder);

    m_status_bar = new QStatusBar();

    auto top_layout = new QVBoxLayout();
    top_layout->addLayout(middle_layout);
    top_layout->addWidget(m_status_bar);

    // Now, since the CSS of the outermost object is ignored within a
    // QStackedWidget...
    auto inner_widget = new QWidget();
    inner_widget->setObjectName(cssconst::CAMERA_INNER_OBJECT);
    inner_widget->setLayout(top_layout);

    // ... we need an outer layout too.
    auto outer_layout = new QVBoxLayout();
    outer_layout->setContentsMargins(uiconst::NO_MARGINS);
    outer_layout->addWidget(inner_widget);
    setLayout(outer_layout);

    setCamera(camera_device);
}

CameraQCamera::~CameraQCamera()
{
#ifndef CAMERA_LOAD_FROM_DISK_PROMPTLY
    // Remove anything that we've saved to disk
    for (auto filename : m_filenames_for_deletion) {
        bool success = QFile::remove(filename);
        qInfo() << "Deleting temporary camera file " << filename
                << (success ? "... success" : "... FAILED!");
    }
#endif
}

// ============================================================================
// Public interface
// ============================================================================

void CameraQCamera::finish()
{
    emit finished();
}

QImage CameraQCamera::image() const
{
    return m_most_recent_image;
#ifndef CAMERA_LOAD_FROM_DISK_PROMPTLY
    QImage img;
    switch (m_captured_state) {
        case CapturedState::Nothing:
            qDebug() << "... no file captured yet";
            break;
        case CapturedState::File:
            qDebug() << "... returning contents of" << m_most_recent_filename;
            qInfo() << "Camera::image: Loading image file...";
            img.load(m_most_recent_filename);
            qInfo() << "Camera::image: ... loaded.";
            break;
        case CapturedState::Buffer:
            qDebug() << "... returning image from buffer";
            img = m_most_recent_image;  // no cost; copy-on-write
            break;
    }
    return img;
#endif
}

// ============================================================================
// Talking to the camera
// ============================================================================

void CameraQCamera::setCamera(const QCameraDevice& camera_device)
{
    // ------------------------------------------------------------------------
    // QCamera
    // ------------------------------------------------------------------------
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO << "Creating camera with device" << camera_device;
#endif
    m_camera = QSharedPointer<QCamera>(new QCamera(camera_device));
#ifdef DEBUG_CAMERA
    qDebug() << "QCamera::supportedViewfinderResolutions() == "
             << m_camera->supportedViewfinderResolutions();
    qDebug() << Q_FUNC_INFO << "... done";
#endif
    m_capture_session.setCamera(m_camera.data());

    connect(
        m_camera.data(),
        &QCamera::errorOccurred,
        this,
        &CameraQCamera::displayCameraError
    );
    // ------------------------------------------------------------------------
    // QImageCapture
    // ------------------------------------------------------------------------
    m_capture = QSharedPointer<QImageCapture>(new QImageCapture);
    m_capture_session.setImageCapture(m_capture.data());

    connect(
        m_capture.data(),
        &QImageCapture::readyForCaptureChanged,
        this,
        &CameraQCamera::readyForCapture
    );
    connect(
        m_capture.data(),
        &QImageCapture::imageSaved,
        this,
        &CameraQCamera::imageSaved
    );
    connect(
        m_capture.data(),
        &QImageCapture::errorOccurred,
        this,
        &CameraQCamera::displayCaptureError
    );

    // ------------------------------------------------------------------------
    // Viewfinder
    // ------------------------------------------------------------------------
    m_capture_session.setVideoOutput(m_viewfinder);

    // ------------------------------------------------------------------------
    // Set up; let's go.
    // ------------------------------------------------------------------------
    readyForCapture(m_capture->isReadyForCapture());
    startCamera();
}

void CameraQCamera::startCamera()
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    m_camera->start();
}

void CameraQCamera::stopCamera()
{
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO;
#endif
    m_camera->stop();
}

void CameraQCamera::takeImage()
{
    m_capturing_image = true;
    // !!! CameraQCamera::takeImage: implement some sort of wait message --
    // but superseded by CameraQml
    updateButtons();
#ifdef DEBUG_CAMERA
    qDebug() << Q_FUNC_INFO << "calling capture()";
#endif
    m_capture->captureToFile();  // a bit slow, so update buttons first
}

void CameraQCamera::displayCaptureError(
    const int id, const QImageCapture::Error error, const QString& error_string
)
{
    qWarning() << "Capture error:" << id << error << error_string;
    ScrollMessageBox::warning(this, tr("Image capture error"), error_string);
    m_capturing_image = false;
    updateButtons();
}

void CameraQCamera::displayCameraError(const QCamera::Error value)
{
    QString err = m_camera->errorString();
    qWarning() << "Camera error:" << value << err;
    ScrollMessageBox::warning(this, tr("Camera error"), err);
}

void CameraQCamera::updateButtons()
{
    if (m_button_take) {
        m_button_take->setEnabled(m_ready && !m_capturing_image);
    }
    if (m_button_cancel) {
        m_button_cancel->setEnabled(!m_capturing_image);
    }
}

void CameraQCamera::readyForCapture(const bool ready)
{
    m_ready = ready;
    updateButtons();
    // If you try to capture when it's not ready, it causes an error;
    // https://doc.qt.io/qt-6.5/qcameraimagecapture.html

    // Because the viewfinder tends to start out too small, this is a good
    // time:
    m_viewfinder->updateGeometry();
}

void CameraQCamera::imageSaved(const int id, const QString& filename)
{
    // Image has arrived via a disk file.
    Q_UNUSED(id)
    qDebug() << "Camera image has arrived via temporary file" << filename;
#ifdef CAMERA_LOAD_FROM_DISK_PROMPTLY
    m_most_recent_image.load(filename);
    qDebug() << "Camera image loaded";
    bool success = QFile::remove(filename);
    qDebug() << "Deleting temporary camera file " << filename
             << (success ? "... success" : "... FAILED!");
#else
    m_filenames_for_deletion.insert(filename);
    m_most_recent_filename = filename;
    m_captured_state = CapturedState::File;
#endif
    m_capturing_image = false;
    emit imageCaptured(image());
    if (m_exiting) {
        close();
    } else {
        updateButtons();
    }
}

void CameraQCamera::closeEvent(QCloseEvent* event)
{
    if (m_capturing_image) {
        setEnabled(false);
        m_exiting = true;
        event->ignore();
    } else {
        event->accept();
    }
}

void CameraQCamera::keyPressEvent(QKeyEvent* event)
{
    if (event->isAutoRepeat()) {
        return;
    }

    switch (event->key()) {
        case Qt::Key_Camera:
            takeImage();
            event->accept();
            break;
        default:
            OpenableWidget::keyPressEvent(event);
    }
}

void CameraQCamera::keyReleaseEvent(QKeyEvent* event)
{
    // This used to handle Qt::Key_CameraFocus, calling
    // unlockCamera(). See git history. Remove if not
    // needed.

    if (event->isAutoRepeat()) {
        return;
    }

    OpenableWidget::keyReleaseEvent(event);
}
