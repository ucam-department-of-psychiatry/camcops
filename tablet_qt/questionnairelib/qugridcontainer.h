/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
#include "questionnairelib/quelement.h"
#include "questionnairelib/qugridcell.h"


class QuGridContainer : public QuElement
{
    // Allows the arrangements of other elements into a grid.

    Q_OBJECT
public:
    // Default constructor, so it can live in a QVector
    QuGridContainer();

    // Initialize with the high-precision QuGridCell:
    QuGridContainer(const QVector<QuGridCell>& cells);
    QuGridContainer(std::initializer_list<QuGridCell> cells);

    // Initialize with a simple "n columns" format. Elements will be assigned
    // to each row, cycling around to the next row once n_columns has been
    // reached.
    QuGridContainer(int n_columns, const QVector<QuElementPtr>& elements);
    QuGridContainer(int n_columns, const QVector<QuElement*>& elements);
    QuGridContainer(int n_columns, std::initializer_list<QuElementPtr> elements);
    QuGridContainer(int n_columns, std::initializer_list<QuElement*> elements);  // takes ownership

    // Add an individual cell.
    QuGridContainer* addCell(const QuGridCell& cell);

    // Force the stretch factor of a column, which affects its width.
    // See .cpp file for discussion.
    QuGridContainer* setColumnStretch(int column, int stretch);

    // Set "fixed grid" mode. In "fixed grid" mode, columns have equal width,
    // unless specified; widgets are told to expand right as required.
    QuGridContainer* setFixedGrid(bool fixed_grid);

    // Should the whole grid expand to the far right of the screen?
    QuGridContainer* setExpandHorizontally(bool expand);

protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual QVector<QuElementPtr> subelements() const override;

private:
    void commonConstructor();

protected:
    QVector<QuGridCell> m_cells;  // our cells
    QMap<int, int> m_column_stretch;  // maps column_index to relative_width
    bool m_expand;  // expand horizontally?
    bool m_fixed_grid;  // columns of equal width (unless specified), as above?
};
