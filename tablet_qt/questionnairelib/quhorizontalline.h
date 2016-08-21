#pragma once
#include "quelement.h"


class QuHorizontalLine : public Cloneable<QuElement, QuHorizontalLine>
{
public:
    QuHorizontalLine();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
