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

#include "researchmenu.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "dialogs/soundtestdialog.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/cardinalexpdetthreshold.h"
#include "tasks/cardinalexpectationdetection.h"
#include "tasks/diagnosisicd9cm.h"
#include "tasks/ided3d.h"
#include "tasks/qolbasic.h"
#include "tasks/qolsg.h"
#include "taskxtra/cardinalexpdetcommon.h"


ResearchMenu::ResearchMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Research tasks (experimental)"),
               uifunc::iconFilename(uiconst::ICON_RESEARCH))
{
    m_items = {
        MAKE_CHANGE_PATIENT(app),
        MAKE_TASK_MENU_ITEM(QolBasic::QOLBASIC_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(QolSG::QOLSG_TABLENAME, app),
        MenuItem(
            cardinalexpdetcommon::SOUNDTEST_TITLE,
            std::bind(&ResearchMenu::soundTestCardinalExpDet, this),
            "",
            cardinalexpdetcommon::SOUNDTEST_SUBTITLE
        ),
        MAKE_TASK_MENU_ITEM(CardinalExpDetThreshold::CARDINALEXPDETTHRESHOLD_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(CardinalExpectationDetection::CARDINALEXPDET_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(DiagnosisIcd9CM::DIAGNOSIS_ICD9CM_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(IDED3D::IDED3D_TABLENAME, app),
        MenuItem("*** chain: qolbasic -> phq9 -> phq15"),
    };
}


void ResearchMenu::soundTestCardinalExpDet()
{
    SoundTestDialog dlg(cardinalexpdetcommon::urlFromStem(
                            cardinalexpdetcommon::AUDITORY_BACKGROUND),
                        cardinalexpdetcommon::SOUNDTEST_VOLUME, this);
    dlg.exec();
}
