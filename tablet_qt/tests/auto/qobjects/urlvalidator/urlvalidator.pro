CONFIG += testcase
QT += testlib

TARGET = bin/test_urlvalidator

SOURCES += \
    testurlvalidator.cpp \
    $$CAMCOPS_SRC/qobjects/urlvalidator.cpp

HEADERS += \
    $$CAMCOPS_SRC/qobjects/urlvalidator.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
