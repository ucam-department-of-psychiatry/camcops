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
#define RESIZE_FOR_HFW  // define this for proper performance!
#define RESIZE_WITH_VANISHING_SCROLLBAR  // define this to look better

// One of these only:
// #define TOUCHSCROLL_DIRECT
#define TOUCHSCROLL_SCROLLER
// #define TOUCHSCROLL_FLICKCHARM

#include "verticalscrollarea.h"
#include <QDebug>
#include <QEvent>
#include <QLayout>
#include <QScrollBar>
#include <QScroller>
#include "common/widgetconst.h"
#include "lib/reentrydepthguard.h"
#include "lib/sizehelpers.h"
#include "lib/uifunc.h"
#include "widgets/margins.h"
#include "widgets/verticalscrollareaviewport.h"

#ifdef TOUCHSCROLL_DIRECT
#include <QGestureEvent>
#endif
#ifdef TOUCHSCROLL_FLICKCHARM
#include "widgets/flickcharm.h"
#endif

#if defined TOUCHSCROLL_DIRECT && (defined TOUCHSCROLL_SCROLLER || defined TOUCHSCROLL_FLICKCHARM)
#error #define only one touch scrolling method
#endif

#if defined TOUCHSCROLL_SCROLLER && (defined TOUCHSCROLL_DIRECT || defined TOUCHSCROLL_FLICKCHARM)
#error #define only one touch scrolling method
#endif

#if defined TOUCHSCROLL_FLICKCHARM && (defined TOUCHSCROLL_DIRECT || defined TOUCHSCROLL_SCROLLER)
#error #define only one touch scrolling method
#endif


const int SQUASH_DOWN_TO_HEIGHT = 100;

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

/*

Leftover problem: you can get this situation:

VerticalScrollArea<0x0000000004de0050 'questionnaire_background_clinician'>, visible, pos[DOWN] (0, 79), size[DOWN] (1920 x 649), hasHeightForWidth()[UP] false, heightForWidth(1920)[UP] -1, minimumSize (369 x 100), maximumSize (16777215 x 679), sizeHint[UP] (551 x 649), minimumSizeHint[UP] (57 x 57), sizePolicy[UP] (Expanding, Expanding) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"] [alignment from layout: <horizontal_none> | <vertical_none>]
    QWidget<0x00000000045e0750 'qt_scrollarea_viewport'>, visible, pos[DOWN] (0, 0), size[DOWN] (1904 x 649), hasHeightForWidth()[UP] false, heightForWidth(1904)[UP] -1, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (-1 x -1), minimumSizeHint[UP] (-1 x -1), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false
    ... Non-layout children of QWidget<0x00000000045e0750 'qt_scrollarea_viewport'>:
        BaseWidget<0x0000000003e87cb0 ''>, visible, pos[DOWN] (0, 0), size[DOWN] (1904 x 679), hasHeightForWidth()[UP] true, heightForWidth(1904)[UP] 649, minimumSize (0 x 0), maximumSize (16777215 x 16777215), sizeHint[UP] (535 x 679), minimumSizeHint[UP] (353 x 679), sizePolicy[UP] (Preferred, Preferred) [hasHeightForWidth=false], stylesheet: false, properties: [_q_styleSheetWidgetFont="Sans Serif,9,-1,5,50,0,0,0,0,0"]

i.e.

- the BaseWidget has HFW 1904 -> 649, but is given height 679 instead
  by the QScrollArea code, because that's its sizeHint().

Could we cope with that using setViewport(), using an HFW
widget rather than a plain widget? ***
Alternative would be to rewrite QScrollArea (and several parent classes)...

*/



