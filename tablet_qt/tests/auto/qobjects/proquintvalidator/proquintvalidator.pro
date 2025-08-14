CONFIG += testcase
QT += testlib

TARGET = bin/test_proquintvalidator

SOURCES += \
    testproquintvalidator.cpp \
    $$CAMCOPS_SRC/qobjects/proquintvalidator.cpp

HEADERS += \
    $$CAMCOPS_SRC/qobjects/proquintvalidator.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
