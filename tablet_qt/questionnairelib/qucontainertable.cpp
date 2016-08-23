#include "qucontainertable.h"
#include <QGridLayout>
#include <QWidget>
#include "questionnaire.h"


QuContainerTable::QuContainerTable()
{
}


QuContainerTable::QuContainerTable(const QList<QuTableCell>& cells) :
    m_cells(cells)
{
}


QuContainerTable::QuContainerTable(std::initializer_list<QuTableCell> cells) :
    m_cells(cells)
{
}


QuContainerTable* QuContainerTable::addCell(const QuTableCell& cells)
{
    m_cells.append(cells);
    return this;
}


QPointer<QWidget> QuContainerTable::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    QGridLayout* layout = new QGridLayout();
    widget->setLayout(layout);
    for (auto c : m_cells) {
        QuElementPtr e = c.element;
        QPointer<QWidget> w = e->widget(questionnaire);
        layout->addWidget(w, c.row, c.column,
                          c.row_span, c.column_span, c.alignment);
    }
    return widget;
}


QList<QuElementPtr> QuContainerTable::subelements() const
{
    QList<QuElementPtr> elements;
    for (auto cell : m_cells) {
        elements.append(cell.element);
    }
    return elements;
}
