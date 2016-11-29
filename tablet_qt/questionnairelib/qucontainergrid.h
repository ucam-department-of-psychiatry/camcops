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
    QuContainerGrid* setFixedGrid(bool fixed_grid);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QList<QuElementPtr> subelements() const override;
private:
    void commonConstructor();
protected:
    QList<QuGridCell> m_cells;
    QMap<int, int> m_column_stretch;
    bool m_fixed_grid;
};
