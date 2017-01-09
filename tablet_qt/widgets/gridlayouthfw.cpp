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

// From qgridlayout.cpp:
/****************************************************************************
**
** Copyright (C) 2016 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the QtWidgets module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 3 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL3 included in the
** packaging of this file. Please review the following information to
** ensure the GNU Lesser General Public License version 3 requirements
** will be met: https://www.gnu.org/licenses/lgpl-3.0.html.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 2.0 or (at your option) the GNU General
** Public license version 3 or any later version approved by the KDE Free
** Qt Foundation. The licenses are as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL2 and LICENSE.GPL3
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-2.0.html and
** https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

#define DEBUG_LAYOUT
#define Q_OS_MAC  // for testing only, just to be sure it compiles OK...

#include "gridlayouthfw.h"
#include <QApplication>
#include <QWidget>
#include <QList>
#include <QSizePolicy>
#include <QVector>
#include <QVarLengthArray>
// #include "qlayoutengine_p.h"
// #include "qlayout_p.h"

#ifdef DEBUG_LAYOUT
#include <QDebug>
#endif

using qtlayouthelpers::checkLayout;
using qtlayouthelpers::checkWidget;
using qtlayouthelpers::createWidgetItem;
using qtlayouthelpers::QQLayoutStruct;
using qtlayouthelpers::qMaxExpCalc;
using qtlayouthelpers::qSmartSpacing;


struct QQGridLayoutSizeTriple
{
    QSize minS;
    QSize hint;
    QSize maxS;
};


// Three internal classes related to QGridLayout: (1) QQGridBox is a
// QLayoutItem with (row, column) information and (torow, tocolumn)
// information; (3) QGridLayoutData is the internal representation of a
// QGridLayout.

// RNC: renamed (Q prefix); also there is no (2) in that list.

// ============================================================================
// QQGridBox
// ============================================================================

class QQGridBox
{
public:
    QQGridBox(QLayoutItem* lit) { item_ = lit; }

    QQGridBox(const QLayout* l, QWidget* wid) { item_ = createWidgetItem(l, wid); }
    ~QQGridBox() { delete item_; }

    QSize sizeHint() const { return item_->sizeHint(); }
    QSize minimumSize() const { return item_->minimumSize(); }
    QSize maximumSize() const { return item_->maximumSize(); }
    Qt::Orientations expandingDirections() const { return item_->expandingDirections(); }
    bool isEmpty() const { return item_->isEmpty(); }

    bool hasHeightForWidth() const { return item_->hasHeightForWidth(); }
    int heightForWidth(int w) const { return item_->heightForWidth(w); }

    void setAlignment(Qt::Alignment a) { item_->setAlignment(a); }
    void setGeometry(const QRect &r) { item_->setGeometry(r); }
    Qt::Alignment alignment() const { return item_->alignment(); }
    QLayoutItem* item() { return item_; }
    void setItem(QLayoutItem* newitem) { item_ = newitem; }
    QLayoutItem* takeItem() { QLayoutItem* i = item_; item_ = 0; return i; }

    int hStretch() { return item_->widget() ?
                         item_->widget()->sizePolicy().horizontalStretch() : 0; }
    int vStretch() { return item_->widget() ?
                         item_->widget()->sizePolicy().verticalStretch() : 0; }

private:
    friend class GridLayoutHfw;

    inline int toRow(int rr) const { return torow >= 0 ? torow : rr - 1; }
    inline int toCol(int cc) const { return tocol >= 0 ? tocol : cc - 1; }

    QLayoutItem* item_;
    int row, col;
    int torow, tocol;
};


// ============================================================================
// from QGridLayoutPrivate
// ============================================================================

// void GridLayoutHfw::effectiveMargins(int* left, int* top,
//                                      int* right, int* bottom) const
Margins GridLayoutHfw::effectiveMargins(const Margins& contents_margins) const
{
    int l = contents_margins.left();
    int t = contents_margins.top();
    int r = contents_margins.right();
    int b = contents_margins.bottom();
#ifdef Q_OS_MAC
    int leftMost = INT_MAX;
    int topMost = INT_MAX;
    int rightMost = 0;
    int bottomMost = 0;

    QWidget* w = 0;
    const int n = m_things.count();
    for (int i = 0; i < n; ++i) {
        QQGridBox* box = m_things.at(i);
        QLayoutItem* itm = box->item();
        w = itm->widget();
        if (w) {
            bool visualHReversed = m_h_reversed != (w->layoutDirection() == Qt::RightToLeft);
            QRect lir = itm->geometry();
            QRect wr = w->geometry();
            if (box->col <= leftMost) {
                if (box->col < leftMost) {
                    // we found an item even closer to the margin, discard.
                    leftMost = box->col;
                    if (visualHReversed) {
                        r = contents_margins.right();  // m_right_margin;
                    } else {
                        l = contents_margins.left();  // m_left_margin;
                    }
                }
                if (visualHReversed) {
                    r = qMax(r, wr.right() - lir.right());
                } else {
                    l = qMax(l, lir.left() - wr.left());
                }
            }
            if (box->row <= topMost) {
                if (box->row < topMost) {
                    // we found an item even closer to the margin, discard.
                    topMost = box->row;
                    if (m_v_reversed) {
                        b = contents_margins.bottom();  // m_bottom_margin;
                    } else {
                        t = contents_margins.top();  // m_top_margin;
                    }
                }
                if (m_v_reversed) {
                    b = qMax(b, wr.bottom() - lir.bottom());
                } else {
                    t = qMax(t, lir.top() - wr.top());
                }
            }
            if (box->toCol(m_ncol) >= rightMost) {
                if (box->toCol(m_ncol) > rightMost) {
                    // we found an item even closer to the margin, discard.
                    rightMost = box->toCol(m_ncol);
                    if (visualHReversed) {
                        l = contents_margins.left();  // m_left_margin;
                    } else {
                        r = contents_margins.right();  // m_right_margin;
                    }
                }
                if (visualHReversed) {
                    l = qMax(l, lir.left() - wr.left());
                } else {
                    r = qMax(r, wr.right() - lir.right());
                }

            }
            if (box->toRow(m_nrow) >= bottomMost) {
                if (box->toRow(m_nrow) > bottomMost) {
                    // we found an item even closer to the margin, discard.
                    bottomMost = box->toRow(m_nrow);
                    if (m_v_reversed) {
                        t = contents_margins.top();  // m_top_margin;
                    } else {
                        b = contents_margins.bottom();  // m_bottom_margin;
                    }
                }
                if (m_v_reversed) {
                    t = qMax(t, lir.top() - wr.top());
                } else {
                    b = qMax(b, wr.bottom() - lir.bottom());
                }
            }
        }
    }

#endif
    // if (left) {
    //     *left = l;
    // }
    // if (top) {
    //     *top = t;
    // }
    // if (right) {
    //     *right = r;
    // }
    // if (bottom) {
    //     *bottom = b;
    // }

    return Margins(l, t, r, b);
}


void GridLayoutHfw::deleteAll()
{
    while (!m_things.isEmpty()) {
        delete m_things.takeFirst();
    }
    delete m_hfw_data;
}


bool GridLayoutHfw::hasHeightForWidth(int hSpacing, int vSpacing) const
{
    setupLayoutData(hSpacing, vSpacing);
    return m_has_hfw;
}


void GridLayoutHfw::recalcHFW(int w) const
{
    // Assumes that setupLayoutData() has been called, and that
    // qGeomCalc() has filled in colData with appropriate values.

    // Go through all children, using colData and heightForWidth()
    // and put the results in hfwData.

    if (!m_hfw_data) {
        m_hfw_data = new QVector<QLayoutStruct>(m_nrow);
    }
    setupHfwLayoutData();
    QVector<QLayoutStruct>& rData = *m_hfw_data;

    int h = 0;
    int mh = 0;
    for (int r = 0; r < m_nrow; r++) {
        int spacing = rData.at(r).spacing;
        h += rData.at(r).size_hint + spacing;
        mh += rData.at(r).minimum_size + spacing;
    }

    m_hfw_width = w;
    m_hfw_height = qMin(QLAYOUTSIZE_MAX, h);
    m_hfw_minheight = qMin(QLAYOUTSIZE_MAX, mh);
}


int GridLayoutHfw::heightForWidth(int w, int hSpacing, int vSpacing) const
{
    setupLayoutData(hSpacing, vSpacing);
    if (!m_has_hfw) {
        return -1;
    }
    // int left, top, right, bottom;
    // effectiveMargins(&left, &top, &right, &bottom);
    Margins effmarg = effectiveMargins();

    // int hMargins = left + right;
    // if (w - hMargins != m_hfw_width) {
    //     qGeomCalc(m_col_data, 0, m_cc, 0, w - hMargins);
    //     recalcHFW(w - hMargins);
    // }
    // return m_hfw_height + top + bottom;

    int inner_width = effmarg.removeLeftRightMarginsFrom(w);
    if (inner_width != m_hfw_width) {
        qGeomCalc(m_col_data, 0, m_ncol, 0, inner_width);
        recalcHFW(inner_width);
    }
    return effmarg.addTopBottomMarginsTo(m_hfw_height);
}


int GridLayoutHfw::minimumHeightForWidth(int w,
                                         int hSpacing, int vSpacing) const
{
    (void)heightForWidth(w, hSpacing, vSpacing);
    if (!m_has_hfw) {
        return -1;
    }
    // int top, bottom;
    // effectiveMargins(0, &top, 0, &bottom);
    // return m_hfw_minheight + top + bottom;
    return effectiveMargins().addTopBottomMarginsTo(m_hfw_minheight);
}


QSize GridLayoutHfw::findSize(int QLayoutStruct::* size,
                              int hSpacing, int vSpacing) const
{
    // "size" is a pointer to an integer non-static member of QLayoutStruct;
    // http://en.cppreference.com/w/cpp/language/pointer#Pointers_to_data_members

    setupLayoutData(hSpacing, vSpacing);

    int w = 0;
    int h = 0;

    for (int r = 0; r < m_nrow; r++) {
        h += m_row_data.at(r).*size + m_row_data.at(r).spacing;
    }
    for (int c = 0; c < m_ncol; c++) {
        w += m_col_data.at(c).*size + m_col_data.at(c).spacing;
    }

    w = qMin(QLAYOUTSIZE_MAX, w);
    h = qMin(QLAYOUTSIZE_MAX, h);

    return QSize(w, h);
}


Qt::Orientations GridLayoutHfw::expandingDirections(int hSpacing,
                                                    int vSpacing) const
{
    setupLayoutData(hSpacing, vSpacing);
    Qt::Orientations ret;

    for (int r = 0; r < m_nrow; r++) {
        if (m_row_data.at(r).expansive) {
            ret |= Qt::Vertical;
            break;
        }
    }
    for (int c = 0; c < m_ncol; c++) {
        if (m_col_data.at(c).expansive) {
            ret |= Qt::Horizontal;
            break;
        }
    }
    return ret;
}


QSize GridLayoutHfw::sizeHint(int hSpacing, int vSpacing) const
{
    return findSize(&QLayoutStruct::size_hint, hSpacing, vSpacing);
}


QSize GridLayoutHfw::maximumSize(int hSpacing, int vSpacing) const
{
    return findSize(&QLayoutStruct::maximum_size, hSpacing, vSpacing);
}


QSize GridLayoutHfw::minimumSize(int hSpacing, int vSpacing) const
{
    return findSize(&QLayoutStruct::minimum_size, hSpacing, vSpacing);
}


void GridLayoutHfw::setSize(int r, int c)
{
    if ((int)m_row_data.size() < r) {
        int newR = qMax(r, m_nrow * 2);
        m_row_data.resize(newR);
        m_r_stretches.resize(newR);
        m_r_min_heights.resize(newR);
        for (int i = m_nrow; i < newR; i++) {
            m_row_data[i].init();
            m_row_data[i].maximum_size = 0;
            m_row_data[i].pos = 0;
            m_row_data[i].size = 0;
            m_r_stretches[i] = 0;
            m_r_min_heights[i] = 0;
        }
    }
    if ((int)m_col_data.size() < c) {
        int newC = qMax(c, m_ncol * 2);
        m_col_data.resize(newC);
        m_c_stretches.resize(newC);
        m_c_min_widths.resize(newC);
        for (int i = m_ncol; i < newC; i++) {
            m_col_data[i].init();
            m_col_data[i].maximum_size = 0;
            m_col_data[i].pos = 0;
            m_col_data[i].size = 0;
            m_c_stretches[i] = 0;
            m_c_min_widths[i] = 0;
        }
    }

    if (m_hfw_data && (int)m_hfw_data->size() < r) {
        delete m_hfw_data;
        m_hfw_data = 0;
        m_hfw_width = -1;
    }
    m_nrow = r;
    m_ncol = c;
}


void GridLayoutHfw::setNextPosAfter(int row, int col)
{
    if (m_add_vertical) {
        if (col > m_next_c || (col == m_next_c && row >= m_next_r)) {
            m_next_r = row + 1;
            m_next_c = col;
            if (m_next_r >= m_nrow) {
                m_next_r = 0;
                m_next_c++;
            }
        }
    } else {
        if (row > m_next_r || (row == m_next_r && col >= m_next_c)) {
            m_next_r = row;
            m_next_c = col + 1;
            if (m_next_c >= m_ncol) {
                m_next_c = 0;
                m_next_r++;
            }
        }
    }
}


void GridLayoutHfw::add(QQGridBox* box, int row, int col)
{
    expand(row + 1, col + 1);
    box->row = box->torow = row;
    box->col = box->tocol = col;
    m_things.append(box);
    setDirty();
    setNextPosAfter(row, col);
}


void GridLayoutHfw::add(QQGridBox* box, int row1, int row2, int col1, int col2)
{
    if (Q_UNLIKELY(row2 >= 0 && row2 < row1)) {
        qWarning("QGridLayout: Multi-cell fromRow greater than toRow");
    }
    if (Q_UNLIKELY(col2 >= 0 && col2 < col1)) {
        qWarning("QGridLayout: Multi-cell fromCol greater than toCol");
    }
    if (row1 == row2 && col1 == col2) {
        add(box, row1, col1);
        return;
    }
    expand(qMax(row1, row2) + 1, qMax(col1, col2) + 1);
    box->row = row1;
    box->col = col1;

    box->torow = row2;
    box->tocol = col2;

    m_things.append(box);
    setDirty();
    if (col2 < 0) {
        col2 = m_ncol - 1;
    }

    setNextPosAfter(row2, col2);
}


void GridLayoutHfw::addData(QQGridBox* box, const QQGridLayoutSizeTriple& sizes,
                            bool r, bool c) const
{
    const QWidget* widget = box->item()->widget();

    if (box->isEmpty() && widget) {
        return;
    }

    if (c) {
        QLayoutStruct* data = &m_col_data[box->col];
        if (!m_c_stretches.at(box->col)) {
            data->stretch = qMax(data->stretch, box->hStretch());
        }
        data->size_hint = qMax(sizes.hint.width(), data->size_hint);
        data->minimum_size = qMax(sizes.minS.width(), data->minimum_size);

        qMaxExpCalc(data->maximum_size, data->expansive, data->empty,
                    sizes.maxS.width(),
                    box->expandingDirections() & Qt::Horizontal,
                    box->isEmpty());
    }
    if (r) {
        QLayoutStruct* data = &m_row_data[box->row];
        if (!m_r_stretches.at(box->row)) {
            data->stretch = qMax(data->stretch, box->vStretch());
        }
        data->size_hint = qMax(sizes.hint.height(), data->size_hint);
        data->minimum_size = qMax(sizes.minS.height(), data->minimum_size);

        qMaxExpCalc(data->maximum_size, data->expansive, data->empty,
                    sizes.maxS.height(),
                    box->expandingDirections() & Qt::Vertical,
                    box->isEmpty());
    }
}


static void initEmptyMultiBox(QVector<QQLayoutStruct> &chain, int start, int end)
{
    for (int i = start; i <= end; i++) {
        QQLayoutStruct* data = &chain[i];
        if (data->empty && data->maximum_size == 0) {  // truly empty box
            data->maximum_size = QWIDGETSIZE_MAX;
        }
        data->empty = false;
    }
}


static void distributeMultiBox(QVector<QQLayoutStruct> &chain, int start,
                               int end, int minSize, int sizeHint,
                               QVector<int>& stretchArray, int stretch)
{
    int i;
    int w = 0;
    int wh = 0;
    int max = 0;

    for (i = start; i <= end; i++) {
        QQLayoutStruct* data = &chain[i];
        w += data->minimum_size;
        wh += data->size_hint;
        max += data->maximum_size;
        if (stretchArray.at(i) == 0) {
            data->stretch = qMax(data->stretch, stretch);
        }

        if (i != end) {
            int spacing = data->spacing;
            w += spacing;
            wh += spacing;
            max += spacing;
        }
    }

    if (max < minSize) { // implies w < minSize

        // We must increase the maximum size of at least one of the
        // items. qGeomCalc() will put the extra space in between the
        // items. We must recover that extra space and put it
        // somewhere. It does not really matter where, since the user
        // can always specify stretch factors and avoid this code.

        qGeomCalc(chain, start, end - start + 1, 0, minSize);
        int pos = 0;
        for (i = start; i <= end; i++) {
            QQLayoutStruct* data = &chain[i];
            int nextPos = (i == end) ? minSize : chain.at(i + 1).pos;
            int realSize = nextPos - pos;
            if (i != end) {
                realSize -= data->spacing;
            }
            if (data->minimum_size < realSize) {
                data->minimum_size = realSize;
            }
            if (data->maximum_size < data->minimum_size) {
                data->maximum_size = data->minimum_size;
            }
            pos = nextPos;
        }
    } else if (w < minSize) {
        qGeomCalc(chain, start, end - start + 1, 0, minSize);
        for (i = start; i <= end; i++) {
            QQLayoutStruct* data = &chain[i];
            if (data->minimum_size < data->size) {
                data->minimum_size = data->size;
            }
        }
    }

    if (wh < sizeHint) {
        qGeomCalc(chain, start, end - start + 1, 0, sizeHint);
        for (i = start; i <= end; i++) {
            QQLayoutStruct* data = &chain[i];
            if (data->size_hint < data->size) {
                data->size_hint = data->size;
            }
        }
    }
}


static QQGridBox* &gridAt(QQGridBox* grid[], int r, int c, int cc,
                         Qt::Orientation orientation = Qt::Vertical)
{
    if (orientation == Qt::Horizontal) {
        qSwap(r, c);
    }
    return grid[(r * cc) + c];
}


void GridLayoutHfw::setupSpacings(QVector<QLayoutStruct> &chain,
                                  QQGridBox* grid[], int fixedSpacing,
                                  Qt::Orientation orientation) const
{
    int numRows = m_nrow;       // or columns if orientation is horizontal
    int numColumns = m_ncol;    // or rows if orientation is horizontal

    if (orientation == Qt::Horizontal) {
        qSwap(numRows, numColumns);
    }

    QStyle* style = nullptr;
    if (fixedSpacing < 0) {
        if (QWidget* parent_widget = parentWidget()) {
            style = parent_widget->style();
        }
    }

    for (int c = 0; c < numColumns; ++c) {
        QQGridBox* previousBox = 0;
        int previousRow = -1;       // previous *non-empty* row

        for (int r = 0; r < numRows; ++r) {
            if (chain.at(r).empty) {
                continue;
            }

            QQGridBox* box = gridAt(grid, r, c, m_ncol, orientation);
            if (previousRow != -1 && (!box || previousBox != box)) {
                int spacing = fixedSpacing;
                if (spacing < 0) {
                    QSizePolicy::ControlTypes controlTypes1 = QSizePolicy::DefaultType;
                    QSizePolicy::ControlTypes controlTypes2 = QSizePolicy::DefaultType;
                    if (previousBox) {
                        controlTypes1 = previousBox->item()->controlTypes();
                    }
                    if (box) {
                        controlTypes2 = box->item()->controlTypes();
                    }

                    if ((orientation == Qt::Horizontal && m_h_reversed)
                            || (orientation == Qt::Vertical && m_v_reversed)) {
                        qSwap(controlTypes1, controlTypes2);
                    }

                    if (style) {
                        spacing = style->combinedLayoutSpacing(
                                    controlTypes1, controlTypes2,
                                    orientation, 0, parentWidget());
                    }
                } else {
                    if (orientation == Qt::Vertical) {
                        QQGridBox* sibling = m_v_reversed ? previousBox : box;
                        if (sibling) {
                            QWidget* wid = sibling->item()->widget();
                            if (wid) {
                                spacing = qMax(
                                        spacing,
                                        sibling->item()->geometry().top() -
                                            wid->geometry().top() );
                            }
                        }
                    }
                }

                if (spacing > chain.at(previousRow).spacing) {
                    chain[previousRow].spacing = spacing;
                }
            }

            previousBox = box;
            previousRow = r;
        }
    }
}


//#define QT_LAYOUT_DISABLE_CACHING

void GridLayoutHfw::setupLayoutData(int hSpacing, int vSpacing) const
{
#ifndef QT_LAYOUT_DISABLE_CACHING
    if (!m_dirty) {
        return;
    }
#endif
    m_has_hfw = false;
    int i;

    for (i = 0; i < m_nrow; i++) {
        m_row_data[i].init(m_r_stretches.at(i), m_r_min_heights.at(i));
        m_row_data[i].maximum_size = m_r_stretches.at(i) ? QLAYOUTSIZE_MAX : m_r_min_heights.at(i);
    }
    for (i = 0; i < m_ncol; i++) {
        m_col_data[i].init(m_c_stretches.at(i), m_c_min_widths.at(i));
        m_col_data[i].maximum_size = m_c_stretches.at(i) ? QLAYOUTSIZE_MAX : m_c_min_widths.at(i);
    }

    int n = m_things.size();
    QVarLengthArray<QQGridLayoutSizeTriple> sizes(n);

    bool has_multi = false;

    // Grid of items. We use it to determine which items are
    // adjacent to which and compute the spacings correctly.

    QVarLengthArray<QQGridBox*> grid(m_nrow * m_ncol);
    memset(grid.data(), 0, m_nrow * m_ncol * sizeof(QQGridBox*));

    // Initialize 'sizes' and 'grid' data structures, and insert
    // non-spanning items to our row and column data structures.

    for (i = 0; i < n; ++i) {
        QQGridBox* const box = m_things.at(i);
        sizes[i].minS = box->minimumSize();
        sizes[i].hint = box->sizeHint();
        sizes[i].maxS = box->maximumSize();

        if (box->hasHeightForWidth()) {
            m_has_hfw = true;
        }

        if (box->row == box->toRow(m_nrow)) {
            addData(box, sizes[i], true, false);
        } else {
            initEmptyMultiBox(m_row_data, box->row, box->toRow(m_nrow));
            has_multi = true;
        }

        if (box->col == box->toCol(m_ncol)) {
            addData(box, sizes[i], false, true);
        } else {
            initEmptyMultiBox(m_col_data, box->col, box->toCol(m_ncol));
            has_multi = true;
        }

        for (int r = box->row; r <= box->toRow(m_nrow); ++r) {
            for (int c = box->col; c <= box->toCol(m_ncol); ++c) {
                gridAt(grid.data(), r, c, m_ncol) = box;
            }
        }
    }

    setupSpacings(m_col_data, grid.data(), hSpacing, Qt::Horizontal);
    setupSpacings(m_row_data, grid.data(), vSpacing, Qt::Vertical);

    // Insert multicell items to our row and column data structures.
    // This must be done after the non-spanning items to obtain a
    // better distribution in distributeMultiBox().

    if (has_multi) {
        for (i = 0; i < n; ++i) {
            QQGridBox* const box = m_things.at(i);

            if (box->row != box->toRow(m_nrow)) {
                distributeMultiBox(m_row_data, box->row, box->toRow(m_nrow), sizes[i].minS.height(),
                                   sizes[i].hint.height(), m_r_stretches, box->vStretch());
            }
            if (box->col != box->toCol(m_ncol)) {
                distributeMultiBox(m_col_data, box->col, box->toCol(m_ncol), sizes[i].minS.width(),
                                   sizes[i].hint.width(), m_c_stretches, box->hStretch());
            }
        }
    }

    for (i = 0; i < m_nrow; i++) {
        m_row_data[i].expansive = m_row_data.at(i).expansive || m_row_data.at(i).stretch > 0;
    }
    for (i = 0; i < m_ncol; i++) {
        m_col_data[i].expansive = m_col_data.at(i).expansive || m_col_data.at(i).stretch > 0;
    }

    // m_contents_margins = Margins::getContentsMargins(this);
    m_effective_margins = effectiveMargins();  // RNC: stores in cache

    m_dirty = false;
}


void GridLayoutHfw::addHfwData(QQGridBox* box, int width) const
{
    QVector<QLayoutStruct> &rData = *m_hfw_data;
    if (box->hasHeightForWidth()) {
        int hint = box->heightForWidth(width);
        rData[box->row].size_hint = qMax(hint, rData.at(box->row).size_hint);
        rData[box->row].minimum_size = qMax(hint, rData.at(box->row).minimum_size);
    } else {
        QSize hint = box->sizeHint();
        QSize minS = box->minimumSize();
        rData[box->row].size_hint = qMax(hint.height(), rData.at(box->row).size_hint);
        rData[box->row].minimum_size = qMax(minS.height(), rData.at(box->row).minimum_size);
    }
}


void GridLayoutHfw::setupHfwLayoutData() const
{
    // Similar to setupLayoutData(), but uses heightForWidth(colData)
    // instead of sizeHint(). Assumes that setupLayoutData() and
    // qGeomCalc(colData) has been called.

    QVector<QLayoutStruct> &rData = *m_hfw_data;
    for (int i = 0; i < m_nrow; i++) {
        rData[i] = m_row_data.at(i);
        rData[i].minimum_size = rData[i].size_hint = m_r_min_heights.at(i);
    }

    for (int pass = 0; pass < 2; ++pass) {
        for (int i = 0; i < m_things.size(); ++i) {
            QQGridBox* box = m_things.at(i);
            int r1 = box->row;
            int c1 = box->col;
            int r2 = box->toRow(m_nrow);
            int c2 = box->toCol(m_ncol);
            int w = m_col_data.at(c2).pos + m_col_data.at(c2).size - m_col_data.at(c1).pos;

            if (r1 == r2) {
                if (pass == 0)
                    addHfwData(box, w);
            } else {
                if (pass == 0) {
                    initEmptyMultiBox(rData, r1, r2);
                } else {
                    QSize hint = box->sizeHint();
                    QSize min = box->minimumSize();
                    if (box->hasHeightForWidth()) {
                        int hfwh = box->heightForWidth(w);
                        if (hfwh > hint.height())
                            hint.setHeight(hfwh);
                        if (hfwh > min.height())
                            min.setHeight(hfwh);
                    }
                    distributeMultiBox(rData, r1, r2, min.height(), hint.height(),
                                       m_r_stretches, box->vStretch());
                }
            }
        }
    }
    for (int i = 0; i < m_nrow; i++) {
        rData[i].expansive = rData.at(i).expansive || rData.at(i).stretch > 0;
    }
}


void GridLayoutHfw::distribute(QRect r, int hSpacing, int vSpacing)
{
    bool visualHReversed = m_h_reversed;
    QWidget* parent = parentWidget();
    if (parent && parent->isRightToLeft()) {
        visualHReversed = !visualHReversed;
    }

    setupLayoutData(hSpacing, vSpacing);

    // int left, top, right, bottom;
    // effectiveMargins(&left, &top, &right, &bottom);
    // r.adjust(+left, +top, -right, -bottom);
    Margins effmarg = effectiveMargins();
    effmarg.addMarginsToInPlace(r);

    qGeomCalc(m_col_data, 0, m_ncol, r.x(), r.width());
    QVector<QLayoutStruct>* rDataPtr;
    if (m_has_hfw) {
        recalcHFW(r.width());
        qGeomCalc(*m_hfw_data, 0, m_nrow, r.y(), r.height());
        rDataPtr = m_hfw_data;
    } else {
        qGeomCalc(m_row_data, 0, m_nrow, r.y(), r.height());
        rDataPtr = &m_row_data;
    }
    QVector<QLayoutStruct> &rData = *rDataPtr;
    int i;

    // RNC: rect is a member of QLayoutPrivate, which we're not using.
    // In QLayoutPrivate::doResize, we see q->setGeometry(rect);
    // Therefore I think we can recover the information with:
    QRect rect = geometry();  // RNC

    bool reverse = (
                (r.bottom() > rect.bottom()) ||
                (r.bottom() == rect.bottom() &&
                    ((r.right() > rect.right()) != visualHReversed)));
    int n = m_things.size();
    for (i = 0; i < n; ++i) {
        QQGridBox* box = m_things.at(reverse ? n-i-1 : i);
        int r2 = box->toRow(m_nrow);
        int c2 = box->toCol(m_ncol);

        int x = m_col_data.at(box->col).pos;
        int y = rData.at(box->row).pos;
        int x2p = m_col_data.at(c2).pos + m_col_data.at(c2).size; // x2+1
        int y2p = rData.at(r2).pos + rData.at(r2).size;    // y2+1
        int w = x2p - x;
        int h = y2p - y;

        if (visualHReversed) {
            x = r.left() + r.right() - x - w + 1;
        }
        if (m_v_reversed) {
            y = r.top() + r.bottom() - y - h + 1;
        }

        box->setGeometry(QRect(x, y, w, h));
    }
}


QLayoutItem* GridLayoutHfw::replaceAt(int index, QLayoutItem* newitem)
{
    if (!newitem) {
        return 0;
    }
    QLayoutItem* item = 0;
    QQGridBox* b = m_things.value(index);
    if (b) {
        item = b->takeItem();
        b->setItem(newitem);
    }
    return item;
}


// ============================================================================
// from QGridLayout
// ============================================================================

GridLayoutHfw::GridLayoutHfw(QWidget* parent)
    : QLayout(parent)
{
    m_add_vertical = false;
    setDirty();
    m_nrow = m_ncol = 0;
    m_next_r = m_next_c = 0;
    m_hfw_data = 0;
    m_h_reversed = false;
    m_v_reversed = false;
    m_horizontal_spacing = -1;
    m_vertical_spacing = -1;

    expand(1, 1);
}


// \internal (mostly)
//
// Sets the positioning mode used by addItem(). If \a orient is
// Qt::Horizontal, this layout is expanded to \a n columns, and items
// will be added columns-first. Otherwise it is expanded to \a n rows and
// items will be added rows-first.

void GridLayoutHfw::setDefaultPositioning(int n, Qt::Orientation orient)
{
    if (orient == Qt::Horizontal) {
        expand(1, n);
        m_add_vertical = false;
    } else {
        expand(n,1);
        m_add_vertical = true;
    }
}


// Destroys the grid layout. Geometry management is terminated if
// this is a top-level grid.
//
// The layout's widgets aren't destroyed.

GridLayoutHfw::~GridLayoutHfw()
{
    deleteAll();
}


void GridLayoutHfw::setHorizontalSpacing(int spacing)
{
    m_horizontal_spacing = spacing;
    invalidate();
}


int GridLayoutHfw::horizontalSpacing() const
{
    if (m_horizontal_spacing >= 0) {
        return m_horizontal_spacing;
    } else {
        return qSmartSpacing(this, QStyle::PM_LayoutHorizontalSpacing);
    }
}


void GridLayoutHfw::setVerticalSpacing(int spacing)
{
    m_vertical_spacing = spacing;
    invalidate();
}


int GridLayoutHfw::verticalSpacing() const
{
    if (m_vertical_spacing >= 0) {
        return m_vertical_spacing;
    } else {
        return qSmartSpacing(this, QStyle::PM_LayoutVerticalSpacing);
    }
}


void GridLayoutHfw::setSpacing(int spacing)
{
    m_horizontal_spacing = m_vertical_spacing = spacing;
    invalidate();
}


int GridLayoutHfw::spacing() const
{
    int hSpacing = horizontalSpacing();
    if (hSpacing == verticalSpacing()) {
        return hSpacing;
    } else {
        return -1;
    }
}


int GridLayoutHfw::rowCount() const
{
    return numRows();
}


int GridLayoutHfw::columnCount() const
{
    return numCols();
}


QSize GridLayoutHfw::sizeHint() const
{
    QSize result(sizeHint(horizontalSpacing(), verticalSpacing()));
    // int left, top, right, bottom;
    // effectiveMargins(&left, &top, &right, &bottom);
    // result += QSize(left + right, top + bottom);
    // return result;
    return effectiveMargins().addMarginsTo(result);
}


QSize GridLayoutHfw::minimumSize() const
{
    QSize result(minimumSize(horizontalSpacing(), verticalSpacing()));
    // int left, top, right, bottom;
    // effectiveMargins(&left, &top, &right, &bottom);
    // result += QSize(left + right, top + bottom);
    // return result;
    return effectiveMargins().addMarginsTo(result);
}


QSize GridLayoutHfw::maximumSize() const
{
    QSize s = maximumSize(horizontalSpacing(), verticalSpacing());
    // int left, top, right, bottom;
    // effectiveMargins(&left, &top, &right, &bottom);
    // s += QSize(left + right, top + bottom);
    s = effectiveMargins().addMarginsTo(s);
    s = s.boundedTo(QSize(QLAYOUTSIZE_MAX, QLAYOUTSIZE_MAX));
    if (alignment() & Qt::AlignHorizontal_Mask) {
        s.setWidth(QLAYOUTSIZE_MAX);
    }
    if (alignment() & Qt::AlignVertical_Mask) {
        s.setHeight(QLAYOUTSIZE_MAX);
    }
    return s;
}


bool GridLayoutHfw::hasHeightForWidth() const
{
    return hasHeightForWidth(horizontalSpacing(), verticalSpacing());
}


int GridLayoutHfw::heightForWidth(int w) const
{
    return heightForWidth(w, horizontalSpacing(), verticalSpacing());
}


int GridLayoutHfw::minimumHeightForWidth(int w) const
{
    return minimumHeightForWidth(w, horizontalSpacing(), verticalSpacing());
}


int GridLayoutHfw::count() const
{
    return m_things.count();
}


QLayoutItem* GridLayoutHfw::itemAt(int index) const
{
    if (index < m_things.count()) {
        return m_things.at(index)->item();
    } else {
        return nullptr;
    }
}


QLayoutItem* GridLayoutHfw::itemAtPosition(int row, int column) const
{
    int n = m_things.count();
    for (int i = 0; i < n; ++i) {
        QQGridBox* box = m_things.at(i);
        if (row >= box->row && row <= box->toRow(m_nrow)
                && column >= box->col && column <= box->toCol(m_ncol)) {
            return box->item();
        }
    }
    return nullptr;
}


QLayoutItem* GridLayoutHfw::takeAt(int index)
{
    if (index < m_things.count()) {
        if (QQGridBox* b = m_things.takeAt(index)) {
            QLayoutItem* item = b->takeItem();
            if (QLayout* l = item->layout()) {
                // sanity check in case the user passed something weird to QObject::setParent()
                if (l->parent() == this) {
                    l->setParent(nullptr);
                }
            }
            delete b;
            return item;
        }
    }
    return nullptr;
}


void GridLayoutHfw::getItemPosition(int index, int* row, int* column,
                                    int* rowSpan, int* columnSpan) const
{
    if (index < m_things.count()) {
        const QQGridBox* b =  m_things.at(index);
        int toRow = b->toRow(m_nrow);
        int toCol = b->toCol(m_ncol);
        *row = b->row;
        *column = b->col;
        *rowSpan = toRow - *row + 1;
        *columnSpan = toCol - *column +1;
    }
}


void GridLayoutHfw::setGeometry(const QRect &rect)
{
    if (isDirty() || rect != geometry()) {
        QRect cr = alignment() ? alignmentRect(rect) : rect;
        // RNC: note that distribute() is the main thinking function here
        distribute(cr, horizontalSpacing(), verticalSpacing());
        QLayout::setGeometry(rect);
    }
}


QRect GridLayoutHfw::cellRect(int row, int column) const
{
    if (row < 0 || row >= m_nrow || column < 0 || column >= m_ncol) {
        return QRect();
    }

    const QVector<QLayoutStruct>* rDataPtr;
    if (m_has_hfw && m_hfw_data) {
        rDataPtr = m_hfw_data;
    } else {
        rDataPtr = &m_row_data;
    }
    return QRect(m_col_data.at(column).pos, rDataPtr->at(row).pos,
                 m_col_data.at(column).size, rDataPtr->at(row).size);
}


void GridLayoutHfw::addItem(QLayoutItem* item)
{
    int r, c;
    getNextPos(r, c);
    addItem(item, r, c);
}


void GridLayoutHfw::addItem(QLayoutItem* item, int row, int column,
                            int rowSpan, int columnSpan,
                            Qt::Alignment alignment)
{
    QQGridBox* b = new QQGridBox(item);
    b->setAlignment(alignment);
    add(b,
        row, (rowSpan < 0) ? -1 : row + rowSpan - 1,
        column, (columnSpan < 0) ? -1 : column + columnSpan - 1);
    invalidate();
}


void GridLayoutHfw::addWidget(QWidget* widget, int row, int column,
                              Qt::Alignment alignment)
{
    if (!checkWidget(widget, this)) {
        return;
    }
    if (Q_UNLIKELY(row < 0 || column < 0)) {
        qWarning("QGridLayout: Cannot add %s/%s to %s/%s at row %d column %d",
                 widget->metaObject()->className(),
                 widget->objectName().toLocal8Bit().data(),
                 metaObject()->className(),
                 objectName().toLocal8Bit().data(), row, column);
        return;
    }
    addChildWidget(widget);
    QWidgetItem* b = createWidgetItem(this, widget);
    addItem(b, row, column, 1, 1, alignment);
}


void GridLayoutHfw::addWidget(QWidget* widget, int fromRow, int fromColumn,
                              int rowSpan, int columnSpan,
                              Qt::Alignment alignment)
{
    if (!checkWidget(widget, this)) {
        return;
    }
    int toRow = (rowSpan < 0) ? -1 : fromRow + rowSpan - 1;
    int toColumn = (columnSpan < 0) ? -1 : fromColumn + columnSpan - 1;
    addChildWidget(widget);
    QQGridBox* b = new QQGridBox(this, widget);
    b->setAlignment(alignment);
    add(b, fromRow, toRow, fromColumn, toColumn);
    invalidate();
}


void GridLayoutHfw::addLayout(QLayout* layout, int row, int column,
                              Qt::Alignment alignment)
{
    if (!checkLayout(layout, this)) {
        return;
    }
    if (!adoptLayout(layout)) {
        return;
    }
    QQGridBox* b = new QQGridBox(layout);
    b->setAlignment(alignment);
    add(b, row, column);
}

void GridLayoutHfw::addLayout(QLayout* layout, int row, int column,
                              int rowSpan, int columnSpan,
                              Qt::Alignment alignment)
{
    if (!checkLayout(layout, this)) {
        return;
    }
    if (!adoptLayout(layout)) {
        return;
    }
    QQGridBox* b = new QQGridBox(layout);
    b->setAlignment(alignment);
    add(b,
        row, (rowSpan < 0) ? -1 : row + rowSpan - 1,
        column, (columnSpan < 0) ? -1 : column + columnSpan - 1);
}


void GridLayoutHfw::setRowStretch(int row, int stretch)
{
    expand(row + 1, 0);
    m_r_stretches[row] = stretch;
    invalidate();
}


int GridLayoutHfw::rowStretch(int row) const
{
    return m_r_stretches.at(row);
}


int GridLayoutHfw::columnStretch(int column) const
{
    return m_c_stretches.at(column);
}


void GridLayoutHfw::setColumnStretch(int column, int stretch)
{
    expand(0, column + 1);
    m_c_stretches[column] = stretch;
    invalidate();
}


void GridLayoutHfw::expand(int rows, int cols)  // was in QGridLayoutPrivate
{
    setSize(qMax(rows, m_nrow), qMax(cols, m_ncol));
}


void GridLayoutHfw::setRowMinimumHeight(int row, int minSize)
{
    expand(row + 1, 0);
    m_r_min_heights[row] = minSize;
    invalidate();
}


int GridLayoutHfw::rowMinimumHeight(int row) const
{
    return rowSpacing(row);
}


void GridLayoutHfw::setColumnMinimumWidth(int column, int minSize)
{
    expand(0, column + 1);
    m_c_min_widths[column] = minSize;
    invalidate();
}


int GridLayoutHfw::columnMinimumWidth(int column) const
{
    return colSpacing(column);
}


Qt::Orientations GridLayoutHfw::expandingDirections() const
{
    return expandingDirections(horizontalSpacing(), verticalSpacing());
}


void GridLayoutHfw::setOriginCorner(Qt::Corner corner)
{
    setReversed(corner == Qt::BottomLeftCorner || corner == Qt::BottomRightCorner,
                corner == Qt::TopRightCorner || corner == Qt::BottomRightCorner);
}


Qt::Corner GridLayoutHfw::originCorner() const
{
    if (horReversed()) {
        return verReversed() ? Qt::BottomRightCorner : Qt::TopRightCorner;
    } else {
        return verReversed() ? Qt::BottomLeftCorner : Qt::TopLeftCorner;
    }
}


void GridLayoutHfw::invalidate()
{
    setDirty();
    QLayout::invalidate();
}


// ============================================================================
// RNC additional
// ============================================================================

inline void GridLayoutHfw::setDirty()
{
    // Was inline in header
    // http://stackoverflow.com/questions/3992980/c-inline-member-function-in-cpp-file
    // https://isocpp.org/wiki/faq/inline-functions#where-to-put-inline-keyword

#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif

    m_dirty = true;
    m_hfw_width = -1;
}


Margins GridLayoutHfw::effectiveMargins() const
{
    // RNC: cache added, because we use this quite a lot, and (at least for
    // the #ifdef Q_OS_MAC) there's a bit of thinking involved.
#ifdef GRIDLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    if (m_dirty) {
        clearCaches();
    }
#endif
    if (!m_effective_margins.isSet()) {
        Margins contents_margins = Margins::getContentsMargins(this);
        m_effective_margins = effectiveMargins(contents_margins);
    }
    return m_effective_margins;
}


#ifdef GRIDLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
void GridLayoutHfw::clearCaches()
{
    m_effective_margins.clear();
    m_dirty = false;
}
#endif
