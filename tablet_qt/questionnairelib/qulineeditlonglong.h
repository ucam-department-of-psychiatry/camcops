#pragma once
#include "questionnairelib/qulineedit.h"


class QuLineEditLongLong : public QuLineEdit
{
    // Offers a one-line text editor, for an integer.

    Q_OBJECT
public:
    QuLineEditLongLong(FieldRefPtr fieldref, bool allow_empty = true);
    QuLineEditLongLong(FieldRefPtr fieldref, qlonglong minimum,
                        qlonglong maximum, bool allow_empty = true);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    void commonConstructor();
protected:
    qlonglong m_minimum;
    qlonglong m_maximum;
    bool m_allow_empty;
};
