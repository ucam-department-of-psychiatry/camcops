#pragma once
#include "quelement.h"
#include <functional>
#include <QMap>
#include <QString>
#include <QVariant>


class QuButton : public Cloneable<QuElement, QuButton>
{
public:
    typedef QMap<QString, QVariant> Args;
    typedef std::function<void()> CallbackFunction;
    // To pass other arguments, use std::bind to bind them before passing here
    QuButton(const QString& label, const CallbackFunction& callback);
    // *** icon (+ icon-touchable-state), callback
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected slots:
    void clicked();
protected:
    QString m_label;
    CallbackFunction m_callback;
};
