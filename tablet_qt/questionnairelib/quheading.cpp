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

#include "quheading.h"
#include "common/cssconst.h"
#include "common/uiconst.h"
#include "layouts/layouts.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#include "widgets/labelwordwrapwide.h"


QuHeading::QuHeading(const QString& text) :
    QuText(text)
{
    commonConstructor();
}


QuHeading::QuHeading(FieldRefPtr fieldref) :
    QuText(fieldref)
{
    commonConstructor();
}


void QuHeading::commonConstructor()
{
    m_fontsize = uiconst::FontSize::Heading;
    m_bold = false;
}


QPointer<QWidget> QuHeading::makeWidget(Questionnaire* questionnaire)
{
    // Call parent, ignore result:
    QuText::makeWidget(questionnaire);
    // Add background:

    m_container = new BaseWidget();
    HBoxLayout* layout = new HBoxLayout();
    m_container->setObjectName(cssconst::QUHEADING);
    m_container->setLayout(layout);
    layout->addWidget(m_label, 0, Qt::AlignLeft | Qt::AlignTop);
    layout->addStretch();
    return m_container;
}
