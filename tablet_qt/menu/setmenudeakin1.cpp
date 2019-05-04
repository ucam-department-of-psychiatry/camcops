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

#include "setmenudeakin1.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "dialogs/soundtestdialog.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/ace3.h"
#include "tasks/bdi.h"
#include "tasks/bmi.h"
#include "tasks/caps.h"
#include "tasks/cardinalexpdetthreshold.h"
#include "tasks/cardinalexpectationdetection.h"
#include "tasks/cecaq3.h"
#include "tasks/cgisch.h"
#include "tasks/deakin1healthreview.h"
#include "tasks/diagnosisicd9cm.h"
#include "tasks/gaf.h"
#include "tasks/nart.h"
#include "tasks/panss.h"
#include "taskxtra/cardinalexpdetcommon.h"


SetMenuDeakin1::SetMenuDeakin1(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
}


QString SetMenuDeakin1::title() const
{
    return "Deakin JB — 1";
}


QString SetMenuDeakin1::subtitle() const
{
    return tr("Deakin JB, University of Cambridge, UK — "
              "antibody-mediated psychosis");
}


void SetMenuDeakin1::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(Ace3::ACE3_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Bdi::BDI_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Bmi::BMI_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Caps::CAPS_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(CecaQ3::CECAQ3_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(CgiSch::CGISCH_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(DiagnosisIcd9CM::DIAGNOSIS_ICD9CM_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Deakin1HealthReview::DEAKIN1HEALTHREVIEW_TABLENAME, m_app),
        MenuItem(
            cardinalexpdetcommon::ExpDetTextConst::soundtestTitle(),
            std::bind(&SetMenuDeakin1::soundTestCardinalExpDet, this),
            "",
            cardinalexpdetcommon::ExpDetTextConst::soundtestSubtitle()
        ),
        MAKE_TASK_MENU_ITEM(CardinalExpDetThreshold::CARDINALEXPDETTHRESHOLD_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(CardinalExpectationDetection::CARDINALEXPDET_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Gaf::GAF_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Nart::NART_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Panss::PANSS_TABLENAME, m_app),
    };
}


void SetMenuDeakin1::soundTestCardinalExpDet()
{
    SoundTestDialog dlg(cardinalexpdetcommon::urlFromStem(
                            cardinalexpdetcommon::AUDITORY_BACKGROUND),
                        cardinalexpdetcommon::SOUNDTEST_VOLUME, this);
    dlg.exec();
}
