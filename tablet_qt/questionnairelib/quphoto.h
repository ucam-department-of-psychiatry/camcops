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

#define QUPHOTO_USE_CAMERA_QML

#include "db/blobfieldref.h"
#include "questionnairelib/quelement.h"

class AspectRatioPixmap;
class CameraQCamera;
class CameraQml;
class QLabel;
class QWidget;


class QuPhoto : public QuElement
{
    // Allows users to take a photo using the device's camera.

    Q_OBJECT
public:
    QuPhoto(BlobFieldRefPtr fieldref);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    void rotate(int angle_degrees_clockwise);
    void rotateWorker(int angle_degrees_clockwise);
protected slots:
    void fieldValueChanged(const FieldRef* fieldref);
    void takePhoto();
    void resetFieldToNull();
    void rotateLeft();
    void rotateRight();

    void cameraCancelled();
    void rawImageCaptured(const QByteArray& data,
                          const QString& extension_without_dot,
                          const QString& mimetype);
    void imageCaptured(const QImage& image);

protected:
    BlobFieldRefPtr m_fieldref;
    bool m_have_camera;

    QPointer<Questionnaire> m_questionnaire;
    QPointer<QLabel> m_incomplete_optional_label;
    QPointer<QLabel> m_incomplete_mandatory_label;
    QPointer<QLabel> m_field_problem_label;
    QPointer<AspectRatioPixmap> m_image_widget;
#ifdef QUPHOTO_USE_CAMERA_QML
    QPointer<CameraQml> m_camera;
#else
    QPointer<CameraQCamera> m_camera;
#endif
    QPointer<QWidget> m_main_widget;
};
