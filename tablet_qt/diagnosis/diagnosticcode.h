/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once
#include <QDebug>
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
    static constexpr int COLUMN_SELECTABLE = 3;
    static constexpr int N_COLUMNS = 4;
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
    QVector<int> childIndexes() const;
    void addChildIndex(int index);
    void addChildIndexes(const QVector<int> indexes);

protected:
    DiagnosticCode* m_parent;
    QVector<DiagnosticCode*> m_children;  // owns its children

    QString m_code;
    QString m_description;
    int m_depth;
    bool m_selectable;
    bool m_show_code_in_full_name;

public:
    friend QDebug operator<<(QDebug debug, const DiagnosticCode& dc);
};
