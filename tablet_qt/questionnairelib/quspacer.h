#pragma once
#include "quelement.h"


class QuSpacer : public QuElement
{
    Q_OBJECT
public:
    QuSpacer();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
