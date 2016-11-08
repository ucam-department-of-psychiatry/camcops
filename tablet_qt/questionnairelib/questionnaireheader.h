#pragma once
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"
#include "qupage.h"

class QAbstractButton;
class QLabel;
class QPushButton;


class QuestionnaireHeader : public QWidget
{
    // Provides a questionnaire's title and its control buttons (e.g. page
    // movement, cancellation).

    Q_OBJECT
public:
    QuestionnaireHeader(QWidget* parent, const QString& title,
                        bool read_only, bool jump_allowed, bool within_chain,
                        const QString& css_name, bool debug_allowed = false);
    void setButtons(bool previous, bool next, bool finish);
signals:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();
    void debugLayout();
protected:
    QString m_title;
    QPointer<QPushButton> m_button_debug;
    QPointer<QAbstractButton> m_button_jump;
    QPointer<QAbstractButton> m_button_previous;
    QPointer<QAbstractButton> m_button_next;
    QPointer<QAbstractButton> m_button_finish;
    QPointer<QLabel> m_icon_no_next;
};
