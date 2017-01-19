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

// #define DEBUG_LAYOUT
#define UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS

#include "verticalscrollarea.h"
#include <QDebug>
#include <QEvent>
#include <QLayout>
#include <QScrollBar>
#include "lib/sizehelpers.h"
#include "widgets/margins.h"

const int MIN_HEIGHT = 100;

/*

Widget layout looks like this:

    .   VerticalScrollArea [widget]                     // this
    v       QWidget 'qt_scrollarea_viewport' [widget]   // viewport()
            ... Non-layout children:
                SomeWidget [widget]                     // widget()
        ... Non-layout children:
            QWidget 'qt_scrollarea_hcontainer' [widget] [HIDDEN]
                QBoxLayout [layout]
                    QScrollBar [widget]
    S       QWidget 'qt_scrollarea_vcontainer' [widget] // QAbstractScrollAreaScrollBarContainer
                QBoxLayout [layout]
                    QScrollBar [widget]                 // verticalScrollBar() -> QScrollBar* QAbstractScrollAreaPrivate::vbar

    .............................................................
    .                                                           .
    . vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv SSS .
    . vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv SSS .
    . vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv SSS .
    . vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv SSS .
    . vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv SSS .
    . vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv SSS .
    .                                                           .
    .............................................................

Typical values:

    . 810 x 118 @   0, 0        X extent   0-809    Y extent 0-117
    v 798 x 116 @   1, 1        X extent   1-798    Y extent 1-116
    S  10 x 116 @ 799, 1        X extent 799-808    Y extent 1-116

I was doing this:

    QRect viewport_rect = viewport()->geometry();
    QRect scrollarea_rect = geometry();
    Margins diffmargins = Margins::rectDiff(scrollarea_rect, viewport_rect);
    new_min_width += diffmargins.totalWidth();
    new_max_height += diffmargins.totalHeight();

and similar; but sometimes, e.g. in sizeHint(), scrollarea_rect doesn't
contain viewport_rect; e.g.

    scrollarea_rect -- outer QRect(0,2 802x119)
    viewport_rect   -- inner QRect(1,1 790x117)

Aha! The second isn't in the same coordinates; it's relative to the top.
So we want to use this instead:

    Margins::subRectMargins(scrollarea_rect, viewport_rect);

Sometimes the viewport is at (0,0) and is the same size as the scroll area,
so you have to check.

*/

VerticalScrollArea::VerticalScrollArea(QWidget* parent) :
    QScrollArea(parent),
    m_updating_geometry(false),
    m_last_widget_width(-1)
{
    setWidgetResizable(true);
    // ... definitely true! If false, you get a narrow strip of widgets
    // instead of them expanding to the full width.

    // Vertical scroll bar if required:
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);

    // RNC addition:
    // setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);
    // ... see notes at end
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    // ... even better, when also we set our maximum height upon widget resize?

    // NOT THIS: enlarges the scroll area rather than scrolling...
    // setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    // Do NOT make VerticalScrollArea height-for-width itself.
    // setSizePolicy(sizehelpers::expandingExpandingHFWPolicy());

    // NOT THIS: doesn't work
    // setSizePolicy(UiFunc::expandingMaximumHFWPolicy());

    setSizeAdjustPolicy(QAbstractScrollArea::AdjustToContents);
    // http://doc.qt.io/qt-5/qabstractscrollarea.html#SizeAdjustPolicy-enum
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
            // We must not call the parent event filter; that can also cause
            // an infinite loop, e.g. QScrollArea can call updateScrollBars()
            // which can trigger a widget resize, etc.
#ifdef DEBUG_LAYOUT
            qDebug() << Q_FUNC_INFO << "- preventing infinite loop";
#endif
            return false;
        }
#endif

        bool parent_result = QScrollArea::eventFilter(o, e);  // will call d->updateScrollBars();
        resetSizeLimits();
        // return false;  // DEFINITELY NEED THIS, NOT FALL-THROUGH TO PARENT
        return parent_result;  // or do we?

    } else {
        return QScrollArea::eventFilter(o, e);
    }
}


// RNC addition:
// Without this (and a vertical size policy of Maximum), it's very hard to
// get the scroll area to avoid one of the following:
// - expand too large vertically; distribute its contents vertically; thus
//   need an internal spacer at the end of its contents; thus have a duff
//   endpoint;
// - be too small vertically (e.g. if a spacer is put below it to prevent it
//   expanding too much) when there is vertical space available to use.
// So the answer is a Maximum(*) vertical size policy, and a size hint that is
// exactly that of its contents.
// (*) Or Expanding with an explicit maximum set.

