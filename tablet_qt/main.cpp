#define TEST_QT_BASIC

#ifdef TEST_QT_BASIC
#include <QApplication>  // for minimal_qt_app
#include <QPushButton>  // for minimal_qt_app
#endif
#include "common/camcops_app.h"

#ifdef TEST_QT_BASIC
int minimal_qt_app(int argc, char *argv[])
{
    QApplication app(argc, argv);

    QPushButton button("Hello, world!");
    button.show();

    return app.exec();
}
#endif


int main(int argc, char *argv[])
{
#ifdef TEST_QT_BASIC
    // For when it all breaks!
    return minimal_qt_app(argc, argv);
#else
    CamcopsApp app(argc, argv);
    return app.run();
#endif
}
