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

#include "qugridcell.h"
#include <QDebug>


QuGridCell::QuGridCell(const QuElementPtr element,
                       int row,
                       int column,
                       int row_span,
                       int column_span,
                       Qt::Alignment alignment) :
    element(element),
    row(row),
    column(column),
    row_span(row_span),
    column_span(column_span),
    alignment(alignment)
{
}


QuGridCell::QuGridCell(QuElement* element,  // takes ownership...
                       int row,
                       int column,
                       int row_span,
                       int column_span,
                       Qt::Alignment alignment) :
    element(QuElementPtr(element)),  // ... here
    row(row),
    column(column),
    row_span(row_span),
    column_span(column_span),
    alignment(alignment)
{
}


QDebug operator<<(QDebug debug, const QuGridCell& cell)
{
    debug.nospace()
        << "QuGridCell(element=" << cell.element
        << ", row=" << cell.row
        << ", column=" << cell.column
        << ", row_span=" << cell.row_span
        << ", column_span=" << cell.column_span
        << ", alignment=" << cell.alignment << ")";
    return debug;
}
