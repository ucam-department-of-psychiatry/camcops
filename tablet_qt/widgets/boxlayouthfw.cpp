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

// From qboxlayout.cpp:
/****************************************************************************
**
** Copyright (C) 2016 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the QtWidgets module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 3 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL3 included in the
** packaging of this file. Please review the following information to
** ensure the GNU Lesser General Public License version 3 requirements
** will be met: https://www.gnu.org/licenses/lgpl-3.0.html.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 2.0 or (at your option) the GNU General
** Public license version 3 or any later version approved by the KDE Free
** Qt Foundation. The licenses are as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL2 and LICENSE.GPL3
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-2.0.html and
** https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

// #define DEBUG_LAYOUT
// #define DISABLE_CACHING
// #define Q_OS_MAC  // for testing only, just to be sure it compiles OK...

#include "boxlayouthfw.h"
#include <QApplication>
#include <QDebug>
#include <QList>
#include <QSizePolicy>
#include <QSpacerItem>
#include <QStyle>
#include <QVector>
#include <QWidget>
#include "common/widgetconst.h"
#include "lib/reentrydepthguard.h"
#include "lib/sizehelpers.h"
#include "widgets/qtlayouthelpers.h"

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
#include "common/globals.h"  // for qHash(const QRect&)
#endif

using qtlayouthelpers::checkLayout;
using qtlayouthelpers::checkWidget;
using qtlayouthelpers::createSpacerItem;
using qtlayouthelpers::createWidgetItem;
using qtlayouthelpers::defaultRectOfWidth;
using qtlayouthelpers::qGeomCalc;
using qtlayouthelpers::qMaxExpCalc;
using qtlayouthelpers::qSmartSpacing;

/*

===============================================================================
RNC: what is the optimal way of doing height-for-width, in theory?
===============================================================================

(1) TRADE OFF HEIGHT AND WIDTH: WORD WRAPPING
    Let's consider a simple word-wrapping widget, which contains 5 "words",
    each 20 units wide and 5 units high, with no other spacing. The widget is
    happy with (w x h):
        100 x 5     all words on first line
         80 x 10    4 + 1, for two lines
         60 x 10    3 + 2, for two lines
         40 x 15    2 + 1 + 1, for three lines
         20 x 25    all words on separate lines, for five lines
    So it will have these parameters:
        minimum width 20            (minimum height 5 = heightForWidth(MAXIMUM width))
        maximum width 100           (maximum height 25 = heightForWidth(MINIMUM width))
        preferred (hint) width 100  (preferred height 5 = heightForWidth(preferred width))
        hasHeightForWidth() -> true
        heightForWidth() -> mapping as above, and any width values in between

    We want its containing layout, like the widget itself, to be able to say:
    "I'd like to be 100 x 5, but if you force me to be 20 wide, then I must be
    25 high."

(2) LOCK ASPECT RATIO
    This hypothetical widget wants to be in a 2:1 aspect ratio, and would
    like to be 100 x 50, but is happy being anything from 10-200 wide.
    So it will have these parameters:
        minimum width 10            (minimum height 5 = heightForWidth(MINIMUM width))
        maximum width 200           (maximum height 100 = heightForWidth(MAXIMUM width))
        preferred (hint) width 100  (preferred height 50 = heightForWidth(preferred width))
        hasHeightForWidth() -> true
        heightForWidth() -> mapping as above, and any width values in between

    Here, the widget is saying "I'd like to be 100 x 50, but if you force me
    to be 20 wide, then I must be 10 high."

What are the things to which a LAYOUT's size matters?

Well, firstly, other layouts. Layouts read the layout parameters of other
layouts just like they do widgets, through the QLayoutItem interface. So we
should try to achieve everything possible by implementing that interface on
our layout, e.g. sizeHint(), minimumSize(), maximumSize().

In a recursive fashion, the guarantee that we (as a layout) will be given an
appropriate height comes from the way that we give our children an appropriate
height, via setGeometry().

That applies to everything except top-level widgets (which own top-level
layouts).


===============================================================================
Robert Knight's blog
http://kdemonkey.blogspot.co.uk/2013/11/understanding-qwidget-layout-flow.html
===============================================================================

Thursday, November 21, 2013

Understanding the QWidget layout flow
-------------------------------------

When layouts in a UI are not behaving as expected or performance is poor, it
can be helpful to have a mental model of the layout process in order to know
where to start debugging.  For web browsers there are some good resources [1]
which provide a description of the process at different levels. The layout
documentation [2] for Qt describes the various layout facilities that are
available but I haven't found a detailed description of the flow, so this is
my attempt to explain what happens when a layout is triggered that ultimately
ends up with the widgets being resized and repositioned appropriately.

1.  A widget's contents are modified in some way that require a layout update.
    Such changes can include:

    -   Changes to the content of the widget (eg. the text in a label, content
        margins being altered)

    -   Changes to the sizePolicy() of the widget

    -   Changes to the layout() of the widget, such as new child widgets being
        added or removed

2.  The widget calls QWidget::updateGeometry() which then performs several      [RNC: QWidget::updateGeometry()]
    steps to trigger a layout:

    1.  It invalidates any cached size information for the QWidgetItem
        associated with the widget in the parent layout.                        [RNC: QWidgetPrivate::updateGeometry_helper()]

    2.  It recursively climbs up the widget tree (first to the parent widget,   [RNC: QLayout::invalidate()]
        then the grandparent and so on), invalidating that widget's layout. The [RNC: QLayout::update()]
        process stops when we reach a widget that is a top level window or
        doesn't have its own layout - we'll call this widget the top-level
        widget, though it might not actually be a window.

    3.  If the top-level widget is not yet visible, then the process stops and
        layout is deferred until the widget is due to be shown.                 [RNC: QLayout::update()]

    4.  If the top-level widget is shown, a LayoutRequest event is posted
        asynchronously to the top-level widget, so a layout will be performed
        on the next pass through the event loop.                                [RNC: QLayout::update()]

    5.  If multiple layout requests are posted to the same top-level widget
        during a pass through the event loop, they will get compressed into a
        single layout request. This is similar to the way that multiple
        QWidget::update() requests are compressed into a single paint event.

3.  The top-level widget receives the LayoutRequest event on the next pass      [RNC: QApplication::notify()]
    through the event loop. This can then be handled in one of two ways:

    1.  If the widget has a layout, the layout will intercept the LayoutRequest [RNC: QLayout::widgetEvent()]
        event using an event filter and handle it by calling
        QLayout::activate()

    2.  If the widget does not have a layout, it may handle the LayoutRequest   [RNC: if QWidget subclasses so desire]
        event itself and manually set the geometry of its children.

4.  When the layout is activated, it first sets the fixed, minimum and/or       [RNC: QLayout::activate()]
    maximum size constraints of the widget depending on
    QLayout::sizeConstraint(), using the values calculated by                   [RNC: AT THIS POINT, LAYOUT SIZE HINTS MUST BE CORRECT]
    QLayout::minimumSize(), maximumSize() and sizeHint(). These functions will
    recursively proceed down the layout tree to determine the constraints for
    each item and produce a final size constraint for the whole layout. This    [RNC: (1) -> QLayoutPrivate::doResize(), in qlayout.cpp]
    may or may not alter the current size of the widget.                        [RNC: (2) -> then QWidget::updateGeometry() for the widget that owns the layout]

5.  The layout is then asked to resize its contents to fit the current size of  [RNC: as above: QLayoutPrivate::doResize(), in qlayout.cpp]
    the widget using QLayout::setGeometry(widget->size()). The specific         [RNC: ... q->setGeometry(rect);]
    implementation of the layout - whether it is a box layout, grid layout or   [     = QLayout::setGeometry()]
    something else then lays out its child items to fit this new size.          [RNC: AT THIS POINT, LAYOUT IS TOLD ITS WIDTH]

6.  For each item in the layout, the QLayoutItem::setGeometry() implementation  [RNC: QLayoutItem::setGeometry()]
    will typically ask the item for various size parameters (minimum size,
    maximum size, size hint, height for width) and then decide upon a final
    size and position for the item. It will then invoke
    QLayoutItem::setGeometry() to update the position and size of the widget.

7.  If the layout item is itself a layout or a widget, steps 5-6 proceed        [... for widgets, overridden by QWidgetItem::setGeometry()]
    recursively down the tree, updating all of the items whose constraints have [... QWidget::setGeometry()]
    been modified.                                                              [... QWidgetPrivate::setGeometry_sys()]
                                                                                [... applies constraints, posts a QResizeEvent]
                                                                                [... i.e. drawing is deferred]

A layout update is an expensive operation, so there are a number of steps taken
to avoid unnecessary re-layouts:

-   Multiple layout update requests submitted in a single pass through the
    event loop are coalesced into a single update

-   Layout updates for widgets that are not visible and layouts that are not
    enabled are deferred until the widget is shown or the layout is re-enabled

-   The QLayoutItem::setGeometry() implementations will typically check whether
    the current and new geometry differ or whether they have been invalidated
    in some way before performing an update. This prunes parts of the widget
    tree from the layout process which have not been altered.

-   The QWidgetItem associated with a widget in a layout caches information
    which is expensive to calculate, such as sizeHint(). This cached data is
    then returned until the widget invalidates it using
    QWidget::updateGeometry()

Given this flow, there are a few things to bear in mind to avoid unexpected
behaviour:

-   Qt provides multiple ways to set constraints such as fixed and minimum
    sizes.

    -   Using QWidget::setFixedSize(), setMinimumSize() or setMaximumSize().
        This is simple and available whether you control the widget or not.

    -   Implementing the sizeHint() and minimumSizeHint() functions and using
        QWidget::setSizePolicy() to determine how these hints are handled by
        the layouts. If you control the widget, it is almost always preferable
        to use sizePolicy() together with the layout hints.

-   The layout management documentation suggests that handling LayoutRequest
    events in QWidget::event() is an alternative to implementing a custom
    layout. A potential problem with this is that LayoutRequest events are
    delivered asynchronously on the next pass through the event loop. If your
    widget is likely to update its own geometry in response to the
    LayoutRequest event then this can trigger layout flicker where several
    passes through the event loop occur before the layout process is fully
    finished. Each of the intermediate stages will flicker on screen briefly,
    as the event loop may process a paint event on each pass as well as the
    layout update, which looks poor. So if you need a custom layout,
    subclassing QLayout/QLayoutItem is the recommended approach unless you're
    sure that your widget will always be used as a top-level widget.

Posted by Robert Knight at 8:29 AM

[1] http://taligarsiel.com/Projects/howbrowserswork1.htm#Layout
[2] http://qt-project.org/doc/qt-4.8/layout.html


===============================================================================
When a widget is resized, what happens to its (child) layout?
===============================================================================

-   QLayout::widgetEvent(), which is protected and non-virtual, detects
    QEvent::Resize, QEvent::ChildRemoved, and QEvent::LayoutRequests.
    For a resize event, then unless the layout is already activated, it calls
    QLayoutPrivate::doResize(), which calls QLayout::setGeometry.
    Note that this does NOT by default invalidate the layout, as far as I can
    see.

-   It looks like this is done by QApplicationPrivate::notify_helper()
    [in qapplication.cpp] checking for any layout owned by any widget receiving
    an event, and sending that same event on to the layout via
    layout->widgetEvent(e).


===============================================================================
Thoughts within setGeometry()
===============================================================================

Once we've called qqGeomCalc, we know the distribution along the layout's
direction of interest. So, for HORIZONTAL layouts, we now know each widget's
width. That allows us then to go back and determine the layout's height...
But that doesn't help, because the layout's height is already set!
(In various forms, it's currently in r, cr, and s.)
So there's nothing else we can do here.

Can we trigger a layout resize here, though?
Logic would be:
- calculate final height based on children's heightForWidth()
- if our height is that, hoorah, and lay out our children
- if not, trigger a resize event that will come back here (having
  propagated any necessary changes to parents)
- ... but in that situation, don't bother to lay out children

We may have altered minimum_size / maximum_size / size_hint
within the array a, as above. Therefore we DO NOT use calcHfw() or
its results, which operate on the less constrained m_geom_array.

Is this really needed, though?

Well, yes, we are getting called here and saying things, for a
vertical layout, like "child 0 must be set to 610 pixels high,
because its minimum, maximum, and preferred height is 610, but
we only have 142 pixels of space for the layout, so qqGeomCalc is
saying 'call it 142, then'."

ATTEMPTED SOLUTION: the call to the parent widget's updateGeometry()
above.

That didn't work.

ANOTHER THOUGHT: if the width arriving at setGeometry() is the same as last
time, draw the widgets. If not, set the minimumSize() etc. according to the
width we've just received, then call invalidate (but in a way that doesn't
invalidate minimum size -- just calling the parent QLayout::invalidate()).

AT THE END OF setGeometry():
... the next bit is the critical bit that tells the widgets where to be, using
their own setGeometry() calls.
Note that for the direction of interest, it uses the "pos" and "size" elements
from QLayoutStruct, stored in a, copied from m_geom_array. For the
perpendicular direction, it uses the layout's overall dimension from s.
(Indirectly, the size of s will have been determined by the layout's
min/max/hint size.)

===============================================================================
Other notes
===============================================================================

QLAYOUTSIZE_MAX = INT_MAX / 256 / 16
    INT_MAX = __INT_MAX__ = 0x7FFFFFFF = 2,147,483,647
    => QLAYOUTSIZE_MAX = 524288

See also
- http://stackoverflow.com/questions/24264320/qt-layouts-keep-widget-aspect-ratio-while-resizing
- ? Google for "public qlayout" heightforwidth
- http://qt.shoutwiki.com/wiki/How_to_create_flexible_Portrait_-_Landscape_rotation_layout_in_Qt

- http://stackoverflow.com/questions/452333/how-to-maintain-widgets-aspect-ratio-in-qt/1160476#1160476
- http://thread.gmane.org/gmane.comp.lib.qt.general/18281

*/


