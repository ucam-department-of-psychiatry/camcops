#include "qugridcell.h"
#include <QDebug>


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
