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

#define USE_HFW_LAYOUT  // good

#include "quheading.h"
#include <QHBoxLayout>
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#include "widgets/labelwordwrapwide.h"
#ifdef USE_HFW_LAYOUT
#include "widgets/hboxlayouthfw.h"
#endif


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
    m_fontsize = UiConst::FontSize::Heading;
    m_bold = false;
}


QPointer<QWidget> QuHeading::makeWidget(Questionnaire* questionnaire)
{
    // Call parent, ignore result:
    QuText::makeWidget(questionnaire);
    // Add background:

    m_container = new BaseWidget();

#ifdef USE_HFW_LAYOUT
    HBoxLayoutHfw* layout = new HBoxLayoutHfw();
#else
    QHBoxLayout* layout = new QHBoxLayout();
#endif

    m_container->setObjectName(CssConst::QUHEADING);
    m_container->setLayout(layout);
    layout->addWidget(m_label, 0, Qt::AlignLeft | Qt::AlignTop);
    layout->addStretch();
    return m_container;
}
