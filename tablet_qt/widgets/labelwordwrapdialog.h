/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include <QLabel>


class LabelWordWrapDialog : public QLabel
{
    // Label suitable for display in dialogs which will only wrap if
    // the label's width exceeds the width of the display. This is the
    // case on iOS where dialogs are full screen. On desktop platforms
    // the dialog expands to the width of the label
    Q_OBJECT
public:
    explicit LabelWordWrapDialog(const QString& text, QWidget* parent = nullptr);

    // Default constructor.
    explicit LabelWordWrapDialog(QWidget* parent = nullptr);

public slots:
    // Set the text of the label.
    void setText(const QString& text);
};
