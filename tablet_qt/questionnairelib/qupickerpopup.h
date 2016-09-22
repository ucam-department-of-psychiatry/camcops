#pragma once
#include "lib/fieldref.h"
#include "namevalueoptions.h"
#include "quelement.h"

class ClickableLabel;


class QuPickerPopup : public QuElement
{
    // Offers a pop-up dialogue of choices, or device equivalent.

    Q_OBJECT
public:
    QuPickerPopup(FieldRefPtr fieldref, const NameValueOptions& options);
    QuPickerPopup* setPopupTitle(const QString& popup_title);
    QuPickerPopup* setRandomize(bool randomize);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void clicked();
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    NameValueOptions m_options;
    QString m_popup_title;
    bool m_randomize;
    QPointer<ClickableLabel> m_label;
};
