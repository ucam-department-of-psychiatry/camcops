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

#include <QPushButton>
#include "common/gui_defines.h"
#include "layouts/layouts.h"
class LabelWordWrapWide;


class ClickableLabelWordWrapWide : public QPushButton
{
    Q_OBJECT
public:
    ClickableLabelWordWrapWide(const QString& text, bool stretch = false,
                               QWidget* parent = nullptr);
    ClickableLabelWordWrapWide(bool stretch = false,
                               QWidget* parent = nullptr);

    virtual void setTextFormat(Qt::TextFormat format);
    virtual void setWordWrap(bool on);
    virtual void setAlignment(Qt::Alignment alignment);
    virtual void setOpenExternalLinks(bool open);
    virtual void setText(const QString& text);

    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
#ifdef GUI_USE_RESIZE_FOR_HEIGHT
    virtual void resizeEvent(QResizeEvent* event) override;
#endif
protected:
    void commonConstructor(bool stretch);
    QSize translateSize(const QSize& size) const;

protected:
    LabelWordWrapWide* m_label;
    VBoxLayout* m_layout;
};
