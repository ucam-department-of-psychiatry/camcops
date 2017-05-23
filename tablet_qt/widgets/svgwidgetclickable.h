/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
#include <QSvgWidget>


class SvgWidgetClickable : public QSvgWidget
{
    // We have a choice of deriving from QGraphicsSvgItem or QSvgWidget.
    // The main differences are:
    // - QSvgWidget can be used in a more general context
    // - QSvgWidget owns its QSvgRenderer, but you can access it, while if you
    //   use a QGraphicsSvgItem, you have to manage the lifetime of the
    //   renderer separately, which is something of a pain.
    // For clicks:
    // - https://stackoverflow.com/questions/36372615/how-can-i-capture-click-events-signals-of-a-qgraphicssvgitem
    Q_OBJECT
public:
    SvgWidgetClickable(QWidget* parentitem = nullptr);
    SvgWidgetClickable(const QString& filename,
                       QWidget* parentitem = nullptr);
protected:
    void commonConstructor();
    virtual void mousePressEvent(QMouseEvent* event) override;
signals:
    void clicked();
};
