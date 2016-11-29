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

#include "quheading.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/labelwordwrapwide.h"


QuHeading::QuHeading(const QString& text) :
    QuText(text)
{
    m_fontsize = UiConst::FontSize::Heading;
    m_bold = true;
}


QuHeading::QuHeading(FieldRefPtr fieldref) :
    QuText(fieldref)
{
    m_fontsize = UiConst::FontSize::Heading;
    m_bold = true;
}