VerticalScrollArea::VerticalScrollArea(QWidget* parent) :
    QScrollArea(parent),
    m_last_widget_width(-1),
    m_reentry_depth(0)
{
    // ------------------------------------------------------------------------
    // Viewport: change from the default
    // ------------------------------------------------------------------------
#ifdef RESIZE_FOR_HFW
    VerticalScrollAreaViewport* vp = new VerticalScrollAreaViewport();
    setViewport(vp);
#endif

    // ------------------------------------------------------------------------
    // Sizing
    // ------------------------------------------------------------------------
    setWidgetResizable(true);
    // ... definitely true! If false, you get a narrow strip of widgets
    // instead of them expanding to the full width.

    // Vertical scroll bar if required:
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
#ifdef RESIZE_WITH_VANISHING_SCROLLBAR
    setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
#else
    setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
#endif

#ifdef RESIZE_FOR_HFW
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
#else
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    setSizeAdjustPolicy(QAbstractScrollArea::AdjustIgnored);
#endif

    // ------------------------------------------------------------------------
    // For scroll-by-swipe:
    // ------------------------------------------------------------------------

#ifdef TOUCHSCROLL_DIRECT
    setAttribute(Qt::WA_AcceptTouchEvents);
    grabGesture(Qt::SwipeGesture);  // will arrive via event()

    // Note that mouse "gestures" are not supported. They can be manually
    // calculated/simulated; see
    // https://doc.qt.io/archives/qq/qq18-mousegestures.html
    // https://forum.qt.io/topic/27422/solved-qswipegesture-implementation-on-desktop/4
#endif

#ifdef TOUCHSCROLL_SCROLLER
    uifunc::applyScrollGestures(viewport());
#endif

#ifdef TOUCHSCROLL_FLICKCHARM
    // If that doesn't work, try
    FlickCharm charm;
    charm.activateOn(this);
#endif
}


bool VerticalScrollArea::event(QEvent* event)
{
#ifdef TOUCHSCROLL_DIRECT
    // http://doc.qt.io/qt-5.7/gestures-overview.html
    if (event->type() == QEvent::Gesture) {
        return gestureEvent(static_cast<QGestureEvent*>(event));
    }
#endif
    return QScrollArea::event(event);
}


bool VerticalScrollArea::gestureEvent(QGestureEvent* event)
{
#ifdef TOUCHSCROLL_DIRECT
    qDebug() << Q_FUNC_INFO;
    // http://doc.qt.io/qt-5.7/gestures-overview.html
    if (QGesture* swipe = event->gesture(Qt::SwipeGesture)) {
        swipeTriggered(static_cast<QSwipeGesture*>(swipe));
    }
#else
    Q_UNUSED(event);
#endif
    return true;
}


void VerticalScrollArea::swipeTriggered(QSwipeGesture* gesture)
{
#ifdef TOUCHSCROLL_DIRECT
    qDebug() << Q_FUNC_INFO;
    if (gesture->state() == Qt::GestureUpdated) {
        bool up = gesture->verticalDirection() == QSwipeGesture::Up;
        bool down = gesture->verticalDirection() == QSwipeGesture::Down;
        if (up || down) {
            int dy = 50;
            if (down) {
                dy = -dy;
            }
            scroll(0, dy);  // dx, dy
        }
    }
#else
    Q_UNUSED(gesture);
#endif
}


