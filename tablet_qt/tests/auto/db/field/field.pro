CONFIG += testcase
QT += network
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_field

SOURCES += \
    testfield.cpp \
    $$CAMCOPS_SRC/common/cssconst.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/db/field.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/css.cpp \
    $$CAMCOPS_SRC/lib/customtypes.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/filefunc.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/timerfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/lib/widgetfunc.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/cssconst.h \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/textconst.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/db/field.h \
    $$CAMCOPS_SRC/lib/convert.h \
    $$CAMCOPS_SRC/lib/css.h \
    $$CAMCOPS_SRC/lib/customtypes.h \
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/filefunc.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/timerfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/maths/mathfunc.h

INCLUDEPATH += "$${QT_BASE_DIR}/eigen/eigen-$$EIGEN_VERSION"
INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
