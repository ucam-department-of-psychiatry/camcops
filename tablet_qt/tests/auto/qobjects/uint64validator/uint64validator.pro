CONFIG += testcase
QT += testlib

TARGET = bin/test_uint64validator

SOURCES += \
    testuint64validator.cpp \
    $$CAMCOPS_SRC/qobjects/uint64validator.cpp


HEADERS += \
    $$CAMCOPS_SRC/qobjects/uint64validator.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
