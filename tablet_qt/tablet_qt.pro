#-------------------------------------------------
#
# Project created by QtCreator 2016-05-30T22:51:39
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = tablet_qt
TEMPLATE = app


SOURCES += main.cpp\
    menulib/menu_window.cpp \
    menu/main_menu.cpp \
    lib/uifunc.cpp \
    menulib/menu_item.cpp \
    common/gv.cpp

HEADERS  += \
    menulib/menu_window.h \
    menu/main_menu.h \
    menulib/menu_item.h \
    common/ui_constants.h \
    lib/uifunc.h \
    common/gv.h

CONFIG += mobility
MOBILITY = 

RESOURCES += \
    camcops.qrc

DISTFILES += \
    notes/qt_notes.txt

