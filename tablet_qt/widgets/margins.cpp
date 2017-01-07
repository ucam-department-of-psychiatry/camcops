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

#include "margins.h"
#include <QWidget>
#include <QLayout>


Margins::Margins()
{
    clear();
}


Margins::Margins(int left, int top, int right, int bottom)
{
    set(left, top, right, bottom);
}


void Margins::clear()
{
    m_left = 0;
    m_top = 0;
    m_right = 0;
    m_bottom = 0;
    m_set = false;
}


void Margins::set(int left, int top, int right, int bottom)
{
    m_left = left;
    m_top = top;
    m_right = right;
    m_bottom = bottom;
    m_set = true;
}


Margins Margins::getContentsMargins(const QWidget* widget)
{
    Margins m;
    if (widget) {
        int left, top, right, bottom;
        widget->getContentsMargins(&left, &top, &right, &bottom);
        m.set(left, top, right, bottom);
    }
    return m;
}


Margins Margins::getContentsMargins(const QLayout* layout)
{
    Margins m;
    if (layout) {
        int left, top, right, bottom;
        layout->getContentsMargins(&left, &top, &right, &bottom);
        m.set(left, top, right, bottom);
    }
    return m;
}


QSize Margins::totalMarginExtra() const
{
    return QSize(m_left + m_right, m_top + m_bottom);
}


int Margins::removeLeftRightMarginsFrom(int width) const
{
    return width - (m_left + m_right);
}


int Margins::addLeftRightMarginsTo(int width) const
{
    return width + (m_left + m_right);
}


int Margins::removeTopBottomMarginsFrom(int height) const
{
    return height - (m_top + m_bottom);
}


int Margins::addTopBottomMarginsTo(int height) const
{
    return height + (m_top + m_bottom);
}


QSize Margins::addMarginsTo(const QSize& size) const
{
    return QSize(size.width() + m_left + m_right,
                 size.height() + m_top + m_bottom);
}


QSize Margins::removeMarginsFrom(const QSize& size) const
{
    return QSize(size.width() - (m_left + m_right),
                 size.height() - (m_top + m_bottom));
}


QRect Margins::addMarginsTo(const QRect& rect) const
{
    return rect.adjusted(-m_left, -m_top, +m_right, +m_bottom);
}


QRect Margins::removeMarginsFrom(const QRect& rect) const
{
    return rect.adjusted(+m_left, +m_top, -m_right, -m_bottom);
}


void Margins::addMarginsToInPlace(QRect& rect) const
{
    rect.adjust(-m_left, -m_top, +m_right, +m_bottom);
}


void Margins::removeMarginsFromInPlace(QRect& rect) const
{
    rect.adjust(+m_left, +m_top, -m_right, -m_bottom);
}
