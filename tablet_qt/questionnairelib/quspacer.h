#pragma once
#include "quelement.h"


class QuSpacer : public Cloneable<QuElement, QuSpacer>
{
public:
    QuSpacer();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
