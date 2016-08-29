#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class FocusWatcher;
class QLineEdit;


class QuLineEdit : public QuElement
{
    Q_OBJECT
public:
    QuLineEdit(FieldRefPtr fieldref);
    QuLineEdit* setHint(const QString& hint);
    virtual void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual void extraLineEditCreation(QLineEdit* editor);  // override to specialize
protected slots:
    virtual void widgetTextChanged();
    virtual void fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator = nullptr);
    virtual void widgetFocusChanged(bool in);
protected:
    FieldRefPtr m_fieldref;
    QString m_hint;
    QPointer<QLineEdit> m_editor;
    QPointer<FocusWatcher> m_focus_watcher;
};
