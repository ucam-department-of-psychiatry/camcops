// MODIFIED FROM:
// http://doc.qt.io/qt-5/qtmultimedia-multimediawidgets-camera-camera-cpp.html

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


#include "camera.h"
#include <QCameraInfo>
#include <QCameraViewfinder>
#include <QCloseEvent>
#include <QFile>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QLabel>
#include <QMessageBox>
#include <QPushButton>
#include <QStackedWidget>
#include <QStatusBar>
#include <QTimer>
#include <QVBoxLayout>
#include <QVideoFrame>
#include "common/cssconst.h"
#include "common/uiconst.h"
#include "graphics/imagefunc.h"
#include "imagebutton.h"


Camera::Camera(const QString& stylesheet, QWidget* parent) :
    OpenableWidget(parent)
{
    commonConstructor(stylesheet);
    setCamera(QCameraInfo::defaultCamera());
}


Camera::Camera(const QCameraInfo& camera_info, const QString& stylesheet,
               QWidget* parent) :
    OpenableWidget(parent)
{
    commonConstructor(stylesheet);
    setCamera(camera_info);
}


Camera::~Camera()
{
    // Remove anything that we've saved to disk
    for (auto filename : m_filenames_for_deletion) {
        bool success = QFile::remove(filename);
        qDebug() << "Deleting " << filename
                 << (success ? "... success" : "... FAILED!");
    }
}


void Camera::commonConstructor(const QString& stylesheet)
{
    m_camera.clear();
    m_capture.clear();
    m_ready = false;
    m_capturing_image = false;
    m_exiting = false;
    m_captured_state = CapturedState::Nothing;

    Qt::Alignment align = Qt::AlignLeft | Qt::AlignTop;

    setStyleSheet(stylesheet);

    m_button_take = new QPushButton(tr("Take"));
    connect(m_button_take, &QAbstractButton::clicked,
            this, &Camera::takeImage);

    m_button_cancel = new QPushButton(tr("Cancel"));
    connect(m_button_cancel, &QAbstractButton::clicked,
            this, &Camera::cancelled);

    m_lock_button = new QPushButton("lock button");

    QVBoxLayout* button_layout = new QVBoxLayout();
    button_layout->addWidget(m_button_take, 0, align);
    button_layout->addWidget(m_lock_button, 0, align);
    button_layout->addWidget(m_button_cancel, 0, align);
    button_layout->addStretch();
    QWidget* button_widget = new QWidget();
    button_widget->setLayout(button_layout);

    m_viewfinder = new QCameraViewfinder();
    // m_viewfinder->setSizePolicy(QSizePolicy::Minimum, QSizePolicy::Minimum);

    QHBoxLayout* middle_layout = new QHBoxLayout();
    middle_layout->addWidget(button_widget, 0, align);
    middle_layout->addWidget(m_viewfinder, 0, align);
    middle_layout->addStretch();

    m_status_bar = new QStatusBar();

    QVBoxLayout* top_layout = new QVBoxLayout();
    top_layout->addLayout(middle_layout);
    top_layout->addStretch();
    top_layout->addWidget(m_status_bar);

    setLayout(top_layout);

    // *** problem: viewfinder image too small (usually!)

    // Now, since the CSS of the outermost object is ignored within a
    // QStackedWidget...
    QWidget* inner_widget = new QWidget();
    inner_widget->setObjectName(cssconst::CAMERA_INNER_OBJECT);
    inner_widget->setLayout(top_layout);

    // ... we need an outer layout too.
    QVBoxLayout* outer_layout = new QVBoxLayout();
    outer_layout->setContentsMargins(uiconst::NO_MARGINS);
    outer_layout->addWidget(inner_widget);
    setLayout(outer_layout);
}


// ============================================================================
// Talking to the camera
// ============================================================================

