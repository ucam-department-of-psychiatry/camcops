#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class FocusWatcher;
class QLineEdit;


class QuLineEdit : public QuElement
{
    // Offers a one-line text editor, for a string.
    // (For a bigger version, see QuTextEdit.)

    Q_OBJECT
public:
    QuLineEdit(FieldRefPtr fieldref);
    QuLineEdit* setHint(const QString& hint);
protected:
    virtual void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual void extraLineEditCreation(QLineEdit* editor);  // override to specialize
protected slots:
    virtual void keystroke();
    virtual void widgetTextChangedMaybeValid();
    virtual void widgetTextChangedAndValid();
    virtual void fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator = nullptr);
    virtual void widgetFocusChanged(bool in);
protected:
    FieldRefPtr m_fieldref;
    QString m_hint;
    QPointer<QLineEdit> m_editor;
    QPointer<FocusWatcher> m_focus_watcher;
    QSharedPointer<QTimer> m_timer;
};
