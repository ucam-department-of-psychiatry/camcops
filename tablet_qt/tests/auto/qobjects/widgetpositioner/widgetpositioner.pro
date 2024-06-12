CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_widgetpositioner

SOURCES += \
    testwidgetpositioner.cpp \
    $$CAMCOPS_SRC/qobjects/widgetpositioner.cpp


HEADERS += \
    $$CAMCOPS_SRC/qobjects/widgetpositioner.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
