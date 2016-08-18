#pragma once
#include "quelement.h"


class QuHorizontalLine : public QuElement
{
public:
    QuHorizontalLine();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
