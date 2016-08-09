// #define TEST_QT_BASIC

#ifdef TEST_QT_BASIC
#include <QApplication>  // for minimal_qt_app
#include <QPushButton>  // for minimal_qt_app
#endif
#include "common/camcops_app.h"


#ifdef TEST_QT_BASIC
int runMinimalQtAapp(int& argc, char *argv[])
{
    QApplication app(argc, argv);
    QPushButton button("Hello, world!");
    button.show();
    return app.exec();
}
#endif


int main(int argc, char *argv[])
{
    // NOTE: argc must be passed as a REFERENCE to int, or the app will
    // crash. See
    // https://bugreports.qt.io/browse/QTBUG-5637
    // http://doc.qt.io/qt-5/qapplication.html

#ifdef TEST_QT_BASIC
    // For when it all breaks!
    return runMinimalQtAapp(argc, argv);
#else
    CamcopsApp app(argc, argv);
    return app.run();
#endif
}
