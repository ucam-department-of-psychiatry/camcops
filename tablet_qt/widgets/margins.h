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
#include <QRect>
#include <QSize>
class QLayout;
class QWidget;


class Margins {
    // Generic margin structure, because QRect isn't quite right for this,
    // and passing around lots of separate integers is awkward.
public:
    Margins();
    Margins(int left, int top, int right, int bottom);
    void set(int left, int top, int right, int bottom);
    void clear();

    bool isSet() const { return m_set; }
    inline int left() const { return m_left; }
    inline int top() const { return m_top; }
    inline int right() const { return m_right; }
    inline int bottom() const { return m_bottom; }

    QSize totalMarginExtra() const;
    int removeLeftRightMarginsFrom(int width) const;
    int addLeftRightMarginsTo(int width) const;
    int removeTopBottomMarginsFrom(int height) const;
    int addTopBottomMarginsTo(int height) const;
    QSize addMarginsTo(const QSize& size) const;
    QSize removeMarginsFrom(const QSize& size) const;
    QRect addMarginsTo(const QRect& rect) const;
    QRect removeMarginsFrom(const QRect& rect) const;
    void addMarginsToInPlace(QRect& rect) const;
    void removeMarginsFromInPlace(QRect& rect) const;

    static Margins getContentsMargins(const QWidget* widget);
    static Margins getContentsMargins(const QLayout* layout);

private:
    bool m_set;
    int m_left;
    int m_top;
    int m_right;
    int m_bottom;
};
