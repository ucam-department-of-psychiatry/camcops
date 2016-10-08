#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class FocusWatcher;
class GrowingTextEdit;


class QuTextEdit : public QuElement
{
    // Offers an expanding editor for entry of large quantities of text.
    // (For a smaller version, see QuLineEdit.)

    Q_OBJECT
public:
    QuTextEdit(FieldRefPtr fieldref, bool accept_rich_text = false);
    QuTextEdit* setHint(const QString& hint);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void keystroke();
    void textChanged();
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
    void widgetFocusChanged(bool in);
protected:
    FieldRefPtr m_fieldref;
    bool m_accept_rich_text;
    QString m_hint;
    QPointer<GrowingTextEdit> m_editor;
    bool m_ignore_widget_signal;
    QPointer<FocusWatcher> m_focus_watcher;
    QSharedPointer<QTimer> m_timer;
};
