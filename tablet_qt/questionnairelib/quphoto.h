#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class AspectRatioPixmapLabel;
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
    QPointer<AspectRatioPixmapLabel> m_image;
    QPointer<Camera> m_camera;
    QPointer<QWidget> m_main_widget;
};
