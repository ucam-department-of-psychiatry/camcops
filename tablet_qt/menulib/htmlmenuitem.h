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
#include <QString>


struct HtmlMenuItem
{
    // Exists only to improve polymorphic constructor of MenuItem
public:
    HtmlMenuItem(const QString& title = "", const QString& filename = "",
                 const QString& icon = "", bool fullscreen = false) :
        title(title),
        filename(filename),
        icon(icon),
        fullscreen(fullscreen)
    {}
public:
    // These are the title/icon shown on the HTML page, not the menu
    QString title;
    QString filename;
    QString icon;
    bool fullscreen;
};
