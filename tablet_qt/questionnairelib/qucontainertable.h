#pragma once
#include "quelement.h"

struct QuTableCell
{
public:
    QuTableCell(const QuElementPtr element, int row, int column,
                int row_span = 1, int column_span = 1,
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
};


class QuContainerTable : public QuElement
{
public:
    QuContainerTable();
    QuContainerTable(const QList<QuTableCell>& cells);
    QuContainerTable(std::initializer_list<QuTableCell> cells);
    QuContainerTable* addCell(const QuTableCell& cell);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuTableCell> m_cells;
};
