#pragma once
#include "quelement.h"


class QuSpacer : public QuElement
{
    // Provides a fixed-size spacer object.

    Q_OBJECT
public:
    QuSpacer();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
