#pragma once
#include <QDialog>
#include <QString>
#include "questionnairelib/namevalueoptions.h"

class QVariant;


class NvpChoiceDialog : public QDialog
{
    // Dialog to choose between a set of name/value pairs (offering the names,
    // returning the chosen value via a pointer).

    Q_OBJECT
public:
    NvpChoiceDialog(QWidget* parent, const NameValueOptions& options,
                    const QString& title = "");
    virtual int choose(QVariant* new_value);
protected slots:
    void itemClicked(int index);
protected:
    NameValueOptions m_options;
    QString m_title;
    QVariant* m_new_value;
};
