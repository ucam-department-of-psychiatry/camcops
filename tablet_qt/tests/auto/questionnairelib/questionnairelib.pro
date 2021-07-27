CONFIG += testcase
QT += testlib
QT += network
QT += widgets
QT -= gui

TARGET = bin/test_questionnairelib

SOURCES += \
    testnamevalueoptions.cpp \
    $$PWD/../../../questionnairelib/namevalueoptions.cpp \
    $$PWD/../../../questionnairelib/namevaluepair.cpp

HEADERS += \
    $$PWD/../../../questionnairelib/namevalueoptions.h \
    $$PWD/../../../questionnairelib/namevaluepair.h

INCLUDEPATH += \
    $$PWD/../../../

DEFINES += SRCDIR=\\\"$$PWD/\\\"
