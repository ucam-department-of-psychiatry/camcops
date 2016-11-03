#pragma once
#include <QObject>

// This should be a private (nested) class of QuMCQGrid, but you can't nest
// Q_OBJECT classes ("Error: Meta object features not supported for nested
// classes").

class FieldRef;
class QuMCQGridDouble;


class QuMCQGridDoubleSignaller : public QObject {
    Q_OBJECT
public:
    QuMCQGridDoubleSignaller(QuMCQGridDouble* recipient, int question_index,
                             bool first_field);
public slots:
    void valueChanged(const FieldRef* fieldref);
protected:
    QuMCQGridDouble* m_recipient;
    int m_question_index;
    bool m_first_field;
};
