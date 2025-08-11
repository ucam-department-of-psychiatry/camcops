CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_int64validator

SOURCES += \
    testint64validator.cpp \
    $$CAMCOPS_SRC/qobjects/int64validator.cpp


HEADERS += \
    $$CAMCOPS_SRC/qobjects/int64validator.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
