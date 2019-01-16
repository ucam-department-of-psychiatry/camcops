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

// Size policies that take a few statements to create (i.e. that have
// height-for-width set!).
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
// widgets if you use Qt layouts like QVBoxLayout.
// This is NOT used within our better HFW framework; see gui_defines.h.
void resizeEventForHFWParentWidget(QWidget* widget);

// More size helper functions, e.g. "how much extra space do I need for
// the stylesheet margins?"
QSize contentsMarginsAsSize(const QWidget* widget);
QSize contentsMarginsAsSize(const QLayout* layout);

// Returns a layout's spacing() as a QSize(2 * spacing(), 2 * spacing()) --
// that is, when you add all the spacing up.
QSize spacingAsSize(const QLayout* layout);

// How much extra space does a QWidget need for its layout margins or its
// stylesheet?
QSize widgetExtraSizeForCssOrLayout(const QWidget* widget,
                                    const QStyleOption* opt,
                                    const QSize& child_size,
                                    bool add_style_element,
                                    QStyle::ContentsType contents_type);

// widgetExtraSizeForCssOrLayout() for QPushButton.
QSize pushButtonExtraSizeRequired(const QPushButton* button,
                                  const QStyleOptionButton* opt,
                                  const QSize& child_size);

// widgetExtraSizeForCssOrLayout() for QFrame.
QSize frameExtraSizeRequired(const QFrame* frame,
                             const QStyleOptionFrame* opt,
                             const QSize& child_size);

// widgetExtraSizeForCssOrLayout() for QLabel.
QSize labelExtraSizeRequired(const QLabel* label,
                             const QStyleOptionFrame* opt,
                             const QSize& child_size);

// Does the widget have a fixed height that is equal to "height"?
bool fixedHeightEquals(QWidget* widget, int height);

}  // namespace sizehelpers
