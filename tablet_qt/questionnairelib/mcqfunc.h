/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
#include "layouts/layouts.h"

class BooleanWidget;
class FieldRef;
class NameValueOptions;
class QString;


namespace mcqfunc {

// Assistance functions for questionnaire items.

void addVerticalLine(GridLayout* grid, int col, int n_rows);
void addQuestion(GridLayout* grid, int row, const QString& question);
void addTitle(GridLayout* grid, int row, const QString& title);
void addSubtitle(GridLayout* grid, int row, const QString& subtitle);
void addStem(GridLayout* grid, int row, int firstcol, int colspan,
             const QString& stem);
void addOption(GridLayout* grid, int row, int col, const QString& option);
void addOptionBackground(GridLayout* grid, int row,
                         int firstcol, int ncols, int nrows = 1);
void addStripeBackground(GridLayout* grid, int row,
                         int firstcol, int ncols, int nrows = 1);

void setResponseWidgets(
        const NameValueOptions& options,
        const QVector<QPointer<BooleanWidget>>& question_widgets,
        const FieldRef* fieldref);

void toggleBooleanField(FieldRef* fieldref, bool allow_unset = false);

// Alignment constants
extern const Qt::Alignment question_text_align;
extern const Qt::Alignment question_widget_align;

extern const Qt::Alignment title_text_align;
extern const Qt::Alignment title_widget_align;

extern const Qt::Alignment option_text_align;
extern const Qt::Alignment option_widget_align;

extern const Qt::Alignment response_widget_align;

extern const Qt::Alignment stem_text_align;
extern const Qt::Alignment stem_widget_align;

}  // namespace mcqfunc
