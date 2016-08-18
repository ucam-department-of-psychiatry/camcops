#pragma once
#include "lib/fieldref.h"
#include "quelement.h"


class QuImage : public QuElement
{
public:
    QuImage(const QString& filename);
    QuImage(FieldRefPtr fieldref);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_filename;
    FieldRefPtr m_fieldref;
};