// ============================================================================
// Ancillary structs/classes
// ============================================================================

struct BoxLayoutHfwItem
{
    BoxLayoutHfwItem(QLayoutItem* it, int stretch_ = 0) :
        item(it), stretch(stretch_), magic(false)
    {}
    ~BoxLayoutHfwItem() { delete item; }

    int hfw(int w)
    {
        if (item->hasHeightForWidth()) {
            return item->heightForWidth(w);
        } else {
            return item->sizeHint().height();
        }
    }
    int minhfw(int w)  // was mhfw
    {
        if (item->hasHeightForWidth()) {
            return item->heightForWidth(w);
        } else {
            return item->minimumSize().height();
        }
    }
    int maxhfw(int w)  // RNC
    {
        if (item->hasHeightForWidth()) {
            return item->heightForWidth(w);
        } else {
            return item->maximumSize().height();
        }
    }
    int hStretch()
    {
        if (stretch == 0 && item->widget()) {
            return item->widget()->sizePolicy().horizontalStretch();
        } else {
            return stretch;
        }
    }
    int vStretch()
    {
        if (stretch == 0 && item->widget()) {
            return item->widget()->sizePolicy().verticalStretch();
        } else {
            return stretch;
        }
    }

    QLayoutItem* item;
    int stretch;
    bool magic;
};


// ============================================================================
// Helper functions
// ============================================================================

static inline bool horz(BoxLayoutHfw::Direction dir)
{
    return dir == BoxLayoutHfw::RightToLeft || dir == BoxLayoutHfw::LeftToRight;
}


// ============================================================================
// BoxLayoutHfw
// ============================================================================

