#pragma once
#include "lib/fieldref.h"
#include "namevalueoptions.h"
#include "quelement.h"

class QComboBox;
class QLabel;


class QuPickerInline : public QuElement
{
    Q_OBJECT
public:
    QuPickerInline(FieldRefPtr fieldref, const NameValueOptions& options);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void currentIndexChanged(int index);
    void valueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    NameValueOptions m_options;
    QPointer<QComboBox> m_cbox;
    QPointer<QLabel> m_label;
};
