// main.cpp
// Attempt to demonstrate bug for https://bugreports.qt.io/browse/QTBUG-68012

#include <QDebug>
#include <QColor>
#include "other.h"

const QColor STATIC_NAME_INIT_MAIN_CPP("purple");  // may work, may fail
const QColor STATIC_NUMERIC_INIT(128, 0, 128);  // works

int main(int argc, char *argv[])
{
    Q_UNUSED(argc)
    Q_UNUSED(argv)

    const QColor AFTER_MAIN_BEGINS_NAME_INIT("purple");  // works

    qDebug() << "STATIC_NAME_INIT_MAIN_CPP" << STATIC_NAME_INIT_MAIN_CPP;
    qDebug() << "STATIC_NAME_INIT_OTHER_CPP" << STATIC_NAME_INIT_OTHER_CPP;
    qDebug() << "STATIC_NUMERIC_INIT" << STATIC_NUMERIC_INIT;
    qDebug() << "AFTER_MAIN_BEGINS_NAME_INIT" << AFTER_MAIN_BEGINS_NAME_INIT;
}


/*

Output when compiled with gcc 5.4.0 using Qt 5.10.0:

STATIC_NAME_INIT_MAIN_CPP QColor(ARGB 1, 0.501961, 0, 0.501961)
STATIC_NAME_INIT_OTHER_CPP QColor(ARGB 1, 0.501961, 0, 0.501961)
STATIC_NUMERIC_INIT QColor(ARGB 1, 0.501961, 0, 0.501961)
AFTER_MAIN_BEGINS_NAME_INIT QColor(ARGB 1, 0.501961, 0, 0.501961)

Output when compiled with Microsoft Visual Studio 2017 using Qt 5.10.1:

... can look like this, which looks fine:

STATIC_NAME_INIT_MAIN_CPP QColor(ARGB 1, 0.501961, 0, 0.501961)
STATIC_NAME_INIT_OTHER_CPP QColor(ARGB 1, 0.501961, 0, 0.501961)
STATIC_NUMERIC_INIT QColor(ARGB 1, 0.501961, 0, 0.501961)
AFTER_MAIN_BEGINS_NAME_INIT QColor(ARGB 1, 0.501961, 0, 0.501961)

... but with some combinations of object files (real example involved Qt
5.10.0, and many object files, but the same principle/structure) you can get
this:

STATIC_NAME_INIT_MAIN_CPP ?  // real example didn't have one in main()
STATIC_NAME_INIT_OTHER_CPP QColor(Invalid)  // <-- this is the problem
STATIC_NUMERIC_INIT QColor(ARGB 1, 0.501961, 0, 0.501961)
AFTER_MAIN_BEGINS_NAME_INIT QColor(ARGB 1, 0.501961, 0, 0.501961)

As I said, it's a slightly unpredictable bug that I think depends on the
compiler and some luck of the draw in terms of module static initialization
order.

*/

