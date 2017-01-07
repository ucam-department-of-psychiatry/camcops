/*
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

#define GRIDLAYOUTHFW_ALTER_FROM_QBOXLAYOUT  // comment out to revert to QGridLayout behaviour

#include <QLayout>
#include <QHash>
#include <QVector>
#include "margins.h"
#include "qtlayouthelpers.h"
class QQGridBox;
class QQGridLayoutSizeTriple;


class GridLayoutHfw : public QLayout
{
    // This is to QGridLayout as BoxLayoutHfw (q.v.) is to QBoxLayout.
    // Main changes are:
    // - the layout handling, conditional on #define
    //   GRIDLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    // - change from PIMPL to conventional class idiom
    // - changes from:
    //      MyClass::constFunction() const
    //      {
    //          MyClass* that = const_cast<MyClass*>(this);
    //          that->nonConstFunction();  // modifies m_member
    //      }
    //   to using "mutable"
    // - Margins objects

    Q_OBJECT
    using QLayoutStruct = qtlayouthelpers::QQLayoutStruct;

public:
    explicit GridLayoutHfw(QWidget* parent = nullptr);

    ~GridLayoutHfw();

    QSize sizeHint() const override;
    QSize minimumSize() const override;
    QSize maximumSize() const override;

    void setHorizontalSpacing(int spacing);
    int horizontalSpacing() const;
    void setVerticalSpacing(int spacing);
    int verticalSpacing() const;
    void setSpacing(int spacing);
    int spacing() const;

    void setRowStretch(int row, int stretch);
    void setColumnStretch(int column, int stretch);
    int rowStretch(int row) const;
    int columnStretch(int column) const;

    void setRowMinimumHeight(int row, int minSize);
    void setColumnMinimumWidth(int column, int minSize);
    int rowMinimumHeight(int row) const;
    int columnMinimumWidth(int column) const;

    int columnCount() const;
    int rowCount() const;

    QRect cellRect(int row, int column) const;

    bool hasHeightForWidth() const override;
    int heightForWidth(int) const override;
    int minimumHeightForWidth(int) const override;

    Qt::Orientations expandingDirections() const override;
    void invalidate() override;

    inline void addWidget(QWidget* w) { QLayout::addWidget(w); }
    void addWidget(QWidget* w, int row, int column, Qt::Alignment = Qt::Alignment());
    void addWidget(QWidget* w, int row, int column, int rowSpan, int columnSpan, Qt::Alignment = Qt::Alignment());
    void addLayout(QLayout* w, int row, int column, Qt::Alignment = Qt::Alignment());
    void addLayout(QLayout* w, int row, int column, int rowSpan, int columnSpan, Qt::Alignment = Qt::Alignment());

    void setOriginCorner(Qt::Corner);
    Qt::Corner originCorner() const;

    QLayoutItem* itemAt(int index) const override;
    QLayoutItem* itemAtPosition(int row, int column) const;
    QLayoutItem* takeAt(int index) override;
    int count() const override;
    void setGeometry(const QRect&) override;

    void addItem(QLayoutItem* item, int row, int column, int rowSpan = 1, int columnSpan = 1, Qt::Alignment = Qt::Alignment());

    void setDefaultPositioning(int n, Qt::Orientation orient);
    void getItemPosition(int idx, int* row, int* column,
                         int* rowSpan, int* columnSpan) const;

protected:
    void addItem(QLayoutItem* item) override;

private:
    // Disable copy-constructor and copy-assignment-operator:
    GridLayoutHfw(GridLayoutHfw const&) = delete;
    void operator=(GridLayoutHfw const& x) = delete;

    // ------------------------------------------------------------------------
    // From QGridLayoutPrivate:
    // ------------------------------------------------------------------------
private:
    void add(QQGridBox*, int row, int col);
    void add(QQGridBox*, int row1, int row2, int col1, int col2);
    QSize sizeHint(int hSpacing, int vSpacing) const;
    QSize minimumSize(int hSpacing, int vSpacing) const;
    QSize maximumSize(int hSpacing, int vSpacing) const;

    Qt::Orientations expandingDirections(int hSpacing, int vSpacing) const;

    void distribute(QRect rect, int hSpacing, int vSpacing);
    inline int numRows() const { return m_rr; }
    inline int numCols() const { return m_cc; }
    inline int rowSpacing(int r) const { return m_r_min_heights.at(r); }
    inline int colSpacing(int c) const { return m_c_min_widths.at(c); }
    inline void setReversed(bool r, bool c) { m_h_reversed = c; m_v_reversed = r; }
    inline bool horReversed() const { return m_h_reversed; }
    inline bool verReversed() const { return m_v_reversed; }
    inline void setDirty() { m_need_recalc = true; m_hfw_width = -1; }
    inline bool isDirty() const { return m_need_recalc; }
    bool hasHeightForWidth(int hSpacing, int vSpacing) const;
    int heightForWidth(int width, int hSpacing, int vSpacing) const;
    int minimumHeightForWidth(int width, int hSpacing, int vSpacing) const;

    inline void getNextPos(int& row, int& col) { row = m_next_r; col = m_next_c; }

    QLayoutItem* replaceAt(int index, QLayoutItem* newitem);  // RNC: was override (of QLayoutPrivate)
    void deleteAll();

    void expand(int rows, int cols);

private:
    void setNextPosAfter(int r, int c);
    void recalcHFW(int w) const;
    void addHfwData(QQGridBox* box, int width) const;
    void init();
    QSize findSize(int QLayoutStruct::* size,
                   int hSpacing, int vSpacing) const;
    void addData(QQGridBox* box, const QQGridLayoutSizeTriple& sizes,
                 bool r, bool c) const;
    void setSize(int rows, int cols);
    void setupSpacings(QVector<QLayoutStruct> &chain, QQGridBox* grid[],
                       int fixedSpacing, Qt::Orientation orientation) const;
    void setupLayoutData(int hSpacing, int vSpacing) const;
    void setupHfwLayoutData() const;
    // void effectiveMargins(int* left, int* top, int* right, int* bottom) const;
    Margins effectiveMargins() const;

    int m_rr;
    int m_cc;
    mutable QVector<QLayoutStruct> m_row_data;
    mutable QVector<QLayoutStruct> m_col_data;
    mutable QVector<QLayoutStruct>* m_hfw_data;
    mutable QVector<int> m_r_stretches;
    mutable QVector<int> m_c_stretches;
    QVector<int> m_r_min_heights;
    QVector<int> m_c_min_widths;
    QList<QQGridBox*> m_things;

    mutable int m_hfw_width;
    mutable int m_hfw_height;
    mutable int m_hfw_minheight;
    int m_next_r;
    int m_next_c;

    int m_horizontal_spacing;
    int m_vertical_spacing;

    mutable Margins m_contents_margins;
    // mutable int m_left_margin;
    // mutable int m_top_margin;
    // mutable int m_right_margin;
    // mutable int m_bottom_margin;

    bool m_h_reversed;  // RNC: was uint : 1
    bool m_v_reversed;  // RNC: was uint : 1
    mutable bool m_need_recalc;  // RNC: was uint : 1
    mutable bool m_has_hfw;  // RNC: was uint : 1
    bool m_add_vertical;  // RNC: was uint : 1
};
