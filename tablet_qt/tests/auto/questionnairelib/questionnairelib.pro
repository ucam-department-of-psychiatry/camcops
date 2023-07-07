CONFIG += testcase
QT += testlib
QT += network
QT += widgets
QT -= gui

QT_BASE_DIR = $$(CAMCOPS_QT6_BASE_DIR)  # value at time of qmake ("now")
isEmpty(QT_BASE_DIR) {
    error("Environment variable CAMCOPS_QT6_BASE_DIR is undefined")
}

CAMCOPS_SRC = $$PWD/../../..

MOC_DIR = moc
OBJECTS_DIR = obj
TARGET = bin/test_questionnairelib

SOURCES += \
    testnamevalueoptions.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/maths/ccrandom.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp \
    $$CAMCOPS_SRC/questionnairelib/namevalueoptions.cpp \
    $$CAMCOPS_SRC/questionnairelib/namevaluepair.cpp \
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
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/maths/ccrandom.h \
    $$CAMCOPS_SRC/maths/mathfunc.h \
    $$CAMCOPS_SRC/questionnairelib/namevalueoptions.h \
    $$CAMCOPS_SRC/questionnairelib/namevaluepair.h \
    $$CAMCOPS_SRC/whisker/whiskerapi.h \
    $$CAMCOPS_SRC/whisker/whiskerconnectionstate.h \
    $$CAMCOPS_SRC/whisker/whiskerconstants.h \
    $$CAMCOPS_SRC/whisker/whiskerinboundmessage.h \
    $$CAMCOPS_SRC/whisker/whiskeroutboundcommand.h

INCLUDEPATH += "$${QT_BASE_DIR}/eigen/eigen-3.4.0"
INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
