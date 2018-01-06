/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once

#define CAMERA_LOAD_FROM_DISK_PROMPTLY
#define CAMERA_QCAMERA_USE_VIDEO_SURFACE_VIEWFINDER  // required for viewfinder on Android

/*

SUMMARY OF DECISIONS about camera methods:
1.  QCamera with QCameraViewFinder
    - fine under Linux
    - under Android, blank viewfinder, and warning:
      warning: The video surface is not compatible with any format supported by the camera

2.  QCamera with custom CameraFrameGrabber
    - fine under Linux
    - under Android, segfault with:
      attachToContext: invalid current EGLDisplay

3.  QML
    - not only fine under Linux, but significantly better (features +/- speed)
    - declarative-camera demo works under Android
- see CameraQml class

*/

#include <QCamera>
#include <QCameraImageCapture>
#include <QImage>
#include <QPointer>
#include <QSet>
#include "widgets/openablewidget.h"
class CameraFrameGrabber;
class QAbstractButton;
class QCameraInfo;
class QCameraViewfinder;
class QLabel;
class QQuickWidget;
class QPushButton;
class QStatusBar;
class QStackedWidget;
class QVideoFrame;

#ifndef CAMERA_QCAMERA_USE_VIDEO_SURFACE_VIEWFINDER
#define CAMERA_QCAMERA_USE_QCAMERAVIEWFINDER
#endif


class CameraQCamera : public OpenableWidget
{
    // Widget to take a photo.

    Q_OBJECT
public:
    // ========================================================================
    // Constructor/destructor
    // ========================================================================
    CameraQCamera(const QString& stylesheet, QWidget* parent = nullptr);
    CameraQCamera(const QCameraInfo& camera_info, const QString& stylesheet,
           QWidget* parent = nullptr);
    ~CameraQCamera();
    // ========================================================================
    // Public interface
    // ========================================================================
    void finish();
    QImage image() const;
    void setPreviewResolution(const QSize& resolution);
    void setMainResolution(const QSize& resolution);
signals:
    void imageCaptured(QImage image);  // QImage is copy-on-write
    void cancelled();
    // ========================================================================
    // Internals
    // ========================================================================
protected:
    void commonConstructor(const QString& stylesheet);
protected:
    void updateButtons();
    void startCamera();
    void stopCamera();
    void setCamera(const QCameraInfo& camera_info);
    void toggleLock();
    void unlockCamera();
    void searchAndLockCamera();
    void setExposureCompensation(int index);
    // void configureImageSettings();
    void closeEvent(QCloseEvent* event);
    void keyPressEvent(QKeyEvent* event);
    void keyReleaseEvent(QKeyEvent* event);

protected slots:
    void takeImage();
    void updateCameraState(QCamera::State state);
    void displayCameraError(QCamera::Error value);
    void updateLockStatus(QCamera::LockStatus status,
                          QCamera::LockChangeReason reason);
    void readyForCapture(bool ready);
    void imageSaved(int id, const QString& filename);
    void imageAvailable(int id, const QVideoFrame& buffer);
    void displayCaptureError(int id, QCameraImageCapture::Error error,
                             const QString& error_string);
#ifdef CAMERA_QCAMERA_USE_VIDEO_SURFACE_VIEWFINDER
    void handleFrame(QImage image);  // QImage is copy-on-write
#endif

protected:
    QSize m_resolution_preview;
    QSize m_resolution_main;
    QSharedPointer<QCamera> m_camera;
    QSharedPointer<QCameraImageCapture> m_capture;
#ifdef CAMERA_QCAMERA_USE_QCAMERAVIEWFINDER
    QPointer<QCameraViewfinder> m_viewfinder;
#endif
#ifdef CAMERA_QCAMERA_USE_VIDEO_SURFACE_VIEWFINDER
    QPointer<CameraFrameGrabber> m_framegrabber;
    QPointer<QLabel> m_label_viewfinder;
#endif
    QPointer<QPushButton> m_lock_button;
    QPointer<QPushButton> m_button_cancel;
    QPointer<QStatusBar> m_status_bar;
    QPointer<QAbstractButton> m_button_take;

    QImageEncoderSettings imageSettings;
    bool m_ready;
    bool m_capturing_image;
    bool m_exiting;
    QImage m_most_recent_image;
#ifndef CAMERA_LOAD_FROM_DISK_PROMPTLY
    QSet<QString> m_filenames_for_deletion;
    QString m_most_recent_filename;
    enum class CapturedState {
        Nothing,
        File,
        Buffer,
    };
    CapturedState m_captured_state;
#endif
};
