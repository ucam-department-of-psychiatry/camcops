/*
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

// #define DEBUG_OPENABLE_WIDGET_LAYOUT

#include "openablewidget.h"
#ifdef DEBUG_OPENABLE_WIDGET_LAYOUT
#include "qobjects/showwatcher.h"
#endif

OpenableWidget::OpenableWidget(QWidget* parent) :
    QWidget(parent),
    m_wants_fullscreen(false)
{
#ifdef DEBUG_OPENABLE_WIDGET_LAYOUT
    ShowWatcher* showwatcher = new ShowWatcher(this, true);
    Q_UNUSED(showwatcher);
#endif
}


void OpenableWidget::build()
{
}


bool OpenableWidget::wantsFullscreen()
{
    return m_wants_fullscreen;
}


void OpenableWidget::setWantsFullscreen(bool fullscreen)
{
    m_wants_fullscreen = fullscreen;
}
