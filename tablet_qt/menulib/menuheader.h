#pragma once
#include <QWidget>
#include "common/camcopsapp.h"


class MenuHeader : public QWidget
{
    Q_OBJECT
public:
    MenuHeader(QWidget* parent,
               CamcopsApp& app,
               bool top,
               const QString& title,
               const QString& icon_filename = "");
signals:
    void back();
protected:
    void backClicked();  // slot
    void lockStateChanged(LockState lockstate);  // slot
    void whiskerConnectionStateChanged(bool connected);  // slot
protected:
    CamcopsApp& m_app;
    QLabel* m_icon_whisker_connected;
    QAbstractButton* m_button_locked;
    QAbstractButton* m_button_unlocked;
    QAbstractButton* m_button_privileged;
};
