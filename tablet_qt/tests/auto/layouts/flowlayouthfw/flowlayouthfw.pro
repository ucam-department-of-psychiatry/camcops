CONFIG += testcase
QT += network
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_flowlayouthfw

SOURCES += \
    testflowlayouthfw.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/layouts/flowlayouthfw.cpp \
    $$CAMCOPS_SRC/layouts/qtlayouthelpers.cpp \
    $$CAMCOPS_SRC/layouts/widgetitemhfw.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/customtypes.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/layoutdumper.cpp \
    $$CAMCOPS_SRC/lib/margins.cpp \
    $$CAMCOPS_SRC/lib/sizehelpers.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/preprocessor_aid.h \
    $$CAMCOPS_SRC/common/textconst.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/layouts/flowlayouthfw.h \
    $$CAMCOPS_SRC/layouts/qtlayouthelpers.h \
    $$CAMCOPS_SRC/layouts/widgetitemhfw.h \
    $$CAMCOPS_SRC/lib/convert.h \
    $$CAMCOPS_SRC/lib/customtypes.h \
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/layoutdumper.h \
    $$CAMCOPS_SRC/lib/margins.h \
    $$CAMCOPS_SRC/lib/sizehelpers.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/maths/mathfunc.h

INCLUDEPATH += "$${QT_BASE_DIR}/eigen/eigen-$$EIGEN_VERSION"
INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