void Camera::setCamera(const QCameraInfo& cameraInfo)
{
    // ------------------------------------------------------------------------
    // QCamera
    // ------------------------------------------------------------------------
    m_camera = QSharedPointer<QCamera>(new QCamera(cameraInfo));
    connect(m_camera.data(), &QCamera::stateChanged,
            this, &Camera::updateCameraState);
    // QCamera::error is overloaded.
    // Disambiguate like this:
    void (QCamera::*camera_error)(QCamera::Error) = &QCamera::error;
    connect(m_camera.data(), camera_error,
            this, &Camera::displayCameraError);
    // QCamera::lockStatusChanged is overloaded.
    // Disambiguate like this:
    void (QCamera::*camera_lockstatus)(
                QCamera::LockStatus,
                QCamera::LockChangeReason) = &QCamera::lockStatusChanged;
    connect(m_camera.data(), camera_lockstatus,
            this, &Camera::updateLockStatus);

    // ------------------------------------------------------------------------
    // QCameraImageCapture
    // ------------------------------------------------------------------------
    m_capture = QSharedPointer<QCameraImageCapture>(
                new QCameraImageCapture(m_camera.data()));

    updateCameraState(m_camera->state());

    connect(m_capture.data(), &QCameraImageCapture::readyForCaptureChanged,
            this, &Camera::readyForCapture);
    connect(m_capture.data(), &QCameraImageCapture::imageSaved,
            this, &Camera::imageSaved);
    connect(m_capture.data(), &QCameraImageCapture::imageAvailable,
            this, &Camera::imageAvailable);
    // QCameraImageCapture::error is overloaded.
    // Disambiguate like this:
    void (QCameraImageCapture::*capture_error)(
                int,
                QCameraImageCapture::Error,
                const QString&) = &QCameraImageCapture::error;
    connect(m_capture.data(), capture_error,
            this, &Camera::displayCaptureError);

    bool use_buffer = m_capture->isCaptureDestinationSupported(
                QCameraImageCapture::CaptureToBuffer);
    // use_buffer = false;
    if (use_buffer) {
        qDebug() << Q_FUNC_INFO << "Capturing to buffer";
        m_capture->setCaptureDestination(QCameraImageCapture::CaptureToBuffer);
    } else {
        qDebug() << Q_FUNC_INFO << "Capturing to file";
        m_capture->setCaptureDestination(QCameraImageCapture::CaptureToFile);
    }

    // ------------------------------------------------------------------------
    // QCameraViewfinder
    // ------------------------------------------------------------------------
    m_camera->setViewfinder(m_viewfinder);

    // ------------------------------------------------------------------------
    // Set up; let's go.
    // ------------------------------------------------------------------------
    if (m_camera->isCaptureModeSupported(QCamera::CaptureStillImage)) {
        m_camera->setCaptureMode(QCamera::CaptureStillImage);
    } else {
        qWarning() << Q_FUNC_INFO
                   << "Camera does not support QCamera::CaptureStillImage";
    }
    updateLockStatus(m_camera->lockStatus(),
                     QCamera::LockChangeReason::UserRequest);
    readyForCapture(m_capture->isReadyForCapture());
    m_camera->start();
}


void Camera::startCamera()
{
    m_camera->start();
}


void Camera::stopCamera()
{
    m_camera->stop();
}


void Camera::toggleLock()
{
    switch (m_camera->lockStatus()) {
    case QCamera::Searching:
    case QCamera::Locked:
        m_camera->unlock();
        break;
    case QCamera::Unlocked:
        m_camera->searchAndLock();
    }
}


void Camera::updateLockStatus(QCamera::LockStatus status,
                              QCamera::LockChangeReason reason)
{
    QColor indicationColor = Qt::black;

    switch (status) {
    case QCamera::Searching:
        indicationColor = Qt::yellow;
        m_status_bar->showMessage(tr("Focusing..."));
        m_lock_button->setText(tr("Focusing..."));
        break;
    case QCamera::Locked:
        indicationColor = Qt::darkGreen;
        m_lock_button->setText(tr("Unlock"));
        m_status_bar->showMessage(tr("Focused"), 2000);
        break;
    case QCamera::Unlocked:
        indicationColor = reason == QCamera::LockFailed ? Qt::red : Qt::black;
        m_lock_button->setText(tr("Focus"));
        if (reason == QCamera::LockFailed) {
            m_status_bar->showMessage(tr("Focus failed"), 2000);
        } else {
            m_status_bar->showMessage(tr("Camera"));
        }
    }

    QPalette palette = m_lock_button->palette();
    palette.setColor(QPalette::ButtonText, indicationColor);
    m_lock_button->setPalette(palette);
    updateButtons();
}


void Camera::takeImage()
{
    m_capturing_image = true;
    // *** Camera::takeImage implement some sort of wait message
    updateButtons();
    m_capture->capture();  // a bit slow, so update buttons first
}


void Camera::displayCaptureError(int id, QCameraImageCapture::Error error,
                                 const QString& error_string)
{
    qWarning() << "Capture error:" << id << error << error_string;
    QMessageBox::warning(this, tr("Image capture error"), error_string);
    m_capturing_image = false;
    updateButtons();
}


void Camera::displayCameraError(QCamera::Error value)
{
    QString err = m_camera->errorString();
    qWarning() << "Camera error:" << value << err;
    QMessageBox::warning(this, tr("Camera error"), err);
}


