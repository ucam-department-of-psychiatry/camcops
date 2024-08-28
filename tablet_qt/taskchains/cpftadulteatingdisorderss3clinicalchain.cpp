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

#include "cpftadulteatingdisorderss3clinicalchain.h"

#include "tasks/cia.h"
#include "tasks/edeq.h"
#include "tasks/eq5d5l.h"
#include "tasks/gad7.h"
#include "tasks/phq9.h"

CpftAdultEatingDisordersS3ClinicalChain::
    CpftAdultEatingDisordersS3ClinicalChain(CamcopsApp& app) :
    TaskChain(
        app,
        {
            Edeq::EDEQ_TABLENAME,
            Cia::CIA_TABLENAME,
            Eq5d5l::EQ5D5L_TABLENAME,
            Gad7::GAD7_TABLENAME,
            Phq9::PHQ9_TABLENAME,
            // Sequence as per JES to MB, 2023-02-27 and 2023-03-17.
        },
        TaskChain::CreationMethod::OnDemandOrAbort,
        // ... as per JES 2023-03-14; also the default.
        tr("S3 Clinical")
    )
{
}
