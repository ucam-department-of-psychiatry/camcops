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

#define DEBUG_LAYOUT
#define UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS

#include "verticalscrollarea.h"
#include <QDebug>
#include <QEvent>
#include <QScrollBar>
#include "lib/uifunc.h"

/*

Widget layout looks like this:

VerticalScrollArea<0x0000000004dbe8f0 'questionnaire_background_patient'>, visible, pos[DOWN] (0, 183), size[DOWN] (634 x 186), heightForWidth(634)[UP] -1, minimumSize (133 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (301 x 844), minimumSizeHint[UP] (50 x 50), sizePolicy[UP] (Expanding, Maximum) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
    QWidget<0x0000000004e1a040 'qt_scrollarea_viewport'>, visible, pos[DOWN] (0, 0), size[DOWN] (624 x 186), heightForWidth(624)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (-1 x -1), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false
    ... Non-layout children of QWidget<0x0000000004e1a040 'qt_scrollarea_viewport'>:
        BaseWidget<0x0000000004f02f70 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (624 x 844), heightForWidth(624)[UP] 844, minimumSize (0 x 844), maximumSize (16777215 x 844), sizeHint[UP] (301 x 844), minimumSizeHint[UP] (123 x 844), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"]
            Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (123 x 844), sizeHint[UP] (301 x 844), maximumSize[UP] (301 x 844), hasHeightForWidth[UP] true, margin (l=7,t=7,r=7,b=7), spacing[UP] 4, heightForWidth(624)[UP] 844, minimumHeightForWidth(624)[UP] 844, spacing 4
                LabelWordWrapWide<0x0000000004d27cb0 ''>, visible, pos[DOWN] (7, 7), size[DOWN] (610 x 45), heightForWidth(610)[UP] 45, minimumSize (0 x 45), maximumSize (16777215 x 45), sizeHint[UP] (897 x 15), minimumSizeHint[UP] (90 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e81220 ''>, visible, pos[DOWN] (7, 56), size[DOWN] (76 x 15), heightForWidth(76)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (76 x 15), minimumSizeHint[UP] (46 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e97010 ''>, visible, pos[DOWN] (7, 75), size[DOWN] (67 x 15), heightForWidth(67)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (67 x 15), minimumSizeHint[UP] (32 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d7f580 ''>, visible, pos[DOWN] (7, 94), size[DOWN] (62 x 15), heightForWidth(62)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (62 x 15), minimumSizeHint[UP] (32 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d61200 ''>, visible, pos[DOWN] (7, 113), size[DOWN] (610 x 30), heightForWidth(610)[UP] 30, minimumSize (0 x 30), maximumSize (16777215 x 30), sizeHint[UP] (1499 x 15), minimumSizeHint[UP] (81 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e1b7a0 ''>, visible, pos[DOWN] (7, 147), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d4d0a0 ''>, visible, pos[DOWN] (7, 169), size[DOWN] (83 x 15), heightForWidth(83)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (83 x 15), minimumSizeHint[UP] (53 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004db3c90 ''>, visible, pos[DOWN] (7, 188), size[DOWN] (296 x 15), heightForWidth(296)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (296 x 15), minimumSizeHint[UP] (55 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d95e50 ''>, visible, pos[DOWN] (7, 207), size[DOWN] (610 x 171), heightForWidth(610)[UP] 171, minimumSize (0 x 171), maximumSize (16777215 x 171), sizeHint[UP] (5515 x 18), minimumSizeHint[UP] (109 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e97d20 ''>, visible, pos[DOWN] (7, 382), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e202c0 ''>, visible, pos[DOWN] (7, 404), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004eb8390 ''>, visible, pos[DOWN] (7, 426), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e85820 ''>, visible, pos[DOWN] (7, 448), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d286a0 ''>, visible, pos[DOWN] (7, 470), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004dabab0 ''>, visible, pos[DOWN] (7, 492), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d4f500 ''>, visible, pos[DOWN] (7, 514), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004b2b6c0 ''>, visible, pos[DOWN] (7, 536), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d41cc0 ''>, visible, pos[DOWN] (7, 558), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004f04a60 ''>, visible, pos[DOWN] (7, 580), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004de5100 ''>, visible, pos[DOWN] (7, 602), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004eb1690 ''>, visible, pos[DOWN] (7, 624), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e76e90 ''>, visible, pos[DOWN] (7, 646), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d44350 ''>, visible, pos[DOWN] (7, 668), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e8a0a0 ''>, visible, pos[DOWN] (7, 690), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e8fcd0 ''>, visible, pos[DOWN] (7, 712), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e53090 ''>, visible, pos[DOWN] (7, 734), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e7f8b0 ''>, visible, pos[DOWN] (7, 756), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004d35fd0 ''>, visible, pos[DOWN] (7, 778), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004f05c80 ''>, visible, pos[DOWN] (7, 800), size[DOWN] (58 x 18), heightForWidth(58)[UP] 18, minimumSize (0 x 18), maximumSize (16777215 x 18), sizeHint[UP] (58 x 18), minimumSizeHint[UP] (30 x 18), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                LabelWordWrapWide<0x0000000004e6fce0 ''>, visible, pos[DOWN] (7, 822), size[DOWN] (287 x 15), heightForWidth(287)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (287 x 15), minimumSizeHint[UP] (76 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
... Non-layout children of VerticalScrollArea<0x0000000004dbe8f0 'questionnaire_background_patient'>:
    QWidget<0x0000000004ddcb00 'qt_scrollarea_hcontainer'>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (100 x 30), heightForWidth(100)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (40 x 10), minimumSizeHint[UP] (40 x 10), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"]
        Layout: QBoxLayout, constraint SetMaximumSize, minimumSize[UP] (40 x 10), sizeHint[UP] (40 x 10), maximumSize[UP] (524287 x 10), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 0, heightForWidth(100)[UP] -1, minimumHeightForWidth(100)[UP] -1, spacing 0
            QScrollBar<0x0000000004dc8dc0 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (100 x 30), heightForWidth(100)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (40 x 10), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Minimum, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
    QWidget<0x0000000004d7f710 'qt_scrollarea_vcontainer'>, visible, pos[DOWN] (624, 0), size[DOWN] (10 x 186), heightForWidth(10)[UP] -1, minimumSize (0 x 0), maximumSize (10 x 524287), sizeHint[UP] (10 x 40), minimumSizeHint[UP] (10 x 40), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"]
        Layout: QBoxLayout, constraint SetMaximumSize, minimumSize[UP] (10 x 40), sizeHint[UP] (10 x 40), maximumSize[UP] (10 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 0, heightForWidth(10)[UP] -1, minimumHeightForWidth(10)[UP] -1, spacing 0
            QScrollBar<0x0000000004ec5bf0 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (10 x 186), heightForWidth(10)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (10 x 40), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Fixed, Minimum) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
QSpacerItem: sizeHint (0 x 0), sizePolicy (Minimum, Expanding) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]


So note the following:
- Here, the content is being scrolled and most of it is not visible.
- The scroll area is 634 W x 186 H.
- The 'qt_scrollarea_viewport' widget is also 186 H (but a bit narrower,
  because there's a scroll bar on the right).
- In this example there's no horizontal scroll bar (it's there but not visible).
- The vertical scroll bar is also 186 H.
- The owned widget, which is what you get from QScrollArea::widget(), is here
  a BaseWidget that is 844 high.

So far, so good. But what about here?


VerticalScrollArea<0x00000000046722e0 'questionnaire_background_patient'>, visible, pos[DOWN] (0, 71), size[DOWN] (662 x 280), heightForWidth(662)[UP] -1, minimumSize (406 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (432 x 280), minimumSizeHint[UP] (50 x 50), sizePolicy[UP] (Expanding, Maximum) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
    QWidget<0x0000000004da85d0 'qt_scrollarea_viewport'>, visible, pos[DOWN] (0, 0), size[DOWN] (662 x 280), heightForWidth(662)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (-1 x -1), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false
    ... Non-layout children of QWidget<0x0000000004da85d0 'qt_scrollarea_viewport'>:
        BaseWidget<0x0000000004e20830 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (662 x 226), heightForWidth(662)[UP] 280, minimumSize (0 x 226), maximumSize (16777215 x 226), sizeHint[UP] (432 x 280), minimumSizeHint[UP] (432 x 280), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()]
            Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (432 x 280), sizeHint[UP] (432 x 280), maximumSize[UP] (524287 x 280), hasHeightForWidth[UP] true, margin (l=7,t=7,r=7,b=7), spacing[UP] 4, heightForWidth(662)[UP] 280, minimumHeightForWidth(662)[UP] 280, [WARNING: parent->size() < this->minimumSize()], spacing 4
                BaseWidget<0x0000000004ea8e10 'quheading'>, visible, pos[DOWN] (7, 7), size[DOWN] (648 x 34), heightForWidth(648)[UP] 34, minimumSize (0 x 34), maximumSize (16777215 x 34), sizeHint[UP] (225 x 34), minimumSizeHint[UP] (104 x 34), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                    Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (104 x 34), sizeHint[UP] (225 x 34), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] true, margin (l=7,t=7,r=7,b=7), spacing[UP] 4, heightForWidth(648)[UP] 34, minimumHeightForWidth(648)[UP] 34, spacing 4
                        LabelWordWrapWide<0x00000000045a39b0 ''>, visible, pos[DOWN] (7, 7), size[DOWN] (211 x 20), heightForWidth(211)[UP] 20, minimumSize (0 x 20), maximumSize (16777215 x 20), sizeHint[UP] (211 x 20), minimumSizeHint[UP] (90 x 20), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: AlignLeft | AlignTop]
                        QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                BaseWidget<0x0000000004569e60 ''>, visible, pos[DOWN] (7, 43), size[DOWN] (648 x 32), heightForWidth(648)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (418 x 48), minimumSizeHint[UP] (418 x 48), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                    Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (418 x 48), sizeHint[UP] (418 x 48), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, [WARNING: parent->size() < this->minimumSize()], spacing 4
                        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (418 x 15), sizeHint[UP] (418 x 15), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, spacing 4
                            QLabel<0x0000000004558bc0 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (48 x 48), heightForWidth(48)[UP] -1, minimumSize (48 x 48), maximumSize (48 x 48), sizeHint[UP] (48 x 48), minimumSizeHint[UP] (48 x 48), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QLabel<0x0000000004557820 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (38 x 14), heightForWidth(38)[UP] 15, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (38 x 15), minimumSizeHint[UP] (38 x 15), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QLabel<0x0000000004ec8400 ''>, visible, pos[DOWN] (42, 0), size[DOWN] (376 x 14), heightForWidth(376)[UP] 15, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (376 x 15), minimumSizeHint[UP] (376 x 15), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (170 x 29), sizeHint[UP] (170 x 29), maximumSize[UP] (524287 x 29), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, spacing 4
                            QPushButton<0x0000000004e69790 ''>, visible, pos[DOWN] (0, 18), size[DOWN] (113 x 14), heightForWidth(113)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (113 x 29), minimumSizeHint[UP] (113 x 29), sizePolicy[UP] (Fixed, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QPushButton<0x00000000045360d0 ''>, visible, pos[DOWN] (117, 18), size[DOWN] (53 x 14), heightForWidth(53)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (53 x 29), minimumSizeHint[UP] (53 x 29), sizePolicy[UP] (Fixed, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                BaseWidget<0x00000000045623b0 'quheading'>, visible, pos[DOWN] (7, 79), size[DOWN] (648 x 34), heightForWidth(648)[UP] 34, minimumSize (0 x 34), maximumSize (16777215 x 34), sizeHint[UP] (358 x 34), minimumSizeHint[UP] (105 x 34), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                    Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (105 x 34), sizeHint[UP] (358 x 34), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] true, margin (l=7,t=7,r=7,b=7), spacing[UP] 4, heightForWidth(648)[UP] 34, minimumHeightForWidth(648)[UP] 34, spacing 4
                        LabelWordWrapWide<0x0000000004db6800 ''>, visible, pos[DOWN] (7, 7), size[DOWN] (344 x 20), heightForWidth(344)[UP] 20, minimumSize (0 x 20), maximumSize (16777215 x 20), sizeHint[UP] (344 x 20), minimumSizeHint[UP] (91 x 20), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: AlignLeft | AlignTop]
                        QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                BaseWidget<0x0000000004592bf0 ''>, visible, pos[DOWN] (7, 115), size[DOWN] (648 x 32), heightForWidth(648)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (418 x 48), minimumSizeHint[UP] (418 x 48), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                    Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (418 x 48), sizeHint[UP] (418 x 48), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, [WARNING: parent->size() < this->minimumSize()], spacing 4
                        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (418 x 15), sizeHint[UP] (418 x 15), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, spacing 4
                            QLabel<0x00000000045966f0 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (48 x 48), heightForWidth(48)[UP] -1, minimumSize (48 x 48), maximumSize (48 x 48), sizeHint[UP] (48 x 48), minimumSizeHint[UP] (48 x 48), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QLabel<0x00000000048bf120 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (38 x 14), heightForWidth(38)[UP] 15, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (38 x 15), minimumSizeHint[UP] (38 x 15), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QLabel<0x0000000004e88cb0 ''>, visible, pos[DOWN] (42, 0), size[DOWN] (376 x 14), heightForWidth(376)[UP] 15, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (376 x 15), minimumSizeHint[UP] (376 x 15), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (170 x 29), sizeHint[UP] (170 x 29), maximumSize[UP] (524287 x 29), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, spacing 4
                            QPushButton<0x0000000004e88fb0 ''>, visible, pos[DOWN] (0, 18), size[DOWN] (113 x 14), heightForWidth(113)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (113 x 29), minimumSizeHint[UP] (113 x 29), sizePolicy[UP] (Fixed, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QPushButton<0x0000000004e0c990 ''>, visible, pos[DOWN] (117, 18), size[DOWN] (53 x 14), heightForWidth(53)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (53 x 29), minimumSizeHint[UP] (53 x 29), sizePolicy[UP] (Fixed, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                BaseWidget<0x00000000045570a0 'quheading'>, visible, pos[DOWN] (7, 151), size[DOWN] (648 x 34), heightForWidth(648)[UP] 34, minimumSize (0 x 34), maximumSize (16777215 x 34), sizeHint[UP] (247 x 34), minimumSizeHint[UP] (104 x 34), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                    Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (104 x 34), sizeHint[UP] (247 x 34), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] true, margin (l=7,t=7,r=7,b=7), spacing[UP] 4, heightForWidth(648)[UP] 34, minimumHeightForWidth(648)[UP] 34, spacing 4
                        LabelWordWrapWide<0x00000000048bdb40 ''>, visible, pos[DOWN] (7, 7), size[DOWN] (233 x 20), heightForWidth(233)[UP] 20, minimumSize (0 x 20), maximumSize (16777215 x 20), sizeHint[UP] (233 x 20), minimumSizeHint[UP] (90 x 20), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: true, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: AlignLeft | AlignTop]
                        QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                BaseWidget<0x00000000045648d0 ''>, visible, pos[DOWN] (7, 187), size[DOWN] (648 x 32), heightForWidth(648)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (206 x 48), minimumSizeHint[UP] (206 x 48), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                    Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (206 x 48), sizeHint[UP] (206 x 48), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, [WARNING: parent->size() < this->minimumSize()], spacing 4
                        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (206 x 15), sizeHint[UP] (206 x 15), maximumSize[UP] (524287 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, spacing 4
                            QLabel<0x00000000045a7810 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (48 x 48), heightForWidth(48)[UP] -1, minimumSize (48 x 48), maximumSize (48 x 48), sizeHint[UP] (48 x 48), minimumSizeHint[UP] (48 x 48), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QLabel<0x0000000004d35210 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (25 x 14), heightForWidth(25)[UP] 15, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (25 x 15), minimumSizeHint[UP] (25 x 15), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QLabel<0x0000000004594660 ''>, visible, pos[DOWN] (29, 0), size[DOWN] (177 x 14), heightForWidth(177)[UP] 15, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (177 x 15), minimumSizeHint[UP] (177 x 15), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
                        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (170 x 29), sizeHint[UP] (170 x 29), maximumSize[UP] (524287 x 29), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(648)[UP] -1, minimumHeightForWidth(648)[UP] -1, spacing 4
                            QPushButton<0x0000000004b4ad10 ''>, visible, pos[DOWN] (0, 18), size[DOWN] (113 x 14), heightForWidth(113)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (113 x 29), minimumSizeHint[UP] (113 x 29), sizePolicy[UP] (Fixed, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QPushButton<0x0000000004b4b070 ''>, visible, pos[DOWN] (117, 18), size[DOWN] (53 x 14), heightForWidth(53)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (53 x 29), minimumSizeHint[UP] (53 x 29), sizePolicy[UP] (Fixed, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()] [alignment from layout: <horizontal_none> | <vertical_none>]
                            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]
... Non-layout children of VerticalScrollArea<0x00000000046722e0 'questionnaire_background_patient'>:
    QWidget<0x0000000004d8f2e0 'qt_scrollarea_hcontainer'>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (100 x 30), heightForWidth(100)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (40 x 10), minimumSizeHint[UP] (40 x 10), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"]
        Layout: QBoxLayout, constraint SetMaximumSize, minimumSize[UP] (40 x 10), sizeHint[UP] (40 x 10), maximumSize[UP] (524287 x 10), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 0, heightForWidth(100)[UP] -1, minimumHeightForWidth(100)[UP] -1, spacing 0
            QScrollBar<0x0000000004e36a50 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (100 x 30), heightForWidth(100)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (40 x 10), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Minimum, Fixed) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
    QWidget<0x0000000004552c80 'qt_scrollarea_vcontainer'>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (100 x 30), heightForWidth(100)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (10 x 40), minimumSizeHint[UP] (10 x 40), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()]
        Layout: QBoxLayout, constraint SetMaximumSize, minimumSize[UP] (10 x 40), sizeHint[UP] (10 x 40), maximumSize[UP] (10 x 524287), hasHeightForWidth[UP] false, margin (l=0,t=0,r=0,b=0), spacing[UP] 0, heightForWidth(100)[UP] -1, minimumHeightForWidth(100)[UP] -1, [WARNING: parent->size() < this->minimumSize()], spacing 0
            QScrollBar<0x0000000004dc65d0 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (100 x 30), heightForWidth(100)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (10 x 40), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Fixed, Minimum) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]

We had a large (relatively speaking) window open, sufficient to display
everything, and we opened the diagnostic code page of the demo questionnaire.
The QPushButton widgets are squashed vertically, and you can see the warnings
above. The error goes away as soon as you resize the window.

- The layout wants to be 280 high.
- The viewport has correctly sized to 280 H.
- The owned widget (the BaseWidget) is at 226 high, which is too small.

Here's the problem:


...
camcops[14453]: 2017-01-04T01:06:08.015: debug: ../tablet_qt/widgets/basewidget.cpp(49): virtual void BaseWidget::resizeEvent(QResizeEvent*) QSize(769, 226)
camcops[14453]: 2017-01-04T01:06:08.015: debug: ../tablet_qt/lib/uifunc.cpp(584): void UiFunc::resizeEventForHFWParentWidget(QWidget*) w 769 -> h 226
...
    VerticalScrollArea<0x0000000003f2dab0 'questionnaire_background_patient'>, visible, pos[DOWN] (0, 71), size[DOWN] (769 x 280), heightForWidth(769)[UP] -1, minimumSize (406 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (432 x 280), minimumSizeHint[UP] (50 x 50), sizePolicy[UP] (Expanding, Maximum) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
        QWidget<0x00000000040034e0 'qt_scrollarea_viewport'>, visible, pos[DOWN] (0, 0), size[DOWN] (769 x 280), heightForWidth(769)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (-1 x -1), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false
        ... Non-layout children of QWidget<0x00000000040034e0 'qt_scrollarea_viewport'>:
            BaseWidget<0x0000000004006c50 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (769 x 226), heightForWidth(769)[UP] 280, minimumSize (0 x 226), maximumSize (16777215 x 226), sizeHint[UP] (432 x 280), minimumSizeHint[UP] (432 x 280), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"], [WARNING: geometry() < minimumSizeHint()]
                Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (432 x 280), sizeHint[UP] (432 x 280), maximumSize[UP] (524287 x 280), hasHeightForWidth[UP] true, margin (l=7,t=7,r=7,b=7), spacing[UP] 4, heightForWidth(769)[UP] 280, minimumHeightForWidth(769)[UP] 280, [WARNING: parent->size() < this->minimumSize()], spacing 4
...

... i.e. the BaseWidget is getting heightForWidth(769) -> 226, and setting
its height accordingly, and then something is changing, because when the
layout is displayed, heightForWidth(769) -> 280 instead.

Aha! Is it because there's a layout within a layout, here?

BaseWidget<0x0000000003338220 ''>, visible, pos[DOWN] (7, 45), size[DOWN] (1186 x 81), heightForWidth(1186)[UP] 48, minimumSize (0 x 81), maximumSize (16777215 x 81), sizeHint[UP] (418 x 48), minimumSizeHint[UP] (129 x 48), sizePolicy[UP] (Expanding, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
    Layout: QVBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (129 x 48), sizeHint[UP] (418 x 48), maximumSize[UP] (524287 x 48), hasHeightForWidth[UP] true, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(1186)[UP] 48, minimumHeightForWidth(1186)[UP] 48, spacing 4
        Layout: QHBoxLayout, constraint SetDefaultConstraint, minimumSize[UP] (128 x 15), sizeHint[UP] (418 x 15), maximumSize[UP] (524287 x 15), hasHeightForWidth[UP] true, margin (l=0,t=0,r=0,b=0), spacing[UP] 4, heightForWidth(1186)[UP] 15, minimumHeightForWidth(1186)[UP] 15, spacing 4
            QLabel<0x00000000033331f0 ''>, HIDDEN, pos[DOWN] (0, 0), size[DOWN] (48 x 48), heightForWidth(48)[UP] -1, minimumSize (48 x 48), maximumSize (48 x 48), sizeHint[UP] (48 x 48), minimumSizeHint[UP] (48 x 48), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
            LabelWordWrapWide<0x0000000003334020 ''>, visible, pos[DOWN] (0, 11), size[DOWN] (38 x 15), heightForWidth(38)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (38 x 15), minimumSizeHint[UP] (38 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
            LabelWordWrapWide<0x0000000003334960 ''>, visible, pos[DOWN] (42, 11), size[DOWN] (376 x 15), heightForWidth(376)[UP] 15, minimumSize (0 x 15), maximumSize (16777215 x 15), sizeHint[UP] (376 x 15), minimumSizeHint[UP] (86 x 15), sizePolicy[UP] (Maximum, Fixed) [hasHeightForWidth=true], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
            QSpacerItem: sizeHint (0 x 0), sizePolicy (Expanding, Minimum) [hasHeightForWidth=false], constraint <no_layout> [alignment <horizontal_none> | <vertical_none>]

... mmm; no, shouldn't be (inner widgets will trigger layout invalidation, etc.)
*/