bool VerticalScrollArea::eventFilter(QObject* o, QEvent* e)
{
    // This deals with the "owned" widget changing size.

    // Return true for "I've dealt with it; nobody else should".
    // http://doc.qt.io/qt-5.7/eventsandfilters.html

    // We use eventFilter(), not event(), because we are looking for events on
    // the widget that we are scrolling, not our own widget.
    // This works because QScrollArea::setWidget installs an eventFilter on the
    // widget.

    if (o && o == widget() && e && e->type() == QEvent::Resize) {
#ifdef DEBUG_LAYOUT
        QWidget* w = dynamic_cast<QWidget*>(o);
        qDebug() << Q_FUNC_INFO << "- Child is resizing to" << w->geometry();
#endif

#ifdef RESIZE_FOR_HFW
        // --------------------------------------------------------------------
        // Prevent infinite recursion
        // --------------------------------------------------------------------
        if (m_reentry_depth >= widgetconst::SET_GEOMETRY_MAX_REENTRY_DEPTH) {
#ifdef DEBUG_LAYOUT
            qDebug() << Q_FUNC_INFO << "- ... recursion depth exceeded; ignoring";
#endif
            return false;
        }
        ReentryDepthGuard guard(m_reentry_depth);
        Q_UNUSED(guard);

        bool parent_result = QScrollArea::eventFilter(o, e);  // will call d->updateScrollBars();
        resetSizeLimits();
        return parent_result;
#else
        return QScrollArea::eventFilter(o, e);
#endif
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
    // "A. The size my widget wants to be (or is), so my scroll bars can
    //     disappear."
    // ... although we also have a small margin to deal with, even when
    // scrollbars have gone.
    QWidget* w = widget();
    if (!w) {
        return QSize();
    }

    // Work out best size for widget
    QSize sh = w->sizeHint();
    if (w->hasHeightForWidth()) {
        int widget_working_width;
        if (m_last_widget_width == -1) {
            // First time through
            int widget_preferred_width = sh.width();
            widget_working_width = widget_preferred_width;
        } else {
            // The widget's not (necessarily) getting its preferred width, but
            // we have an idea of the width that it *is* getting.
            widget_working_width = m_last_widget_width;
        }
        int likely_best_height = w->heightForWidth(widget_working_width);
        sh.rheight() = likely_best_height;
    }

#ifndef RESIZE_WITH_VANISHING_SCROLLBAR
    int scrollbar_width = verticalScrollBar()->width();
    sh.rwidth() += scrollbar_width;
#endif

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
    // We get here when our child widget resizes.

    // We use this code plus the Expanding policy.

    QWidget* w = widget();  // The contained widget being scrolled.
    if (!w) {
        return;
    }
    bool widget_has_hfw = w->hasHeightForWidth();

    QScrollBar* vsb = verticalScrollBar();
    if (!vsb) {
        qWarning() << "No vertical scrollbar!";
        return;
    }

    // The widget size coming here might be this (w widget, s scrollbar):
    //
    //      www  ss
    //      www  ss
    //      www  ss
    //      www  ss
    //
    // or this:
    //
    //      wwww
    //      wwww
    //      wwww
    //
    // Can we distinguish these?

    int scrollbar_width = vsb->width();
#ifdef DEBUG_LAYOUT
    int vsb_value = vsb->value();
    bool scrollbar_active = vsb_value != vsb->minimum() ||
            vsb_value != vsb->maximum();
    QString hfw_explanation = scrollbar_active ? "[scrollbar active] "
                                               : "[scrollbar inactive] ";
#endif

    // And: in this example, we want (I think) our minimum width to be 4,
    // which is either width + scrollbar (if present), or width (if absent),
    // ... for HFW widgets.

    int widget_min_width = qMax(0, w->minimumSizeHint().width());
    int new_min_width = widget_min_width;

    // Minimum height: if the widget is small, then the widget height (3 in
    // this example, i.e. without scrollbars), but if it's large, then
    // SQUASH_DOWN_TO_HEIGHT.
    //
    // Rephrased:
    // Vertically, the scroller can get as SMALL as the widget if that's less
    // than SQUASH_DOWN_TO_HEIGHT, but if the widget is bigger, the MINIMUM
    // size of the scroller can be something small, if the window is small,
    // i.e. SQUASH_DOWN_TO_HEIGHT.
    // But it's also possible that the widget's minimum height is -1, which
    // we'll translate to 0.
    int widget_min_height = w->minimumSizeHint().height();
    int new_min_height = qMin(qMax(0, widget_min_height),
                              SQUASH_DOWN_TO_HEIGHT);

    // Maximum height: that with scrollbars (4 in this example), for HFW
    // widgets.

    int widget_max_height = w->maximumHeight();
    int new_max_height;
    if (widget_has_hfw) {
        int widget_width = w->geometry().width();
        m_last_widget_width = widget_width;
        if (false) {
            // It is quite likely that the widget is now a sensible width for
            // us without scroll bars - so when we add scroll bars, it'll get
            // narrower and thus taller. If we don't account for these, our
            // scroll area will often be a fraction too short vertically.
            int narrower_widget_width = qMax(1, widget_width - scrollbar_width);
            new_max_height = w->heightForWidth(narrower_widget_width);
#ifdef DEBUG_LAYOUT
            hfw_explanation += QString("widget's width %1 -> narrowed %2 in case scrollbars added -> HFW %3")
                    .arg(widget_width)
                    .arg(narrower_widget_width)
                    .arg(new_max_height);
#endif
        } else {
            new_max_height = w->heightForWidth(widget_width);
#ifdef DEBUG_LAYOUT
            hfw_explanation += QString("widget's width %1 -> not narrowed -> max height remains %2")
                    .arg(widget_width)
                    .arg(new_max_height);
#endif
        }
    } else {
        new_max_height = widget_max_height;
#ifdef DEBUG_LAYOUT
        hfw_explanation += QString("widget's maximum height is %1")
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
            << " (" << hfw_explanation << ") "
            << "[viewport margins: " << viewport_margins
            << ", viewport_geometry: " << viewport_rect
            << ", scrollarea_geometry: " << scrollarea_rect
            << "]";
#endif

    // --------------------------------------------------------------------
    // Prevent infinite recursion
    // --------------------------------------------------------------------
    if (m_reentry_depth >= widgetconst::SET_GEOMETRY_MAX_REENTRY_DEPTH) {
        return;
    }
    ReentryDepthGuard guard(m_reentry_depth);
    Q_UNUSED(guard);

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
