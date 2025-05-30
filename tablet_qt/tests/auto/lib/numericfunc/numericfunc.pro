CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_numericfunc

SOURCES += \
    testnumericfunc.cpp \
    $$CAMCOPS_SRC/lib/numericfunc.cpp


HEADERS += \
    $$CAMCOPS_SRC/lib/numericfunc.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
