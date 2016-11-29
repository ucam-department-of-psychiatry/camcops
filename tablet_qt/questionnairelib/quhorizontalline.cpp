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

#include "quhorizontalline.h"
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "widgets/horizontalline.h"


QuHorizontalLine::QuHorizontalLine()
{
}


QPointer<QWidget> QuHorizontalLine::makeWidget(Questionnaire* questionnaire)
{
    Q_UNUSED(questionnaire)
    HorizontalLine* horizline = new HorizontalLine(
                UiConst::QUESTIONNAIRE_HLINE_WIDTH);
    horizline->setObjectName(CssConst::QUESTIONNAIRE_HORIZONTAL_LINE);
    return QPointer<QWidget>(horizline);
}
