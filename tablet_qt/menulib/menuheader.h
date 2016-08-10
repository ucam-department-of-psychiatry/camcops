#pragma once
#include <QWidget>
#include "common/camcops_app.h"


class MenuHeader : public QWidget
{
    Q_OBJECT
public:
    MenuHeader(QWidget* parent,
               CamcopsApp& app,
               bool top,
               const QString& title);
signals:
    void back();
protected:
    void backClicked();  // slot
    void lockStateChanged(LockState lockstate);
protected:
    CamcopsApp& m_app;
    QAbstractButton* m_button_locked;
    QAbstractButton* m_button_unlocked;
    QAbstractButton* m_button_privileged;
};
