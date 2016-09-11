// #define DEBUG_GRID_CREATION
#include "qucontainergrid.h"
#include <QDebug>
#include <QGridLayout>
#include <QWidget>
#include "questionnaire.h"


QuContainerGrid::QuContainerGrid()
{
}


QuContainerGrid::QuContainerGrid(const QList<QuGridCell>& cells) :
    m_cells(cells)
{
}


QuContainerGrid::QuContainerGrid(std::initializer_list<QuGridCell> cells) :
    m_cells(cells)
{
}


QuContainerGrid* QuContainerGrid::addCell(const QuGridCell& cells)
{
    m_cells.append(cells);
    return this;
}


QuContainerGrid* QuContainerGrid::setColumnStretch(int column, int stretch)
{
    m_column_stretch[column] = stretch;
    return this;
}


QPointer<QWidget> QuContainerGrid::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
#ifdef DEBUG_GRID_CREATION
    widget->setObjectName("debug_green");
#endif
    QGridLayout* grid = new QGridLayout();
    widget->setLayout(grid);
    for (auto c : m_cells) {
        QuElementPtr e = c.element;
        QPointer<QWidget> w = e->widget(questionnaire);
#ifdef DEBUG_GRID_CREATION
        w->setObjectName("debug_red");
        qDebug() << Q_FUNC_INFO << "-" << c;
#endif
        grid->addWidget(w, c.row, c.column,
                        c.row_span, c.column_span, c.alignment);
    }
    QMapIterator<int, int> it(m_column_stretch);
    while (it.hasNext()) {
        it.next();
        int column = it.key();
        int stretch = it.value();
#ifdef DEBUG_GRID_CREATION
        qDebug().nospace() << "... setColumnStretch(" << column
                           << "," << stretch << ")";
#endif
        grid->setColumnStretch(column, stretch);
    }
    return widget;
}


QList<QuElementPtr> QuContainerGrid::subelements() const
{
    QList<QuElementPtr> elements;
    for (auto cell : m_cells) {
        elements.append(cell.element);
    }
    return elements;
}