BoxLayoutHfw::BoxLayoutHfw(Direction dir, QWidget* parent) :
    QLayout(parent),
    m_dir(dir),
    m_spacing(-1),
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    m_width_last_size_constraints_based_on(-1),
    m_rect_for_next_size_constraints(qtlayouthelpers::QT_DEFAULT_RECT),
    // ... the framework always seems to ask about QRect(0,0 640x480), from
    // QWidgetPrivate::init()), so we may as well
    // anticipate it; this will mean that minimumSize() etc. trigger a geometry
    // calculation for 640x480 at first use
#else
    m_cached_hfw_width(-1),
#endif
    m_dirty(true),
    m_reentry_depth(0)
{
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    // setSizeConstraint(QLayout::SetMinAndMaxSize);

    // Without this, you are using QLayout::SetDefaultConstraint, which
    // constrains the widget's minimum size to our minimumSize() unless the
    // widget has its own minimumSize(). With those constraints, the following
    // can happen:
    // - QWidget checks out its default rectangle of 640x480.
    // - We say "for 640 wide, we need to be 112 high".
    // - The widget says "OK, have 800x112", and sizes itself thus.
    // - We say "ah, but for 800 wide, we need to be 84 high".
    // - The widget thinks "well, you're asking for 84 and you have 112, so
    //   you're sorted" and doesn't change its height.
    // - The net effect, for a vertical layout, is usually excess vertical
    //   space between items.
    //
    // If you use QLayout::SetMinAndMaxSize, then the widget will proceed
    // to resize itself to 800x84 next, and all's well.

    // HOWEVER, abandoned, as the owning widget still wasn't obeying
    // constraints resulting from our call to QLayout::activate() from
    // setGeometry(). Instead, we use the other trick of calling the parent's
    // setFixedHeight() and updateGeometry(), removing the need for this
    // constraint.
#endif
}


/*
    Destroys this box layout.
    The layout's widgets aren't destroyed.
*/
BoxLayoutHfw::~BoxLayoutHfw()
{
    deleteAll();
}


// ----------------------------------------------------------------------------
// Add/modify/remove components
// ----------------------------------------------------------------------------

QLayoutItem* BoxLayoutHfw::replaceAt(int index, QLayoutItem* item)
{
    if (!item) {
        return nullptr;
    }
    BoxLayoutHfwItem* b = m_list.value(index);
    if (!b) {
        return nullptr;
    }
    QLayoutItem* r = b->item;

    b->item = item;
    invalidate();
    return r;
}



void BoxLayoutHfw::deleteAll()
{
    while (!m_list.isEmpty()) {
        delete m_list.takeFirst();
    }
}


void BoxLayoutHfw::setSpacing(int spacing)
{
    m_spacing = spacing;
    invalidate();
}


void BoxLayoutHfw::addItem(QLayoutItem* item)
{
    BoxLayoutHfwItem* it = new BoxLayoutHfwItem(item);
    m_list.append(it);
    invalidate();
}


void BoxLayoutHfw::insertItem(int index, QLayoutItem* item)
{
    if (index < 0) {  // append
        index = m_list.count();
    }

    BoxLayoutHfwItem* it = new BoxLayoutHfwItem(item);
    m_list.insert(index, it);
    invalidate();
}


void BoxLayoutHfw::insertSpacing(int index, int size)
{
    if (index < 0) {  // append
        index = m_list.count();
    }

    QLayoutItem* b;
    if (horz(m_dir)) {
        b = createSpacerItem(this, size, 0,
                             QSizePolicy::Fixed, QSizePolicy::Minimum);
    } else {
        b = createSpacerItem(this, 0, size,
                             QSizePolicy::Minimum, QSizePolicy::Fixed);
    }

    try {
        BoxLayoutHfwItem* it = new BoxLayoutHfwItem(b);
        it->magic = true;
        m_list.insert(index, it);

    } catch (...) {
        delete b;
        throw;
    }
    invalidate();
}


void BoxLayoutHfw::insertStretch(int index, int stretch)
{
    if (index < 0) {  // append
        index = m_list.count();
    }

    QLayoutItem* b;
    if (horz(m_dir)) {
        b = createSpacerItem(this, 0, 0,
                             QSizePolicy::Expanding, QSizePolicy::Minimum);
    } else {
        b = createSpacerItem(this, 0, 0,
                             QSizePolicy::Minimum, QSizePolicy::Expanding);
    }

    BoxLayoutHfwItem* it = new BoxLayoutHfwItem(b, stretch);
    it->magic = true;
    m_list.insert(index, it);
    invalidate();
}


void BoxLayoutHfw::insertSpacerItem(int index, QSpacerItem* spacerItem)
{
    if (index < 0) {  // append
        index = m_list.count();
    }

    BoxLayoutHfwItem* it = new BoxLayoutHfwItem(spacerItem);
    it->magic = true;
    m_list.insert(index, it);
    invalidate();
}


void BoxLayoutHfw::insertLayout(int index, QLayout* layout, int stretch)
{
    if (!checkLayout(layout, this)) {
        return;
    }
    if (!adoptLayout(layout)) {
        return;
    }
    if (index < 0) {  // append
        index = m_list.count();
    }
    BoxLayoutHfwItem* it = new BoxLayoutHfwItem(layout, stretch);
    m_list.insert(index, it);
    invalidate();
}


void BoxLayoutHfw::insertWidget(int index, QWidget* widget, int stretch,
                                Qt::Alignment alignment)
{
    if (!checkWidget(widget, this)) {
        return;
    }
    addChildWidget(widget);
    if (index < 0) {  // append
        index = m_list.count();
    }
#if 0  // #ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    bool use_hfw_capable_item = true;
#else
    bool use_hfw_capable_item = false;
#endif
    QWidgetItem* b = createWidgetItem(this, widget, use_hfw_capable_item);
    b->setAlignment(alignment);

    BoxLayoutHfwItem* it;
    try {
        it = new BoxLayoutHfwItem(b, stretch);
    } catch (...) {
        delete b;
        throw;
    }

    try {
        m_list.insert(index, it);
    } catch (...) {
        delete it;
        throw;
    }
    invalidate();
}


void BoxLayoutHfw::addSpacing(int size)
{
    insertSpacing(-1, size);
}


void BoxLayoutHfw::addStretch(int stretch)
{
    insertStretch(-1, stretch);
}


void BoxLayoutHfw::addSpacerItem(QSpacerItem* spacer_item)
{
    insertSpacerItem(-1, spacer_item);
}


void BoxLayoutHfw::addWidget(QWidget* widget, int stretch,
                             Qt::Alignment alignment)
{
    insertWidget(-1, widget, stretch, alignment);
}


void BoxLayoutHfw::addLayout(QLayout* layout, int stretch)
{
    insertLayout(-1, layout, stretch);
}


void BoxLayoutHfw::addStrut(int size)
{
    QLayoutItem* b;
    if (horz(m_dir)) {
        b = createSpacerItem(this, 0, size,
                             QSizePolicy::Fixed, QSizePolicy::Minimum);
    } else {
        b = createSpacerItem(this, size, 0,
                             QSizePolicy::Minimum, QSizePolicy::Fixed);
    }

    BoxLayoutHfwItem* it = new BoxLayoutHfwItem(b);
    it->magic = true;
    m_list.append(it);
    invalidate();
}


bool BoxLayoutHfw::setStretchFactor(QWidget* widget, int stretch)
{
    if (!widget) {
        return false;
    }
    for (int i = 0; i < m_list.size(); ++i) {
        BoxLayoutHfwItem* box = m_list.at(i);
        if (box->item->widget() == widget) {
            box->stretch = stretch;
            invalidate();
            return true;
        }
    }
    return false;
}


bool BoxLayoutHfw::setStretchFactor(QLayout* layout, int stretch)
{
    for (int i = 0; i < m_list.size(); ++i) {
        BoxLayoutHfwItem* box = m_list.at(i);
        if (box->item->layout() == layout) {
            if (box->stretch != stretch) {
                box->stretch = stretch;
                invalidate();
            }
            return true;
        }
    }
    return false;
}


