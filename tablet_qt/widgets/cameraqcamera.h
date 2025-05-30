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

#define CAMERA_LOAD_FROM_DISK_PROMPTLY

/*

SUMMARY OF DECISIONS about camera methods, updated 2023-01-04 for Qt6.5 :

Qt is now built with FFmpeg for all platforms except iOS.

1.  QCamera
    - Works mostly well on all platforms (with Android patch applied by the
    build script). On MacOS the preview is snowy but the actual photos taken
    are fine. https://bugreports.qt.io/browse/QTBUG-119834

2.  QML
    - multiple issues with our modified version of the declarative camera
    example:
    https://bugreports.qt.io/browse/QTBUG-111460 (closed but still observed)
    https://bugreports.qt.io/browse/QTBUG-116195
    https://bugreports.qt.io/browse/QTBUG-116292

    There is also a crash on MacOS when the Please wait... window
    (slowguiguard) is closed: "Window modal dialog has no transient parent"

*/

#include <QCamera>
#include <QImage>
#include <QImageCapture>
#include <QMediaCaptureSession>
#include <QPointer>
#include <QSet>

#include "widgets/openablewidget.h"
class QAbstractButton;
class QCameraDevice;
class QLabel;
class QQuickWidget;
class QPushButton;
class QStatusBar;
class QVideoFrame;
class QVideoWidget;

class CameraQCamera : public OpenableWidget
{
    // Widget to take a photo.
    // DEPRECATED at present in favour of QML version; see CameraQml.

    Q_OBJECT

public:
    // ========================================================================
    // Constructor/destructor
    // ========================================================================

    // Construct with stylesheet.
    CameraQCamera(const QString& stylesheet, QWidget* parent = nullptr);

    // Construct with QCameraDevice and stylesheet.
    CameraQCamera(
        const QCameraDevice& camera_device,
        const QString& stylesheet,
        QWidget* parent = nullptr
    );

    // Destructor.
    ~CameraQCamera();

    // ========================================================================
    // Public interface
    // ========================================================================

    // Emit the finished() signal.
    void finish();

    // Return the latest image captured.
    QImage image() const;

signals:
    // "We've captured this image."
    // - Note that QImage is copy-on-write; passing QImage is efficient.
    void imageCaptured(QImage image);

    // "User chose to cancel."
    void cancelled();

    // ========================================================================
    // Internals
    // ========================================================================

protected:
    // Update the display state for the buttons ("take", "lock", "cancel").
    void updateButtons();

    // Start the camera object.
    void startCamera();

    // Stop the camera object.
    void stopCamera();

    // Choose a camera.
    void setCamera(const QCameraDevice& camera_device);

    // Standard Qt overrides.
    void closeEvent(QCloseEvent* event);
    void keyPressEvent(QKeyEvent* event);
    void keyReleaseEvent(QKeyEvent* event);

protected slots:

    // "User has clicked the 'Take' button."
    void takeImage();

    // "Pop up a message showing a camera error."
    void displayCameraError(QCamera::Error value);

    // "Change the ready-for-capture state."
    void readyForCapture(bool ready);

    // "An image has arrived via a temporary disk file."
    void imageSaved(int id, const QString& filename);

    // "Display an error that occurred during the image capture process."
    void displayCaptureError(
        int id, QImageCapture::Error error, const QString& error_string
    );

protected:
    QSharedPointer<QCamera> m_camera;  // our camera
    QSharedPointer<QImageCapture> m_capture;  // records images
    QPointer<QVideoWidget> m_viewfinder;  // our viewfinder
    QMediaCaptureSession m_capture_session;
    QPointer<QPushButton> m_button_cancel;  // "Cancel"
    QPointer<QStatusBar> m_status_bar;  // shows status messages
    QPointer<QAbstractButton> m_button_take;  // "Take"

    // QImageEncoderSettings m_image_settings;  // image encoder settings

    bool m_ready;  // ready to capture?
    bool m_capturing_image;  // currently capturing?
    bool m_exiting;  // closing/exiting?
    QImage m_most_recent_image;  // most recently captured image
#ifndef CAMERA_LOAD_FROM_DISK_PROMPTLY
    QSet<QString> m_filenames_for_deletion;  // temporary files to delete
    QString m_most_recent_filename;  // file with most recent image
    enum class CapturedState {  // ways we may have captured an image
        Nothing,
        File,
        Buffer,
    };
    CapturedState m_captured_state;  // what have we captured?
#endif
};
