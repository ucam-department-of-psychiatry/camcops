#pragma once
#include "db/fieldref.h"
#include "namevalueoptions.h"
#include "quelement.h"

class QComboBox;
class QLabel;


class QuPickerInline : public QuElement
{
    // Offers a drop-down list of choices, or device equivalent.

    Q_OBJECT
public:
    QuPickerInline(FieldRefPtr fieldref, const NameValueOptions& options);
    QuPickerInline* setRandomize(bool randomize);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void currentIndexChanged(int index);
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    NameValueOptions m_options;
    bool m_randomize;
    QPointer<QComboBox> m_cbox;
};
