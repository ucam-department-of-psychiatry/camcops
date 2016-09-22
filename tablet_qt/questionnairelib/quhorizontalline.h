#pragma once
#include "quelement.h"


class QuHorizontalLine : public QuElement
{
    // Provides a plain horizontal divider line.

    Q_OBJECT
public:
    QuHorizontalLine();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
