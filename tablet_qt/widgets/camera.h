/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
#include <QCamera>
#include <QCameraImageCapture>
#include <QImage>
#include <QPointer>
#include <QSet>
#include "openablewidget.h"

class QAbstractButton;
class QCameraInfo;
class QCameraViewfinder;
class QLabel;
class QPushButton;
class QStatusBar;
class QStackedWidget;
class QVideoFrame;

// See http://doc.qt.io/qt-5/qtmultimedia-multimediawidgets-camera-example.html


class Camera : public OpenableWidget
{
    // Widget to take a photo.

    Q_OBJECT
public:
    Camera(const QString& stylesheet, QWidget* parent = nullptr);
    Camera(const QCameraInfo& camera_info, const QString& stylesheet,
           QWidget* parent = nullptr);
    ~Camera();
    void finish();
    QImage image() const;
protected:
    void commonConstructor(const QString& stylesheet);
    void updateButtons();
protected slots:
    void setCamera(const QCameraInfo& camera_info);

    void startCamera();
    void stopCamera();

    void toggleLock();
    void updateLockStatus(QCamera::LockStatus status,
                          QCamera::LockChangeReason reason);
    void takeImage();
    void displayCaptureError(int id, QCameraImageCapture::Error error,
                             const QString& error_string);
    void displayCameraError(QCamera::Error value);

    void updateCameraState(QCamera::State state);

    void setExposureCompensation(int index);

    void readyForCapture(bool ready);

    void imageSaved(int id, const QString& filename);
    void imageAvailable(int id, const QVideoFrame& buffer);
    void closeEvent(QCloseEvent* event);

    // void configureImageSettings();

    void keyPressEvent(QKeyEvent *event);
    void keyReleaseEvent(QKeyEvent *event);

signals:
    void imageCaptured(const QImage& image);
    void cancelled();

protected:
    QSharedPointer<QCamera> m_camera;
    QSharedPointer<QCameraImageCapture> m_capture;

    QPointer<QCameraViewfinder> m_viewfinder;
    QPointer<QPushButton> m_lock_button;
    QPointer<QPushButton> m_button_cancel;
    QPointer<QStatusBar> m_status_bar;
    QPointer<QAbstractButton> m_button_take;

    QImageEncoderSettings imageSettings;
    bool m_ready;
    bool m_capturing_image;
    bool m_exiting;
    QSet<QString> m_filenames_for_deletion;
    QString m_most_recent_filename;
    QImage m_most_recent_image;
    enum class CapturedState {
        Nothing,
        File,
        Buffer,
    };
    CapturedState m_captured_state;
};
