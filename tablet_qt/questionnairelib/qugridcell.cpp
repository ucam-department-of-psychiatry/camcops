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
