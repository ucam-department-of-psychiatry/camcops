#pragma once
#include <QMap>
#include "quelement.h"
#include "qugridcell.h"


class QuContainerGrid : public QuElement
{
    // Allows the arrangements of other elements into a grid.

    Q_OBJECT
public:
    QuContainerGrid();
    QuContainerGrid(const QList<QuGridCell>& cells);
    QuContainerGrid(std::initializer_list<QuGridCell> cells);
    QuContainerGrid* addCell(const QuGridCell& cell);
    QuContainerGrid* setColumnStretch(int column, int stretch);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
protected:
    QList<QuGridCell> m_cells;
    QMap<int, int> m_column_stretch;
};
