#include <QApplication>
#include "common/ui_constants.h"
#include "lib/filefunc.h"
#include "menu/main_menu.h"


int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    app.setStyleSheet(get_textfile_contents(CSS_CAMCOPS));
    MainMenu win;
    win.show();
    return app.exec();
}
