#pragma once
#include <QDebug>
#include <QList>
#include <QString>

class CamcopsApp;

// http://doc.qt.io/qt-5/qtwidgets-itemviews-simpletreemodel-example.html


class DiagnosticCode
{
public:
    // Column 0 in a QTreeView gets the expand/collapse artwork, so we want
    // our "display" one there.
    static constexpr int COLUMN_FULLNAME = 0;
    static constexpr int COLUMN_CODE = 1;
    static constexpr int COLUMN_DESCRIPTION = 2;
    // http://stackoverflow.com/questions/22318787/const-int-variable-cannot-appear-in-a-constant-expression

public:
    DiagnosticCode(const QString& code, const QString& description,
                   DiagnosticCode* parent, int depth, bool selectable,
                   bool show_code_in_full_name = true);
    ~DiagnosticCode();

    // For our tree structure:
    void appendChild(DiagnosticCode* child);
    DiagnosticCode* child(int row) const;
    DiagnosticCode* parent() const;
    int childCount() const;
    int descendantCount() const;
    int row() const;
    int columnCount() const;
    QVariant data(int column) const;

    // Actual data
    QString code() const;
    QString description() const;
    QString fullname() const;  // for pick-lists

    int depth() const;  // for convenience only
    bool selectable() const;
    bool hasChildren() const;
    QList<int> childIndexes() const;
    void addChildIndex(int index);
    void addChildIndexes(const QList<int> indexes);

protected:
    DiagnosticCode* m_parent;
    QList<DiagnosticCode*> m_children;  // owns its children

    QString m_code;
    QString m_description;
    int m_depth;
    bool m_selectable;
    bool m_show_code_in_full_name;

public:
    friend QDebug operator<<(QDebug debug, const DiagnosticCode& dc);
};
