#pragma once
#include <QString>
#include "widgets/waitbox.h"

class QApplication;
class QWidget;
class WaitBox;


class SlowGuiGuard
{
    // Create an instance of this object on the stack in a block containing
    // a slow GUI operation. It will:
    //  (1) show a wait box
    //  (2) refresh the GUI manually using processEvents()
    //  ... then you do your slow GUI thing
    //  ... and on destruction:
    //  (3) clear the wait box.

public:
    SlowGuiGuard(QApplication& app,
                 QWidget* parent,
                 const QString& text = "Operation in progress...",
                 const QString& title = "Please wait...",
                 int minimum_duration_ms = 100);
    ~SlowGuiGuard();
protected:
    WaitBox* m_wait_box;
    static bool s_waiting;
};
