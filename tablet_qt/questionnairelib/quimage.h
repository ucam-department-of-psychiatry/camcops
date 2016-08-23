#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class QLabel;


class QuImage : public QuElement
{
    Q_OBJECT
public:
    QuImage(const QString& filename);
    QuImage(FieldRefPtr fieldref);  // field provides raw image data
protected slots:
    void valueChanged(const QVariant& value);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_filename;
    FieldRefPtr m_fieldref;
    QPointer<QLabel> m_label;
};
