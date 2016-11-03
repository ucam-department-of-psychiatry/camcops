#pragma once
#include <QObject>

// This should be a private (nested) class of QuMCQGrid, but you can't nest
// Q_OBJECT classes ("Error: Meta object features not supported for nested
// classes").

class FieldRef;
class QuMCQGridSingleBoolean;


class QuMCQGridSingleBooleanSignaller : public QObject {
    Q_OBJECT
public:
    QuMCQGridSingleBooleanSignaller(QuMCQGridSingleBoolean* recipient,
                                    int question_index);
public slots:
    void mcqFieldValueChanged(const FieldRef* fieldref);
    void booleanFieldValueChanged(const FieldRef* fieldref);
protected:
    QuMCQGridSingleBoolean* m_recipient;
    int m_question_index;
};
