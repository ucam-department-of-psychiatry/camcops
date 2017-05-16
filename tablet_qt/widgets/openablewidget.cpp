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

// #define DEBUG_OPENABLE_WIDGET_LAYOUT  // Dumps layout when widget shown

#include "openablewidget.h"
#include <QGraphicsView>
#include <QKeyEvent>
#include <QVBoxLayout>
#include "lib/uifunc.h"
#include "lib/sizehelpers.h"
#ifdef DEBUG_OPENABLE_WIDGET_LAYOUT
#include "qobjects/showwatcher.h"
#endif


OpenableWidget::OpenableWidget(QWidget* parent) :
    QWidget(parent),
    m_wants_fullscreen(false),
    m_escape_key_can_abort(true),
    m_escape_aborts_without_confirmation(false)
{
#ifdef DEBUG_OPENABLE_WIDGET_LAYOUT
    ShowWatcher* showwatcher = new ShowWatcher(this, true);
    Q_UNUSED(showwatcher);
#endif
}


void OpenableWidget::build()
{
}


bool OpenableWidget::wantsFullscreen() const
{
    return m_wants_fullscreen;
}


void OpenableWidget::setWantsFullscreen(bool fullscreen)
{
    m_wants_fullscreen = fullscreen;
}


void OpenableWidget::setGraphicsViewAsOnlyContents(QGraphicsView* view,
                                                   int margin,
                                                   bool fullscreen)
{
    setWantsFullscreen(fullscreen);
    setEscapeKeyCanAbort(true, false);

    QVBoxLayout* layout = new QVBoxLayout(this);
    layout->setMargin(margin);
    layout->addWidget(view);
}


bool OpenableWidget::escapeKeyCanAbort() const
{
    return m_escape_key_can_abort;
}


void OpenableWidget::setEscapeKeyCanAbort(bool esc_can_abort,
                                          bool without_confirmation)
{
    m_escape_key_can_abort = esc_can_abort;
    m_escape_aborts_without_confirmation = without_confirmation;
}


void OpenableWidget::keyPressEvent(QKeyEvent* event)
{
    if (!event) {
        return;
    }
    if (event->key() == Qt::Key_Escape && event->type() == QEvent::KeyPress) {
        // Escape key pressed
        if (m_escape_key_can_abort) {
            if (m_escape_aborts_without_confirmation ||
                    uifunc::confirm(tr("Abort: are you sure?"),
                                    tr("Abort?"),
                                    "", "", this)) {
                // User confirms: abort
                emit finished();
            }
        }
    }
}
