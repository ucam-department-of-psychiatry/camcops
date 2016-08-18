#include "qubutton.h"
#include <QPushButton>


QuButton::QuButton(const QString& label,
                   const CallbackFunction& callback) :
    m_label(label),
    m_callback(callback)
{
}


QPointer<QWidget> QuButton::makeWidget(Questionnaire* questionnaire)
{
    (void)questionnaire;
    QPushButton* button = new QPushButton(m_label);
    QSizePolicy sp(QSizePolicy::Fixed, QSizePolicy::Fixed);
    button->setSizePolicy(sp);
    connect(button, &QPushButton::clicked,
            this, &QuButton::clicked);
    return QPointer<QWidget>(button);
}


void QuButton::clicked()
{
    m_callback();
}
