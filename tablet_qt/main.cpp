#include "menu/main_menu.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MainMenu w;
    w.show();

    return a.exec();
}
