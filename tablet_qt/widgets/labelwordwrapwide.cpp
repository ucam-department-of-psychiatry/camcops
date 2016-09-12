#include "labelwordwrapwide.h"
#include <QDebug>


// A QLabel, with setWordWrap(true), has a tendency to expand vertically and
// not use all the available horizontal space.
// ... Ah, no, that's the consequence of adjacent stretch.
// However, there is a sizing bug, fixed by this code:
// - https://bugreports.qt.io/browse/QTBUG-37673

// See also:
// - http://stackoverflow.com/questions/13995657/why-does-qlabel-prematurely-wrap
// - http://stackoverflow.com/questions/13994902/how-do-i-get-a-qlabel-to-expand-to-full-width#13994902


LabelWordWrapWide::LabelWordWrapWide(const QString& text, QWidget* parent) :
    ClickableLabel(text, parent)
{
    setClickable(false);  // by default; change if you want
    setWordWrap(true);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Minimum);
    // If the horizontal policy if Preferred (with vertical Minimum), then
    // the text tries to wrap (increasing height) when other things tell it
    // that it can. So Expanding/Minimum is better.
    // However, that does sometimes mean that the widget expands horizontally
    // when you don't want it to.
    // setObjectName("debug_green");
}


void LabelWordWrapWide::resizeEvent(QResizeEvent* event)
{
    QLabel::resizeEvent(event);
    if (wordWrap() && sizePolicy().verticalPolicy() == QSizePolicy::Minimum) {
        // heightForWidth relies on minimumSize to evaulate, so reset it...
        setMinimumHeight(0);
        // ... before defining minimum height:
        int w = width();
        setMinimumHeight(qMax(0, heightForWidth(w)));
        // suspect heightForWidth(w) can give -1 with no text present

        // The heightForWidth() function, in qlabel.cpp,
        // works out (for a text label) a size, using sizeForWidth(),
        // then returns the height of that size.
        //
        // The complex bit is then in QLabelPrivate::sizeForWidth
    }
}
