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
#include <QPointer>
#include <QWidget>
#include "widgets/basewidget.h"
class QGraphicsView;


class OpenableWidget : public QWidget
{
    // Widget that the CamCOPS main app knows how to open as a screen.
    // - See CamcopsApp::open().
    // - Examples include MenuWindow, HtmlInfoWindow, and Questionnaire.
    // - Tasks that run plain graphics may use them directly; see e.g. QolSG,
    //   which uses a ScreenLikeGraphicsView in an OpenableWidget.
    // - It is also a widget in its own right, so you can nest them; an example
    //   is the IDED3D task, which has a Questionnaire config screen followed
    //   by a graphics view.

    Q_OBJECT
public:
    OpenableWidget(QWidget* parent = nullptr);
    virtual void build();  // opportunity to do stuff between creation and opening
    bool wantsFullscreen() const;
    void setWantsFullscreen(bool fullscreen = true);
    void setWidgetAsOnlyContents(QWidget* widget,
                                 int margin = 0,
                                 bool fullscreen = true,
                                 bool esc_can_abort = true);
    bool escapeKeyCanAbort() const;
    void setEscapeKeyCanAbort(bool esc_can_abort,
                              bool without_confirmation = false);
    virtual void resizeEvent(QResizeEvent* event) override;
    virtual void keyPressEvent(QKeyEvent* event) override;
signals:
    void aborting();
    void finished();
    void enterFullscreen();
    void leaveFullscreen();
protected:
    QPointer<QWidget> m_subwidget;
    bool m_wants_fullscreen;
    bool m_escape_key_can_abort;
    bool m_escape_aborts_without_confirmation;
};
