CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_useragentdialog

SOURCES += \
    testuseragentdialog.cpp \
    $$CAMCOPS_SRC/common/cssconst.cpp \
    $$CAMCOPS_SRC/common/platform.cpp \
    $$CAMCOPS_SRC/dialogs/useragentdialog.cpp \
    $$CAMCOPS_SRC/lib/css.cpp \
    $$CAMCOPS_SRC/lib/widgetfunc.cpp \
    $$CAMCOPS_SRC/qobjects/widgetpositioner.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/cssconst.h \
    $$CAMCOPS_SRC/common/platform.h \
    $$CAMCOPS_SRC/dialogs/useragentdialog.h \
    $$CAMCOPS_SRC/lib/css.h \
    $$CAMCOPS_SRC/lib/widgetfunc.h \
    $$CAMCOPS_SRC/qobjects/widgetpositioner.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
