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

#include <QAbstractButton>
#include "layouts/layouts.h"
class ClickableLabelWordWrapWide;
class ImageButton;


class BooleanWidget : public QAbstractButton
{
    // - Encapsulates a widget that can take a variety of appearances, but
    //   embodies some or all of the states true, false, null (not required),
    //   null (required).
    // - Can display as an image or a text button. Because those things don't
    //   play nicely together, owns widgets rather than inheriting.
    // - Main signal is: clicked
    // - RESIST the temptation to have this widget do value logic.
    //   That's the job of its owner.

    // - DON'T try multiple inheritance (inheriting from a custom ABC and
    //   a QObject). It just messes up ("can't convert to QObject", when
    //   access is from ABC pointer; etc.).

    Q_OBJECT
public:
    enum class State {
        Disabled,
        Null,
        NullRequired,
        False,
        True,
    };
    enum class Appearance {
        CheckBlack,
        CheckRed,
        Radio,
        Text,
    };
public:
    BooleanWidget(QWidget* parent = nullptr);
    // Used at construction time:
    virtual void setReadOnly(bool read_only = false);
    void setSize(bool big = false);
    void setBold(bool bold);
    void setAppearance(BooleanWidget::Appearance appearance);
    // Used live:
    void setState(BooleanWidget::State state);
    void setValue(const QVariant& value, bool mandatory,
                  bool disabled = false);
    void setText(const QString& text);
protected:
    virtual void paintEvent(QPaintEvent* e) override;
    void updateWidget(bool full_refresh);
protected:
    bool m_read_only;
    bool m_big;
    bool m_bold;
    Appearance m_appearance;
    bool m_as_image;
    State m_state;
    ImageButton* m_imagebutton;
    ClickableLabelWordWrapWide* m_textbutton;
    VBoxLayout* m_layout;
};
