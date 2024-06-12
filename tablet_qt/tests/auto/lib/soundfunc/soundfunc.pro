CONFIG += testcase
QT += multimedia
QT += network
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_soundfunc

SOURCES += \
    testsoundfunc.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/customtypes.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/soundfunc.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/maths/ccrandom.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp \
    $$CAMCOPS_SRC/whisker/whiskerapi.cpp \
    $$CAMCOPS_SRC/whisker/whiskerconnectionstate.cpp \
    $$CAMCOPS_SRC/whisker/whiskerconstants.cpp \
    $$CAMCOPS_SRC/whisker/whiskerinboundmessage.cpp \
    $$CAMCOPS_SRC/whisker/whiskeroutboundcommand.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/textconst.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/lib/convert.h \
    $$CAMCOPS_SRC/lib/customtypes.h \
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/soundfunc.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/maths/ccrandom.h \
    $$CAMCOPS_SRC/maths/mathfunc.h \
    $$CAMCOPS_SRC/whisker/whiskerapi.h \
    $$CAMCOPS_SRC/whisker/whiskerconnectionstate.h \
    $$CAMCOPS_SRC/whisker/whiskerconstants.h \
    $$CAMCOPS_SRC/whisker/whiskerinboundmessage.h \
    $$CAMCOPS_SRC/whisker/whiskeroutboundcommand.h

INCLUDEPATH += "$${QT_BASE_DIR}/eigen/eigen-$$EIGEN_VERSION"
INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
