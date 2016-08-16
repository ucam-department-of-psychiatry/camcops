#pragma once
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"
#include "page.h"

class QAbstractButton;
class QLabel;


class QuestionnaireHeader : public QWidget
{
    Q_OBJECT
public:
    QuestionnaireHeader(QWidget* parent, const QString& title,
                        bool read_only, bool jump_allowed, bool within_chain,
                        int fontsize, const QString& css_name);
    void setButtons(bool previous, bool next, bool finish);
signals:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();
protected:
    QString m_title;
    QPointer<QAbstractButton> m_button_jump;
    QPointer<QAbstractButton> m_button_previous;
    QPointer<QAbstractButton> m_button_next;
    QPointer<QAbstractButton> m_button_finish;
};
