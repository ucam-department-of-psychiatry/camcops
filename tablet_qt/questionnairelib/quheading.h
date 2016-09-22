#pragma once
#include <QString>
#include "qutext.h"


class QuHeading : public QuText
{
    // Provides text with a heading style.

    Q_OBJECT
public:
    QuHeading(const QString& text);
    QuHeading(FieldRefPtr fieldref);
};
