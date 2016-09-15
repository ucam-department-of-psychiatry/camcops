#include "progressbox.h"


ProgressBox::ProgressBox(const QString& label, int n_steps,
                         QWidget* parent) :
    QProgressDialog(label,
                    "",  // cancelButtonText
                    0,  // minimum
                    n_steps,  // maximum
                    parent,
                    Qt::WindowFlags())
{
    setCancelButton(nullptr);  // don't show cancel button
}