void BoxLayoutHfw::setStretch(int index, int stretch)
{
    if (index >= 0 && index < m_list.size()) {
        BoxLayoutHfwItem* box = m_list.at(index);
        if (box->stretch != stretch) {
            box->stretch = stretch;
            invalidate();
        }
    }
}


QLayoutItem* BoxLayoutHfw::takeAt(int index)
{
    if (index < 0 || index >= m_list.count()) {
        return nullptr;
    }
    BoxLayoutHfwItem* b = m_list.takeAt(index);
    QLayoutItem* item = b->item;
    b->item = nullptr;
    delete b;

    if (QLayout* l = item->layout()) {
        // sanity check in case the user passed something weird to QObject::setParent()
        if (l->parent() == this) {
            l->setParent(nullptr);
        }
    }

    invalidate();
    return item;
}


void BoxLayoutHfw::setDirection(Direction direction)
{
    if (m_dir == direction) {
        return;
    }
    if (horz(m_dir) != horz(direction)) {
        //swap around the spacers (the "magic" bits)
        //#### a bit yucky, knows too much.
        //#### probably best to add access functions to spacerItem
        //#### or even a QSpacerItem::flip()
        for (int i = 0; i < m_list.size(); ++i) {
            BoxLayoutHfwItem* box = m_list.at(i);
            if (box->magic) {
                QSpacerItem* sp = box->item->spacerItem();
                if (sp) {
                    if (sp->expandingDirections() == Qt::Orientations(0) /*No Direction*/) {
                        //spacing or strut
                        QSize s = sp->sizeHint();
                        sp->changeSize(s.height(), s.width(),
                            horz(direction) ? QSizePolicy::Fixed:QSizePolicy::Minimum,
                            horz(direction) ? QSizePolicy::Minimum:QSizePolicy::Fixed);

                    } else {
                        //stretch
                        if (horz(direction)) {
                            sp->changeSize(0, 0, QSizePolicy::Expanding,
                                           QSizePolicy::Minimum);
                        } else {
                            sp->changeSize(0, 0, QSizePolicy::Minimum,
                                           QSizePolicy::Expanding);
                        }
                    }
                }
            }
        }
    }
    m_dir = direction;
    invalidate();
}


// ----------------------------------------------------------------------------
// Other public information
// ----------------------------------------------------------------------------

int BoxLayoutHfw::spacing() const
{
    if (m_spacing >= 0) {
        return m_spacing;
    } else {
        return qSmartSpacing(this,
                             m_dir == LeftToRight || m_dir == RightToLeft
                                ? QStyle::PM_LayoutHorizontalSpacing
                                : QStyle::PM_LayoutVerticalSpacing);
    }
}


int BoxLayoutHfw::count() const
{
    return m_list.count();
}


QLayoutItem* BoxLayoutHfw::itemAt(int index) const
{
    return index >= 0 && index < m_list.count()
            ? m_list.at(index)->item
            : nullptr;
}


BoxLayoutHfw::Direction BoxLayoutHfw::direction() const
{
    return m_dir;
}


int BoxLayoutHfw::stretch(int index) const
{
    if (index >= 0 && index < m_list.size()) {
        return m_list.at(index)->stretch;
    }
    return -1;
}


// ----------------------------------------------------------------------------
// Internal information
// ----------------------------------------------------------------------------

BoxLayoutHfw::Direction BoxLayoutHfw::getVisualDir() const
{
    Direction visual_dir = m_dir;
    QWidget* parent = parentWidget();
    if (parent && parent->isRightToLeft()) {
        if (m_dir == LeftToRight) {
            visual_dir = RightToLeft;
        } else if (m_dir == RightToLeft) {
            visual_dir = LeftToRight;
        }
    }
    return visual_dir;
}


// ----------------------------------------------------------------------------
// Provide size information to owner
// ----------------------------------------------------------------------------

QSize BoxLayoutHfw::sizeHint() const
{
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    GeomInfo gi = getGeomInfo(m_rect_for_next_size_constraints);
    m_width_last_size_constraints_based_on = m_rect_for_next_size_constraints.width();
#else
    GeomInfo gi = getGeomInfo();
#endif
#ifdef DEBUG_LAYOUT
    qDebug().nospace() << Q_FUNC_INFO << " -> " << gi.m_size_hint
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
                       << " (based on notional width of "
                       << m_width_last_size_constraints_based_on << ")"
#endif
                          ;
#endif
    return gi.m_size_hint;
}


QSize BoxLayoutHfw::minimumSize() const
{
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    GeomInfo gi = getGeomInfo(m_rect_for_next_size_constraints);
    m_width_last_size_constraints_based_on = m_rect_for_next_size_constraints.width();
#else
    GeomInfo gi = getGeomInfo();
#endif
#ifdef DEBUG_LAYOUT
    qDebug().nospace() << Q_FUNC_INFO << " -> " << gi.m_min_size
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
                       << " (based on notional width of "
                       << m_width_last_size_constraints_based_on << ")"
#endif
                          ;
#endif
    return gi.m_min_size;
}


QSize BoxLayoutHfw::maximumSize() const
{
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    GeomInfo gi = getGeomInfo(m_rect_for_next_size_constraints);
    m_width_last_size_constraints_based_on = m_rect_for_next_size_constraints.width();
#else
    GeomInfo gi = getGeomInfo();
#endif
    QSize s = gi.m_max_size.boundedTo(QSize(QLAYOUTSIZE_MAX, QLAYOUTSIZE_MAX));
    if (alignment() & Qt::AlignHorizontal_Mask) {
        s.setWidth(QLAYOUTSIZE_MAX);
    }
    if (alignment() & Qt::AlignVertical_Mask) {
        s.setHeight(QLAYOUTSIZE_MAX);
    }
#ifdef DEBUG_LAYOUT
    qDebug().nospace() << Q_FUNC_INFO << " -> " << s
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
                       << " (based on notional width of "
                       << m_width_last_size_constraints_based_on << ")"
#endif
                          ;
#endif
    return s;
}


bool BoxLayoutHfw::hasHeightForWidth() const
{
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    GeomInfo gi = getGeomInfo(m_rect_for_next_size_constraints);
    // ... seems dumb to use geometry to ask that quest, but we have to have
    // calculated at least one geometry to know that we've checked our contents
    // since last invalidate(), so we may as well use the m_has_hfw from one of
    // the geometries

    // no need to set m_width_last_size_constraints_based_on here, though
#else
    GeomInfo gi = getGeomInfo();
#endif
    return gi.m_has_hfw;
}


int BoxLayoutHfw::heightForWidth(int w) const
{
    if (!hasHeightForWidth()) {
        return -1;
    }
    HfwInfo hfw_info = getHfwInfo(w);
    return hfw_info.hfw_height;
}


int BoxLayoutHfw::minimumHeightForWidth(int w) const
{
    if (!hasHeightForWidth()) {
        return -1;
    }
    HfwInfo hfw_info = getHfwInfo(w);
    return hfw_info.hfw_min_height;
}


Qt::Orientations BoxLayoutHfw::expandingDirections() const
{
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    GeomInfo gi = getGeomInfo(m_rect_for_next_size_constraints);
#else
    GeomInfo gi = getGeomInfo();
#endif
    // ... see hasHeightForWidth() for rationale
    return gi.m_expanding;
}


// ----------------------------------------------------------------------------
// The complex bit (1): layout - virtual functions
// ----------------------------------------------------------------------------

