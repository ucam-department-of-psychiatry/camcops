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

#define GRIDLAYOUTHFW_ALTER_FROM_QGRIDLAYOUT  // comment out to revert to QGridLayout behaviour

#include <QLayout>
#include <QHash>
#include <QVector>
#include "lib/margins.h"
#include "layouts/qtlayouthelpers.h"
class QQGridBox;
struct QQGridLayoutSizeTriple;


class GridLayoutHfw : public QLayout
{
    // This is to QGridLayout as BoxLayoutHfw (q.v.) is to QBoxLayout.
    // Main changes are:
    // - the layout handling, conditional on #define
    //   GRIDLAYOUTHFW_ALTER_FROM_QGRIDLAYOUT
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

    struct GeomInfo {  // RNC
        QVector<QLayoutStruct> m_row_data;
        QVector<QLayoutStruct> m_col_data;
        QVector<QLayoutStruct> m_hfw_data;  // was a pointer
        QSize m_size_hint;
        QSize m_min_size;
        QSize m_max_size;
        Qt::Orientations m_expanding;
        bool m_has_hfw;
        int m_hfw_height;
        int m_hfw_min_height;
    };

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

    void setRowMinimumHeight(int row, int min_size);
    void setColumnMinimumWidth(int column, int min_size);
    int rowMinimumHeight(int row) const;
    int columnMinimumWidth(int column) const;

    int columnCount() const;
    int rowCount() const;

    QRect cellRect(const GeomInfo& gi, int row, int column) const;

    bool hasHeightForWidth() const override;
    int heightForWidth(int) const override;
    int minimumHeightForWidth(int) const override;

    Qt::Orientations expandingDirections() const override;
    void invalidate() override;

    inline void addWidget(QWidget* w) { QLayout::addWidget(w); }
    void addWidget(QWidget* w, int row, int column,
                   Qt::Alignment = Qt::Alignment());
    void addWidget(QWidget* w, int row, int column,
                   int row_span, int column_span,
                   Qt::Alignment = Qt::Alignment());
    void addLayout(QLayout* w, int row, int column,
                   Qt::Alignment = Qt::Alignment());
    void addLayout(QLayout* w, int row, int column,
                   int row_span, int column_span,
                   Qt::Alignment = Qt::Alignment());

    void setOriginCorner(Qt::Corner);
    Qt::Corner originCorner() const;

    QLayoutItem* itemAt(int index) const override;
    QLayoutItem* itemAtPosition(int row, int column) const;
    QLayoutItem* takeAt(int index) override;
    int count() const override;
    void setGeometry(const QRect&) override;

    void addItem(QLayoutItem* item, int row, int column,
                 int row_span = 1, int column_span = 1,
                 Qt::Alignment = Qt::Alignment());

    void setDefaultPositioning(int n, Qt::Orientation orient);
    void getItemPosition(int idx, int* row, int* column,
                         int* row_span, int* column_span) const;

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
    void distribute(const QRect& layout_rect);
    inline int numRows() const { return m_nrow; }
    inline int numCols() const { return m_ncol; }
    inline int rowSpacing(int r) const { return m_r_min_heights.at(r); }
    inline int colSpacing(int c) const { return m_c_min_widths.at(c); }
    inline void setReversed(bool r, bool c) { m_h_reversed = c; m_v_reversed = r; }
    inline bool horReversed() const { return m_h_reversed; }
    inline bool verReversed() const { return m_v_reversed; }
    void setDirty();  // RNC: was inline and defined here
    inline bool isDirty() const { return m_dirty; }
    inline void getNextPos(int& row, int& col) { row = m_next_r; col = m_next_c; }

    QLayoutItem* replaceAt(int index, QLayoutItem* newitem);  // RNC: was override (of QLayoutPrivate)
    void deleteAll();

    void expand(int rows, int cols);

private:
    void setNextPosAfter(int r, int c);
    void recalcHFW(int w) const;
    void addHfwData(GeomInfo& gi, QQGridBox* box, int width) const;
    void init();
    void addData(GeomInfo& gi, QQGridBox* box,
                 const QQGridLayoutSizeTriple& sizes, bool r, bool c) const;
    void setSize(int rows, int cols);
    void setupSpacings(QVector<QLayoutStruct> &chain, QQGridBox* grid[],
                       int fixedSpacing, Qt::Orientation orientation) const;
    void setupHfwLayoutData() const;
    // void effectiveMargins(int* left, int* top, int* right, int* bottom) const;
    Margins effectiveMargins(const Margins& contents_margins) const;  // RNC
    Margins effectiveMargins() const;  // RNC
    QRect getContentsRect(const QRect& layout_rect) const; // RNC
    QSize findSize(const GeomInfo& gi, int QLayoutStruct::* size) const;

#ifdef GRIDLAYOUTHFW_ALTER_FROM_QGRIDLAYOUT
    void clearCaches() const;  // RNC
    int getParentTargetHeight(QWidget* parent, const Margins& parent_margins,
                              const GeomInfo& gi) const;
    GeomInfo getGeomInfo(const QRect& layout_rect) const;  // RNC
#endif
    GeomInfo getGeomInfo() const;  // RNC
    GeomInfo getGeomInfoForHfw(int w) const;  // RNC

    // These describe what items we have:

    int m_nrow;  // was rr; number of rows
    int m_ncol;  // was cc; number of columns
    mutable QVector<int> m_r_stretches;
    mutable QVector<int> m_c_stretches;
    QVector<int> m_r_min_heights;
    QVector<int> m_c_min_widths;
    QVector<QQGridBox*> m_things;  // list of owned objects

    // These govern where new inserted items are put:

    bool m_add_vertical;  // RNC: was uint : 1
    int m_next_r;
    int m_next_c;

    // Global settings

    int m_horizontal_spacing;
    int m_vertical_spacing;
    bool m_h_reversed;  // RNC: was uint : 1  -- and not sure it ever changes
    bool m_v_reversed;  // RNC: was uint : 1  -- and not sure it ever changes

    // This is layout/geometry/HFW data:

#ifdef GRIDLAYOUTHFW_ALTER_FROM_QGRIDLAYOUT
    mutable int m_width_last_size_constraints_based_on;
    mutable QRect m_rect_for_next_size_constraints;
    mutable QHash<QRect, GeomInfo> m_geom_cache;  // RNC
#else
    mutable GeomInfo m_cached_geominfo;
    mutable int m_cached_hfw_width;
#endif

    mutable Margins m_effective_margins;  // RNC; replacing leftMargin, topMargin, rightMargin, bottomMargin

    mutable bool m_dirty;  // RNC: was uint : 1  -- was needRecalc
    int m_reentry_depth;  // RNC

public:
    friend QDebug operator<<(QDebug debug, const GeomInfo& gi);
};
