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

#include "khandakermojochain.h"
#include "tasks/khandakermojomedical.h"
#include "tasks/khandakermojomedicationtherapy.h"
#include "tasks/khandakermojosociodemographics.h"


KhandakerMojoChain::KhandakerMojoChain(CamcopsApp& app) :
    TaskChain(app, {
        KhandakerMojoSociodemographics::KHANDAKER2MOJOSOCIODEMOGRAPHICS_TABLENAME,
        KhandakerMojoMedical::KHANDAKERMOJOMEDICAL_TABLENAME,
        KhandakerMojoMedicationTherapy::KHANDAKERMOJOMEDICATIONTHERAPY_TABLENAME,
        // *** Actual sequence to be confirmed.
    }, TaskChain::CreationMethod::OnDemandOrAbort)
{
}
