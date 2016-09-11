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
    QImage imageFromVideoFrame(const QVideoFrame& buffer) const;
    void closeEvent(QCloseEvent* event);

    // void configureImageSettings();

    void keyPressEvent(QKeyEvent *event);
    void keyReleaseEvent(QKeyEvent *event);

signals:
    void imageCaptured();
    void cancelled();

protected:
    QSharedPointer<QCamera> m_camera;
    QSharedPointer<QCameraImageCapture> m_capture;

    QPointer<QCameraViewfinder> m_viewfinder;
    QPointer<QPushButton> m_lock_button;
    QPointer<QPushButton> m_button_finished;
    QPointer<QPushButton> m_button_cancel;
    QPointer<QStatusBar> m_status_bar;
    QPointer<QAbstractButton> m_button_take;

    QImageEncoderSettings imageSettings;
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
