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
#include <QSharedPointer>
#include <QWidget>
class QGraphicsView;


class OpenableWidget : public QWidget
{
    // Widget that the CamCOPS main app knows how to open as a screen.

    Q_OBJECT
public:
    OpenableWidget(QWidget* parent = nullptr);
    virtual void build();  // opportunity to do stuff between creation and opening
    bool wantsFullscreen() const;
    void setWantsFullscreen(bool fullscreen = true);
    void setGraphicsViewAsOnlyContents(QGraphicsView* view,
                                       int margin = 0,
                                       bool fullscreen = true);
    bool escapeKeyCanAbort() const;
    void setEscapeKeyCanAbort(bool esc_can_abort,
                              bool without_confirmation = false);
    virtual void keyPressEvent(QKeyEvent* event) override;
signals:
    void aborting();
    void finished();
protected:
    bool m_wants_fullscreen;
    bool m_escape_key_can_abort;
    bool m_escape_aborts_without_confirmation;
};
