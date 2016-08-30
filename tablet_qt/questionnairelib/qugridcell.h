#pragma once
#include "quelement.h"


struct QuGridCell
{
public:
    QuGridCell(const QuElementPtr element,
               int row,  // y position, starting from 0, going down
               int column,  // x position, starting from 0, going right
               int row_span = 1,   // height
               int column_span = 1,  // width
               Qt::Alignment alignment = 0) :
        element(element),
        row(row),
        column(column),
        row_span(row_span),
        column_span(column_span),
        alignment(alignment)
    {}
public:
    QuElementPtr element;
    int row;
    int column;
    int row_span;
    int column_span;
    Qt::Alignment alignment;
    // http://doc.qt.io/qt-5.7/qgridlayout.html
public:
    friend QDebug operator<<(QDebug debug, const QuGridCell& plan);
};
