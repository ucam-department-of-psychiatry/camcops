#pragma once
#include "db/fieldref.h"
#include "quelement.h"

class QLabel;


class QuImage : public QuElement
{
    // Displays an image (from a static filename or a field).
    // No user response offered.

    Q_OBJECT
public:
    QuImage(const QString& filename);
    QuImage(FieldRefPtr fieldref);  // field provides raw image data
protected slots:
    void valueChanged(const FieldRef* fieldref);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_filename;
    FieldRefPtr m_fieldref;
    QPointer<QLabel> m_label;
};
