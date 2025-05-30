CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_strictintvalidator

SOURCES += \
    teststrictintvalidator.cpp \
    $$CAMCOPS_SRC/lib/numericfunc.cpp \
    $$CAMCOPS_SRC/qobjects/strictintvalidator.cpp


HEADERS += \
    $$CAMCOPS_SRC/lib/numericfunc.h \
    $$CAMCOPS_SRC/qobjects/strictintvalidator.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
