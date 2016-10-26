// #define DEBUG_LAYOUT

#include "labelwordwrapwide.h"
#ifdef DEBUG_LAYOUT
#include <QDebug>
#endif
#include <QFontMetrics>
#include <QStyle>
#include <QStyleOptionFrame>
#include "lib/uifunc.h"

// A QLabel, with setWordWrap(true), has a tendency to expand vertically and
// not use all the available horizontal space.
// ... Ah, no, that's the consequence of adjacent stretch.
// However, there is a sizing bug, fixed by this code:
// - https://bugreports.qt.io/browse/QTBUG-37673

// See also:
// - http://stackoverflow.com/questions/13995657/why-does-qlabel-prematurely-wrap
// - http://stackoverflow.com/questions/13994902/how-do-i-get-a-qlabel-to-expand-to-full-width#13994902
// - http://doc.qt.io/qt-5/layout.html#layout-issues
// - http://stackoverflow.com/questions/31535143/how-to-prevent-qlabel-from-unnecessary-word-wrapping
// - http://www.qtcentre.org/threads/62059-QLabel-Word-Wrapping-adds-unnecessary-line-breaks


LabelWordWrapWide::LabelWordWrapWide(const QString& text, QWidget* parent) :
    QLabel(text, parent)
{
    commonConstructor();
}


LabelWordWrapWide::LabelWordWrapWide(QWidget* parent) :
    QLabel(parent)
{
    commonConstructor();
}


void LabelWordWrapWide::commonConstructor()
{
    setSizePolicy(UiFunc::horizMaximumHFWPolicy());

    setWordWrap(true);  // will also do setHeightForWidth(true);

    // If the horizontal policy is Preferred (with vertical Minimum), then
    // the text tries to wrap (increasing height) when other things tell it
    // that it can. So Expanding/Minimum is better.
    // However, that does sometimes mean that the widget expands horizontally
    // when you don't want it to.

    // We were using vertical QSizePolicy::Minimum, and in resizeEvent setting
    // setMinimumHeight(); presumably if we use QSizePolicy::Fixed we should
    // use setFixedHeight().

    // Expanding = GrowFlag | ShrinkFlag | ExpandFlag
    // This is better than MinimumExpanding, because it is possible to squeeze
    // a label right down and still be OK.

    // Maximum = ShrinkFlag

    // setObjectName("debug_red");
}


void LabelWordWrapWide::resizeEvent(QResizeEvent* event)
{
    QLabel::resizeEvent(event);

    // We were making what follows conditional on:
    //     QSizePolicy::Policy vsp = sizePolicy().verticalPolicy();
    //     if (wordWrap() && (vsp == QSizePolicy::Minimum ||
    //                       vsp == QSizePolicy::Fixed)) { ...
    // ... but I'm not sure that's necessary.

    // heightForWidth relies on minimumSize to evaulate, so reset it...
    setMinimumHeight(0);
    // ... before defining minimum height:

    int w = width();  // will give the label TEXT width, I think
    int h = qMax(0, heightForWidth(w));
    // suspect heightForWidth(w) can give -1 with no text present

    // The heightForWidth() function, in qlabel.cpp,
    // works out (for a text label) a size, using sizeForWidth(),
    // then returns the height of that size.
    //
    // The complex bit is then in QLabelPrivate::sizeForWidth

    // qDebug() << Q_FUNC_INFO << "w" << w << "h" << h;

    setFixedHeight(h);
    updateGeometry();
}


// QLabel::sizeHint() produces a golden ratio, which is fine. If you want a
// LabelWordWrapWide to expand horizontally, set its horizontal size policy to
// include the ExpandFlag, and MAKE SURE YOU DON'T SPECIFY A HORIZONTAL
// ALIGNMENT.

// Except... we want to be able to use Maximum, not just Expanding, as a
// horizontal size policy. That means the widget will expand up to its
// sizeHint, but not further. And for that, its sizeHint shouldn't be the
// QLabel-preferred golden ratio, but the maximum possible width (with one
// line).
// (This is particularly important when using the wrapped text as a button;
// you don't want decorated buttons expanding to the width of the screen.)

QSize LabelWordWrapWide::sizeHint() const
{
    // Following the logic of QLabel::minimumSizeHint(), and
    // QLabelPrivate::sizeForWidth():

    // HEIGHT: easy
    int height = heightForWidth(QWIDGETSIZE_MAX);

    // WIDTH: harder?
    // - For the internal Qt macros like Q_D, see qglobal.h:
    //   #define Q_D(Class) Class##Private * const d = d_func()
    //      ... Q_D gives the class a pointer to its private-class member
    //   #define Q_Q(Class) Class * const q = q_func()
    //      ... Q_Q gives the private class a pointer to its public-class member
    // Ah, not that much harder.
    // - http://stackoverflow.com/questions/1337523/measuring-text-width-in-qt
    // Compare:
    // - http://doc.qt.io/qt-5.7/qfontmetrics.html#width
    // - http://doc.qt.io/qt-5.7/qfontmetrics.html#boundingRect
    // - http://stackoverflow.com/questions/37671839/how-to-use-qfontmetrics-boundingrect-to-measure-size-of-multilne-message
    QFontMetrics fm = fontMetrics();
    // int width = fm.width(text());
    int width = fm.boundingRect(QRect(0, 0, QWIDGETSIZE_MAX, QWIDGETSIZE_MAX),
                                0,  // definitely not Qt::TextWordWrap
                                text()).width();
    QSize text_size(width, height);
    QSize final_size;
#ifdef DEBUG_LAYOUT
    QSize stylesheet_extra_size(0, 0);
#endif

    // Needs adjustment for stylesheet?
    // - In the case of a label inside a pushbutton, the owner (the pushbutton)
    //   should do this.
    // - Can a QLabel have its own stylesheet info? Yes:
    //   http://doc.qt.io/qt-5.7/stylesheet-reference.html
    QStyleOptionFrame opt;
    initStyleOption(&opt);  // protected
    QStyle* mystyle = style();
    if (mystyle) {
        final_size = mystyle->sizeFromContents(QStyle::CT_PushButton, &opt,
                                               text_size, this);
        // Is QStyle::CT_PushButton right?
#ifdef DEBUG_LAYOUT
        stylesheet_extra_size = final_size - text_size;
#endif
    }

    // QSize size = QLabel::sizeHint();
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO << "text_size" << text_size
             << "plus stylesheet" << stylesheet_extra_size
             << "gives" << final_size
             << "for text" << text();
#endif
    return final_size;
}
