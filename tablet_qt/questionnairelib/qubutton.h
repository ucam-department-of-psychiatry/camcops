#pragma once
#include "quelement.h"
#include <functional>
#include <QMap>
#include <QString>
#include <QVariant>


class QuButton : public QuElement
{
    Q_OBJECT
public:
    using Args = QMap<QString, QVariant>;
    using CallbackFunction = std::function<void()>;
    // To pass other arguments, use std::bind to bind them before passing here

    QuButton(const QString& label, const CallbackFunction& callback);
    QuButton(const QString& icon_filename, bool filename_is_camcops_stem,
             bool alter_unpressed_image, const CallbackFunction& callback);
    QuButton* setActive(bool active);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected slots:
    void clicked();
protected:
    QString m_label;
    QString m_icon_filename;
    bool m_filename_is_camcops_stem;
    bool m_alter_unpressed_image;
    CallbackFunction m_callback;
    bool m_active;
};
