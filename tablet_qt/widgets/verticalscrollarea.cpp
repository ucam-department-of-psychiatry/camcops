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

#define UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS
#include "verticalscrollarea.h"
#include <QDebug>
#include <QEvent>
#include <QScrollBar>


VerticalScrollArea::VerticalScrollArea(QWidget* parent) :
    QScrollArea(parent),
    m_updating_geometry(false)
{
    setWidgetResizable(true);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    // RNC addition:
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);

    setSizeAdjustPolicy(QAbstractScrollArea::AdjustToContents);
}


bool VerticalScrollArea::eventFilter(QObject* o, QEvent* e)
{
    // Return true for "I've dealt with it; nobody else should".
    // http://doc.qt.io/qt-5.7/eventsandfilters.html

    // This works because QScrollArea::setWidget installs an eventFilter on the
    // widget
    if (o && o == widget() && e && e->type() == QEvent::Resize) {

#ifdef UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS
        if (m_updating_geometry) {
            return false;
        }
#endif

        // RNC: HORIZONTAL: this plus the Expanding policy.
        setMinimumWidth(widget()->minimumSizeHint().width() +
                        verticalScrollBar()->width());

        // RNC:
        // qDebug().nospace()
        //         << "VerticalScrollArea::eventFilter [QEvent::Resize]"
        //         << "; minimumHeight(): " << minimumHeight()
        //         << "; minimumSizeHint(): " << minimumSizeHint()
        //         << "; size(): " << size()
        //         << "; sizeHint(): " << sizeHint()
        //         << "; widget()->size(): " << widget()->size()
        //         << "; widget()->sizeHint(): " << widget()->sizeHint();

        // If the scrollbox starts out small (because its contents are small),
        // and the contents grow, we will learn about it here -- and we need
        // to grow ourselves. When your sizeHint() changes, you should call
        // updateGeometry().

        // Except...
        // http://doc.qt.io/qt-5/qwidget.html
        // Warning: Calling setGeometry() inside resizeEvent() or moveEvent()
        // can lead to infinite recursion.
        // ... and we certainly had infinite recursion.
        // One way in which this can happen:
        // http://stackoverflow.com/questions/9503231/strange-behaviour-overriding-qwidgetresizeeventqresizeevent-event

#ifdef UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS
        m_updating_geometry = true;
        updateGeometry();
        m_updating_geometry = false;
        // even contained text scroll areas work without updateGeometry() on shrike
#endif

        return false;  // DEFINITELY NEED THIS, NOT FALL-THROUGH TO PARENT

        // RESIDUAL PROBLEM:
        // - On some machines (e.g. wombat, Linux), when a multiline text box
        //   within a smaller-than-full-screen VerticalScroll area grows, the
        //   VerticalScrollBox stays the same size but its scroll bar adapts
        //   to the contents. Not ideal.
        // - On other machines (e.g. shrike, Linux), the VerticalScrollArea
        //   also grows, until it needs to scroll. This is optimal.
        // - Adding an updateGeometry() call fixed the problem on wombat.
        // - However, it caused a crash via infinite recursion on shrike,
        //   because (I think) the VerticalScrollBar's updateGeometry() call
        //   triggered similar geometry updating in the contained widgets (esp.
        //   LabelWordWrapWide), which triggered an update for the
        //   VerticalScrollBar, which...
        // - So, better to be cosmetically imperfect than to crash.
        // - Not sure if this can be solved consistently and perfectly.
        // - Try a guard (m_updating_geometry) so it can only do this once.
        //   Works well on Wombat!
    } else {
        return QScrollArea::eventFilter(o, e);
    }
}


// RNC addition:
// VERTICAL.
// Without this (and a vertical size policy of Maximum), it's very hard to
// get the scroll area to avoid one of the following:
// - expand too large vertically; distribute its contents vertically; thus
//   need an internal spacer at the end of its contents; thus have a duff
//   endpoint;
// - be too small vertically (e.g. if a spacer is put below it to prevent it
//   expanding too much) when there is vertical space available to use.
// So the answer is a Maximum vertical size policy, and a size hint that is
// exactly that of its contents.

QSize VerticalScrollArea::sizeHint() const
{
    // qDebug() << Q_FUNC_INFO << widget()->sizeHint();
    return widget()->sizeHint();
}
