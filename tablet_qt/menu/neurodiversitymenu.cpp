/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "neurodiversitymenu.h"

#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasks/aq.h"

NeurodiversityMenu::NeurodiversityMenu(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_NEURODIVERSITY))
{
    /*
        Icon per
        - https://commons.wikimedia.org/wiki/File:Neurodiversity_Symbol.svg
        - ... derived from rainbow infinity symbol, e.g.
          https://commons.wikimedia.org/wiki/File:Autism_spectrum_infinity_awareness_symbol.svg
        - ... reputedly credited to Singer (1998), at least according to
          https://autismoutreach.ca/wp-content/uploads/2022/09/Popard-Handout_Supporting-Neurodiversity.pdf
        - ... that being:
          Singer, J. (1998). Odd people in: The birth of community amongst
          people on the autistic spectrum: A personal exploration of a new
          social movement based on neurological diversity.
          Unpublished thesis: Faculty of Humanities and Social Science,
          University of Technology, Sydney.
    */
}

QString NeurodiversityMenu::title() const
{
    return tr("Neurodiversity");
}

void NeurodiversityMenu::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(Aq::AQ_TABLENAME, m_app),
    };
}
