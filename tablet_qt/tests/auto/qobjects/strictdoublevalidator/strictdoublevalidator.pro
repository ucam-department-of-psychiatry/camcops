CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_strictdoublevalidator

SOURCES += \
    teststrictdoublevalidator.cpp \
    $$CAMCOPS_SRC/lib/numericfunc.cpp \
    $$CAMCOPS_SRC/qobjects/strictdoublevalidator.cpp


HEADERS += \
    $$CAMCOPS_SRC/lib/numericfunc.h \
    $$CAMCOPS_SRC/qobjects/strictdoublevalidator.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
