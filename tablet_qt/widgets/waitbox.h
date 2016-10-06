#pragma once
#include <QProgressDialog>


class WaitBox : public QProgressDialog
{
    Q_OBJECT
public:
    WaitBox(QWidget* parent, const QString& text, const QString& title,
            int minimum_duration_ms = 0);
    virtual ~WaitBox();
};