VerticalScrollArea::VerticalScrollArea(QWidget* parent) :
    QScrollArea(parent),
    m_updating_geometry(false)
{
    setWidgetResizable(true);
    // ... definitely true! If false, you get a narrow strip of widgets
    // instead of them expanding to the full width.

    // Vertical scroll bar if required:
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);

    // RNC addition:
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);
    // ... see notes at end

    // NOT THIS: enlarges the scroll area rather than scrolling...
    // setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    // setSizePolicy(UiFunc::expandingMaximumHFWPolicy());  // doesn't work

    setSizeAdjustPolicy(QAbstractScrollArea::AdjustToContents);
    // http://doc.qt.io/qt-5/qabstractscrollarea.html#SizeAdjustPolicy-enum
}


bool VerticalScrollArea::eventFilter(QObject* o, QEvent* e)
{
    // Return true for "I've dealt with it; nobody else should".
    // http://doc.qt.io/qt-5.7/eventsandfilters.html

    // This works because QScrollArea::setWidget installs an eventFilter on the
    // widget
    if (o && o == widget() && e && e->type() == QEvent::Resize) {

//#ifdef UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS
//        if (m_updating_geometry) {
//#ifdef DEBUG_LAYOUT
//            qDebug() << Q_FUNC_INFO << "- preventing infinite loop";
//#endif
//            return false;
//        }
//#endif

        QWidget* w = widget();  // The contained widget being scrolled.

        // RNC: HORIZONTAL: this plus the Expanding policy.
        setMinimumWidth(w->minimumSizeHint().width() +
                        verticalScrollBar()->width());

        // RNC:
        // qDebug().nospace()
        //         << "VerticalScrollArea::eventFilter [QEvent::Resize]"
        //         << "; minimumHeight(): " << minimumHeight()
        //         << "; minimumSizeHint(): " << minimumSizeHint()
        //         << "; size(): " << size()
        //         << "; sizeHint(): " << sizeHint()
        //         << "; widget()->size(): " << widget()->size()
        //         << "; widget()->sizeHint(): " << widget()->sizeHint();

        // If the scrollbox starts out small (because its contents are small),
        // and the contents grow, we will learn about it here -- and we need
        // to grow ourselves. When your sizeHint() changes, you should call
        // updateGeometry().

        // Except...
        // http://doc.qt.io/qt-5/qwidget.html
        // Warning: Calling setGeometry() inside resizeEvent() or moveEvent()
        // can lead to infinite recursion.
        // ... and we certainly had infinite recursion.
        // One way in which this can happen:
        // http://stackoverflow.com/questions/9503231/strange-behaviour-overriding-qwidgetresizeeventqresizeevent-event

#ifdef UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS
        m_updating_geometry = true;
        updateGeometry();
        m_updating_geometry = false;
        // even contained text scroll areas work without updateGeometry() on shrike
#endif

        // Now, a further nasty hack...
        //
        // QWidget* pw = w->parentWidget();
        // if (!pw) {
        //     qDebug() << Q_FUNC_INFO << "Bug: no parent widget";
        // }
        //
        // I think pw is now the QWidget named 'qt_scrollarea_viewport' that
        // is the "viewport" member of QAbstractScrollAreaPrivate.
        // And we want to do things to its size...
        // ... no, we don't.

        return false;  // DEFINITELY NEED THIS, NOT FALL-THROUGH TO PARENT

        // RESIDUAL PROBLEM:
        // - On some machines (e.g. wombat, Linux), when a multiline text box
        //   within a smaller-than-full-screen VerticalScroll area grows, the
        //   VerticalScrollBox stays the same size but its scroll bar adapts
        //   to the contents. Not ideal.
        // - On other machines (e.g. shrike, Linux), the VerticalScrollArea
        //   also grows, until it needs to scroll. This is optimal.
        // - Adding an updateGeometry() call fixed the problem on wombat.
        // - However, it caused a crash via infinite recursion on shrike,
        //   because (I think) the VerticalScrollBar's updateGeometry() call
        //   triggered similar geometry updating in the contained widgets (esp.
        //   LabelWordWrapWide), which triggered an update for the
        //   VerticalScrollBar, which...
        // - So, better to be cosmetically imperfect than to crash.
        // - Not sure if this can be solved consistently and perfectly.
        // - Try a guard (m_updating_geometry) so it can only do this once.
        //   Works well on Wombat!
    } else {
        return QScrollArea::eventFilter(o, e);
    }
}


// RNC addition:
// VERTICAL.
// Without this (and a vertical size policy of Maximum), it's very hard to
// get the scroll area to avoid one of the following:
// - expand too large vertically; distribute its contents vertically; thus
//   need an internal spacer at the end of its contents; thus have a duff
//   endpoint;
// - be too small vertically (e.g. if a spacer is put below it to prevent it
//   expanding too much) when there is vertical space available to use.
// So the answer is a Maximum vertical size policy, and a size hint that is
// exactly that of its contents.

QSize VerticalScrollArea::sizeHint() const
{
    // qDebug() << Q_FUNC_INFO << widget()->sizeHint();
    return widget()->sizeHint();
}


/*
void VerticalScrollArea::showEvent(QShowEvent* e)
{
    // Additional extra... trying to sort out the "initial mis-sizing" bug
    // above.
    Q_UNUSED(e);
    qDebug() << Q_FUNC_INFO;
    if (QWidget* w = widget()) {
        qDebug() << "... calling w->updateGeometry()";
        w->updateGeometry();
    }
    // Nope... called 3 times but no benefit.
}
*/
