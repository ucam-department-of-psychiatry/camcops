#pragma once
#include <QObject>

// This should be a private (nested) class of QuMCQGrid, but you can't nest
// Q_OBJECT classes ("Error: Meta object features not supported for nested
// classes").

class FieldRef;
class QuMCQGrid;


class QuMCQGridSignaller : public QObject {
    Q_OBJECT
public:
    QuMCQGridSignaller(QuMCQGrid* recipient, int question_index);
public slots:
    void valueChanged(const FieldRef* fieldref);
protected:
    QuMCQGrid* m_recipient;
    int m_question_index;
};
