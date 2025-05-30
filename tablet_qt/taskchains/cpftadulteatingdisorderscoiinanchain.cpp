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

#include "cpftadulteatingdisorderscoiinanchain.h"

#include "tasks/chit.h"
#include "tasks/ided3d.h"
#include "tasks/isaaq10.h"
#include "tasks/isaaqed.h"
#include "tasks/kirby.h"
#include "tasks/suppsp.h"

CpftAdultEatingDisordersCoiinAnChain::CpftAdultEatingDisordersCoiinAnChain(
    CamcopsApp& app
) :
    TaskChain(
        app,
        {
            Chit::CHIT_TABLENAME,
            Suppsp::SUPPSP_TABLENAME,
            Isaaq10::ISAAQ10_TABLENAME,
            IsaaqEd::ISAAQED_TABLENAME,
            Kirby::KIRBY_TABLENAME,
            IDED3D::IDED3D_TABLENAME,
            // Sequence as per JES to MB, 2023-02-27.
        },
        TaskChain::CreationMethod::OnDemandOrAbort,
        // ... as per JES 2023-03-14; also the default.
        tr("COIIN-AN")
    )
{
}
