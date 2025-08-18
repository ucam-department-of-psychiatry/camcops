CONFIG += testcase
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_urllineedit

RESOURCES += \
    $$CAMCOPS_SRC/test.qrc

SOURCES += \
    testurllineedit.cpp \
    $$CAMCOPS_SRC/common/cssconst.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/platform.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/lib/css.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/filefunc.cpp \
    $$CAMCOPS_SRC/lib/timerfunc.cpp \
    $$CAMCOPS_SRC/lib/widgetfunc.cpp \
    $$CAMCOPS_SRC/qobjects/focuswatcher.cpp \
    $$CAMCOPS_SRC/qobjects/urlvalidator.cpp \
    $$CAMCOPS_SRC/widgets/urllineedit.cpp \
    $$CAMCOPS_SRC/widgets/validatinglineedit.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/cssconst.h \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/platform.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/lib/css.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/filefunc.h \
    $$CAMCOPS_SRC/lib/timerfunc.h \
    $$CAMCOPS_SRC/lib/widgetfunc.h \
    $$CAMCOPS_SRC/qobjects/focuswatcher.h \
    $$CAMCOPS_SRC/qobjects/urlvalidator.h \
    $$CAMCOPS_SRC/widgets/urllineedit.h \
    $$CAMCOPS_SRC/widgets/validatinglineedit.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
