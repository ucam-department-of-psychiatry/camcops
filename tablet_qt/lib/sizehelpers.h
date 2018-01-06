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

#pragma once

#include <QSizePolicy>
#include <QStyle>
class QFrame;
class QLayout;
class QLabel;
class QPushButton;
class QStyleOptionButton;
class QStyleOptionFrame;
class QWidget;


namespace sizehelpers {

// Size policies that take a few statements to create (i.e. have height-for-width set)
// Remember: these take the widget's sizeHint() as the reference.
QSizePolicy expandingFixedHFWPolicy();
QSizePolicy expandingPreferredHFWPolicy();
QSizePolicy expandingMaximumHFWPolicy();
QSizePolicy expandingExpandingHFWPolicy();
QSizePolicy maximumFixedHFWPolicy();
QSizePolicy maximumMaximumHFWPolicy();
QSizePolicy preferredPreferredHFWPolicy();
QSizePolicy preferredFixedHFWPolicy();

// The ugly stuff you have to do for widgets that own height-for-width
// widgets if you use Qt layouts like QVBoxLayout:
void resizeEventForHFWParentWidget(QWidget* widget);

// More size helper functions, e.g. "how much extra space do I need for
// the stylesheet margins?"
QSize contentsMarginsAsSize(const QWidget* widget);
QSize contentsMarginsAsSize(const QLayout* layout);
QSize spacingAsSize(const QLayout* layout);
QSize widgetExtraSizeForCssOrLayout(const QWidget* widget,
                                    const QStyleOption* opt,
                                    const QSize& child_size,
                                    bool add_style_element,
                                    QStyle::ContentsType contents_type);
QSize pushButtonExtraSizeRequired(const QPushButton* button,
                                  const QStyleOptionButton* opt,
                                  const QSize& child_size);
QSize frameExtraSizeRequired(const QFrame* frame,
                             const QStyleOptionFrame* opt,
                             const QSize& child_size);
QSize labelExtraSizeRequired(const QLabel* label,
                             const QStyleOptionFrame* opt,
                             const QSize& child_size);
bool fixedHeightEquals(QWidget* widget, int height);

}  // namespace sizehelpers