void Camera::updateCameraState(QCamera::State state)
{
    // *** Camera::updateCameraState
    // Update the UI to reflect the camera's state
    switch (state) {
    case QCamera::ActiveState:
        /*
        ui->actionStartCamera->setEnabled(false);
        ui->actionStopCamera->setEnabled(true);
        ui->captureWidget->setEnabled(true);
        ui->actionSettings->setEnabled(true);
        */
        break;
    case QCamera::UnloadedState:
    case QCamera::LoadedState:
        /*
        ui->actionStartCamera->setEnabled(true);
        ui->actionStopCamera->setEnabled(false);
        ui->captureWidget->setEnabled(false);
        ui->actionSettings->setEnabled(false);
        */
        break;
    }
    updateButtons();
}


void Camera::updateButtons()
{
    if (m_button_take) {
        m_button_take->setEnabled(m_ready && !m_capturing_image);
    }
    if (m_lock_button) {
        m_lock_button->setEnabled(!m_capturing_image);
    }
    if (m_button_cancel) {
        m_button_cancel->setEnabled(!m_capturing_image);
    }
}


void Camera::setExposureCompensation(int index)
{
    m_camera->exposure()->setExposureCompensation(index * 0.5);
}


void Camera::readyForCapture(bool ready)
{
    m_ready = ready;
    updateButtons();
    // If you try to capture when it's not ready, it causes an error;
    // http://doc.qt.io/qt-5/qcameraimagecapture.html

    // Because the viewfinder tends to start out too small, this is a good
    // time:
    m_viewfinder->updateGeometry();
}


void Camera::imageSaved(int id, const QString& filename)
{
    // Image has arrived via a disk file.
    Q_UNUSED(id);
    m_filenames_for_deletion.insert(filename);
    m_most_recent_filename = filename;
    m_captured_state = CapturedState::File;
    m_capturing_image = false;
    emit imageCaptured(image());
    if (m_exiting) {
        close();
    } else {
        updateButtons();
    }
}


void Camera::imageAvailable(int id, const QVideoFrame& buffer)
{
    // Image has arrived via a buffer.

    // http://stackoverflow.com/questions/27297657/how-to-qvideoframe-to-qimage
    // http://stackoverflow.com/questions/27829830/convert-qvideoframe-to-qimage

    Q_UNUSED(id);
    m_most_recent_image = imagefunc::imageFromVideoFrame(buffer);
    m_captured_state = CapturedState::Buffer;
    m_capturing_image = false;
    emit imageCaptured(image());
    if (m_exiting) {
        close();
    } else {
        updateButtons();
    }
}


void Camera::closeEvent(QCloseEvent* event)
{
    if (m_capturing_image) {
        setEnabled(false);
        m_exiting = true;
        event->ignore();
    } else {
        event->accept();
    }
}


void Camera::keyPressEvent(QKeyEvent* event)
{
    if (event->isAutoRepeat()) {
        return;
    }

    switch (event->key()) {
    case Qt::Key_CameraFocus:
        m_camera->searchAndLock();
        event->accept();
        break;
    case Qt::Key_Camera:
        if (m_camera->captureMode() == QCamera::CaptureStillImage) {
            takeImage();
        }
        event->accept();
        break;
    default:
        OpenableWidget::keyPressEvent(event);
    }
}


void Camera::keyReleaseEvent(QKeyEvent* event)
{
    if (event->isAutoRepeat()) {
        return;
    }

    switch (event->key()) {
    case Qt::Key_CameraFocus:
        m_camera->unlock();
        break;
    default:
        OpenableWidget::keyReleaseEvent(event);
    }
}


/*
void Camera::configureImageSettings()
{
    ImageSettings settingsDialog(imageCapture);

    settingsDialog.setImageSettings(imageSettings);

    if (settingsDialog.exec()) {
        imageSettings = settingsDialog.imageSettings();
        imageCapture->setEncodingSettings(imageSettings);
    }
}
*/


void Camera::finish()
{
    emit finished();
}


QImage Camera::image() const
{
    QImage img;
    switch (m_captured_state) {
    case CapturedState::Nothing:
        qDebug() << "... no file captured yet";
        break;
    case CapturedState::File:
        qDebug() << "... returning contents of" << m_most_recent_filename;
        img.load(m_most_recent_filename);
        break;
    case CapturedState::Buffer:
        qDebug() << "... returning image from buffer";
        img = m_most_recent_image;  // no cost; copy-on-write
        break;
    }
    return img;
}
