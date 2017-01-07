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

#include "questionnairefunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qutext.h"


QuElement* questionnairefunc::defaultGridRawPointer(
        const QList<GridRowDefinition>& deflist,
        int left_column_span,
        int right_column_span,
        Qt::Alignment label_alignment,
        Qt::Alignment left_column_alignment,
        Qt::Alignment right_column_alignment)
{
    QList<QuGridCell> cells;
    int row = 0;
    const int left_col = 0;
    const int right_col = 1;
    const int row_span = 1;
    const int col_span = 1;
    for (GridRowDefinition def : deflist) {
        QString text = def.first;
        QuElementPtr label_element = QuElementPtr(
                    (new QuText(text))->setAlignment(label_alignment));
        QuGridCell label_cell(label_element, row, left_col,
                              row_span, col_span,
                              left_column_alignment);
        QuElementPtr main_element = def.second;
        QuGridCell main_cell(main_element, row, right_col,
                             row_span, col_span,
                             right_column_alignment);
        cells.append(label_cell);
        cells.append(main_cell);
        ++row;
    }
    QuGridContainer* grid = new QuGridContainer(cells);
    grid->setColumnStretch(left_col, left_column_span);
    grid->setColumnStretch(right_col, right_column_span);
    return grid;
}


QuElementPtr questionnairefunc::defaultGrid(
        const QList<GridRowDefinition>& deflist,
        int left_column_span,
        int right_column_span,
        Qt::Alignment label_alignment,
        Qt::Alignment left_column_alignment,
        Qt::Alignment right_column_alignment)
{
    return QuElementPtr(defaultGridRawPointer(
                            deflist, left_column_span, right_column_span,
                            label_alignment,
                            left_column_alignment, right_column_alignment));
}


QuElementPtr questionnairefunc::defaultGrid(
        std::initializer_list<GridRowDefinition> defs,
        int left_column_span,
        int right_column_span,
        Qt::Alignment label_alignment,
        Qt::Alignment left_column_alignment,
        Qt::Alignment right_column_alignment)
{
    QList<GridRowDefinition> deflist(defs);
    return defaultGrid(deflist, left_column_span, right_column_span,
                       label_alignment,
                       left_column_alignment, right_column_alignment);
}


QuElement* questionnairefunc::defaultGridRawPointer(
        std::initializer_list<GridRowDefinitionRawPtr> defs,
        int left_column_span,
        int right_column_span,
        Qt::Alignment label_alignment,
        Qt::Alignment left_column_alignment,
        Qt::Alignment right_column_alignment)
{
    QList<GridRowDefinition> deflist;
    for (auto rawptrdef : defs) {
        // rawptrdef will be of type GridRowDefinitionRawPtr
        //
        GridRowDefinition sharedptrdef(rawptrdef.first,
                                       QuElementPtr(rawptrdef.second));
        deflist.append(sharedptrdef);
    }
    return defaultGridRawPointer(
                deflist, left_column_span, right_column_span,
                label_alignment,
                left_column_alignment, right_column_alignment);
}
