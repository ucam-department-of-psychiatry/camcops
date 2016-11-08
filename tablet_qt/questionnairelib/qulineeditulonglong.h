#pragma once
#include "questionnairelib/qulineedit.h"


class QuLineEditULongLong : public QuLineEdit
{
    // Offers a one-line text editor, for an integer.

    Q_OBJECT
public:
    QuLineEditULongLong(FieldRefPtr fieldref, bool allow_empty = true);
    QuLineEditULongLong(FieldRefPtr fieldref, qulonglong minimum,
                        qulonglong maximum, bool allow_empty = true);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    void commonConstructor();
protected:
    qulonglong m_minimum;
    qulonglong m_maximum;
    bool m_allow_empty;
};
