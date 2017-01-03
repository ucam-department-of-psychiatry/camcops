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

#pragma once

// #define GUI_USE_HFW_LAYOUT
// ... for many things

#define GUI_USE_RESIZE_FOR_HEIGHT
// ... for BaseWidget, LabelWordWrapWide, AspectRatioPixmapLabel...

#if defined(GUI_USE_HFW_LAYOUT) == defined(GUI_USE_RESIZE_FOR_HEIGHT)
#error Define GUI_USE_HFW_LAYOUT xor GUI_USE_RESIZE_FOR_HEIGHT
#endif