QSize VerticalScrollArea::sizeHint() const
{
    // "Q. How big would you *like* to be?"
    // "A. The size my widget wants to be, so my scroll bars can disappear."
    // ... although we also have a small margin to deal with, even when
    // scrollbars have gone.
    QWidget* w = widget();
    if (!w) {
        return QSize();
    }

    // Work out best size for widget
    QSize sh = w->sizeHint();
    if (w->hasHeightForWidth()) {
        int likely_best_height;
        if (m_last_widget_width == -1) {
            // First time through
            int widget_preferred_width = sh.width();
            likely_best_height = w->heightForWidth(widget_preferred_width);
        } else {
            // The widget's not getting its preferred width, but we have an
            // idea of the width that it *is* getting.
            likely_best_height = w->heightForWidth(m_last_widget_width);
        }
        // int likely_width = widget_preferred_width - verticalScrollBar()->width();
        // int likely_best_height = w->heightForWidth(likely_width);
        sh.rheight() = likely_best_height;
    }

    // Correct for our margins
    QRect viewport_rect = viewport()->geometry();
    QRect scrollarea_rect = geometry();
    Margins marg = Margins::subRectMargins(scrollarea_rect, viewport_rect);
    sh.rheight() += marg.totalHeight();

#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO << "->" << sh;
#endif
    return sh;
}


void VerticalScrollArea::resetSizeLimits()
{
    // RNC: this code plus the Expanding policy.
    QWidget* w = widget();  // The contained widget being scrolled.
    if (!w) {
        return;
    }
    int widget_min_width = w->minimumSizeHint().width();
    int scrollbar_width = verticalScrollBar()->width();
    int new_min_width = widget_min_width + scrollbar_width;
    int widget_max_height = w->maximumHeight();
    int new_max_height;
#ifdef DEBUG_LAYOUT
    QString hfw_explanation;
#endif
    if (w->hasHeightForWidth()) {
        // It is quite likely that the widget is now a sensible width for us
        // without scroll bars - so when we add scroll bars, it'll get narrower
        // and thus taller. If we don't account for these, our scroll area will
        // often be a fraction too short vertically.
        int widget_width = w->geometry().width();
        m_last_widget_width = widget_width;
        int narrower_widget_width = widget_width - scrollbar_width;
        new_max_height = w->heightForWidth(narrower_widget_width);
#ifdef DEBUG_LAYOUT
        hfw_explanation = QString("widget's width %1 -> narrowed %2 -> HFW %3")
                .arg(widget_width)
                .arg(narrower_widget_width)
                .arg(new_max_height);
#endif
    } else {
        new_max_height = widget_max_height;
#ifdef DEBUG_LAYOUT
        hfw_explanation = QString("widget's maximum height is %1")
                .arg(widget_max_height);
#endif
    }

    // The only other odd bit is that VerticalScrollArea can position its
    // qt_scrollarea_viewport widget at e.g. pos (1, 1), not (0, 0), so our
    // maximum height is a little too small.
    // Basically, there is small boundary, as above.
    QRect viewport_rect = viewport()->geometry();
    QRect scrollarea_rect = geometry();
    Margins marg = Margins::subRectMargins(scrollarea_rect, viewport_rect);
    new_min_width += marg.totalWidth();
    new_max_height += marg.totalHeight();
    int new_min_height = qMin(w->minimumSizeHint().height(), MIN_HEIGHT);

#ifdef DEBUG_LAYOUT
    QMargins viewport_margins = viewportMargins();  // zero!
    qDebug().nospace().noquote()
            << Q_FUNC_INFO
            << " - Child widget resized to " << w->geometry()
            << "; setting VerticalScrollArea minimum width to "
            << new_min_width
            << " (" << widget_min_width << " for widget, "
            << scrollbar_width << " for scrollbar)"
            << "; setting minimum height to " << new_min_height
            << "; setting maximum height to " << new_max_height
            << " (" << hfw_explanation << ") ["
            << "viewport margins: " << viewport_margins << ", "
            << ", viewport_geometry: " << viewport_rect
            << ", scrollarea_geometry: " << scrollarea_rect
            << "]";
#endif

#ifdef UPDATE_GEOMETRY_FROM_EVENT_FILTER_POSSIBLY_DANGEROUS
    m_updating_geometry = true;  // guard round all the dangerous stuff

    // We're not doing horizontal scrolling, so we must be at least as wide
    // as our widget's minimum:
    setMinimumWidth(new_min_width);

    // We don't have a maximum width; we'll expand as required.

    // We do NOT allow our *minimum* height to be determined by the widget.
    // If the widget's minimum height is very big, well, we'll scroll.
    // If it's tiny, though, we'll respect it and not go bigger.
    setMinimumHeight(new_min_height);

    // We don't want to be any taller than the maximum space our widget wants
    // (plus our margins).
    setMaximumHeight(new_max_height);

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

    updateGeometry();
    // Do NOT attempt to invalidate the parent widget's layout here.

    m_updating_geometry = false;
#endif

    // PREVIOUS RESIDUAL PROBLEM:
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
}
