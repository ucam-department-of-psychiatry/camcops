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
#include "db/fieldref.h"
#include "quelement.h"

class AspectRatioPixmap;
class Camera;
class QLabel;
class QWidget;


class QuPhoto : public QuElement
{
    // Allows users to take a photo using the device's camera.

    Q_OBJECT
public:
    QuPhoto(FieldRefPtr fieldref);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    void rotate(qreal angle_degrees);
    void rotateWorker(qreal angle_degrees);
protected slots:
    void fieldValueChanged(const FieldRef* fieldref);
    void takePhoto();
    void resetFieldToNull();
    void rotateLeft();
    void rotateRight();

    void cameraCancelled();
    void imageCaptured(const QImage& image);

protected:
    FieldRefPtr m_fieldref;
    bool m_have_camera;

    QPointer<Questionnaire> m_questionnaire;
    QPointer<QLabel> m_incomplete_optional;
    QPointer<QLabel> m_incomplete_mandatory;
    QPointer<QLabel> m_field_problem;
    QPointer<AspectRatioPixmap> m_image;
    QPointer<Camera> m_camera;
    QPointer<QWidget> m_main_widget;
};
