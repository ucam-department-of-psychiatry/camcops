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

#include "setmenufromperinatal.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/bprs.h"
#include "tasks/core10.h"
#include "tasks/epds.h"
#include "tasks/gad7.h"
#include "tasks/honos.h"
#include "tasks/honosca.h"
#include "tasks/iesr.h"
#include "tasks/pdss.h"
#include "tasks/perinatalpoem.h"
#include "tasks/phq9.h"
#include "tasks/ybocs.h"


SetMenuFromPerinatal::SetMenuFromPerinatal(CamcopsApp& app) :
    MenuWindow(app,
               tr("FROM-Perinatal"),
               uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
    m_subtitle = "RCPsych Framework for Routine Outcome Measurement in "
                 "Perinatal Psychiatry (FROM-Perinatal)";
    m_items = {
        MAKE_CHANGE_PATIENT(app),

        MenuItem(tr("COMMON MENTAL HEALTH DISORDERS")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(Epds::EPDS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Phq9::PHQ9_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Gad7::GAD7_TABLENAME, app),

        MenuItem(tr("GENERIC MEASURES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(Honos::HONOS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Honosca::HONOSCA_TABLENAME, app),
        // ReQoL...
        // CORE-OM...
        MAKE_TASK_MENU_ITEM(Core10::CORE10_TABLENAME, app),
        // CAN-M

        // MenuItem(tr("MOTHER–INFANT MEASURES")).setLabelOnly(),
        // PBQ...
        // BMIS...
        // MORS-SF...
        // CARE-Index...
        // PIIOS...
        // NICHD...

        // MenuItem(tr("INFANT MEASURE")).setLabelOnly(),
        // ADBB...

        MenuItem(tr("PATIENT EXPERIENCE MEASURES")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(PerinatalPoem::PERINATAL_POEM_TABLENAME, app),
        // Perinatal VOICE...

        MenuItem(tr("SPECIFIC CONDITIONS")).setLabelOnly(),
        MAKE_TASK_MENU_ITEM(Bprs::BPRS_TABLENAME, app),
        // YMRS...
        // DERS...
        // DERS-SF...
        // SHAI...
        MAKE_TASK_MENU_ITEM(Ybocs::YBOCS_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Iesr::IESR_TABLENAME, app),
        MAKE_TASK_MENU_ITEM(Pdss::PDSS_TABLENAME, app),
        // MI...
    };
}
