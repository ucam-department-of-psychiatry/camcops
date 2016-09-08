#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class QLabel;


class QuPhoto : public QuElement
{
    Q_OBJECT
public:
    QuPhoto(FieldRefPtr fieldref);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);
    void takePhoto();
    void photoChanged();
    void resetFieldToNull();
protected:
    FieldRefPtr m_fieldref;

    bool m_have_camera;
    QPointer<QLabel> m_missing_indicator;
};
