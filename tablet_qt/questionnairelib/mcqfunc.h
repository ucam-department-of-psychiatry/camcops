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
#include <QList>
#include <QPointer>

class BooleanWidget;
class FieldRef;
class NameValueOptions;
class QGridLayout;
class QString;


namespace McqFunc
{
    // Assistance functions for questionnaire items.

    void addVerticalLine(QGridLayout* grid, int col, int n_rows);
    void addQuestion(QGridLayout* grid, int row, const QString& question);
    void addTitle(QGridLayout* grid, int row, const QString& title);
    void addSubtitle(QGridLayout* grid, int row, const QString& subtitle);
    void addOption(QGridLayout* grid, int row, int col, const QString& option);
    void addOptionBackground(QGridLayout* grid, int row,
                             int firstcol, int ncols);

    void setResponseWidgets(
            const NameValueOptions& options,
            const QList<QPointer<BooleanWidget>>& question_widgets,
            const FieldRef* fieldref);

    void toggleBooleanField(FieldRef* fieldref, bool allow_unset = false);

    // Alignment constants
    extern Qt::Alignment question_text_align;
    extern Qt::Alignment question_widget_align;

    extern Qt::Alignment title_text_align;
    extern Qt::Alignment title_widget_align;

    extern Qt::Alignment option_text_align;
    extern Qt::Alignment option_widget_align;

    extern Qt::Alignment response_widget_align;
}
