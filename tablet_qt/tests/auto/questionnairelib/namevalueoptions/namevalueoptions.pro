CONFIG += testcase
QT += testlib
QT += network
QT += widgets
QT -= gui

TARGET = bin/test_namevalueoptions

SOURCES += \
    testnamevalueoptions.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/customtypes.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/maths/ccrandom.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp \
    $$CAMCOPS_SRC/questionnairelib/namevalueoptions.cpp \
    $$CAMCOPS_SRC/questionnairelib/namevaluepair.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/textconst.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/lib/convert.h \
    $$CAMCOPS_SRC/lib/customtypes.h \
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/maths/ccrandom.h \
    $$CAMCOPS_SRC/maths/mathfunc.h \
    $$CAMCOPS_SRC/questionnairelib/namevalueoptions.h \
    $$CAMCOPS_SRC/questionnairelib/namevaluepair.h

INCLUDEPATH += "$${QT_BASE_DIR}/eigen/eigen-$$EIGEN_VERSION"
INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