void BoxLayoutHfw::invalidate()
{
    // This will be called by the framework, via:
    //
    //      QLayout::activate()
    //      -> QLayout::activateRecursiveHelper()
    //      -> BoxLayoutHfw::invalidate()
    //
    //      MenuHeader::MenuHeader()
    //      -> QWidget::setLayout()
    //      -> BoxLayoutHfw::invalidate()
    //
    //      MenuHeader::MenuHeader()
    //      -> BoxLayoutHfw::addLayout()
    //      -> BoxLayoutHfw::insertLayout()
    //      -> BoxLayoutHfw::invalidate()
    //
    // and for widgets setting their style, etc.
    // There are many calls here before the layout even gets asked about its
    // geometry. So, should be FAST. Hence, use m_dirty.
    //                         ^^^^

    // ... so think twice before clearing m_cached_layout_width.
    // BUT ALSO will be called by the framework if our widgets (or their
    // children, etc.) call their updateGeometry() and have changed size.
    // So we do need to invalidate...
    // ... except not if we triggered it ourself.

    setDirty();
    QLayout::invalidate();
}


void BoxLayoutHfw::setGeometry(const QRect& initial_rect)
{
    // RNC: when this is called, it's too late to alter the layout's size;
    // the instruction is "this is your size; now lay out your children".

    // ------------------------------------------------------------------------
    // Prevent infinite recursion
    // ------------------------------------------------------------------------
    if (m_reentry_depth >= widgetconst::SET_GEOMETRY_MAX_REENTRY_DEPTH) {
        return;
    }
    ReentryDepthGuard guard(m_reentry_depth);
    Q_UNUSED(guard);

    // ------------------------------------------------------------------------
    // Initialize
    // ------------------------------------------------------------------------
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    QRect r = initial_rect;  // we may modify it, below
#else
    const QRect& r = initial_rect;  // just an alias
#endif

    // RNC: r is the overall rectangle for the layout

    // ------------------------------------------------------------------------
    // Announce
    // ------------------------------------------------------------------------
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif

    // ------------------------------------------------------------------------
    // Skip because nothing's changed?
    // ------------------------------------------------------------------------
#ifndef DISABLE_CACHING
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    bool geometry_previously_calculated = m_geom_cache.contains(r);
    if (geometry_previously_calculated && r == geometry()) {
#else
    if (!m_dirty && r == geometry()) {
#endif
        // Exactly the same geometry as last time, and we're all set up.
#ifdef DEBUG_LAYOUT
        qDebug() << "... nothing to do, for" << r;
#endif
        return;
    }
#endif

    // ------------------------------------------------------------------------
    // Recalculate geometry
    // ------------------------------------------------------------------------
    // So, if we're here, we've previously calculated the geometry,
    // but the new geometry doesn't match our current geometry(); this means
    // that we need to change geometry but we've already had a pass through
    // in which we've had a chance to notify our parent widget.

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    GeomInfo gi = getGeomInfo(r);
#else
    GeomInfo gi = getGeomInfo();
#endif

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    // This is the trickiest bit.
    // If you call QWidget::setFixedHeight(), do it *last* in this function,
    // because that can call back in. From bottom to top:
    //      BoxLayoutHfw::setGeometry
    //      QLayoutPrivate::doResize(QSize const&)
    //      QLayout::activate()
    //      QApplicationPrivate::notify_helper(QObject *, QEvent *)
    //      QApplication::notify(QObject *, QEvent *)
    //      QCoreApplication::notifyInternal2(QObject *, QEvent *)
    //      QWidgetPrivate::setGeometry_sys(int, int, int, int, bool)
    //      QWidget::resize(QSize const&)
    //      QWidget::setMaximumSize(int, int)
    //      QWidget::setFixedHeight(int)
    //      BoxLayoutHfw::setGeometry

    if (gi.m_has_hfw) {
        // Only if we have hfw can our size hints vary with width.
        if (r.width() != m_width_last_size_constraints_based_on) {
            // The width has changed since we last told our owning widget what
            // size we need to be.
            // This means that our minimum height (etc.) may be wrong. So we
            // need to invalidate the layout (at least partly).
#ifdef DEBUG_LAYOUT
            qDebug().nospace()
                    << "... resetting width hints, for " << r
                    << " (because width=" << r.width()
                    << " but last size constraints were based on width of "
                    << m_width_last_size_constraints_based_on << ")";
#endif
            m_rect_for_next_size_constraints = r;
            // QLayout::activate();  // not invalidate(); not activate()
        }
    }
    QWidget* parent = parentWidget();
    Margins parent_margins = Margins::getContentsMargins(parent);
    if (!parent) {
        qWarning() << Q_FUNC_INFO << "Layout has no parent widget";
    }
    int parent_new_height = getParentTargetHeight(parent, parent_margins, gi);
    if (parent_new_height != -1) {
        // We will, under these circumstances, call
        // parent->updateGeometry().

        // Note, however, that calling parent->updateGeometry() doesn't
        // necessarily trigger a call back to us here. So we must lay
        // out our children (or they can fail to be drawn), and we
        // should therefore lay them out where they *will* be once the
        // parent has changed its size.

        // Moreover, if we call parent->updateGeometry(), it must be
        // the LAST thing we do, as above.

        // So:
        r.setHeight(parent_new_height - parent_margins.totalHeight());  // change

        // Don't think we need to call gi = getGeomInfo(r) again,
        // as the width hasn't changed.
    }
#endif

    // ------------------------------------------------------------------------
    // Lay out children and call QLayout::setGeometry()
    // ------------------------------------------------------------------------
    QRect old_rect = geometry();
    QLayout::setGeometry(r);
    distribute(gi, r, old_rect);

    // ------------------------------------------------------------------------
    // Ask our parent to resize, if necessary
    // ------------------------------------------------------------------------
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    if (parent_new_height != -1) {
        bool change = !sizehelpers::fixedHeightEquals(parent,
                                                      parent_new_height);
        if (change) {
            parent->setFixedHeight(parent_new_height);  // RISK OF INFINITE RECURSION
            parent->updateGeometry();
        }
    }
#endif
}


int BoxLayoutHfw::getParentTargetHeight(QWidget* parent,
                                        const Margins& parent_margins,
                                        const GeomInfo& gi) const
{
    // Returns -1 if no change required.

    if (!parent || !gi.m_has_hfw) {
        return -1;
    }
    int parent_new_height = -1;

    // Remember we may also have a mix of hfw and non-hfw items; the
    // non-hfw may have min/max heights that differ.
    int target_min_height = gi.m_min_size.height();
    int target_max_height = gi.m_max_size.height();

    target_min_height += parent_margins.totalHeight();
    target_max_height += parent_margins.totalHeight();

    if (parent->geometry().height() < target_min_height) {
#ifdef DEBUG_LAYOUT
        qDebug().nospace()
                << "... will set parent height to " << target_min_height
                << " (was " << parent->geometry().height()
                << ", below our min of " << target_min_height
                << " [including parent margin height of "
                << parent_margins.totalHeight() << "])";
#endif
        parent_new_height = target_min_height;
    }
    if (parent->geometry().height() > target_max_height) {
#ifdef DEBUG_LAYOUT
        qDebug().nospace()
                << "... will set parent height to " << target_max_height
                << " (was " << parent->geometry().height()
                << ", above our max of " << target_max_height
                << " [including parent margin height of "
                << parent_margins.totalHeight() << "])";
#endif
        parent_new_height = target_max_height;
    }
    return parent_new_height;
}


void BoxLayoutHfw::distribute(const GeomInfo& gi,
                              const QRect& layout_rect, const QRect& old_rect)
{
    const QRect& r = layout_rect;  // alias
    QRect s = getContentsRect(layout_rect);

#ifdef DEBUG_LAYOUT
    qDebug().nospace() << "... called with layout rect " << layout_rect
                       << ", giving final rect for children of " << s;
#endif

    QVector<QLayoutStruct> a = gi.m_geom_array;
    int pos = horz(m_dir) ? s.x() : s.y();  // RNC: starting coordinate (left or top)
    int space = horz(m_dir) ? s.width() : s.height();  // RNC: extent (width or height)
    int n = a.count();

    // The idea here is that when we were asked "how big do you want to be",
    // we returned information from getGeomInfo() that encompassed the range
    // of sizes that our items would permit. However, now we're being asked
    // to lay the items out, and at that point, a height-for-width widget has
    // only one possible size, which is its heightForWidth(its width).
    // Anyway, this is the QVBoxLayout code, but it's equally true for our
    // modified layout... except that we also want to constrain the maximum
    // height.
    if (gi.m_has_hfw && !horz(m_dir)) {
        for (int i = 0; i < n; i++) {
            BoxLayoutHfwItem* box = m_list.at(i);
            if (box->item->hasHeightForWidth()) {
                int width = qBound(box->item->minimumSize().width(),
                                   s.width(),
                                   box->item->maximumSize().width());
                a[i].size_hint = a[i].minimum_size =
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
                        a[i].maximum_size =
#endif
                        box->item->heightForWidth(width);
            }
        }
    }

    qGeomCalc(a, 0, n, pos, space);

    Direction visual_dir = getVisualDir();
    bool reverse = (horz(visual_dir)
                    ? ((r.right() > old_rect.right()) != (visual_dir == RightToLeft))
                    : r.bottom() > old_rect.bottom());
    // ... RNC: this seems to be saying that for vertical layouts, at least,
    // then if the geometry is extending downwards (old_rect ending below
    // current), draw from the bottom up.
    QVector<QRect> childrects = getChildRects(s, a);
    for (int j = 0; j < n; j++) {
        int i = reverse ? (n - j - 1) : j;
        BoxLayoutHfwItem* box = m_list.at(i);
        const QRect& childrect = childrects.at(i);
        box->item->setGeometry(childrect);
        // RNC: NOTE that the rectangle can be TRANSFORMED by the time it
        // reaches a widget's resizeEvent(). The sequence of calls is:
        //      - QLayoutItem::setGeometry()
        //        overridden by QWidgetItem::setGeometry
        //      - QWidget::setGeometry()
        //      - QWidgetPrivate::setGeometry_sys()
        //        ... can apply min/max constraints
        //        ... posts a QResizeEvent
#ifdef DEBUG_LAYOUT
        qDebug() << "... item" << i
                 << "given setGeometry() instruction" << childrect;
#endif
    }

}


// ----------------------------------------------------------------------------
// The complex bit (2): layout - internal functions
// ----------------------------------------------------------------------------

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
BoxLayoutHfw::GeomInfo BoxLayoutHfw::getGeomInfo(const QRect& layout_rect) const
{
    if (m_dirty) {
        clearCaches();
    }
#ifndef DISABLE_CACHING
    if (m_geom_cache.contains(layout_rect)) {
        return m_geom_cache[layout_rect];
    }
#endif

    QRect s = getContentsRect(layout_rect);
    int layout_available_width = s.width();

#else
BoxLayoutHfw::GeomInfo BoxLayoutHfw::getGeomInfo() const
{
#ifndef DISABLE_CACHING
    if (!m_dirty) {
        return m_cached_geominfo;
    }
#endif
#endif

    // vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    // Start of main thinking

    GeomInfo gi;

    int maxw = horz(m_dir) ? 0 : QLAYOUTSIZE_MAX;  // layout maximum width
    int maxh = horz(m_dir) ? QLAYOUTSIZE_MAX : 0;  // layout maximum height
    int minw = 0;  // layout minimum width
    int minh = 0;  // layout minimum height
    int hintw = 0;  // layout preferred width
    int hinth = 0;  // layout preferred height

    bool horexp = false;
    bool verexp = false;

    gi.m_has_hfw = false;

    int n = m_list.count();
    gi.m_geom_array.clear();
    QVector<QLayoutStruct> a(n);  // RNC: extra Q

    QSizePolicy::ControlTypes control_types1;
    QSizePolicy::ControlTypes control_types2;
    int fixed_spacing = spacing();
    int previous_non_empty_index = -1;

    QStyle* style = nullptr;
    if (fixed_spacing < 0) {
        if (QWidget* pw = parentWidget()) {
            style = pw->style();
        }
    }

    for (int i = 0; i < n; i++) {
        BoxLayoutHfwItem* box = m_list.at(i);
        QSize item_min = box->item->minimumSize();
        QSize item_hint = box->item->sizeHint();  // RNC: was just "hint"
        QSize item_max = box->item->maximumSize();  // RNC: was just "max"
        Qt::Orientations expdir = box->item->expandingDirections();  // RNC: was just "exp"
        bool empty = box->item->isEmpty();
        bool ignore = empty && box->item->widget(); // ignore hidden widgets
        int spacing = 0;
        bool dummy = true;

        if (!empty) {
            if (fixed_spacing >= 0) {
                spacing = (previous_non_empty_index >= 0) ? fixed_spacing : 0;
                // RNC: ... we don't apply spacing above the first widget, but
                // above all its successors (as a vertical example)
#ifdef Q_OS_MAC
                // RNC: alters spacing for all but the first widget, somehow,
                // for vertical layouts
                if (!horz(m_dir) && previous_non_empty_index >= 0) {
                    BoxLayoutHfwItem* sibling = (
                                m_dir == BoxLayoutHfw::TopToBottom
                                ? box
                                : m_list.at(previous_non_empty_index));
                    if (sibling) {
                        QWidget* wid = sibling->item->widget();
                        if (wid) {
                            spacing = qMax(spacing, sibling->item->geometry().top() - wid->geometry().top());
                        }
                    }
                }
#endif
            } else {
                control_types1 = control_types2;
                control_types2 = box->item->controlTypes();
                if (previous_non_empty_index >= 0) {
                    QSizePolicy::ControlTypes actual1 = control_types1;
                    QSizePolicy::ControlTypes actual2 = control_types2;
                    if (m_dir == BoxLayoutHfw::RightToLeft ||
                            m_dir == BoxLayoutHfw::BottomToTop) {
                        qSwap(actual1, actual2);
                    }

                    if (style) {
                        spacing = style->combinedLayoutSpacing(
                                    actual1, actual2,
                                    horz(m_dir) ? Qt::Horizontal : Qt::Vertical,
                                    nullptr, parentWidget());
                        if (spacing < 0) {
                            spacing = 0;
                        }
                    }
                }
            }

            if (previous_non_empty_index >= 0) {
                a[previous_non_empty_index].spacing = spacing;
            }
            previous_non_empty_index = i;
        }

        if (horz(m_dir)) {
            // ----------------------------------------------------------------
            // HORIZONTAL
            // ----------------------------------------------------------------
            bool expand = (expdir & Qt::Horizontal || box->stretch > 0);
            horexp = horexp || expand;

            // Widths
            minw += spacing + item_min.width();
            hintw += spacing + item_hint.width();
            maxw += spacing + item_max.width();
            a[i].minimum_size = item_min.width();
            a[i].size_hint = item_hint.width();
            a[i].maximum_size = item_max.width();

            // Heights
            // ... standard height code from QBoxLayout
            // ... we will calculate the actual height below
            if (!ignore) {
                qMaxExpCalc(maxh, verexp, dummy,  // RNC: extra q; alters first three parameters (max, exp, empty)
                            item_max.height(), expdir & Qt::Vertical,
                            box->item->isEmpty());
            }
            minh = qMax(minh, item_min.height());
            hinth = qMax(hinth, item_hint.height());

            // Other
            a[i].expansive = expand;
            a[i].stretch = box->stretch ? box->stretch : box->hStretch();

        } else {
            // ----------------------------------------------------------------
            // VERTICAL
            // ----------------------------------------------------------------
            bool expand = (expdir & Qt::Vertical || box->stretch > 0);
            verexp = verexp || expand;

            // Widths
            if (!ignore) {
                qMaxExpCalc(maxw, horexp, dummy,  // RNC: extra q; alters first three parameters (max, exp, empty)
                            item_max.width(), expdir & Qt::Horizontal,
                            box->item->isEmpty());
            }
            minw = qMax(minw, item_min.width());
            hintw = qMax(hintw, item_hint.width());

            // Heights
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
            // Here we modify by saying "for your likely width, what is the
            // minimum/maximum height"? For a height-for-width item, all the
            // heights will be the same (see BoxLayoutHfwItem). For other
            // items, we will get the same results as the QBoxLayout code.
            int item_width = qBound(item_min.width(),
                                    layout_available_width,
                                    item_max.width());

            int minhfw = box->minhfw(item_width);
            int hfw = box->hfw(item_width);
            int maxhfw = box->maxhfw(item_width);
            minh += spacing + minhfw;
            hinth += spacing + hfw;
            maxh += spacing + maxhfw;
            a[i].minimum_size = minhfw;
            a[i].size_hint = hfw;
            a[i].maximum_size = maxhfw;
            // QLayoutStruct::sizeHint is in the direction of
            // layout travel, so vertical here.
#else
            minh += spacing + item_min.height();
            hinth += spacing + item_hint.height();
            maxh += spacing + item_max.height();
            a[i].minimum_size = item_min.height();
            a[i].size_hint = item_hint.height();
            a[i].maximum_size = item_max.height();
#endif

            // Other
            a[i].expansive = expand;
            a[i].stretch = box->stretch ? box->stretch : box->vStretch();
        }

        a[i].empty = empty;
        a[i].spacing = 0;   // might be initialized with a non-zero value in a later iteration
        gi.m_has_hfw = gi.m_has_hfw || box->item->hasHeightForWidth();
    }

    gi.m_geom_array = a;

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    // RNC extra: for horizontal layouts, redo the layout max/min/hint height
    // calculations now we can work out the widths of all items
    if (gi.m_has_hfw && horz(m_dir)) {
        // Create dummy layout using "a"
        int pos = s.x();
        int space = s.width();
        qGeomCalc(a, 0, n, pos, space);
        minh = 0;
        maxh = QLAYOUTSIZE_MAX;
        hinth = 0;
        for (int i = 0; i < n; ++i) {
            BoxLayoutHfwItem* box = m_list.at(i);
            Qt::Orientations expdir = box->item->expandingDirections();  // RNC: was just "exp"
            bool empty = box->item->isEmpty();
            // for QWidgetItem: return (wid->isHidden() && !wid->sizePolicy().retainSizeWhenHidden()) || wid->isWindow();
            bool ignore = empty && box->item->widget(); // ignore hidden widgets
            //  ... as opposed to hidden layouts?
            bool dummy = true;

            int item_width = a[i].size;  // already solved
            int hfw = box->hfw(item_width);
            int minhfw = box->minhfw(item_width);
            int maxhfw = box->maxhfw(item_width);
            // I'm not sure why QBoxLayout doesn't put the minh/hinth
            // calculations within the "if (!ignore)" test.
            minh = qMax(minh, minhfw);
            hinth = qMax(hinth, hfw);
            if (!ignore) {
                qMaxExpCalc(maxh, verexp, dummy,  // RNC: extra q; alters first three parameters (max, exp, empty)
                            maxhfw,
                            expdir & Qt::Vertical,
                            box->item->isEmpty());
            }
        }
    }
#endif

    gi.m_expanding = (Qt::Orientations) ((horexp ? Qt::Horizontal : 0)
                                         | (verexp ? Qt::Vertical : 0));

    gi.m_min_size = QSize(minw, minh);
    gi.m_max_size = QSize(maxw, maxh).expandedTo(gi.m_min_size);
    gi.m_size_hint = QSize(hintw, hinth).expandedTo(gi.m_min_size).boundedTo(gi.m_max_size);

    Margins effmarg = effectiveMargins();  // caches content/effective margins
    QSize extra = effmarg.totalSize();

    gi.m_min_size += extra;
    gi.m_max_size += extra;
    gi.m_size_hint += extra;

    // End of main thinking
    // ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
    qDebug().nospace()
            << "..."
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
             << " for rect " << layout_rect
#endif
             << " n " << n
             << " m_expanding " << gi.m_expanding
             << " m_min_size " << gi.m_min_size
             << " m_max_size " << gi.m_max_size
             << " m_size_hint " << gi.m_size_hint
             << " m_has_hfw " << gi.m_has_hfw
             << " (margins " << effmarg
             << "; m_dir " << m_dir << ")";
    for (int i = 0; i < n; ++i) {
        const QLayoutStruct& ls = a.at(i);
        qDebug().nospace() << "... item " << i << ": " << ls;
    }
#endif

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    m_geom_cache[layout_rect] = gi;
#else
    m_cached_geominfo = gi;
    m_dirty = false;
#endif
    return gi;
}


BoxLayoutHfw::HfwInfo BoxLayoutHfw::getHfwInfo(int layout_width) const
{
    int w = layout_width;  // name used in original
    // ... but original did the HFW calculations on the INNER width,
    // and we do it on the OUTER width here, so that we can be consistent
    // with getGeomInfo(), which uses the OUTER rect
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    if (m_dirty) {
        clearCaches();
    }
#ifndef DISABLE_CACHING
    if (m_hfw_cache.contains(w)) {
        return m_hfw_cache[w];
    }
#endif
#else
#ifndef DISABLE_CACHING
    if (w == m_cached_hfw_width) {
        return m_cached_hfwinfo;
    }
#endif
#endif

#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    // Find a precalculated GeomInfo with an appropriate width, or
    // calculate one using an arbitrary QRect of the same width.
    QHash<QRect, GeomInfo>::iterator it;
    GeomInfo gi;
    bool found = false;
    for (it = m_geom_cache.begin(); it != m_geom_cache.end(); ++it) {
        if (it.key().width() == w) {
            gi = it.value();
            found = true;
            break;
        }
    }
    if (!found) {
        gi = getGeomInfo(defaultRectOfWidth(w));
    }
#else
    GeomInfo gi = getGeomInfo();
#endif

    // vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    // Start of main thinking

    Margins effmarg = effectiveMargins();
    w -= effmarg.totalWidth();  // RNC; see above for notes and below for compensation

    QVector<QLayoutStruct>& a = gi.m_geom_array;
    int n = a.count();
    int h = 0;
    int mh = 0;

    Q_ASSERT(n == m_list.size());

#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif

    if (horz(m_dir)) {
        // RNC: HORIZONTAL: maximum of {value for each item}, for each of hfw() and mhfw()
        qtlayouthelpers::qGeomCalc(a, 0, n, 0, w);  // chain, start, count, pos, space
        for (int i = 0; i < n; i++) {
            BoxLayoutHfwItem* box = m_list.at(i);
            h = qMax(h, box->hfw(a.at(i).size));
            mh = qMax(mh, box->minhfw(a.at(i).size));
#ifdef DEBUG_LAYOUT
            qDebug() << "... horizontal, item" << i << "width" << a.at(i).size
                     << "taking h to" << h
                     << "and mh to" << mh;
#endif
        }
    } else {
        // RNC: VERTICAL: sum of value for each item, plus spacing, for each of hfw() and mhfw()
        for (int i = 0; i < n; ++i) {
            BoxLayoutHfwItem* box = m_list.at(i);
            int spacing = a.at(i).spacing;
            h += box->hfw(w);
            mh += box->minhfw(w);
            h += spacing;
            mh += spacing;
#ifdef DEBUG_LAYOUT
            qDebug() << "... vertical, item" << i << "width" << w
                     << "has hfw()" << box->hfw(w)
                     << "and minhfw()" << box->minhfw(w)
                     << "taking h to" << h
                     << "and mh to" << mh;
#endif
        }
    }

    HfwInfo hfwinfo;
    hfwinfo.hfw_height = h;
    hfwinfo.hfw_min_height = mh;

    // RNC: compensation back:
    hfwinfo.hfw_height += effmarg.totalHeight();
    hfwinfo.hfw_min_height += effmarg.totalHeight();

    // End of main thinking
    // ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#ifdef DEBUG_LAYOUT
    qDebug().nospace() << "... For layout (contents) width " << w << ":"
                       << " m_hfw_height " << hfwinfo.hfw_height
                       << " m_hfw_min_height " << hfwinfo.hfw_min_height;
#endif
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    m_hfw_cache[w] = hfwinfo;
#else
    m_cached_hfw_width = w;
    m_cached_hfwinfo = hfwinfo;
#endif
    return hfwinfo;
}


QRect BoxLayoutHfw::getContentsRect(const QRect& layout_rect) const
{
    // ... following code from QBoxLayout::setGeometry()
    const QRect& r = layout_rect;  // so variable names match QBoxLayout
    QRect cr = alignment() ? alignmentRect(r) : r;
    // RNC: ... if there is no alignment, cr is the same as r (meaning that we
    // fill our entire space), but if there is an alignment,  we alter our
    // rectangle; see http://doc.qt.io/qt-5/qlayout.html#alignmentRect

    // Margins effmarg = getEffectiveMargins();
    // QRect s(cr.x() + effmarg.left(), cr.y() + effmarg.top(),
    //         cr.width() - (effmarg.left() + effmarg.right()),
    //         cr.height() - (effmarg.top() + effmarg.bottom()));
    // return s;

    // RNC: s is cr with some margins trimmed off the edge, and looks to
    // be the proper working rectangle within which we'll lay out our
    // child widgets.
    // So, equivalently:
    return effectiveMargins().removeMarginsFrom(cr);
}


QVector<QRect> BoxLayoutHfw::getChildRects(
        const QRect& contents_rect,
        const QVector<QLayoutStruct>& a) const
{
    // following code from QBoxLayout::setGeometry()
    const QRect& s = contents_rect;
    int n = a.count();
    QVector<QRect> rects(n);
    Direction visual_dir = getVisualDir();
    for (int i = 0; i < n; ++i) {
        switch (visual_dir) {
        case LeftToRight:
            {
                rects[i] = QRect(
                    a.at(i).pos,  // left
                    s.y(),  // top
                    a.at(i).size,  // width
                    s.height()  // height [NB widget may e.g. align top or bottom within this]
                );
            }
            break;
        case RightToLeft:
            {
                rects[i] = QRect(
                    s.left() + s.right() - a.at(i).pos - a.at(i).size + 1,  // left
                    s.y(),  // top
                    a.at(i).size,  // width
                    s.height()  // height [NB widget may e.g. align top or bottom within this]
                );
            }
            break;
        case TopToBottom:
            rects[i] = QRect(s.x(),  // left
                             a.at(i).pos,  // top
                             s.width(),  // width
                             a.at(i).size);  // height
            // the "size" solution should equal height-for-width if applicable
            break;
        case BottomToTop:
            rects[i] = QRect(s.x(),  // left
                             s.top() + s.bottom() - a.at(i).pos - a.at(i).size + 1,  // top
                             s.width(),  // width
                             a.at(i).size);  // height
            // the "size" solution should equal height-for-width if applicable
            break;
        }
    }
    return rects;
}


// ----------------------------------------------------------------------------
// Margins
// ----------------------------------------------------------------------------

Margins BoxLayoutHfw::effectiveMargins() const
{
    // RNC: cache added, because we use this quite a lot, and (at least for
    // the #ifdef Q_OS_MAC) there's a bit of thinking involved.
#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    if (m_dirty) {
        clearCaches();
    }
#endif
    if (!m_effective_margins.isSet()) {
        Margins contents_margins = Margins::getContentsMargins(this);
        m_effective_margins = effectiveMargins(contents_margins);
    }
    return m_effective_margins;
}


/*
 The purpose of this function is to make sure that widgets are not laid out outside its layout.
 E.g. the layoutItemRect margins are only meant to take of the surrounding margins/spacings.
 However, if the margin is 0, it can easily cover the area of a widget above it.
*/
Margins BoxLayoutHfw::effectiveMargins(const Margins& contents_margins) const
{
    int l = contents_margins.left();
    int t = contents_margins.top();
    int r = contents_margins.right();
    int b = contents_margins.bottom();

#ifdef Q_OS_MAC
    // RNC: in the original left/top/right/bottom were pointers to receive
    // values, and tested to make calculation more efficient.
    bool left = true;
    bool top  = true;
    bool right = true;
    bool bottom = true;

    if (horz(m_dir)) {
        BoxLayoutHfwItem* left_box = 0;
        BoxLayoutHfwItem* right_box = 0;

        if (left || right) {
            left_box = m_list.value(0);
            right_box = m_list.value(m_list.count() - 1);
            if (m_dir == BoxLayoutHfw::RightToLeft) {
                qSwap(left_box, right_box);
            }

            int left_delta = 0;
            int right_delta = 0;
            if (left_box) {
                QLayoutItem* itm = left_box->item;
                if (QWidget* w = itm->widget()) {
                    left_delta = itm->geometry().left() - w->geometry().left();
                }
            }
            if (right_box) {
                QLayoutItem* itm = right_box->item;
                if (QWidget* w = itm->widget()) {
                    right_delta = w->geometry().right() - itm->geometry().right();
                }
            }
            QWidget* w = parentWidget();
            Qt::LayoutDirection layout_direction = w ? w->layoutDirection()
                                                     : QApplication::layoutDirection();
            if (layout_direction == Qt::RightToLeft) {
                qSwap(left_delta, right_delta);
            }

            l = qMax(l, left_delta);
            r = qMax(r, right_delta);
        }

        int count = top || bottom ? m_list.count() : 0;
        for (int i = 0; i < count; ++i) {
            BoxLayoutHfwItem* box = m_list.at(i);
            QLayoutItem* itm = box->item;
            QWidget* w = itm->widget();
            if (w) {
                QRect lir = itm->geometry();
                QRect wr = w->geometry();
                if (top) {
                    t = qMax(t, lir.top() - wr.top());
                }
                if (bottom) {
                    b = qMax(b, wr.bottom() - lir.bottom());
                }
            }
        }
    } else {    // vertical layout
        BoxLayoutHfwItem* top_box = 0;
        BoxLayoutHfwItem* bottom_box = 0;

        if (top || bottom) {
            top_box = m_list.value(0);
            bottom_box = m_list.value(m_list.count() - 1);
            if (m_dir == BoxLayoutHfw::BottomToTop) {
                qSwap(top_box, bottom_box);
            }

            if (top && top_box) {
                QLayoutItem* itm = top_box->item;
                QWidget* w = itm->widget();
                if (w) {
                    t = qMax(t, itm->geometry().top() - w->geometry().top());
                }
            }

            if (bottom && bottom_box) {
                QLayoutItem* itm = bottom_box->item;
                QWidget* w = itm->widget();
                if (w) {
                    b = qMax(b, w->geometry().bottom() - itm->geometry().bottom());
                }
            }
        }

        int count = left || right ? m_list.count() : 0;
        for (int i = 0; i < count; ++i) {
            BoxLayoutHfwItem* box = m_list.at(i);
            QLayoutItem* itm = box->item;
            QWidget* w = itm->widget();
            if (w) {
                QRect lir = itm->geometry();
                QRect wr = w->geometry();
                if (left) {
                    l = qMax(l, lir.left() - wr.left());
                }
                if (right) {
                    r = qMax(r, wr.right() - lir.right());
                }
            }
        }
    }
#endif
    return Margins(l, t, r, b);
}


// ----------------------------------------------------------------------------
// Cache management
// ----------------------------------------------------------------------------

inline void BoxLayoutHfw::setDirty()
{
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif
    m_dirty = true;
#ifndef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
    m_cached_hfw_width = -1;
    m_cached_hfwinfo = HfwInfo();
    m_effective_margins.clear();
#endif
}


#ifdef BOXLAYOUTHFW_ALTER_FROM_QBOXLAYOUT
void BoxLayoutHfw::clearCaches() const
{
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif
    m_hfw_cache.clear();
    m_geom_cache.clear();
    m_effective_margins.clear();
    m_width_last_size_constraints_based_on = -1;
    m_dirty = false;
}
#endif


// ============================================================================
// Bits from QLayoutPrivate
// ============================================================================
