#pragma once
#include <QList>
#include <QString>

class CamcopsApp;


class DiagnosticCode
{
public:
    DiagnosticCode(int index,
                   const QString& code, const QString& description,
                   int parent_index, int depth, bool selectable,
                   bool show_code_in_full_name = true);
    int index() const;
    QString code() const;
    QString description() const;
    QString fullname() const;  // for pick-lists
    int parentIndex() const;
    int depth() const;
    bool selectable() const;
    bool hasChildren() const;
    QList<int> childIndexes() const;
    void addChildIndex(int index);
    void addChildIndexes(const QList<int> indexes);

protected:
    int m_index;
    QString m_code;
    QString m_description;
    int m_parent_index;
    int m_depth;
    bool m_selectable;
    bool m_show_code_in_full_name;
    QList<int> m_child_indexes;
};
