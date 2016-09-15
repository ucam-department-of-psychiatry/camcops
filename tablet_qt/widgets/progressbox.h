#pragma once
#include <QProgressDialog>


// Prototypical use: modal, as per
// http://doc.qt.io/qt-5.7/qprogressdialog.html#details

class ProgressBox : public QProgressDialog
{
    Q_OBJECT
public:
    ProgressBox(const QString& label, int n_steps, QWidget* parent);
};
