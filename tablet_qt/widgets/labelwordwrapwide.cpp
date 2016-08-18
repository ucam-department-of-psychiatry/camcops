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
    QLabel(text, parent)
{
    setWordWrap(true);
    QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Minimum);
    setSizePolicy(sp);
    setObjectName("debug_green"); // ***
}


void LabelWordWrapWide::resizeEvent(QResizeEvent* event)
{
    QLabel::resizeEvent(event);
    if (wordWrap() && sizePolicy().verticalPolicy() == QSizePolicy::Minimum) {
        // heightForWidth relies on minimumSize to evaulate, so reset it...
        setMinimumHeight(0);
        // ... before defining minimum height:
        setMinimumHeight(heightForWidth(width()));
    }
}
