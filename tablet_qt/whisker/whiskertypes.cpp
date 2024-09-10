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

#include "whiskertypes.h"

#include "whisker/whiskerconnectionstate.h"
#include "whisker/whiskerinboundmessage.h"
#include "whisker/whiskeroutboundcommand.h"

namespace whiskertypes {
void registerTypesForQVariant()
{
    // Types that need to be registered with qRegisterMetaType() but are
    // not stored in QVariants, so don't need externally visible type
    // names:
    qRegisterMetaType<WhiskerConnectionState>("WhiskerConnectionState");
    qRegisterMetaType<WhiskerInboundMessage>("WhiskerInboundMessage");
    qRegisterMetaType<WhiskerOutboundCommand>("WhiskerOutboundCommand");
}
}
