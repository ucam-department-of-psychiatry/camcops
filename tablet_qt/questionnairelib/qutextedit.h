#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class GrowingTextEdit;


class QuTextEdit : public QuElement
{
    Q_OBJECT
public:
    QuTextEdit(FieldRefPtr fieldref, bool accept_rich_text = false);
    QuTextEdit* setHint(const QString& hint);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void textChanged();
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
protected:
    FieldRefPtr m_fieldref;
    bool m_accept_rich_text;
    QString m_hint;
    QPointer<GrowingTextEdit> m_editor;
    bool m_ignore_widget_signal;
};
